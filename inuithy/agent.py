## Agent application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, logging, string, random
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
from inuithy.util.cmd_helper import *
from inuithy.util.config_manager import *
from inuithy.common.serial_adapter import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyAgent')

class Agent:
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
    __mutex     = thrd.Lock()
    __mutex_msg = thrd.Lock()

    @property
    def clientid(self):
        return self.__clientid
    
    @clientid.setter
    def clientid(self, val):
        pass
    
    @property
    def host(self):
        return self.__host

    @host.setter
    def host(self, val):
        pass

    @property
    def traffic(self):
        return self.__traffic

    @traffic.setter
    def traffic(self, val):
        pass

    @property
    def tcfg(self):
        return self.__inuithy_cfg

    @tcfg.setter
    def tcfg(self, val):
        pass
    
#    @property
#    def enable_heartbeat(self):
#        return self.__enable_heartbeat
#
#    @enable_heartbeat.setter
#    def enable_heartbeat(self):
#        pass

    @property
    def initialized(self):
        return self.__initialized

    @initialized.setter
    def initialized(self, val):
        if Agent.__mutex.acquire_lock():
            if not self.__initialized:
                self.__initialized = True
            Agent.__mutex.release()

    @property
    def addr2node(self):
        return self.__addr2node

    @addr2node.setter
    def addr2node(self, val):
        pass

    @staticmethod
    def on_connect(client, userdata, rc):
        logger.info(string_write("MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))

    @staticmethod
    def on_message(client, userdata, message):
#        logger.info(string_write("MQ.Message: userdata:[{}]", userdata))
#        logger.info(string_write("MQ.Message: message "+INUITHY_MQTTMSGFMT, 
#            message.dup, message.info, message.mid, message.payload, 
#            message.qos, message.retain, message.state, message.timestamp,
#            message.topic))
        try:
#            userdata.topic_routes[message.topic](message)
            thrd.Thread(target=userdata.topic_routes[message.topic], args=(message,)).start()
        except Exception as ex:
            msg = string_write("Exception on MQ message dispatching: {}", ex)
            logger.error(msg)
            userdata.teardown(msg)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        logger.info(string_write("MQ.Disconnection: client:{} userdata:[{}] rc:{}", client, userdata, rc))

    @staticmethod
    def on_log(client, userdata, level, buf):
        mqlog_map(logger, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        logger.info(string_write("MQ.Publish: client:{} userdata:[{}], mid:{}", client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        logger.info(string_write("MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}", client, userdata, mid, granted_qos))

    def teardown(self, msg=''):
        try:
            if self.initialized:
                pub_status(self.__subscriber, self.tcfg.mqtt_qos, {CFGKW_MSG: msg})
                self.unregister()
#               self.__heartbeat.stop()
                self.__sad.stop_nodes()
                self.__subscriber.disconnect()
        except Exception as ex:
            logger.error(string_write("Exception on teardown: {}", ex))

    def __del__(self):
        pass

    def __str__(self):
        return string_write("clientid:[{}] host:[{}]", self.clientid, self.host)
   
    def heartbeat_route(self):
        logger.info(string_write("Heartbeat route")) 
        try:
            data = {
                CFGKW_CLIENTID: self.clientid,
                CFGKW_HOST:     self.host,
                CFGKW_NODES:    [str(node) for node in self.__sad.nodes]
            }
            pub_heartbeat(self.__subscriber, self.tcfg.mqtt_qos, data)
        except Exception as ex:
            logger.info(string_write("Heartbeat exception:{}", ex)) 

    def register(self):
        """Register an agent to controller
        """
        logger.info(string_write("Registering {}", self.clientid))
#        self.__heartbeat = Heartbeat(target=self.heartbeat_route, name="AgnetHeartbeat")
#        self.__heartbeat.run()
        self.heartbeat_route()

    def unregister(self):
        """Unregister an agent from controller
        """
        logger.info(string_write("Unregistering {}", self.clientid))
        try:
            pub_unregister(self.__subscriber, self.tcfg.mqtt_qos, self.clientid)
        except Exception as ex:
            logger.error(string_write("Unregister failed: {}", ex))

    def create_subscriber(self, host, port):
        self.topic_routes = {
            INUITHY_TOPIC_COMMAND:  self.on_topic_command,
            INUITHY_TOPIC_CONFIG:   self.on_topic_config,
            INUITHY_TOPIC_TRAFFIC:  self.on_topic_traffic,
        }
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect    = Agent.on_connect
        self.__subscriber.on_message    = Agent.on_message
        self.__subscriber.on_disconnect = Agent.on_disconnect
        self.__subscriber.on_log        = Agent.on_log
#        self.__subscriber.on_publish    = Agent.on_publish
        self.__subscriber.on_subscribe  = Agent.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_COMMAND, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_TRAFFIC, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_CONFIG,  self.tcfg.mqtt_qos),
        ])
        self.ctrlcmd_routes = {
            CtrlCmd.NEW_CONTROLLER.name:               self.on_new_controller,
            CtrlCmd.AGENT_RESTART.name:                self.on_agent_restart,
            CtrlCmd.AGENT_STOP.name:                   self.on_agent_stop,
#            CtrlCmd.AGENT_ENABLE_HEARTBEAT.name:       self.on_agent_enable_heartbeat,
#            CtrlCmd.AGENT_DISABLE_HEARTBEAT.name:      self.on_agent_disable_heartbeat,
        }

    def get_clientid(self):
        rd = ''
        if self.tcfg.enable_localdebug:
            from random import randint
            rd = string_write('-{}', hex(randint(1000000,10000000))[2:])
        return string_write(INUITHYAGENT_CLIENT_ID, self.host+rd)

    def set_host(self):
        try:
            self.__host = getpredefaddr()
        except Exception as ex:
            logger.error(string_write("Failed to get predefined static address: {}", ex))
            try:
                self.__host = socket.gethostname() #socket.gethostbyname(socket.gethostname())
            except Exception as ex:
                logger.error(string_write("Failed to get host by name: {}", ex))

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        logger.info(string_write("Do initialization"))
        try:
            self.set_host()
            self.__clientid = self.get_clientid()
            self.create_subscriber(*self.tcfg.mqtt)
            self.__traffic_executors = []
            self.__sad = SerialAdapter(self.__subscriber)
            self.initialized = True
        except Exception as ex:
            logger.error(string_write("Failed to initialize: {}", ex))
    
    def __init__(self, cfgpath='config/inuithy.conf', lg=None):
        self.__initialized = False
#        self.__enable_heartbeat = False
        self.__inuithy_cfg = InuithyConfig(cfgpath)
        self.__addr2node = {}
        if lg != None:
            global logger
            logger = lg
        if False == self.__inuithy_cfg.load():
            logger.error(string_write("Failed to load configure"))
        else:
            self.__do_init()

    def ctrlcmd_dispatch(self, command):
        """
        data = {
            CFGKW_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            CFGKW_CLIENTID: self.clientid,
            ...
        }
        """
        logger.info(string_write("Receive command [{}]", command))
        ctrlcmd = command.get(CFGKW_CTRLCMD)
        logger.debug(command)
        try:
            if self.ctrlcmd_routes.get(ctrlcmd):
                self.ctrlcmd_routes[ctrlcmd](command)
            else:
                logger.error(string_write('Invalid command [{}]', command))
        except Exception as ex:
                logger.error(string_write('Exception on handling command [{}]:{}', command, ex))
#        if Agent.__mutex_msg.acquire():
#            # TODO
#            Agent.__mutex_msg.release()

    def addr_to_node(self):
        logger.info("Map address to node")
        if not self.tcfg.enable_localdebug:
            [self.__addr2node.__setitem__(n.addr, n) for n in self.__sad.nodes]
            return

#            [self.__addr2node.__setitem__(''.join([random.choice(string.hexdigits) for i in range(4)]), n) for n in self.__sad.nodes]
        samples = ['1111', '1112', '1113', '1114', '1121', '1122', '1123', '1124', '1131', '1132', '1133', '1134', '1141', '1142', '1143', '1144']
        [self.__addr2node.__setitem__(addr, n) for addr, n in zip(samples, self.__sad.nodes)]
        [n.__setattr__(CFGKW_ADDR, addr) for addr, n in zip(samples, self.__sad.nodes)]
        [str(n) for n in self.__sad.nodes]

    def start(self):
        if not self.initialized:
            logger.error(string_write("Agent not initialized"))
            return
        status_msg = 'Agent fine'
        try:
            logger.info(string_write("Starting Agent {}", self.clientid))
            self.__sad.scan_nodes()
            logger.info(string_write("Connected nodes: [{}]", self.__sad.nodes))
            self.addr_to_node()
            self.register()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            status_msg = string_write("Agent received keyboard interrupt")
            logger.error(status_msg)
        except Exception as ex:
            status_msg = string_write("Exception on Agent: {}", ex)
            logger.error(status_msg)
        finally:
            self.teardown(status_msg)
            logger.info(string_write("Agent terminated"))

    def on_topic_command(self, message):
        """Command message format:
        """
        logger.info(string_write("On topic command"))
        msg = extract_payload(message.payload)
        try:
            self.ctrlcmd_dispatch(msg)
        except Exception as ex:
            logger.error(string_write("Exception on dispating control command: {}", ex))

    def on_topic_config(self, message):
        """Config message format:
        <key> <value>
        """
        logger.info(string_write("On topic config"))
        try:
            # TODO
            pass
        except Exception as ex:
            logger.error(string_write("Exception on updating config: {}", ex))

    def on_traffic_join(self, data):
        logger.info(string_write("Join request"))
        naddr = data[CFGKW_NODE]
        node = self.addr2node.get(naddr)
        logger.debug(string_write("Found node: {}", node))
        data[CFGKW_CLIENTID] = self.clientid
        data[CFGKW_HOST] = self.host
        if None != node:
            node.join(data)
        else: # DEBUG
            logger.error(string_write("{}: Node [{}] not found", self.clientid, naddr)) 
#                for addr, free_node in self.addr2node.items():
#                    if 0 == len(free_node.addr):
#                        free_node.setaddr(naddr, data)
#                        logger.info(string_write("{}: Set node {}", self.clientid, str(free_node))) 
#                        break
    
    def on_traffic_scmd(self, data):
        logger.info(string_write("SCMD request"))
        """
        data = {
             CFGKW_GENID:        tg.genid,
             CFGKW_DURATION:     tg.duration,
             CFGKW_TIMESLOT:     tg.timeslot,
             CFGKW_SENDER:       tr.sender,
             CFGKW_RECIPIENT:    tr.recipient,
             CFGKW_PKGSIZE:      tr.pkgsize,
             }
        """
        naddr = data[CFGKW_NODE]
        node = self.addr2node.get(naddr)
        logger.debug(string_write("Found node: {}", node))
        if None != node:
            data[CFGKW_CLIENTID] = self.clientid
            data[CFGKW_HOST] = self.host
            cmd = node.prot.traffic(data[RECIPIENT])
            te = TrafficExecutor(node, cmd, data[CFGKW_TIMESLOT], data[CFGKW_DURATION], data)
            self.__traffic_executors.append(te)
        else:
            logger.error(string_write("{}: Node [{}] not found", self.clientid, naddr)) 

    def on_traffic_tsh(self, data):
        logger.info(string_write("TSH request"))
        """
        data = {
            CFGKW_TRAFFIC_TYPE: TrafficType.TSH.name,
            CFGKW_HOST:         host,
            CFGKW_NODE:       node,
            CFGKW_CLIENTID:     self.__ctrl.host2aid[args[0]],
            CFGKW_MSG:          ' '.join(args[1:])
        }
        """
        naddr = data[CFGKW_NODE]
        node = self.addr2node.get(naddr)
        logger.debug(string_write("Found node: {}", node))
        if None != node:
            node.write(data[CFGKW_MSG])
        else: # DEBUG
            logger.error(string_write("{}: Node [{}] not found", self.clientid, naddr)) 

    def on_traffic_start(self, data):
        logger.info(string_write("Traffic start request"))
        try:
            [te.run() for te in self.__traffic_executors]
        except Exception as ex:
            logger.error(string_write("Exception on running traffic: {}", ex))

    def on_topic_traffic(self, message):
        logger.info(string_write("On topic traffic"))
        try:
            data = extract_payload(message.payload)
#           target = data[CFGKW_CLIENTID]
            logger.debug(string_write("Traffic data: {}", data))
            if not self.is_msg_for_me([data[CFGKW_CLIENTID], data[CFGKW_HOST]]): return
            self.traffic_dispatch(data)
        except Exception as ex:
            logger.error(string_write("Failed on handling traffic request: {}", ex))

    def traffic_dispatch(self, data):
        logger.info(string_write("Dispatch traffic request: {}", data))
        if data[CFGKW_TRAFFIC_TYPE] == TrafficType.JOIN.name:
            self.on_traffic_join(data)
        elif data[CFGKW_TRAFFIC_TYPE] == TrafficType.SCMD.name:
            self.on_traffic_scmd(data)
        elif data[CFGKW_TRAFFIC_TYPE] == TrafficType.START.name:
            self.on_traffic_start(data)
        elif data[CFGKW_TRAFFIC_TYPE] == TrafficType.TSH.name:
            self.on_traffic_tsh(data)
        else:
            logger.error(string_write("{}: Unhandled traffic message [{}]", self.clientid, data)) 

    def on_new_controller(self, message):
        logger.info(string_write("New controller"))
        self.register()

    def on_agent_restart(self, message):
        logger.info(string_write("Restart agent"))
        if self.is_msg_for_me([message[CFGKW_CLIENTID], message[CFGKW_HOST]]):
            logger.info(string_write("Stop agent {}", self.clientid))
            self.teardown()
            #TODO

    def is_msg_for_me(self, targets): # FIXME
        for target in targets:
            if target in ['*', self.__host, self.__clientid]: return True
        return False

    def on_agent_stop(self, message):
        if self.is_msg_for_me([message[CFGKW_CLIENTID], message[CFGKW_HOST]]):
            logger.info(string_write("Stop agent {}", self.clientid))
            self.teardown()

#    def on_agent_enable_heartbeat(self, message):
#        logger.info(string_write("Enable heartbeat"))
#        self.__enable_heartbeat = True
#
#    def on_agent_disable_heartbeat(self, message):
#        logger.info(string_write("Disable heartbeat"))
#        self.__enable_heartbeat = False

def start_agent(cfgpath):
    agent = Agent(cfgpath)
    agent.start()

if __name__ == '__main__':
    logger.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Agent"))
    start_agent(INUITHY_CONFIG_PATH)

