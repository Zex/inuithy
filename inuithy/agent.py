"""Agent application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
import sys
sys.path.append('/opt/inuithy')
from inuithy.common.predef import _s, INUITHY_TITLE, TT_NWLAYOUT, TT_TSH, _l,\
__version__, INUITHY_CONFIG_PATH, CtrlCmd, TT_TRAFFIC,\
TT_CONFIG, AGENT_CLIENT_ID, T_ADDR, T_HOST, T_NODE, T_PIDFILE,\
T_CLIENTID, T_TID, T_INTERVAL, T_DURATION, T_NODES, T_DEST, T_DESTS,\
T_TRAFFIC_STATUS, T_MSG, T_CTRLCMD, TrafficStatus, T_TRAFFIC_TYPE,\
TT_COMMAND, TrafficType, DEV_TTY, T_GENID, T_ALL, \
T_SRC, T_PKGSIZE, T_EVERYONE, T_VERSION, T_MSG_TYPE, T_MQTT_VERSION, T_JITTER
from inuithy.common.runtime import Runtime as rt
from inuithy.common.runtime import load_tcfg
from inuithy.common.node_adapter import NodeAdapter, scan_nodes
from inuithy.common.traffic import TrafficExecutor, TRAFFIC_BROADCAST_ADDRESS
from inuithy.util.helper import getpredefaddr, clear_list
from inuithy.util.cmd_helper import pub_status, pub_heartbeat, pub_unregister, extract_payload
from inuithy.util.cmd_helper import Heartbeat, mqlog_map, subscribe, gen_pidfile
from inuithy.util.worker import Worker
import paho.mqtt.client as mqtt
import threading
from random import randint
import time
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

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
        with Agent.__mutex:
            return Agent.__initialized
    @initialized.setter
    def initialized(val):
        with Agent.__mutex:
            if not Agent.__initialized:
                Agent.__initialized = True

    @staticmethod
    def on_connect(client, userdata, rc):
        """MQ connect event handler"""
        _l.info(_s(
            "MQ.Connection client:{} userdata:[{}] rc:{}",
            client, userdata, rc))

    @staticmethod
    def on_message(client, userdata, message):
        """MQ message event handler"""
        _l.info(_s("MQ.Message: userdata:[{}]", userdata))
        _l.info(_s("MQ.Message: message "+INUITHY_MQTTMSGFMT,
            message.dup, message.info, message.mid, message.payload,
            message.qos, message.retain, message.state, message.timestamp,
            message.topic))
        try:
            pass
# Unhandled topic
#            _l.info("On message")
#            userdata.topic_routes[message.topic](message)
        except Exception as ex:
            msg = _s("Exception on MQ message dispatching: {}", ex)
            _l.error(msg)
            userdata.teardown(msg)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        """MQ disconnect event handler"""
        _l.info(_s(
            "MQ.Disconnection: client:{} userdata:[{}] rc:{}",
            client, userdata, rc))
        if 0 != rc:
            _l.error(_s("MQ.Disconnection: disconnection error"))
        userdata.teardown("Teardown from disconnection callback")

    @staticmethod
    def on_log(client, userdata, level, buf):
        """MQ log event handler"""
        mqlog_map(level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        """MQ publish event handler"""
        _l.info(_s(
            "MQ.Publish: client:{} userdata:[{}], mid:{}",
            client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        """MQ subscribe event handler"""
        _l.info(_s(
            "MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}",
            client, userdata, mid, granted_qos))

    def stop_traffic_trigger(self):

        _l.info("Stopping traffic executors")
        while not self.__traffic_executors.empty():
            te = self.__traffic_executors.get()
            te.stop_trigger()

    def teardown(self, msg='Teardown'):
        """Cleanup"""
        if not Agent.initialized:
            return
        _l.info(_s("Agent teardown: {}", self.clientid))
        try:
            if Agent.initialized:
                Agent.initialized = False
                msg = _s("{}:{}", self.clientid, msg)
                self.stop_traffic_trigger()
                if self._heartbeat is not None:
                    self._heartbeat.stop()
                if self.adapter is not None:
                    self.adapter.teardown()
                if self.worker:
                    self.worker.stop()
                pub_status(self.mqclient, {T_MSG: msg})
                self.unregister()
                self.mqclient.disconnect()
        except Exception as ex:
            _l.error(_s("Exception on teardown: {}", ex))

    def __del__(self):
        pass

    def __str__(self):
        return _s("clientid:[{}] host:[{}]", self.clientid, self.host)

    def alive_notification(self, scan_required=True):
        """Post alive notification
        @scan_nodes Whether need to scan connected nodes before post
        """
        _l.info(_s("Alive notification"))
        try:
            if scan_required:
                _l.info(_s("Got scan nodes request"))
                with Agent.__mutex:
                    scan_nodes(self.adapter)#[_s(DEV_TTY, T_EVERYONE)])
                    self.addr_to_node()

            _l.info(_s("Connected nodes: [{}]", len(self.adapter.nodes)))
            data = {
                T_CLIENTID: self.clientid,
                T_HOST: self.host,
                T_NODES: [str(node) for node in self.adapter.nodes.values()],
                T_VERSION: __version__,
                T_MQTT_VERSION: mqtt.VERSION_NUMBER,
            }
            pub_heartbeat(self.mqclient, data)
        except Exception as ex:
            _l.error(_s("Alive notification exception:{}", ex))
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_VERSION: __version__,
                T_MQTT_VERSION: mqtt.VERSION_NUMBER,
                T_CLIENTID: self.clientid,
                T_MSG: 'Hearbeat failed, check me out',
            })
            self.teardown()

    def unregister(self):
        """Unregister an agent from controller
        """
        _l.info(_s("Unregistering {}", self.clientid))
        try:
            pub_unregister(self.mqclient, self.clientid)
        except Exception as ex:
            _l.error(_s("Unregister failed: {}", ex))


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
        subscribe(self.mqclient, _s(TT_COMMAND, self.clientid), Agent.on_topic_command)
        subscribe(self.mqclient, _s(TT_COMMAND, T_ALL), Agent.on_topic_command)
        subscribe(self.mqclient, _s(TT_CONFIG, self.clientid), Agent.on_topic_config)
        subscribe(self.mqclient, _s(TT_CONFIG, T_ALL), Agent.on_topic_config)
        subscribe(self.mqclient, _s(TT_TRAFFIC, self.clientid), Agent.on_topic_traffic)
        subscribe(self.mqclient, _s(TT_TRAFFIC, T_ALL), Agent.on_topic_traffic)
        subscribe(self.mqclient, _s(TT_NWLAYOUT, self.clientid), Agent.on_topic_nwlayout)
        subscribe(self.mqclient, _s(TT_NWLAYOUT, T_ALL), Agent.on_topic_nwlayout)
        subscribe(self.mqclient, _s(TT_TSH, self.clientid), Agent.on_topic_tsh)
        subscribe(self.mqclient, _s(TT_TSH, T_ALL), Agent.on_topic_tsh)
        #TODO agent-based topic
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
            rd = _s('-{}', hex(randint(1048576, 10000000))[2:])
        return _s(AGENT_CLIENT_ID, self.host+rd)

    def set_host(self):
        """Set agent host"""
        try:
            self.__host = getpredefaddr()
        except Exception as ex:
            _l.error(_s("Failed to get predefined static address: {}", ex))

        try: #FIXME
            if self.__host is None or len(self.__host) == 0:
                self.__host = '127.0.0.1'
        except Exception as ex:
            _l.error(_s("Failed to get host by name: {}", ex))

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        _l.info(_s("Do initialization"))
        try:
            self.create_mqtt_client(*rt.tcfg.mqtt)
            self.adapter = NodeAdapter(self.mqclient)
            Agent.initialized = True
        except Exception as ex:
            _l.error(_s("Failed to initialize: {}", ex))
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.INITFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: str(ex),
            })
            raise RuntimeError(_s("Failed to initialize: {}", ex))

    def __init__(self, cfgpath='config/inuithy.conf', cid_surf=None):
        if _l is None:
            _l = logging
        Agent.__initialized = False
        self._enable_heartbeat = False
        self._heartbeat = None
        self._mqclient = None
        self.worker = Worker(2)
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
        _l.info(_s("Receive command [{}]", command))
        ctrlcmd = command.get(T_CTRLCMD)
        _l.debug(command)
        try:
            handler = self.ctrlcmd_routes.get(ctrlcmd)
            if handler is not None:
                self.worker.add_job(handler, command)
            else:
                _l.error(_s('Invalid command [{}]', command))
        except Exception as ex:
            _l.error(_s(\
                'Exception on handling command [{}]:{}', command, ex))

    def addr_to_node(self):
        """Map node address to SerialNode"""
        _l.info("Map address to node")
#        self.__addr2node.clear()
        clear_list(self.__addr2node)
        [self.__addr2node.__setitem__(n.addr, n) for n in self.adapter.nodes.values()]

    def start(self):
        """Start Agent routine"""
        if not Agent.initialized:
            _l.error(_s("Agent not initialized"))
            return
        status_msg = 'OK'
        try:
            _l.info(_s("Starting Agent {}", self.clientid))
            gen_pidfile(rt.tcfg.config.get(T_PIDFILE))
            if self.worker:
                self.worker.start()
            self.alive_notification()
            self.mqclient.loop_forever()
        except KeyboardInterrupt:
            status_msg = _s("Agent received keyboard interrupt")
            _l.error(status_msg)
        except NameError as ex:
            _l.error(_s("ERR: {}", ex))
            raise
        except Exception as ex:
            status_msg = _s("Exception on Agent: {}", ex)
            _l.error(status_msg)
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: status_msg,
            })
        self.teardown(status_msg)
        _l.info(_s("Agent terminated"))

    @staticmethod
    def on_topic_command(client, userdata, message):
        """Topic command handler"""
        self = userdata
        _l.info(_s("On topic command"))
        data = extract_payload(message.payload)
        try:
            self.ctrlcmd_dispatch(data)
        except Exception as ex:
            _l.error(_s("Exception on dispating control command: {}", ex))

    @staticmethod
    def on_topic_config(client, userdata, message):
        """Topic config handler"""
        self = userdata
        _l.info(_s("On topic config"))
        try:
            # TODO
            pass
        except Exception as ex:
            _l.error(_s("Exception on updating config: {}", ex))

    @staticmethod
    def on_topic_nwlayout(client, userdata, message):
        """Network layout handler"""
        self = userdata
        try:
            data = extract_payload(message.payload)
            _l.debug(_s("JOIN: {}", data))
            naddr = data.get(T_NODE)
            if naddr is None:
                _l.error(_s("JOIN: Incorrect command {}", data))
                return
    
            node = self.addr2node.get(naddr)
            if node is None:
                _l.error(_s("JOIN: Node {} not connected", naddr))
                return
            #TODO remove addr->node map    
            if node.addr:
                _l.debug(_s("JOIN: Found node: {}", node))
                node.joined = False
                node.writable.set()
                node.join(data)
            else: # DEBUG
                _l.error(_s("{}: Node [{}] not found", self.clientid, naddr))
        except Exception as ex:
            _l.error(_s("Failure on handling nwlayout request: {}", ex))
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: 'Failed to configure network',
            })

    @staticmethod
    def on_topic_traffic(client, userdata, message):
        """Traffic topic handler"""
        self = userdata
#        _l.info(_s("On topic traffic"))
        try:
            data = extract_payload(message.payload)
            _l.debug(_s("Traffic data: {}", data))
            self.traffic_dispatch(data)
        except Exception as ex:
            _l.error(_s("Failure on handling traffic request: {}", ex))
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_CLIENTID: self.clientid,
                T_MSG: 'Failed to register traffic',
            })

    def on_traffic_scmd(self, data):
        """Serial command handler
        """
        _l.debug(_s("TRAFFIC: {}", data))
        naddr = data.get(T_NODE)
        if naddr is None:
            _l.error(_s("TRAFFIC: Incorrect command {}", data))
            return

        node = self.addr2node.get(naddr)
        if node is None:
            _l.error(_s("TRAFFIC: Node {} not connected", naddr))
            return

        if node.addr and node.addr == data.get(T_SRC):
            _l.debug(_s("TRAFFIC: Found node: {}", node))
            request = {
                T_HOST: self.host,
                T_CLIENTID: self.clientid,
                T_GENID: data.get(T_GENID),
                T_TRAFFIC_TYPE: data.get(T_TRAFFIC_TYPE),
                T_NODE: data.get(T_NODE).encode(),
                T_SRC: data.get(T_SRC).encode(),
                T_DESTS: [d.encode() for d in data.get(T_DESTS)],
                T_PKGSIZE: data.get(T_PKGSIZE),
            }
            te = TrafficExecutor(node, float(data.get(T_INTERVAL)), float(data.get(T_DURATION)), float(data.get(T_JITTER)),\
                request=request, mqclient=self.mqclient, tid=data.get(T_TID))

            self.__traffic_executors.put(te)
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.REGISTERED.name,
                T_CLIENTID: self.clientid,
                T_TID: data.get(T_TID),
            })
# start on registered
#            te.start()
#            pub_status(self.mqclient, {
#                T_TRAFFIC_STATUS: TrafficStatus.RUNNING.name,
#                T_CLIENTID: self.clientid,
#                T_TID: te.tid,
#            })
        else:
            _l.error(_s("{}: Node [{}] not found", self.clientid, naddr))

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
            _l.info(_s("TSH request"))
            data = extract_payload(message.payload)
            naddr = data.get(T_NODE)
            node = self.addr2node.get(naddr)
            if node is not None:
                _l.debug(_s("Found node: {}", node))
                node.tsh_on = True
                node.write(data.get(T_MSG))
            else: # DEBUG
                _l.error(_s("{}: Node [{}] not found", self.clientid, naddr))
        except Exception as ex:
            _l.error(_s("Failure on handling tsh request: {}", ex))

    def on_traffic_start(self, data):
        """Traffic start command handler"""
        _l.info(_s("Traffic start request"))
        traf_thr = threading.Thread(target=self.start_traffic)
        traf_thr.start()

    def start_traffic(self):
        """Start traffic routine"""
        try:
            _l.info(_s("{}: Total traffic executors: [{}]", self.clientid, self.__traffic_executors.qsize()))
            while self.__traffic_executors.qsize() > 0 and Agent.initialized:
                _l.info(_s("{}: executors: {}, agent init: {}", self.clientid, self.__traffic_executors.qsize(), Agent.initialized))
                te = self.__traffic_executors.get()
                te.run()
                pub_status(self.mqclient, {
                    T_TRAFFIC_STATUS: TrafficStatus.RUNNING.name,
                    T_CLIENTID: self.clientid,
                    T_TID: te.tid,
                })
#                te.finished.wait()
        except Exception as ex:
            _l.error(_s("Exception on running traffic: {}", ex))
            pub_status(self.mqclient, {
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_VERSION: __version__,
                T_MQTT_VERSION: mqtt.VERSION_NUMBER,
                T_CLIENTID: self.clientid,
                T_MSG: 'Start traffic failed',
            })

    def traffic_dispatch(self, data):
        """Dispatch traffic topic handlers"""
        _l.info(_s("Dispatch traffic request: {}", data))
        if data.get(T_TRAFFIC_TYPE) == TrafficType.SCMD.name:
            self.on_traffic_scmd(data)
        elif data.get(T_TRAFFIC_TYPE) == TrafficType.START.name:
            self.on_traffic_start(data)
        else:
            _l.error(_s("{}: Unhandled traffic message [{}]", self.clientid, data))

    def on_new_controller(self, message):
        """New controller command handler"""
        _l.info(_s("New controller"))
        self.alive_notification(False)

    def on_agent_stop(self, message):
        """Agent stop command handler"""
        _l.info(_s("On agent stop {}", message))
        _l.info(_s("Stop agent {}", self.clientid))
        self.teardown()

    def on_agent_enable_heartbeat(self, message):
        """Heartbeat enable command handler"""
        _l.info(_s("Enable heartbeat"))
        if self._enable_heartbeat:
            return
        self._enable_heartbeat = True
        self._heartbeat = Heartbeat(interval=float(rt.tcfg.heartbeat.get(T_INTERVAL)),\
            target=self.alive_notification)
        self._heartbeat.run()
        _l.info(_s("Heartbeat enabled"))

    def on_agent_disable_heartbeat(self, message):
        """Heartbeat disable command handler"""
        _l.info(_s("Disable heartbeat"))
        if not self._enable_heartbeat:
            return
        if self._heartbeat is not None:
            self._heartbeat.stop()
        self._enable_heartbeat = False
        _l.info(_s("Heartbeat disabled"))

def start_agent(args=None):
    """Shortcut to start an Agent"""
    rt.handle_args(args)
    agent = Agent()
    agent.start()

if __name__ == '__main__':
    import logging
    _l = logging.getLogger("InuithyAgent")
    _l.info(_s(INUITHY_TITLE, __version__, "Agent"))
    start_agent()

