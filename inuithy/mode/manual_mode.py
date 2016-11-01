## ManualController application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
from inuithy.util.cmd_helper import *
from inuithy.util.config_manager import *
#from inuithy.common.traffic import *
from inuithy.common.agent_info import *
from inuithy.util.traffic_state import *
from inuithy.storage.storage import Storage

lconf.fileConfig(INUITHY_LOGCONFIG)
lg = logging.getLogger('InuithyManualController')

class ManualController:
    """
    Message Flow:
                        heartbeat
        Agent -------------------------> ManualController
                        command
        Agent <------------------------- ManualController
                         config
        Agent <------------------------- ManualController
                        traffic
        Agent <------------------------- ManualController
                       newcontroller
        Agent <------------------------- ManualController
                        response
        Agent -------------------------> ManualController
                         status
        Agent -------------------------> ManualController
                        unregister
        Agent -------------------------> ManualController
    """
    __mutex = thrd.Lock()
    __mutex_msg = thrd.Lock()

    @property
    def traffic_state(self): return self.__traffic_state
    @traffic_state.setter
    def traffic_state(self, val): pass

    @property
    def clientid(self): return self.__clientid
    @clientid.setter
    def clientid(self, val): pass

    @property
    def subscriber(self): return self.__subscriber
    @subscriber.setter
    def subscriber(self, val): pass

    @property
    def host(self): return self.__host
    @host.setter
    def host(self, val): pass

    @property
    def storage(self): return self.__storage
    @storage.setter
    def storage(self, val): pass

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
    def trcfg(self, val): pass

    @property
    def available_agents(self): return self.__available_agents
    @available_agents.setter
    def available_agents(self, val): pass

    @property
    def node2host(self): return self.__node2host
    @node2host.setter
    def node2host(self, val): pass

    @property
    def host2aid(self): return self.__host2aid
    @host2aid.setter
    def host2aid(self, val): pass

    @property
    def initialized(): return ManualController.__initialized
    @initialized.setter
    def initialized(val):
        if ManualController.__mutex.acquire_lock():
            if not ManualController.__initialized:
                ManualController.__initialized = val
            ManualController.__mutex.release()
    
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
        userdata.lg.info(string_write("MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if 0 != rc:
            userdata.lg.info(string_write("MQ.Connection: connection error"))

    @staticmethod
    def on_message(client, userdata, message):
#        userdata.lg.info(string_write("MQ.Message: userdata:[{}]", userdata))
#        userdata.lg.info(string_write("MQ.Message: message "+INUITHY_MQTTMSGFMT, 
#            message.dup, message.info, message.mid, message.payload, 
#            message.qos, message.retain, message.state, message.timestamp,
#            message.topic))
        try:
            userdata.topic_routes[message.topic](message)
        except Exception as ex:
            userdata.lg.error(string_write("Exception on MQ message dispatching: {}", ex))

    @staticmethod
    def on_disconnect(client, userdata, rc):
        userdata.lg.info(string_write("MQ.Disconnection: client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if 0 != rc:
            userdata.lg.info(string_write("MQ.Disconnection: disconnection error"))

    @staticmethod
    def on_log(client, userdata, level, buf):
        mqlog_map(lg, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        userdata.lg.info(string_write("MQ.Publish: client:{} userdata:[{}], mid:{}", client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        userdata.lg.info(string_write("MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}", client, userdata, mid, granted_qos))

    def teardown(self):
        try:
            if ManualController.initialized:
                self.stop_agents()
                ManualController.initialized = False
                self.__traffic_timer.cancel()
                self.storage.close()
                self.__subscriber.disconnect()
        except Exception as ex:
            self.lg.error(string_write("Exception on teardown: {}", ex))

    def start_agents(self):
        self.lg.info("Start agents") 
        cmd = 'pushd /opt/inuithy;nohup python3 inuithy/agent.py'
        for host in self.__expected_agents:
            runonremote('root', host, cmd)

    def stop_agents(self):
        self.lg.info("Stop agents") 
        data = {
            CFGKW_CTRLCMD:  CtrlCmd.AGENT_STOP.name,
            CFGKW_CLIENTID: "*",
        }
        pub_ctrlcmd(self.__subscriber, self.tcfg.mqtt_qos, data)
            

    def __del__(self): pass

    def __str__(self): return string_write("clientid:[{}] host:[{}]", self.clientid, self.host)
    
    def create_mqtt_subscriber(self, host, port):
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect    = ManualController.on_connect
        self.__subscriber.on_message    = ManualController.on_message
        self.__subscriber.on_disconnect = ManualController.on_disconnect
#        self.__subscriber.on_log        = ManualController.on_log
#       self.__subscriber.on_publish    = ManualController.on_publish
#       self.__subscriber.on_subscribe  = ManualController.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_HEARTBEAT,     self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER,    self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS,        self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE,   self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION,  self.tcfg.mqtt_qos),
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
        __expected_agents: list of agents
        __available_agents: agentid => AgentInfo

        """
        self.lg.info(string_write("Do initialization"))
        try:
            for aname in self.trcfg.target_agents:
                agent = self.nwcfg.agent_by_name(aname)
                self.__expected_agents.append(agent[CFGKW_HOST])
            self.__host = socket.gethostname()
            self.__clientid = string_write(INUITHYCONTROLLER_CLIENT_ID, self.host)
            self.register_routes()
            self.create_mqtt_subscriber(*self.tcfg.mqtt)
            ManualController.initialized = True
        except Exception as ex:
            self.lg.error(string_write("Failed to initialize: {}", ex))

    def load_configs(self, inuithy_cfgpath, traffic_cfgpath):
        """Load runtime configure from inuithy configure file, load traffic definitions from traffic file
        """
        is_configured = True
        try:
            self.__inuithy_cfg    = InuithyConfig(inuithy_cfgpath)
            if False == self.__inuithy_cfg.load():
                self.lg.error(string_write("Failed to load inuithy configure"))
                return False
            self.__traffic_cfg  = TrafficConfig(traffic_cfgpath) 
            if False == self.__traffic_cfg.load():
                self.lg.error(string_write("Failed to load traffics configure"))
                return False
            self.__network_cfg  = NetworkConfig(self.__traffic_cfg.nw_cfgpath) 
            if False == self.__network_cfg.load():
                self.lg.error(string_write("Failed to load network configure"))
                return False
            self.__current_nwlayout = ('', '')
            self.node_to_host()
            is_configured = True
        except Exception as ex:
            self.lg.error(string_write("Configure failed: {}", ex))
            is_configured = False
        return is_configured

    def load_storage(self):
        self.lg.info(string_write("Load DB plugin:{}", self.tcfg.storagetype))
        try:
            self.__storage = Storage(self.tcfg, lg)
        except Exception as ex:
            self.lg.error(string_write("Failed to load plugin: {}", ex))

    def __init__(self, inuithy_cfgpath='config/inuithy.conf', traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        """
        @delay Start traffic after @delay seconds
        """
        if lgr != None: self.lg = lgr
        else: self.lg = logging
        ManualController.__initialized = False
        self.__expected_agents = []
        self.__available_agents = {}
        self.__node2host = {}
        self.__host2aid = {}
        self.__nwlayout_chk = {}
        self.__storage = None
        if self.load_configs(inuithy_cfgpath, traffic_cfgpath):
            self.__do_init()
            self.load_storage()
            self.__traffic_state = TrafficState(self)#, lg)
            self.__traffic_timer = thrd.Timer(delay, self.__traffic_state.start)
#    def whohas(self, addr):
#        """Find out which host has node with given address connected
#        """
#        for aid, ainfo in self.available_agents.items():
#            if ainfo.has_node(addr) != None:
#                self.lg.info(string_write("{} has node {}", aid, addr))
#                return aid
#        return None
    def node_to_host(self):
        self.lg.info("Map node address to host")
        for agent in self.nwcfg.agents:
            [self.__node2host.__setitem__(node, agent[CFGKW_HOST]) for node in agent[CFGKW_NODES]]

    def start(self):
        if not ManualController.initialized:
            self.lg.error(string_write("ManualController not initialized"))
            return
        try:
            self.lg.info(string_write("Expected Agents({}): {}", len(self.__expected_agents), self.__expected_agents))
            self.__alive_notification()
#            if self.__traffic_timer != None: self.__traffic_timer.start()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            self.lg.info(string_write("ManualController received keyboard interrupt"))
        except Exception as ex:
            self.lg.error(string_write("Exception on ManualController: {}", ex))
        finally:
            self.teardown()
            self.lg.info(string_write("ManualController terminated"))

    def add_agent(self, agentid, host, nodes):
        if self.__available_agents.get(agentid) == None:
            self.__available_agents[agentid] = AgentInfo(agentid, host, AgentStatus.ONLINE, nodes)
            self.lg.info(string_write("Agent {} added", agentid))
        else:
            self.__available_agents[agentid].nodes = nodes
            self.lg.info(string_write("Agent {} updated", agentid))
        self.__host2aid.__setitem__(host, agentid)

    def del_agent(self, agentid):
        if self.__available_agents.get(agentid):
            del self.__available_agents[agentid]
            self.lg.info(string_write("Agent {} removed", agentid))

    def update_nwlayout_chk(self, nwid, nodes):
        if None == nodes or nwid == None: return
        self.__nwlayout_chk[nwid] = {node:False for node in nodes}

    def is_network_layout_done(self):
        self.lg.info("Is network layout done")
        if len(self.__available_agents) == 0:
            raise ValueError("No agent available")
        for nw in self.__nwlayout_chk.values():
            if len([chk for chk in nw if chk == True]) != len(nw):
                return False
        if self.tcfg.enable_localdebug:
            return True

        return False

    def is_traffic_all_set(self):
        self.lg.info("Is traffic all set")
        #TODO
        if len(self.__available_agents) == 0:
            raise ValueError("No agent available")
        if self.tcfg.enable_localdebug:
            return True
        return False

    def is_agents_all_up(self):
#        self.lg.info("Is agent all up")
#        self.lg.debug(string_write("Expected Agents({}): {}", len(self.__expected_agents), self.__expected_agents))
#        self.lg.debug(string_write("Available Agents({}): {}",
#            len(self.__available_agents),
#            [a for a in self.__available_agents.values()]))
#            [str(a) for a in self.__available_agents.values()]))
        # TODO
        if len(self.__expected_agents) != len(self.__available_agents):
            return False

        avails = []
        for ai in self.__available_agents.values():
            if ai.host not in self.__expected_agents: return False
        if self.tcfg.enable_localdebug:
            return True

        return True

    def on_topic_heartbeat(self, message):
        """Heartbeat message format:
        """
#        self.lg.info(string_write("On topic heartbeat"))
        data = extract_payload(message.payload)
        agentid, host, nodes = data[CFGKW_CLIENTID], data[CFGKW_HOST], data[CFGKW_NODES]
        try:
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
        except Exception as ex:
            self.lg.error(string_write("Exception on registering agent {}: {}", agentid, ex))

    def on_topic_unregister(self, message):
        """Unregister message format:
        <agentid>
        """
        self.lg.info(string_write("On topic unregister"))
        data = extract_payload(message.payload)
        agentid = data[CFGKW_CLIENTID]
        try:
            self.del_agent(agentid)
            self.lg.info(string_write("Available Agents({}): {}", len(self.__available_agents), self.__available_agents))
        except Exception as ex:
            self.lg.error(string_write("Exception on unregistering agent {}: {}", agentid, ex))

    def on_topic_status(self, message):
        """
        NODEJOINED
        AGENTSTARTED
        AGENTSTOPPED
        TRAFFICFINISHED
        """
        self.lg.info(string_write("On topic status"))
        self.lg.debug(message.payload)
        #TODO

    def on_topic_reportwrite(self, message):
        self.lg.info(string_write("On topic reportwrite"))
        data = extract_payload(message.payload)
        self.storage.insert_record(data)

    def on_topic_notification(self, message):
        """{'msgtype': 'RECV', 'host': 'feet.pluto', 'channel': 16, 'genid': '581776fa362ac737abefe32e', 'time': '2016-11-01 00:54:04.464784', 'msg': 'joingrp 6262441166221516', 'traffic_type': 'JOIN', 'node': '1132', 'nodes': ['1121', '1131', '1132', '1133', '1141', '1142', '1143', '1144'], 'gateway': '1144', 'clientid': 'inuithy/agent/feet.pluto-93b73a', 'panid': 6262441166221516}

        """
        self.lg.info(string_write("On topic notification"))
        data = extract_payload(message.payload)
        self.lg.debug(string_write("NOTIFY:", data))
        try:
            if data[CFGKW_TRAFFIC_TYPE] == TrafficType.JOIN.name:
                if None != self.__nwlayout_chk.get(data[CFGKW_PANID]):
                    self.__nwlayout_chk[data[CFGKW_PANID]][data[CFGKW_NODE]] = True
        except Exception as ex:
            self.lg.error(string_write("Update nwlayout failed", ex))
        self.storage.insert_record(data)

    def __alive_notification(self):
        """Broadcast on new controller startup
        """
        self.lg.info(string_write("New controller notification {}", self.clientid))
        data = {
            CFGKW_CTRLCMD:  CtrlCmd.NEW_CONTROLLER.name,
            CFGKW_CLIENTID: self.clientid,
        }
        pub_ctrlcmd(self.__subscriber, self.tcfg.mqtt_qos, data)

def start_controller(tcfg, trcfg):
    controller = ManualController(tcfg, trcfg, lg)
    controller.start()

if __name__ == '__main__':
    lg.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "ManualController"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)

