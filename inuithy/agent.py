"""Agent application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
import sys
sys.path.append('/opt/inuithy')
from inuithy.common.predef import to_string, INUITHY_TITLE, INUITHY_TOPIC_NWLAYOUT, INUITHY_TOPIC_TSH,\
__version__, INUITHY_CONFIG_PATH, CtrlCmd, INUITHY_TOPIC_TRAFFIC,\
INUITHY_TOPIC_CONFIG, INUITHYAGENT_CLIENT_ID, T_ADDR, T_HOST, T_NODE,\
T_CLIENTID, T_TID, T_INTERVAL, T_DURATION, T_NODES, T_DEST,\
T_TRAFFIC_STATUS, T_MSG, T_CTRLCMD, TrafficStatus, T_TRAFFIC_TYPE,\
INUITHY_LOGCONFIG, INUITHY_TOPIC_COMMAND, TrafficType, DEV_TTY, T_GENID,\
T_SRC, T_PKGSIZE, T_EVERYONE, mqlog_map, T_VERSION, T_MSG_TYPE, T_MQTT_VERSION, T_JITTER
from inuithy.common.runtime import Runtime as rt
from inuithy.common.runtime import load_tcfg
from inuithy.common.node_adapter import NodeAdapter, scan_nodes
from inuithy.common.traffic import TrafficExecutor, TRAFFIC_BROADCAST_ADDRESS
from inuithy.util.helper import getpredefaddr, clear_list
from inuithy.util.cmd_helper import pub_status, pub_heartbeat, pub_unregister, extract_payload
from inuithy.util.cmd_helper import Heartbeat
from inuithy.util.worker import Worker
import paho.mqtt.client as mqtt
import logging.config as lconf
import threading
import logging
from random import randint
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty
import time

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
    """General mutex"""
    __mutex = threading.Lock()
    """Message mutex"""
    __mutex_msg = threading.Lock()

    @property
    def clientid(self):
        """Message queue identifier for agent"""
        return self.__clientid
    @clientid.setter
    def clientid(self, val):
        pass

    @property
    def mqclient(self):
        """Message queue client"""
        return self._mqclient
    @mqclient.setter
    def mqclient(self, val):
        pass

    @property
    def host(self):
        """Host that agent running on"""
        return self.__host
    @host.setter
    def host(self, val):
        pass

    @property
    def enable_heartbeat(self):
        """Indicate heartbeat enabled or disabled"""
        return self._enable_heartbeat
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
    def initialized():
        """Agent initialization state"""
        return Agent.__initialized
    @initialized.setter
    def initialized(val):
        with Agent.__mutex:
            if not Agent.__initialized:
                Agent.__initialized = True

    @staticmethod
    def on_connect(client, userdata, rc):
        """MQ connect event handler"""
        userdata.lgr.info(to_string(
            "MQ.Connection client:{} userdata:[{}] rc:{}",
            client, userdata, rc))
#        userdata.register()

    @staticmethod
    def on_message(client, userdata, message):
        """MQ message event handler"""
        userdata.lgr.info(to_string("MQ.Message: userdata:[{}]", userdata))
        userdata.lgr.info(to_string("MQ.Message: message "+INUITHY_MQTTMSGFMT,
            message.dup, message.info, message.mid, message.payload,
            message.qos, message.retain, message.state, message.timestamp,
            message.topic))
        try:
            pass
# Unhandled topic
#            userdata.lgr.info("On message")
#            userdata.topic_routes[message.topic](message)
        except Exception as ex:
            msg = to_string("Exception on MQ message dispatching: {}", ex)
            userdata.lgr.error(msg)
            userdata.teardown(msg)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        """MQ disconnect event handler"""
        userdata.lgr.info(to_string(
            "MQ.Disconnection: client:{} userdata:[{}] rc:{}",
            client, userdata, rc))
        if 0 != rc:
            userdata.lgr.error(to_string("MQ.Disconnection: disconnection error"))
        userdata.teardown("Teardown from disconnection callback")

    @staticmethod
    def on_log(client, userdata, level, buf):
        """MQ log event handler"""
        mqlog_map(userdata.lgr, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        """MQ publish event handler"""
        userdata.lgr.info(to_string(
            "MQ.Publish: client:{} userdata:[{}], mid:{}",
            client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        """MQ subscribe event handler"""
        userdata.lgr.info(to_string(
            "MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}",
            client, userdata, mid, granted_qos))

    def stop_traffic_trigger(self):

        self.lgr.info("Stopping traffic executors")
        while not self.__traffic_executors.empty():
            te = self.__traffic_executors.get()
            te.stop_trigger()

    def teardown(self, msg='Teardown'):
        """Cleanup"""
        if not Agent.initialized:
            return
        self.lgr.info(to_string("Agent teardown: {}", self.clientid))
        try:
            if Agent.initialized:
                Agent.initialized = False
                msg = to_string("{}:{}", self.clientid, msg)
                self.stop_traffic_trigger()
                if self._heartbeat is not None:
                    self._heartbeat.stop()
                if self.adapter is not None:
                    self.adapter.teardown()
                if self.worker:
                    self.worker.stop()
                pub_status(self.mqclient, rt.tcfg.mqtt_qos, {T_MSG: msg})
                self.unregister()
                self.mqclient.disconnect()
        except Exception as ex:
            self.lgr.error(to_string("Exception on teardown: {}", ex))

    def __del__(self):
        pass

    def __str__(self):
        return to_string("clientid:[{}] host:[{}]", self.clientid, self.host)

    def alive_notification(self, scan_required=True):
        """Post alive notification
        @scan_nodes Whether need to scan connected nodes before post
        """
        self.lgr.info(to_string("Alive notification"))
        try:
            if scan_required:
                self.lgr.info(to_string("Got scan nodes request"))
                with Agent.__mutex:
                    scan_nodes(self.adapter)#[to_string(DEV_TTY, T_EVERYONE)])
                    self.addr_to_node()

            self.lgr.info(to_string("Connected nodes: [{}]", len(self.adapter.nodes)))
            data = {
                T_CLIENTID: self.clientid,
                T_HOST: self.host,
                T_NODES: [str(node) for node in self.adapter.nodes.values()],
                T_VERSION: __version__,
                T_MQTT_VERSION: mqtt.VERSION_NUMBER,
            }
            pub_heartbeat(self.mqclient, rt.tcfg.mqtt_qos, data)
        except Exception as ex:
            self.lgr.error(to_string("Alive notification exception:{}", ex))
            pub_status(self.mqclient, rt.tcfg.mqtt_qos, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: 'Check me out',
            })

    def unregister(self):
        """Unregister an agent from controller
        """
        self.lgr.info(to_string("Unregistering {}", self.clientid))
        try:
            pub_unregister(self.mqclient, rt.tcfg.mqtt_qos, self.clientid)
        except Exception as ex:
            self.lgr.error(to_string("Unregister failed: {}", ex))

    def create_mqtt_client(self, host, port):
        """Create MQTT subscriber"""
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self.mqclient.on_connect = Agent.on_connect
        self.mqclient.on_message = Agent.on_message
        self.mqclient.on_disconnect = Agent.on_disconnect
#        self.mqclient.on_log = Agent.on_log
#        self.mqclient.on_publish = Agent.on_publish
#        self.mqclient.on_subscribe = Agent.on_subscribe
        self.mqclient.connect(host, port)
        self.mqclient.subscribe([
            (INUITHY_TOPIC_COMMAND, rt.tcfg.mqtt_qos),
            (INUITHY_TOPIC_TRAFFIC, rt.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NWLAYOUT, rt.tcfg.mqtt_qos),
            (INUITHY_TOPIC_TSH, rt.tcfg.mqtt_qos),
            (INUITHY_TOPIC_CONFIG, rt.tcfg.mqtt_qos),
        ])
        self.mqclient.message_callback_add(INUITHY_TOPIC_COMMAND, Agent.on_topic_command)
        self.mqclient.message_callback_add(INUITHY_TOPIC_CONFIG, Agent.on_topic_config)
        self.mqclient.message_callback_add(INUITHY_TOPIC_TRAFFIC, Agent.on_topic_traffic)
        self.mqclient.message_callback_add(INUITHY_TOPIC_NWLAYOUT, Agent.on_topic_nwlayout)
        self.mqclient.message_callback_add(INUITHY_TOPIC_TSH, Agent.on_topic_tsh)
        self.ctrlcmd_routes = {
            CtrlCmd.NEW_CONTROLLER.name:               self.on_new_controller,
            CtrlCmd.AGENT_STOP.name:                   self.on_agent_stop,
            CtrlCmd.AGENT_ENABLE_HEARTBEAT.name:       self.on_agent_enable_heartbeat,
            CtrlCmd.AGENT_DISABLE_HEARTBEAT.name:      self.on_agent_disable_heartbeat,
        }

    def get_clientid(self, cid_surf=None):
        """Generate client ID"""
        rd = ''
        if cid_surf is not None:
            rd = cid_surf
        elif rt.tcfg.enable_localdebug:
            rd = to_string('-{}', hex(randint(1048576, 10000000))[2:])
        return to_string(INUITHYAGENT_CLIENT_ID, self.host+rd)

    def set_host(self):
        """Set agent host"""
        try:
            self.__host = getpredefaddr()
        except Exception as ex:
            self.lgr.error(to_string("Failed to get predefined static address: {}", ex))

        try: #FIXME
            if self.__host is None or len(self.__host) == 0:
                self.__host = '127.0.0.1'
        except Exception as ex:
            self.lgr.error(to_string("Failed to get host by name: {}", ex))

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        self.lgr.info(to_string("Do initialization"))
        try:
            self.create_mqtt_client(*rt.tcfg.mqtt)
            self.adapter = NodeAdapter(self.mqclient, lgr=self.lgr)
            Agent.initialized = True
        except Exception as ex:
            self.lgr.error(to_string("Failed to initialize: {}", ex))
            pub_status(self.mqclient, rt.tcfg.mqtt_qos, {
                T_TRAFFIC_STATUS: TrafficStatus.INITFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: str(ex),
            })
            raise RuntimeError(to_string("Failed to initialize: {}", ex))

    def __init__(self, cfgpath='config/inuithy.conf', lgr=None, cid_surf=None):
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging
        Agent.__initialized = False
        self._enable_heartbeat = False
        self._heartbeat = None
        self._mqclient = None
        self.worker = Worker(2, self.lgr)
        self.ctrlcmd_routes = {}
        self.__traffic_executors = Queue()

        load_tcfg(rt.tcfg_path)
        self.set_host()
        self.__addr2node = {}
        self.__clientid = self.get_clientid(cid_surf)
        self.__do_init()

    def ctrlcmd_dispatch(self, command):
        """
        data = {
            T_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            T_CLIENTID: self.clientid,
            ...
        }
        """
        self.lgr.info(to_string("Receive command [{}]", command))
        ctrlcmd = command.get(T_CTRLCMD)
        self.lgr.debug(command)
        try:
#            if self.ctrlcmd_routes.get(ctrlcmd):
#                self.ctrlcmd_routes[ctrlcmd](command)
            handler = self.ctrlcmd_routes.get(ctrlcmd)
            if handler is not None:
                self.worker.add_job(handler, command)
            else:
                self.lgr.error(to_string('Invalid command [{}]', command))
        except Exception as ex:
            self.lgr.error(to_string(\
                'Exception on handling command [{}]:{}', command, ex))

    def addr_to_node(self):
        """Map node address to SerialNode"""
        self.lgr.info("Map address to node")
#        self.__addr2node.clear()
        clear_list(self.__addr2node)
#        if not rt.tcfg.enable_localdebug:
        if True:
            [self.__addr2node.__setitem__(n.addr, n) for n in self.adapter.nodes.values()]
            return

        samples = [
                    '1101', '1102', '1103', '1104',
                    '1111', '1112', '1113', '1114',
                    '1121', '1122', '1123', '1124',
                    '1131', '1132', '1133', '1134',
                    '1141', '1142', '1143', '1144',
                    '1151', '1152', '1153', '1154',
                    '1161', '1162', '1163', '1164',
                    '1171', '1172', '1173', '1174',
                    '1181', '1182', '1183', '1184',
                    '1191', '1192', '1193', '1194',
                    '11a1', '11a2', '11a3', '11a4',
                    '11b1', '11b2', '11b3', '11b4',
                    '11c1', '11c2', '11c3', '11c4',
                    '11d1', '11d2', '11d3', '11d4',
                    '11e1', '11e2', '11e3', '11e4',
                    '11f1', '11f2', '11f3', '11f4',
                ]
        [n.__setattr__(T_ADDR, addr) for addr, n in zip(samples, self.adapter.nodes.values())]
        [self.__addr2node.__setitem__(addr, n) for addr, n in zip(samples, self.adapter.nodes.values())]
#        [str(n) for n in self.adapter.nodes.values()]

    def start(self):
        """Start Agent routine"""
        if not Agent.initialized:
            self.lgr.error(to_string("Agent not initialized"))
            return
        status_msg = 'Agent fine'
        try:
            self.lgr.info(to_string("Starting Agent {}", self.clientid))
            if self.worker:
                self.worker.start()
            self.alive_notification()
            self.mqclient.loop_forever()
        except KeyboardInterrupt:
            status_msg = to_string("Agent received keyboard interrupt")
            self.lgr.error(status_msg)
        except NameError as ex:
            self.lgr.error(to_string("ERR: {}", ex))
            raise
        except Exception as ex:
            status_msg = to_string("Exception on Agent: {}", ex)
            self.lgr.error(status_msg)
            pub_status(self.mqclient, rt.tcfg.mqtt_qos, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: status_msg,
            })
        self.teardown(status_msg)
        self.lgr.info(to_string("Agent terminated"))

    @staticmethod
    def on_topic_command(client, userdata, message):
        """Topic command handler"""
        self = userdata
        self.lgr.info(to_string("On topic command"))
        data = extract_payload(message.payload)
        try:
            self.ctrlcmd_dispatch(data)
        except Exception as ex:
            self.lgr.error(to_string("Exception on dispating control command: {}", ex))

    @staticmethod
    def on_topic_config(client, userdata, message):
        """Topic config handler"""
        self = userdata
        self.lgr.info(to_string("On topic config"))
        try:
            # TODO
            pass
        except Exception as ex:
            self.lgr.error(to_string("Exception on updating config: {}", ex))

    @staticmethod
    def on_topic_nwlayout(client, userdata, message):
        """Network layout handler"""
        self = userdata
        try:
            data = extract_payload(message.payload)
            self.lgr.debug(to_string("JOIN: {}", data))
            if not self.is_msg_for_me([data.get(T_CLIENTID)]):
                return
            self.lgr.debug(to_string("Traffic data: {}", data))
            naddr = data.get(T_NODE)
            if naddr is None:
                self.lgr.error(to_string("JOIN: Incorrect command {}", data))
                return
    
            node = self.addr2node.get(naddr)
            if node is None:
                self.lgr.error(to_string("JOIN: Node {} not connected", naddr))
                return
            #TODO remove addr->node map    
            if node.addr:
                self.lgr.debug(to_string("JOIN: Found node: {}", node))
                node.joined = False
                node.writable.set()
                node.join(data)
            else: # DEBUG
                self.lgr.error(to_string("{}: Node [{}] not found", self.clientid, naddr))
        except Exception as ex:
            self.lgr.error(to_string("Failure on handling traffic request: {}", ex))

    @staticmethod
    def on_topic_traffic(client, userdata, message):
        """Traffic topic handler"""
        self = userdata
#        self.lgr.info(to_string("On topic traffic"))
        try:
            data = extract_payload(message.payload)
            if not self.is_msg_for_me([data.get(T_CLIENTID)]):
                return
            self.lgr.debug(to_string("Traffic data: {}", data))
            self.traffic_dispatch(data)
        except Exception as ex:
            self.lgr.error(to_string("Failure on handling traffic request: {}", ex))

    def on_traffic_scmd(self, data):
        """Serial command handler
        """
        self.lgr.debug(to_string("TRAFFIC: {}", data))
        naddr = data.get(T_NODE)
        if naddr is None:
            self.lgr.error(to_string("TRAFFIC: Incorrect command {}", data))
            return

        node = self.addr2node.get(naddr)
        if node is None:
            self.lgr.error(to_string("TRAFFIC: Node {} not connected", naddr))
            return

        if node.addr and node.addr == data.get(T_SRC):
            self.lgr.debug(to_string("TRAFFIC: Found node: {}", node))
            request = {
                T_HOST: self.host,
                T_CLIENTID: self.clientid,
                T_GENID: data.get(T_GENID),
                T_TRAFFIC_TYPE: data.get(T_TRAFFIC_TYPE),
                T_NODE: data.get(T_NODE).encode(),
                T_SRC: data.get(T_SRC).encode(),
                T_DEST: data.get(T_DEST).encode(),
                T_PKGSIZE: data.get(T_PKGSIZE),
            }
            te = None
#            if rt.tcfg.enable_localdebug:
#                dest = None
#                if data.get(T_DEST) == TRAFFIC_BROADCAST_ADDRESS:
#                    dest = set(self.addr2node.values())
#                else:
#                    dest = set([self.addr2node.get(data.get(T_DEST))])
#                te = TrafficExecutor(node, data.get(T_INTERVAL), data.get(T_DURATION),\
#                    request=request, lgr=self.lgr, mqclient=self.mqclient, tid=data.get(T_TID),\
#                    data=dest)
#            else:
            te = TrafficExecutor(node, data.get(T_INTERVAL), data.get(T_DURATION), data.get(T_JITTER), \
                request=request, lgr=self.lgr, mqclient=self.mqclient, tid=data.get(T_TID))

            self.__traffic_executors.put(te)
            pub_status(self.mqclient, rt.tcfg.mqtt_qos, {
                T_TRAFFIC_STATUS: TrafficStatus.REGISTERED.name,
                T_CLIENTID: self.clientid,
                T_TID: data.get(T_TID),
            })
            # start on registered
#            te.start()
#            pub_status(self.mqclient, rt.tcfg.mqtt_qos, {
#                T_TRAFFIC_STATUS: TrafficStatus.RUNNING.name,
#                T_CLIENTID: self.clientid,
#                T_TID: te.tid,
#            })
        else:
            self.lgr.error(to_string("{}: Node [{}] not found", self.clientid, naddr))

    @staticmethod
    def on_topic_tsh(client, userdata, message):
        """
        data = {
            T_TRAFFIC_TYPE: TrafficType.TSH.name,
            T_HOST:         host,
            T_NODE:         node,
            T_CLIENTID:     clientid,
            T_MSG:          ' '.join(args[1:])
        }
        """
        self = userdata
        try:
            self.lgr.info(to_string("TSH request"))
            data = extract_payload(message.payload)
            if not self.is_msg_for_me([data.get(T_CLIENTID)]):
                return
            naddr = data.get(T_NODE)
            node = self.addr2node.get(naddr)
            if node is not None:
                self.lgr.debug(to_string("Found node: {}", node))
                node.write(data.get(T_MSG))
            else: # DEBUG
                self.lgr.error(to_string("{}: Node [{}] not found", self.clientid, naddr))
        except Exception as ex:
            self.lgr.error(to_string("Failure on handling tsh request: {}", ex))

    def on_traffic_start(self, data):
        """Traffic start command handler"""
        self.lgr.info(to_string("Traffic start request"))
        traf_thr = threading.Thread(target=self.start_traffic)
        traf_thr.start()

    def start_traffic(self):
        """Start traffic routine"""
        try:
#            [te.start() for te in self.__traffic_executors]
            self.lgr.info(to_string("{}: Total traffic executors: [{}]", self.clientid, self.__traffic_executors.qsize()))
            while self.__traffic_executors.qsize() > 0 and Agent.initialized:
                self.lgr.info(to_string("{}: executors: {}, agent init: {}", self.clientid, self.__traffic_executors.qsize(), Agent.initialized))
                te = self.__traffic_executors.get()
                te.start()
                pub_status(self.mqclient, rt.tcfg.mqtt_qos, {
                    T_TRAFFIC_STATUS: TrafficStatus.RUNNING.name,
                    T_CLIENTID: self.clientid,
                    T_TID: te.tid,
                })
#                te.finished.wait()
#                self.lgr.debug(to_string("{} finished", te))
        except Exception as ex:
            self.lgr.error(to_string("Exception on running traffic: {}", ex))

    def traffic_dispatch(self, data):
        """Dispatch traffic topic handlers"""
        self.lgr.info(to_string("Dispatch traffic request: {}", data))
        if data.get(T_TRAFFIC_TYPE) == TrafficType.SCMD.name:
            self.on_traffic_scmd(data)
        elif data.get(T_TRAFFIC_TYPE) == TrafficType.START.name:
            self.on_traffic_start(data)
#        elif data.get(T_TRAFFIC_TYPE) == TrafficType.TSH.name:
#            self.on_traffic_tsh(data)
        else:
            self.lgr.error(to_string("{}: Unhandled traffic message [{}]", self.clientid, data))

    def on_new_controller(self, message):
        """New controller command handler"""
        self.lgr.info(to_string("New controller"))
        self.alive_notification(False)

    def is_msg_for_me(self, targets): # FIXME
        """Determine message is for me"""
        for target in targets:
            if target is None:
                continue
            if target in [self.clientid, self.host, T_EVERYONE]:
                return True
        return False

    def on_agent_stop(self, message):
        """Agent stop command handler"""
        self.lgr.info(to_string("On agent stop {}", message))
        if self.is_msg_for_me([message.get(T_CLIENTID)]):
            self.lgr.info(to_string("Stop agent {}", self.clientid))
            self.teardown()

    def on_agent_enable_heartbeat(self, message):
        """Heartbeat enable command handler"""
        self.lgr.info(to_string("Enable heartbeat"))
        if self._enable_heartbeat:
            return
        self._enable_heartbeat = True
        self._heartbeat = Heartbeat(interval=float(rt.tcfg.heartbeat.get(T_INTERVAL)),\
            target=self.alive_notification)
        self._heartbeat.run()
        self.lgr.info(to_string("Heartbeat enabled"))

    def on_agent_disable_heartbeat(self, message):
        """Heartbeat disable command handler"""
        self.lgr.info(to_string("Disable heartbeat"))
        if not self._enable_heartbeat:
            return
        if self._heartbeat is not None:
            self._heartbeat.stop()
        self._enable_heartbeat = False
        self.lgr.info(to_string("Heartbeat disabled"))

def start_agent(args=None, lgr=None):
    """Shortcut to start an Agent"""
    rt.handle_args(args)
    agent = Agent(lgr)
    agent.start()

if __name__ == '__main__':
    lgr = logging.getLogger("InuithyAgent")
    lgr.info(to_string(INUITHY_TITLE, __version__, "Agent"))
    start_agent(lgr=lgr)

