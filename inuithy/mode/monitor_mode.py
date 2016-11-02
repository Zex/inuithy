""" MonitorController application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import T_CTRLCMD, CtrlCmd, T_CLIENTID,\
T_NODE, T_HOST, T_NODES, TRAFFIC_CONFIG_PATH, INUITHY_TOPIC_HEARTBEAT,\
INUITHY_TOPIC_STATUS, INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION,\
T_TID, T_TRAFFIC_STATUS, TrafficStatus, AgentStatus,\
TRAFFIC_CONFIG_PATH, string_write, INUITHYCONTROLLER_CLIENT_ID,\
INUITHY_TOPIC_UNREGISTER, T_TRAFFIC_TYPE, T_PANID, TrafficType,\
INUITHY_CONFIG_PATH, INUITHY_TITLE, INUITHY_LOGCONFIG
from inuithy.util.cmd_helper import pub_ctrlcmd, stop_agents
from inuithy.util.config_manager import create_inuithy_cfg, create_traffic_cfg,\
create_network_cfg
from inuithy.common.agent_info import AgentInfo
from inuithy.util.traffic_state import TrafficState, TrafStatChk
from inuithy.storage.storage import Storage
import paho.mqtt.client as mqtt
import socket, logging
import logging.config as lconf
import threading as thrd

lconf.fileConfig(INUITHY_LOGCONFIG)

class MonitorController(object):
    """
    Message Flow:
                        heartbeat
        Agent -------------------------> MonitorController
                        command
        Agent <------------------------- MonitorController
                         config
        Agent <------------------------- MonitorController
                        traffic
        Agent <------------------------- MonitorController
                       newcontroller
        Agent <------------------------- MonitorController
                        response
        Agent -------------------------> MonitorController
                         status
        Agent -------------------------> MonitorController
                        unregister
        Agent -------------------------> MonitorController
    """
    __mutex = thrd.Lock()
    __mutex_msg = thrd.Lock()

    @property
    def traffic_state(self):
        return self.__traffic_state
    @traffic_state.setter
    def traffic_state(self, val):
        pass

    @property
    def clientid(self):
        return self.__clientid
    @clientid.setter
    def clientid(self, val):
        pass

    @property
    def subscriber(self):
        return self.__subscriber
    @subscriber.setter
    def subscriber(self, val):
        pass

    @property
    def host(self):
        return self.__host
    @host.setter
    def host(self, val):
        pass

    @property
    def storage(self):
        return self.__storage
    @storage.setter
    def storage(self, val):
        pass

    @property
    def tcfg(self):
        """Inuithy configure
        """
        return self.__inuithy_cfg
    @tcfg.setter
    def tcfg(self, val): pass

    @property
    def nwcfg(self):
        """Network configure
        """
        return self.__network_cfg
    @nwcfg.setter
    def nwcfg(self, val): pass

    @property
    def trcfg(self):
        """Traffic configure
        """
        return self.__traffic_cfg
    @trcfg.setter
    def trcfg(self, val):
        pass

    @property
    def available_agents(self):
        return self.chk.available_agents
    @available_agents.setter
    def available_agents(self, val):
        pass

    @property
    def expected_agents(self):
        return self.chk.expected_agents
    @expected_agents.setter
    def expected_agents(self, val):
        pass

    @property
    def node2host(self):
        return self.chk.node2host
    @node2host.setter
    def node2host(self, val):
        pass

    @property
    def host2aid(self):
        return self.chk.host2aid
    @host2aid.setter
    def host2aid(self, val):
        pass

    @property
    def initialized():
        return MonitorController.__initialized
    @initialized.setter
    def initialized(val):
        if MonitorController.__mutex.acquire_lock():
            if not MonitorController.__initialized:
                MonitorController.__initialized = val
            MonitorController.__mutex.release()

    @property
    def current_nwlayout(self):
        """FORMAT: <networkconfig_path>:<networklayout_name>"""
        return getnwlayoutid(*self.__current_nwlayout)

    @current_nwlayout.setter
    def current_nwlayout(self, val):
        if not isinstance(val, tuple):
            raise TypeError("Tuple expected")
        self.__current_nwlayout = val

    @staticmethod
    def on_connect(client, userdata, rc):
        userdata.lgr.info(string_write(
            "MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if 0 != rc:
            userdata.lgr.info(string_write("MQ.Connection: connection error"))

    @staticmethod
    def on_message(client, userdata, message):
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
        userdata.lgr.info(string_write(
            "MQ.Disconnection: client:{} userdata:[{}] rc:{}",
            client, userdata, rc))
        if 0 != rc:
            userdata.lgr.info(string_write("MQ.Disconnection: disconnection error"))

    @staticmethod
    def on_log(client, userdata, level, buf):
        mqlog_map(userdata.lgr, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        userdata.lgr.info(string_write(
            "MQ.Publish: client:{} userdata:[{}], mid:{}", client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        userdata.lgr.info(string_write(
            "MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}",
            client, userdata, mid, granted_qos))

    def teardown(self):
        try:
            if MonitorController.initialized:
                self.lgr.info("Stop agents")
                stop_agents(self.__subscriber, self.tcfg.mqtt_qos)
                MonitorController.initialized = False
                if self.__traffic_timer is not None:
                    self.__traffic_timer.cancel()
                self.__traffic_state.running = False
                self.storage.close()
                self.__subscriber.disconnect()
        except Exception as ex:
            self.lgr.error(string_write("Exception on teardown: {}", ex))

    def __del__(self):
        pass

    def __str__(self):
        return string_write("clientid:[{}] host:[{}]", self.clientid, self.host)

    def create_mqtt_subscriber(self, host, port):
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect = MonitorController.on_connect
        self.__subscriber.on_message = MonitorController.on_message
        self.__subscriber.on_disconnect = MonitorController.on_disconnect
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_HEARTBEAT, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION, self.tcfg.mqtt_qos),
        ])

    def register_routes(self):
        self.topic_routes = {
            INUITHY_TOPIC_HEARTBEAT:      self.on_topic_heartbeat,
            INUITHY_TOPIC_UNREGISTER:     self.on_topic_unregister,
            INUITHY_TOPIC_STATUS:         self.on_topic_status,
            INUITHY_TOPIC_REPORTWRITE:    self.on_topic_reportwrite,
            INUITHY_TOPIC_NOTIFICATION:   self.on_topic_notification,
        }

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network

        """
        self.lgr.info(string_write("Do initialization"))
        try:
            for aname in self.trcfg.target_agents:
                agent = self.nwcfg.agent_by_name(aname)
                self.chk.expected_agents.append(agent[T_HOST])
            self.register_routes()
            self.create_mqtt_subscriber(*self.tcfg.mqtt)
            MonitorController.initialized = True
        except Exception as ex:
            self.lgr.error(string_write("Failed to initialize: {}", ex))

    def load_configs(self, inuithy_cfgpath, traffic_cfgpath):
        """Load runtime configure from inuithy configure file,
        load traffic definitions from traffic file
        """
        is_configured = True
        try:
            self.__inuithy_cfg = create_inuithy_cfg(inuithy_cfgpath)
            if self.__inuithy_cfg is None:
                self.lgr.error(string_write("Failed to load inuithy configure"))
                return False
            self.__traffic_cfg = create_traffic_cfg(traffic_cfgpath)
            if self.__traffic_cfg is None:
                self.lgr.error(string_write("Failed to load traffics configure"))
                return False
            self.__network_cfg = create_network_cfg(self.__traffic_cfg.nw_cfgpath)
            if self.__network_cfg is None:
                self.lgr.error(string_write("Failed to load network configure"))
                return False
            self.__current_nwlayout = ('', '')
            self.node_to_host()
            is_configured = True
        except Exception as ex:
            self.lgr.error(string_write("Configure failed: {}", ex))
            is_configured = False
        return is_configured

    def load_storage(self):
        self.lgr.info(string_write("Load DB plugin:{}", self.tcfg.storagetype))
        try:
            self.__storage = Storage(self.tcfg, self.lgr)
        except Exception as ex:
            self.lgr.error(string_write("Failed to load plugin: {}", ex))

    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        """
        @delay Start traffic after @delay seconds
        """
        if lgr is not None:
            self.lgr = lgr
        else:
            self.lgr = logging
        MonitorController.__initialized = False
        self.__subscriber = None
        self.__storage = None
        self.__host = socket.gethostname()
        self.__clientid = string_write(INUITHYCONTROLLER_CLIENT_ID, self.host)
        self.chk = TrafStatChk()
        if self.load_configs(inuithy_cfgpath, traffic_cfgpath):
            self.__do_init()
            self.load_storage()
            self.__traffic_state = TrafficState(self)
            self.__traffic_timer = thrd.Timer(delay, self.__traffic_state.start)

    def node_to_host(self):
        self.lgr.info("Map node address to host")
        for agent in self.nwcfg.agents:
            [self.chk.node2host.__setitem__(node, agent[T_HOST]) for node in agent[T_NODES]]

    def start(self):
        if not MonitorController.initialized:
            self.lgr.error(string_write("MonitorController not initialized"))
            return
        try:
            self.lgr.info(string_write("Expected Agents({}): {}",
                len(self.chk.expected_agents), self.chk.expected_agents))
            self.__alive_notification()
            if self.__traffic_timer is not None:
                self.__traffic_timer.start()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            self.lgr.info(string_write("MonitorController received keyboard interrupt"))
        except Exception as ex:
            self.lgr.error(string_write("Exception on MonitorController: {}", ex))
        finally:
            self.teardown()
            self.lgr.info(string_write("MonitorController terminated"))

    def add_agent(self, agentid, host, nodes):
        if self.chk.available_agents.get(agentid) is None:
            self.chk.available_agents[agentid] = AgentInfo(agentid, host, AgentStatus.ONLINE, nodes)
            self.lgr.info(string_write("Agent {} added", agentid))
        else:
            self.chk.available_agents[agentid].nodes = nodes
            self.lgr.info(string_write("Agent {} updated", agentid))
        self.chk.host2aid.__setitem__(host, agentid)

    def del_agent(self, agentid):
        if self.chk.available_agents.get(agentid):
            del self.chk.available_agents[agentid]
            self.lgr.info(string_write("Agent {} removed", agentid))

    def on_topic_heartbeat(self, message):
        """Heartbeat message format:
        """
