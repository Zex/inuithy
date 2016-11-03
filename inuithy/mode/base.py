""" Controller base
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_CTRLCMD, CtrlCmd, T_CLIENTID,\
T_HOST, T_NODES, AgentStatus, INUITHY_LOGCONFIG,\
string_write, INUITHYCONTROLLER_CLIENT_ID
from inuithy.util.helper import getnwlayoutid
from inuithy.util.cmd_helper import pub_ctrlcmd
from inuithy.util.traffic_state import TrafficState, TrafStatChk
from inuithy.storage.storage import Storage
from inuithy.common.agent_info import AgentInfo
from inuithy.util.config_manager import create_inuithy_cfg, create_traffic_cfg,\
create_network_cfg
import threading as thrd
import logging, socket
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

class ControllerBase(object):
    """Base of controllers
    """
    __mutex = thrd.Lock()
    __mutex_msg = thrd.Lock()

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
    def subscriber(self):
        """Message queue client"""
        return self._subscriber
    @subscriber.setter
    def subscriber(self, val):
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
    def tcfg(self):
        """Inuithy configure"""
        return self._inuithy_cfg
    @tcfg.setter
    def tcfg(self, val):
        pass

    @property
    def nwcfg(self):
        """Network configure"""
        return self._network_cfg
    @nwcfg.setter
    def nwcfg(self, val):
        pass

    @property
    def trcfg(self):
        """Traffic configure """
        return self._traffic_cfg
    @trcfg.setter
    def trcfg(self, val):
        pass

    @property
    def available_agents(self):
        """Available agent, agentid => AgentInfo"""
        return self.chk.available_agents
    @available_agents.setter
    def available_agents(self, val):
        pass

    @property
    def expected_agents(self):
        """List of expected agents"""
        return self.chk.expected_agents
    @expected_agents.setter
    def expected_agents(self, val):
        pass

    @property
    def node2host(self):
        """Node address => connected host"""
        return self.chk.node2host
    @node2host.setter
    def node2host(self, val):
        pass

    @property
    def host2aid(self):
        """host => agentid"""
        return self.chk.host2aid
    @host2aid.setter
    def host2aid(self, val):
        pass

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
        return ControllerBase.__initialized
    @initialized.setter
    def initialized(val):
        if ControllerBase.__mutex.acquire_lock():
            if not ControllerBase.__initialized:
                ControllerBase.__initialized = val
            ControllerBase.__mutex.release()


    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        """
        @inuithy_cfgpath Path to inuithy configure
        @traffic_cfgpath Path to traffic configure
        @delay Start traffic after @delay seconds
        """
        if lgr is not None:
            self.lgr = lgr
        else:
            self.lgr = logging
        self._subscriber = None
        self._storage = None
        self.topic_routes = {}
        self._current_nwlayout = ('', '')
        self._host = socket.gethostname()
        self._clientid = string_write(INUITHYCONTROLLER_CLIENT_ID, self.host)
        self.chk = TrafStatChk()
        if self.load_configs(inuithy_cfgpath, traffic_cfgpath):
            self._do_init()
            self.load_storage()
            self._traffic_state = TrafficState(self)
            self._traffic_timer = thrd.Timer(delay, self._traffic_state.start)

    def __del__(self):
        pass

    def __str__(self):
        return string_write("clientid:[{}] host:[{}]", self.clientid, self.host)

    @staticmethod
    def on_connect(client, userdata, rc):
        """MQ connect event handler"""
        userdata.lgr.info(string_write(
            "MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if rc != 0:
            userdata.lgr.info(string_write("MQ.Connection: connection error"))

    @staticmethod
    def on_message(client, userdata, message):
        """MQ message event handler"""
#        userdata.lgr.info(string_write("MQ.Message: userdata:[{}]", userdata))
#        userdata.lgr.info(string_write("MQ.Message: message "+INUITHY_MQTTMSGFMT,
#            message.dup, message.info, message.mid, message.payload,
#            message.qos, message.retain, message.state, message.timestamp,
#            message.topic))
        try:
            userdata.topic_routes[message.topic](message)
        except Exception as ex:
            userdata.lgr.error(string_write("Exception on MQ message dispatching: {}", ex))

    @staticmethod
    def on_disconnect(client, userdata, rc):
        """MQ disconnect event handler"""
        userdata.lgr.info(string_write(
            "MQ.Disconnection: client:{} userdata:[{}] rc:{}",
            client, userdata, rc))
        if 0 != rc:
            userdata.lgr.info(string_write("MQ.Disconnection: disconnection error"))

    @staticmethod
    def on_log(client, userdata, level, buf):
        """MQ log event handler"""
        mqlog_map(userdata.lgr, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        """MQ publish event handler"""
        userdata.lgr.info(string_write(
            "MQ.Publish: client:{} userdata:[{}], mid:{}", client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        """MQ subscribe event handler"""
        userdata.lgr.info(string_write(
            "MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}",
            client, userdata, mid, granted_qos))

    def _alive_notification(self):
        """Broadcast on new controller startup
        """
        self.lgr.info(string_write("New controller notification {}", self.clientid))
        data = {
            T_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            T_CLIENTID: self.clientid,
        }
        pub_ctrlcmd(self._subscriber, self.tcfg.mqtt_qos, data)

    def add_agent(self, agentid, host, nodes):
        """Register started agent"""
        if self.chk.available_agents.get(agentid) is None:
            self.chk.available_agents[agentid] = AgentInfo(agentid, host, AgentStatus.ONLINE, nodes)
            self.lgr.info(string_write("Agent {} added", agentid))
        else:
            self.chk.available_agents[agentid].nodes = nodes
            self.lgr.info(string_write("Agent {} updated", agentid))
        self.chk.host2aid.__setitem__(host, agentid)

    def del_agent(self, agentid):
        """Unregister started agent"""
        if self.chk.available_agents.get(agentid):
            del self.chk.available_agents[agentid]
            self.lgr.info(string_write("Agent {} removed", agentid))

    def _do_init(self):
        """
        _host: IP address of agent

        """
        self.lgr.info(string_write("Do initialization"))
        try:
            for aname in self.trcfg.target_agents:
                agent = self.nwcfg.agent_by_name(aname)
                self.chk.expected_agents.append(agent[T_HOST])
            self.register_routes()
            self.create_mqtt_subscriber(*self.tcfg.mqtt)
            ControllerBase.initialized = True
        except Exception as ex:
            self.lgr.error(string_write("Failed to initialize: {}", ex))

    def create_mqtt_subscriber(self, host, port):
        """Create MQTT subscriber"""
        pass

    def register_routes(self):
        """Register topic routes and sub handlers"""
        pass

    def node_to_host(self):
        """Map node address to connected host
        """
        self.lgr.info("Map node address to host")
        for agent in self.nwcfg.agents:
            [self.chk.node2host.__setitem__(node, agent[T_HOST]) for node in agent[T_NODES]]

    def load_configs(self, inuithy_cfgpath, traffic_cfgpath):
        """Load runtime configure from inuithy configure file,
        load traffic definitions from traffic file
        """
        is_configured = True
        try:
            self._inuithy_cfg = create_inuithy_cfg(inuithy_cfgpath)
            if self._inuithy_cfg is None:
                self.lgr.error(string_write("Failed to load inuithy configure"))
                return False
            self._traffic_cfg = create_traffic_cfg(traffic_cfgpath)
            if self._traffic_cfg is None:
                self.lgr.error(string_write("Failed to load traffics configure"))
                return False
            self._network_cfg = create_network_cfg(self._traffic_cfg.nw_cfgpath)
            if self._network_cfg is None:
                self.lgr.error(string_write("Failed to load network configure"))
                return False
            self.node_to_host()
            is_configured = True
        except Exception as ex:
            self.lgr.error(string_write("Configure failed: {}", ex))
            is_configured = False
        return is_configured

    def load_storage(self):
        self.lgr.info(string_write("Load DB plugin:{}", self.tcfg.storagetype))
        try:
            self._storage = Storage(self.tcfg, self.lgr)
        except Exception as ex:
            self.lgr.error(string_write("Failed to load plugin: {}", ex))

