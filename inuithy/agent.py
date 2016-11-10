"""Agent application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import string_write, INUITHY_TITLE,\
INUITHY_VERSION, INUITHY_CONFIG_PATH, CtrlCmd, INUITHY_TOPIC_TRAFFIC,\
INUITHY_TOPIC_CONFIG, INUITHYAGENT_CLIENT_ID, T_ADDR, T_HOST, T_NODE,\
T_CLIENTID, T_TID, T_TIMESLOT, T_DURATION, T_NODES, T_RECIPIENT,\
T_TRAFFIC_STATUS, T_MSG, T_CTRLCMD, TrafficStatus, T_TRAFFIC_TYPE,\
INUITHY_LOGCONFIG, INUITHY_TOPIC_COMMAND, TrafficType
from inuithy.util.helper import getpredefaddr
from inuithy.util.cmd_helper import pub_status, pub_heartbeat, pub_unregister, extract_payload
from inuithy.util.config_manager import create_inuithy_cfg
from inuithy.common.serial_adapter import SerialAdapter
from inuithy.common.traffic import TrafficExecutor
import paho.mqtt.client as mqtt
import logging.config as lconf
import threading as thrd
import socket
import logging
import sys

lconf.fileConfig(INUITHY_LOGCONFIG)

class Agent(object):
    """
    Message Flow:
                        heartbeat
        Agent -------------------------> Controller
                        command
        Agent <------------------------- Controller
                         config
        Agent <------------------------- Controller
                       newcontrller
        Agent <------------------------- Controller
                        traffic
        Agent <------------------------- Controller
                        response
        Agent -------------------------> Controller
                         status
        Agent -------------------------> Controller
                        unregister
        Agent -------------------------> Controller
    """
    __mutex = thrd.Lock()
    __mutex_msg = thrd.Lock()

    @property
    def clientid(self):
        """Message queue identifier for agent"""
        return self.__clientid
    @clientid.setter
    def clientid(self, val):
        pass

    @property
    def host(self):
        """Host that agent running on"""
        return self.__host
    @host.setter
    def host(self, val):
        pass

    @property
    def tcfg(self):
        """Inuithy configure"""
        return self.__inuithy_cfg
    @tcfg.setter
    def tcfg(self, val):
        pass

    @property
    def enable_heartbeat(self):
        """Indicate heartbeat enabled or disabled"""
        return self.__enable_heartbeat
    @enable_heartbeat.setter
    def enable_heartbeat(self):
        pass

    @property
    def addr2node(self):
        """Map node address to SerialNode"""
        return self.__addr2node
    @addr2node.setter
    def addr2node(self, val):
        pass

    @property
    def initialized(self):
        """Agent initialization state"""
        return self.__initialized
    @initialized.setter
    def initialized(self, val):
        if Agent.__mutex.acquire_lock():
            if not self.__initialized:
                self.__initialized = True
            Agent.__mutex.release()

    @staticmethod
    def on_connect(client, userdata, rc):
        """MQ connect event handler"""
        lgr.info(string_write(
            "MQ.Connection client:{} userdata:[{}] rc:{}",
            client, userdata, rc))

    @staticmethod
    def on_message(client, userdata, message):
        """MQ message event handler"""
#        lgr.info(string_write("MQ.Message: userdata:[{}]", userdata))
#        lgr.info(string_write("MQ.Message: message "+INUITHY_MQTTMSGFMT,
#            message.dup, message.info, message.mid, message.payload,
#            message.qos, message.retain, message.state, message.timestamp,
#            message.topic))
        try:
            userdata.topic_routes[message.topic](message)
#            thrd.Thread(target=userdata.topic_routes[message.topic], args=(message,)).start()
        except Exception as ex:
            msg = string_write("Exception on MQ message dispatching: {}", ex)
            lgr.error(msg)
            userdata.teardown(msg)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        """MQ disconnect event handler"""
        lgr.info(string_write(
            "MQ.Disconnection: client:{} userdata:[{}] rc:{}",
            client, userdata, rc))

    @staticmethod
    def on_log(client, userdata, level, buf):
        """MQ log event handler"""
        mqlog_map(lgr, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        """MQ publish event handler"""
        lgr.info(string_write(
            "MQ.Publish: client:{} userdata:[{}], mid:{}",
            client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        """MQ subscribe event handler"""
        lgr.info(string_write(
            "MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}",
            client, userdata, mid, granted_qos))

    def teardown(self, msg='Teardown'):
        try:
            if self.initialized:
                msg = string_write("{}:{}", self.clientid, msg)
                pub_status(self.__subscriber, self.tcfg.mqtt_qos, {T_MSG: msg})
                self.unregister()
                if self.__heartbeat is not None:
                    self.__heartbeat.stop()
                self.__sad.stop_nodes()
                self.__subscriber.disconnect()
                sys.exit()
        except Exception as ex:
            self.lgr.error(string_write("Exception on teardown: {}", ex))

    def __del__(self):
        pass

    def __str__(self):
        return string_write("clientid:[{}] host:[{}]", self.clientid, self.host)

    def heartbeat_routine(self):
        self.lgr.info(string_write("Heartbeat routine"))
        try:
            data = {
                T_CLIENTID: self.clientid,
                T_HOST:     self.host,
                T_NODES:    [str(node) for node in self.__sad.nodes]
            }
            pub_heartbeat(self.__subscriber, self.tcfg.mqtt_qos, data)
        except Exception as ex:
            self.lgr.info(string_write("Heartbeat exception:{}", ex))

    def register(self):
        """Register an agent to controller
        """
        self.lgr.info(string_write("Registering {}", self.clientid))
        self.heartbeat_routine()

    def unregister(self):
        """Unregister an agent from controller
        """
        self.lgr.info(string_write("Unregistering {}", self.clientid))
        try:
            pub_unregister(self.__subscriber, self.tcfg.mqtt_qos, self.clientid)
        except Exception as ex:
            self.lgr.error(string_write("Unregister failed: {}", ex))

    def create_mqtt_subscriber(self, host, port):
        """Create MQTT subscriber"""
        self.topic_routes = {
            INUITHY_TOPIC_COMMAND:  self.on_topic_command,
            INUITHY_TOPIC_CONFIG:   self.on_topic_config,
            INUITHY_TOPIC_TRAFFIC:  self.on_topic_traffic,
        }
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect = Agent.on_connect
        self.__subscriber.on_message = Agent.on_message
        self.__subscriber.on_disconnect = Agent.on_disconnect
#        self.__subscriber.on_log = Agent.on_log
#        self.__subscriber.on_publish = Agent.on_publish
#        self.__subscriber.on_subscribe = Agent.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_COMMAND, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_TRAFFIC, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_CONFIG, self.tcfg.mqtt_qos),
        ])
        self.ctrlcmd_routes = {
            CtrlCmd.NEW_CONTROLLER.name:               self.on_new_controller,
            CtrlCmd.AGENT_RESTART.name:                self.on_agent_restart,
            CtrlCmd.AGENT_STOP.name:                   self.on_agent_stop,
            CtrlCmd.AGENT_ENABLE_HEARTBEAT.name:       self.on_agent_enable_heartbeat,
            CtrlCmd.AGENT_DISABLE_HEARTBEAT.name:      self.on_agent_disable_heartbeat,
        }

    def get_clientid(self):
        """Generate client ID"""
        rd = ''
        if self.tcfg.enable_localdebug:
            from random import randint
            rd = string_write('-{}', hex(randint(1000000, 10000000))[2:])
        return string_write(INUITHYAGENT_CLIENT_ID, self.host+rd)

    def set_host(self):
        """Set agent host"""
        try:
            self.__host = getpredefaddr()
        except Exception as ex:
            self.lgr.error(string_write("Failed to get predefined static address: {}", ex))

        try: #FIXME
            if self.__host is None or len(self.__host) == 0:
                self.__host = '127.0.0.1'#socket.gethostname() #socket.gethostbyname(socket.gethostname())
        except Exception as ex:
            self.lgr.error(string_write("Failed to get host by name: {}", ex))

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        self.lgr.info(string_write("Do initialization"))
        try:
            self.__clientid = self.get_clientid()
            self.create_mqtt_subscriber(*self.tcfg.mqtt)
            self.__sad = SerialAdapter(self.__subscriber)
            self.initialized = True
        except Exception as ex:
            self.lgr.error(string_write("Failed to initialize: {}", ex))

    def __init__(self, cfgpath='config/inuithy.conf', lgr=None):
        if lgr is not None:
            self.lgr = lgr
        else:
            self.lgr = logging
        self.__initialized = False
        self.__enable_heartbeat = False
        self.__heartbeat = None
        self.__subscriber = None
        self.topic_routes = {}
        self.ctrlcmd_routes = {}
        self.__traffic_executors = []
        self.__inuithy_cfg = create_inuithy_cfg(cfgpath)
        self.set_host()
        self.__addr2node = {}
        if self.__inuithy_cfg.load() is False:
            self.lgr.error(string_write("Failed to load configure"))
        else:
            self.__do_init()

    def ctrlcmd_dispatch(self, command):
        """
        data = {
            T_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            T_CLIENTID: self.clientid,
            ...
        }
        """
        self.lgr.info(string_write("Receive command [{}]", command))
        ctrlcmd = command.get(T_CTRLCMD)
        self.lgr.debug(command)
        try:
            if self.ctrlcmd_routes.get(ctrlcmd):
                self.ctrlcmd_routes[ctrlcmd](command)
            else:
                self.lgr.error(string_write(\
                'Invalid command [{}]', command))
        except Exception as ex:
            self.lgr.error(string_write(\
                'Exception on handling command [{}]:{}',
                command, str(ex)))

    def addr_to_node(self):
        """Map node address to SerialNode"""
        self.lgr.info("Map address to node")
        if not self.tcfg.enable_localdebug:
            [self.__addr2node.__setitem__(n.addr, n) for n in self.__sad.nodes]
            return
#       import random, string
#       [self.__addr2node.__setitem__(''.join([random.choice(string.hexdigits)\
#           for i in range(4)]), n) for n in self.__sad.nodes]
        samples = [
                    '1101', '1102', '1103', '1104',
                    '1111', '1112', '1113', '1114',
                    '1121', '1122', '1123', '1124',
                    '1131', '1132', '1133', '1134',
                    '1141', '1142', '1143', '1144',
                    '1151', '1152', '1153', '1154',
                    '1161', '1162', '1163', '1164',
                    '1172', '1173', '1174', '1134',
                    '1181', '1181', '1182', '1183',
                    '1191', '1192', '1193', '1194',
                    '11a1', '11a2', '11a3', '11a4',
                    '11b1', '11b2', '11b3', '11b4',
                    '11c1', '11c2', '11c3', '11c4',
                    '11d1', '11d2', '11d3', '11d4',
                    '11e1', '11e2', '11e3', '11e4',
                    '11f1', '11f2', '11f3', '11f4',
                ]
        [self.__addr2node.__setitem__(addr, n) for addr, n in zip(samples, self.__sad.nodes)]
        [n.__setattr__(T_ADDR, addr) for addr, n in zip(samples, self.__sad.nodes)]
        [str(n) for n in self.__sad.nodes]

    def start(self):
        """Start Agent routine"""
        if not self.initialized:
            self.lgr.error(string_write("Agent not initialized"))
            return
        status_msg = 'Agent fine'
        try:
            self.lgr.info(string_write("Starting Agent {}", self.clientid))
            self.__sad.scan_nodes()
            self.lgr.info(string_write("Connected nodes: [{}]", self.__sad.nodes))
            self.addr_to_node()
            self.register()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            status_msg = string_write("Agent received keyboard interrupt")
            self.lgr.error(status_msg)
        except NameError as ex:
            self.lgr.error(string_write("ERR: {}", ex))
        except Exception as ex:
            status_msg = string_write("Exception on Agent: {}", ex)
            self.lgr.error(status_msg)
        finally:
            self.teardown(status_msg)
            self.lgr.info(string_write("Agent terminated"))

    def on_topic_command(self, message):
        """Topic command handler"""
        self.lgr.info(string_write("On topic command"))
        msg = extract_payload(message.payload)
        try:
            self.ctrlcmd_dispatch(msg)
        except Exception as ex:
            self.lgr.error(string_write("Exception on dispating control command: {}", ex))

    def on_topic_config(self, message):
        """Topic config handler"""
        self.lgr.info(string_write("On topic config"))
        try:
            # TODO
            pass
        except Exception as ex:
            self.lgr.error(string_write("Exception on updating config: {}", ex))

    def on_traffic_join(self, data):
        """Traffic join command handler"""
        self.lgr.info(string_write("Join request"))
        naddr = data[T_NODE]
        node = self.addr2node.get(naddr)
        self.lgr.debug(string_write("Found node: {}", node))
        data[T_CLIENTID] = self.clientid
        data[T_HOST] = self.host
        if node is not None:
            node.join(data)
        else: # DEBUG
            self.lgr.error(string_write("{}: Node [{}] not found", self.clientid, naddr))

    def on_traffic_scmd(self, data):
        """
        data = {
             T_GENID:        tg.genid,
             T_DURATION:     tg.duration,
             T_TIMESLOT:     tg.timeslot,
             T_SENDER:       tr.sender,
             T_RECIPIENT:    tr.recipient,
             T_PKGSIZE:      tr.pkgsize,
             }
        """
        self.lgr.info(string_write("SCMD request"))
        naddr = data.get(T_NODE)
        node = self.addr2node.get(naddr)
        if None != node:
            self.lgr.debug(string_write("Found node: {}", node))
            data[T_CLIENTID] = self.clientid
            data[T_HOST] = self.host
            cmd = node.prot.traffic(data[T_RECIPIENT])
            report = {
                T_GENID: data.get(T_GENID),
                T_TRAFFIC_TYPE: data.get(T_TRAFFIC_TYPE),
                T_NODE: data.get(T_NODE),
                T_HOST: self.host,
                T_CLIENTID: self.clientid,
                T_SENDER: data.get(T_SENDER),
                T_RECIPIENT: data.get(T_RECIPIENT),
                T_PKGSIZE: data.get(T_PKGSIZE),
            }
            te = TrafficExecutor(node, cmd, data[T_TIMESLOT], data[T_DURATION], report)
            self.__traffic_executors.append(te)
            pub_status(self.__subscriber, self.tcfg.mqtt_qos, {
                T_TRAFFIC_STATUS:   TrafficStatus.REGISTERED.name,
                T_CLIENTID:         self.clientid,
                T_TID:              data.get(T_TID),
            })
        else:
            self.lgr.error(string_write("{}: Node [{}] not found", self.clientid, naddr))

    def on_traffic_tsh(self, data):
        """
        data = {
            T_TRAFFIC_TYPE: TrafficType.TSH.name,
            T_HOST:         host,
            T_NODE:         node,
            T_CLIENTID:     self.__ctrl.host2aid[args[0]],
            T_MSG:          ' '.join(args[1:])
        }
        """
        self.lgr.info(string_write("TSH request"))
        naddr = data[T_NODE]
        node = self.addr2node.get(naddr)
        if node is not None:
            self.lgr.debug(string_write("Found node: {}", node))
            node.write(data[T_MSG])
        else: # DEBUG
            self.lgr.error(string_write("{}: Node [{}] not found", self.clientid, naddr))

    def on_traffic_start(self, data):
        """Traffic start command handler"""
        self.lgr.info(string_write("Traffic start request"))
        try:
            for te in self.__traffic_executors:
                self.lgr.debug(string_write("agent:{}, te:{}", self.clientid, te))
                te.run()
#            [te.run() for te in self.__traffic_executors]
            pub_status(self.__subscriber, self.tcfg.mqtt_qos, {
                T_TRAFFIC_STATUS: TrafficStatus.FINISHED.name,
                T_CLIENTID:       self.clientid,
            })
        except Exception as ex:
            self.lgr.error(string_write("Exception on running traffic: {}", ex))

    def on_topic_traffic(self, message):
        """Traffic topic handler"""
        self.lgr.info(string_write("On topic traffic"))
        try:
            data = extract_payload(message.payload)
#           target = data[T_CLIENTID]
            self.lgr.debug(string_write("Traffic data: {}", data))
            if not self.is_msg_for_me([data.get(T_CLIENTID), data.get(T_HOST)]):
                return
            self.traffic_dispatch(data)
        except Exception as ex:
            self.lgr.error(string_write("Failed on handling traffic request: {}", ex))

    def traffic_dispatch(self, data):
        """Dispatch traffic topic handlers"""
        self.lgr.info(string_write("Dispatch traffic request: {}", data))
        if data[T_TRAFFIC_TYPE] == TrafficType.JOIN.name:
            self.on_traffic_join(data)
        elif data[T_TRAFFIC_TYPE] == TrafficType.SCMD.name:
            self.on_traffic_scmd(data)
        elif data[T_TRAFFIC_TYPE] == TrafficType.START.name:
            self.on_traffic_start(data)
        elif data[T_TRAFFIC_TYPE] == TrafficType.TSH.name:
            self.on_traffic_tsh(data)
        else:
            self.lgr.error(string_write("{}: Unhandled traffic message [{}]", self.clientid, data))

    def on_new_controller(self, message):
        """New controller command handler"""
        self.lgr.info(string_write("New controller"))
        self.register()

    def on_agent_restart(self, message):
        """Agent restart command handler"""
        self.lgr.info(string_write("Restart agent"))
        if self.is_msg_for_me([message.get(T_CLIENTID), message.get(T_HOST)]):
            self.lgr.info(string_write("Stop agent {}", self.clientid))
            self.teardown()
            #TODO

    def is_msg_for_me(self, targets): # FIXME
        """Determine message is for me"""
        for target in targets:
            if target in ['*', self.__host, self.__clientid]: return True
        return False

    def on_agent_stop(self, message):
        """Agent stop command handler"""
        self.lgr.info(string_write("On agent stop {}", message))
        if self.is_msg_for_me([message.get(T_CLIENTID)]):
            self.lgr.info(string_write("Stop agent {}", self.clientid))
            self.teardown()

    def on_agent_enable_heartbeat(self, message):
        """Heartbeat enable command handler"""
        self.lgr.info(string_write("Enable heartbeat"))
        self.__enable_heartbeat = True
        self.__heartbeat = Heartbeat(target=self.heartbeat_routine, name="AgnetHeartbeat")
        self.__heartbeat.run()

    def on_agent_disable_heartbeat(self, message):
        """Heartbeat disable command handler"""
        self.lgr.info(string_write("Disable heartbeat"))
        self.__enable_heartbeat = False
        self.__heartbeat.exit()

def start_agent(cfgpath, lgr=None):
    """Shortcut to start an Agent"""
    agent = Agent(cfgpath, lgr)
    agent.start()

if __name__ == '__main__':
    lgr = logging.getLogger("InuithyAgent")
    lgr.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Agent"))
    start_agent(INUITHY_CONFIG_PATH, lgr)

