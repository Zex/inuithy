""" Controller base
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import T_CTRLCMD, CtrlCmd, T_CLIENTID,\
T_HOST, T_NODES, AgentStatus, INUITHY_LOGCONFIG, mqlog_map, T_TID,\
to_string, CTRL_CLIENT_ID, T_TRAFFIC_STATUS, T_MSG,\
T_TRAFFIC_TYPE, TrafficType, T_NODE, TrafficStatus, T_VERSION,\
MessageType
from inuithy.common.predef import INUITHY_TOPIC_HEARTBEAT, INUITHY_TOPIC_STATUS,\
INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION, INUITHY_TOPIC_UNREGISTER
from inuithy.common.runtime import Runtime as rt
from inuithy.common.runtime import load_configs
from inuithy.util.helper import getnwlayoutid
from inuithy.util.cmd_helper import pub_ctrlcmd, extract_payload
from inuithy.util.traffic_state import TrafficState
from inuithy.storage.storage import Storage
from inuithy.common.agent_info import AgentInfo
from inuithy.util.worker import Worker
import threading
import logging
import logging.config as lconf
import os

lconf.fileConfig(INUITHY_LOGCONFIG)

INUITHY_MQTTMSGFMT = "dup:{}, info:{}, mid:{}, payload:[{}], \
qos:{}, retain:{}, state:{}, timestamp:{}, topic:[{}]"

class CtrlBase(object):
    """Base of controllers
    """
    """General mutex"""
    __mutex = threading.Lock()
    """Message mutex"""
    __mutex_msg = threading.Lock()

    @property
    def traffic_state(self):
        """Traffic state transition control"""
        return self._traffic_state
    @traffic_state.setter
    def traffic_state(self, val):
        pass

    @property
    def clientid(self):
        """ identity in MQ network"""
        return self._clientid
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
        """Host that Controller run on"""
        return self._host
    @host.setter
    def host(self, val):
        pass

    @property
    def storage(self):
        """Traffic data storage"""
        return self._storage
    @storage.setter
    def storage(self, val):
        pass

    @property
    def available_agents(self):
        """Available agent, agentid => AgentInfo"""
        return self.traffic_state.chk.available_agents
#    @available_agents.setter
#    def available_agents(self, val):
#        pass

    @property
    def expected_agents(self):
        """List of expected agents"""
        return self.traffic_state.chk.expected_agents
#    @expected_agents.setter
#    def expected_agents(self, val):
#        pass

    @property
    def node2host(self):
        """Node address => connected host"""
        return self.traffic_state.chk.node2host
#    @node2host.setter
#    def node2host(self, val):
#        pass

    @property
    def node2aid(self):
        """Node address => connected host"""
        return self.traffic_state.chk.node2aid

    @property
    def current_nwlayout(self):
        """FORMAT: <networkconfig_path>:<networklayout_name>"""
        return getnwlayoutid(*self._current_nwlayout)

    @current_nwlayout.setter
    def current_nwlayout(self, val):
        if not isinstance(val, tuple):
            raise TypeError("Tuple expected")
        self._current_nwlayout = val

    @property
    def initialized():
        """Indicate Controller initialization status"""
        return CtrlBase.__initialized
    @initialized.setter
    def initialized(val):
        with CtrlBase.__mutex:
            if not CtrlBase.__initialized:
                CtrlBase.__initialized = val

    def __init__(self, lgr=None, delay=4):
        """
        @delay Start traffic after @delay seconds
        """
        self.lgr = lgr is None and logging or lgr
        self._mqclient = None
        self._storage = None
        self._current_nwlayout = ('', '')
        self._host = os.uname()[1]
        self._clientid = to_string(CTRL_CLIENT_ID, self.host)
        self.worker = Worker(2, self.lgr)
        load_configs()

        self._traffic_state = TrafficState(self, self.lgr)
        self._traffic_timer = threading.Timer(delay, self.traffic_state.start)
        self._do_init()
        self.load_storage()

    def __del__(self):
        pass

    def __str__(self):
        return to_string("clientid:[{}] host:[{}]", self.clientid, self.host)

    @staticmethod
    def on_connect(client, userdata, rc):
        """MQ connect event handler"""
        userdata.lgr.info(to_string(
            "MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if rc != 0:
            userdata.lgr.info(to_string("MQ.Connection: connection error"))

    @staticmethod
    def on_message(client, userdata, message):
        """MQ message event handler"""
#        userdata.lgr.info(to_string("MQ.Message: userdata:[{}]", userdata))
#        userdata.lgr.info(to_string("MQ.Message: message "+INUITHY_MQTTMSGFMT,
#            message.dup, message.info, message.mid, message.payload,
#            message.qos, message.retain, message.state, message.timestamp,
#            message.topic))
        try:
            userdata.lgr.info("On message")
#            handler = userdata.topic_routes.get(message.topic)
#            if handler is not None:
#                userdata.worker.add_job(handler, message)
        except Exception as ex:
            userdata.lgr.error(to_string("Exception on MQ message dispatching: {}", ex))

    @staticmethod
    def on_disconnect(client, userdata, rc):
        """MQ disconnect event handler"""
        userdata.lgr.info(to_string(
            "MQ.Disconnection: client:{} userdata:[{}] rc:{}",
            client, userdata, rc))
        if 0 != rc:
            userdata.lgr.error(to_string("MQ.Disconnection: disconnection error"))
        userdata.teardown()

    @staticmethod
    def on_log(client, userdata, level, buf):
        """MQ log event handler"""
        mqlog_map(userdata.lgr, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        """MQ publish event handler"""
        userdata.lgr.info(to_string(
            "MQ.Publish: client:{} userdata:[{}], mid:{}", client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        """MQ subscribe event handler"""
        userdata.lgr.info(to_string(
            "MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}",
            client, userdata, mid, granted_qos))

    def alive_notification(self):
        """Broadcast on new controller startup
        """
        self.lgr.info(to_string("New controller notification {}", self.clientid))
        data = {
            T_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            T_CLIENTID: self.clientid,
        }
        pub_ctrlcmd(self.mqclient, rt.tcfg.mqtt_qos, data)

    def add_agent(self, agentid, host, nodes):
        """Register started agent"""
        self.lgr.info("Add agent") 
        if self.available_agents.get(agentid) is None:
            self.available_agents[agentid] = AgentInfo(agentid, host, AgentStatus.ONLINE, nodes)
            self.lgr.info(to_string("Agent {} added", agentid))
        else:
            self.available_agents[agentid].nodes = nodes
            self.lgr.info(to_string("Agent {} updated", agentid))
        [self.traffic_state.chk.node2aid.__setitem__(node, agentid) for node in nodes]

    def del_agent(self, agentid):
        """Unregister started agent"""
        if self.available_agents.get(agentid):
            del self.available_agents[agentid]
            self.lgr.info(to_string("Agent {} removed", agentid))

    def _do_init(self):
        """
        _host: IP address of agent

        """
        self.lgr.info(to_string("Do initialization"))
        try:
            self.node_to_host()
            for aname in rt.trcfg.target_agents:
                agent = rt.nwcfg.agent_by_name(aname)
                self.expected_agents.append(agent.get(T_HOST))
            self.create_mqtt_client(*rt.tcfg.mqtt)
            CtrlBase.initialized = True
        except Exception as ex:
            self.lgr.error(to_string("Failed to initialize: {}", ex))

    def create_mqtt_client(self, host, port):
        """Create MQTT subscriber"""
        pass

    def node_to_host(self):
        """Map node address to connected host
        """
        self.lgr.info("Map node address to host")
        for agent in rt.nwcfg.agents:
            [self.traffic_state.chk.node2host.__setitem__(node, agent[T_HOST]) for node in agent[T_NODES]]


    def load_storage(self):
        self.lgr.info(to_string("Load DB plugin:{}", rt.tcfg.storagetype))
        try:
            self._storage = Storage(rt.tcfg, self.lgr)
        except Exception as ex:
            self.lgr.error(to_string("Failed to load plugin: {}", ex))

    def teardown(self):
        """Cleanup"""
        try:
            if CtrlBase.initialized:
                CtrlBase.initialized = False
#                self.lgr.info("Stop agents")
#                stop_agents(self._mqclient, rt.tcfg.mqtt_qos)
                if self._traffic_timer:
                    self._traffic_timer.cancel()
                if self.storage:
                    self.storage.close()
                if self.worker:
                    self.worker.stop()
                if self.traffic_state:
                    self.traffic_state.traf_running = False
                    self.traffic_state.chk.set_all()
                if self.mqclient:
                    self.mqclient.disconnect()
#                self.traffic_state.chk.done.set()
        except Exception as ex:
            self.lgr.error(to_string("Exception on teardown: {}", ex))

    @staticmethod
    def on_topic_heartbeat(client, userdata, message):
        """Heartbeat message format:
        """
        self = userdata
        self.lgr.info(to_string("On topic heartbeat"))
        data = extract_payload(message.payload)
        agentid, host, nodes, version = data.get(T_CLIENTID), data.get(T_HOST),\
                data.get(T_NODES), data.get(T_VERSION)
        if version != __version__:
            self.lgr.error(to_string("Agent version not match"))
            self.teardown()
        try:
            self.lgr.info(to_string("On topic heartbeat: Agent Version {}", version))
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
            self.traffic_state.check("is_agents_up")
            self.lgr.info(to_string("Found Agents({})", len(self.available_agents)))
#            self.lgr.debug(to_string("{}", [str(a) for a in self.available_agents.values()]))
        except Exception as ex:
            self.lgr.error(to_string("Exception on registering agent {}: {}", agentid, ex))

    @staticmethod
    def on_topic_unregister(client, userdata, message):
        """Unregister message format:
        <agentid>
        """
        self = userdata
        data = extract_payload(message.payload)
        agentid = data.get(T_CLIENTID)
        self.lgr.info(to_string("On topic unregister: del {}", agentid))

        try:
            self.del_agent(agentid)
            if len(self.available_agents) == 0:
                self.traffic_state.chk._is_traffic_all_unregistered.set()
        except Exception as ex:
            self.lgr.error(to_string("Exception on unregistering agent {}: {}", agentid, ex))

    @staticmethod
    def on_topic_status(client, userdata, message):
        """Status topic handler"""
        self = userdata
        self.lgr.info(to_string("On topic status"))
        data = extract_payload(message.payload)
        if data.get(T_TRAFFIC_STATUS) == TrafficStatus.REGISTERED.name:
            self.lgr.info(to_string("Traffic {} registered on {}",\
                data.get(T_TID), data.get(T_CLIENTID)))
            self.traffic_state.update_stat(data.get(T_TID), TrafficStatus.REGISTERED, "is_traffic_all_registered")
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.RUNNING.name:
            self.lgr.info(to_string("Traffic {} is running on {}",\
                data.get(T_TID), data.get(T_CLIENTID)))
            self.traffic_state.update_stat(data.get(T_TID), TrafficStatus.RUNNING)
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.FINISHED.name:
            self.lgr.info(to_string("Traffic {} finished", data.get(T_TID)))
            self.traffic_state.update_stat(data.get(T_TID), TrafficStatus.FINISHED, "is_phase_finished")
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.INITFAILED.name:
            self.lgr.error(to_string("Agent {} failed to initialize: {}",\
                data.get(T_CLIENTID), data.get(T_MSG)))
            self.teardown()
        elif data.get(T_MSG) is not None:
            self.lgr.info(data.get(T_MSG))
        else:
            self.lgr.debug(to_string("Unhandled status message {}", data))

    @staticmethod
    def on_topic_reportwrite(client, userdata, message):
        """Report-written topic handler"""
        self = userdata
        self.lgr.info(to_string("On topic reportwrite"))
        data = extract_payload(message.payload)
        try:
            if data.get(T_TRAFFIC_TYPE) == TrafficType.JOIN.name:
                self.lgr.debug(to_string("JOINING: {}", data.get(T_NODE)))
            elif data.get(T_TRAFFIC_TYPE) == TrafficType.SCMD.name:
            # Record traffic only
                self.lgr.debug(to_string("REPORT: {}", data))
#                if data.get(T_MSG_TYPE) == MessageType.SEND.name and data.get(T_NODE) is not None:
                if data.get(T_NODE) is not None:
                    self.storage.insert_record(data)
        except Exception as ex:
            self.lgr.error(to_string("Failed to handle report write message: {}", ex))
            self.teardown()

    @staticmethod
    def on_topic_notification(client, userdata, message):
        """Report-read topic handler"""
        self = userdata
        self.lgr.info(to_string("On topic notification"))
        data = extract_payload(message.payload)
        try:
            self.lgr.debug(to_string("NOTIFY: {}", data))
            if data.get(T_TRAFFIC_TYPE) == TrafficType.JOIN.name:
                if self.traffic_state.chk.nwlayout.get(data.get(T_NODE)) is not None:
                    self.traffic_state.chk.nwlayout[data.get(T_NODE)] = True
                    self.traffic_state.check("is_nwlayout_done")
            elif data.get(T_TRAFFIC_TYPE) == TrafficType.SCMD.name:
            # Record traffic only
#                if data.get(T_MSG_TYPE) == MessageType.RECV.name and data.get(T_NODE) is not None:
                if data.get(T_NODE) is not None:
                    self.storage.insert_record(data)
            else:
                pass
#                self.storage.insert_record(data)
        except Exception as ex:
            self.lgr.error(to_string("Failed to handle notification message: {}", ex))
            self.teardown()