#        self.lgr.info(string_write("On topic heartbeat"))
        data = extract_payload(message.payload)
        agentid, host, nodes = data[T_CLIENTID], data[T_HOST], data[T_NODES]
        try:
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
        except Exception as ex:
            self.lgr.error(string_write("Exception on registering agent {}: {}", agentid, ex))

    def on_topic_unregister(self, message):
        """Unregister message format:
        <agentid>
        """
        self.lgr.info(string_write("On topic unregister"))
        data = extract_payload(message.payload)
        agentid = data[T_CLIENTID]
        try:
            self.del_agent(agentid)
            self.lgr.info(string_write("Available Agents({}): {}",
                len(self.chk.available_agents), self.chk.available_agents))
        except Exception as ex:
            self.lgr.error(string_write("Exception on unregistering agent {}: {}", agentid, ex))

    def on_topic_status(self, message):
        self.lgr.info(string_write("On topic status"))
        data = extract_payload(message.payload)
        if data.get(T_TRAFFIC_STATUS) == TrafficStatus.FINISHED.name:
            self.lgr.info(string_write("Traffic finished on {}", data.get(T_CLIENTID)))
            self.chk.traffire[data.get(T_CLIENTID)] = True
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.REGISTERED.name:
            self.lgr.info(string_write("Traffic {} registered on {}",
                data.get(T_TID), data.get(T_CLIENTID)))
            self.chk.traffic_set[data.get(T_TID)] = True
        else:
            self.lgr.debug(string_write("Unhandled status message {}", data))

    def on_topic_reportwrite(self, message):
#        self.lgr.info(string_write("On topic reportwrite"))
        data = extract_payload(message.payload)
        self.storage.insert_record(data)

    def on_topic_notification(self, message):
#       self.lgr.info(string_write("On topic notification"))
        data = extract_payload(message.payload)
        try:
            if data[T_TRAFFIC_TYPE] == TrafficType.JOIN.name:
                if None != self.chk.nwlayout.get(data[T_PANID]):
                    self.chk.nwlayout[data[T_PANID]][data[T_NODE]] = True
            elif data[T_TRAFFIC_TYPE] == TrafficType.SCMD.name:
                pass
            self.lgr.debug("NOTIFY: {}", data)
            self.storage.insert_record(data)
        except Exception as ex:
            self.lgr.error(string_write("Update nwlayout failed", ex))

    def __alive_notification(self):
        """Broadcast on new controller startup
        """
        self.lgr.info(string_write("New controller notification {}", self.clientid))
        data = {
            T_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            T_CLIENTID: self.clientid,
        }
        pub_ctrlcmd(self.__subscriber, self.tcfg.mqtt_qos, data)

def start_controller(tcfg, trcfg, lgr=None):
    controller = MonitorController(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyMonitorController')
    lgr.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "MonitorController"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

