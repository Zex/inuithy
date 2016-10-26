## Controller application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
from inuithy.util.cmd_helper import *
from inuithy.util.config_manager import *
from inuithy.common.traffic import *
from inuithy.common.agent_info import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyController')

class Controller:
    """
    Message Flow:
                        register
        Agent -------------------------> Controller
                        command
        Agent <------------------------- Controller
                         config
        Agent <------------------------- Controller
                        traffic
        Agent <------------------------- Controller
                       newcontroller
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
    def tcfg(self):
        """Inuithy configure
        """
        return self.__inuithy_cfg

    @tcfg.setter
    def tcfg(self, val):
        pass

    @property
    def nwcfg(self):
        """Network configure
        """
        return self.__network_cfg

    @nwcfg.setter
    def nwcfg(self, val):
        pass

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
        return self.__available_agents
    
    @available_agents.setter
    def available_agents(self, val):
        pass

    @property
    def node2host(self):
        return self.__node2host

    @node2host.setter
    def node2host(self, val):
        pass

    @property
    def initialized(self):
        return self.__initialized

    @initialized.setter
    def initialized(self, val):
        if Controller.__mutex.acquire_lock():
            if not self.__initialized:
                self.__initialized = True
            Controller.__mutex.release()
    
    @property
    def current_nwlayout(self):
        """FORMAT: <networkconfig_path>:<networklayout_name>"""
        return getnwlayoutid(*self.__current_nwlayout)

    @current_nwlayout.setter
    def current_nwlayout(self, val):
        if not isinstance(tuple, val):
            raise TypeError("Tuple expected")
        self.__current_nwlayout = val

    @staticmethod
    def on_connect(client, userdata, rc):
        logger.info(string_write("MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if 0 != rc:
            logger.info(string_write("MQ.Connection: connection error"))

    @staticmethod
    def on_message(client, userdata, message):
        logger.info(string_write("MQ.Message: userdata:[{}]", userdata))
        logger.info(string_write("MQ.Message: message "+INUITHY_MQTTMSGFMT, 
            message.dup, message.info, message.mid, message.payload, 
            message.qos, message.retain, message.state, message.timestamp,
            message.topic))
        try:
            userdata.topic_routes[message.topic](message)
        except Exception as ex:
            logger.error(string_write("Exception on MQ message dispatching: {}", ex))

    @staticmethod
    def on_disconnect(client, userdata, rc):
        logger.info(string_write("MQ.Disconnection: client:{} userdata:[{}] rc:{}", client, userdata, rc))
        if 0 != rc:
            logger.info(string_write("MQ.Disconnection: disconnection error"))

    @staticmethod
    def on_log(client, userdata, level, buf):
        mqlog_map(logger, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        logger.info(string_write("MQ.Publish: client:{} userdata:[{}], mid:{}", client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        logger.info(string_write("MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}", client, userdata, mid, granted_qos))

    def teardown(self):
        try:
            if self.initialized:
                self.__subscriber.disconnect()
        except Exception as ex:
            logger.error(string_write("Exception on teardown: {}", ex))

    def __del__(self):
        pass

    def __str__(self):
        return string_write("clientid:[{}] host:[{}]", self.clientid, self.host)
    
    def create_mqtt_subscriber(self, host, port):
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect    = Controller.on_connect
        self.__subscriber.on_message    = Controller.on_message
        self.__subscriber.on_disconnect = Controller.on_disconnect
        self.__subscriber.on_log        = Controller.on_log
        #self.__subscriber.on_publish    = Controller.on_publish
        self.__subscriber.on_subscribe  = Controller.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_REGISTER,      self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER,    self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS,        self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE,   self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION,  self.tcfg.mqtt_qos),
        ])

    def register_routes(self):
        self.topic_routes = {
            INUITHY_TOPIC_REGISTER:       self.on_topic_register,
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
        logger.info(string_write("Do initialization"))
        try:
            self.__expected_agents = self.trcfg.target_agents
            self.__available_agents = {}
            self.__host = socket.gethostname()
            self.__clientid = string_write(INUITHYCONTROLLER_CLIENT_ID, self.host)
            self.register_routes()
            self.create_mqtt_subscriber(*self.tcfg.mqtt)
            self.initialized = True
        except Exception as ex:
            logger.error(string_write("Failed to initialize: {}", ex))

    def load_configs(self, inuithy_cfgpath, traffic_cfgpath):
        is_configured = True
        try:
            self.__inuithy_cfg    = InuithyConfig(inuithy_cfgpath)
            if False == self.__inuithy_cfg.load():
                logger.error(string_write("Failed to load inuithy configure"))
                return False
            self.__traffic_cfg  = TrafficConfig(traffic_cfgpath) 
            if False == self.__traffic_cfg.load():
                logger.error(string_write("Failed to load traffics configure"))
                return False
            self.__network_cfg  = NetworkConfig(self.__traffic_cfg.nw_cfgpath) 
            if False == self.__network_cfg.load():
                logger.error(string_write("Failed to load network configure"))
                return False
            self.__current_nwlayout = ('', '')
            self.node_to_host()
            is_configured = True
        except Exception as ex:
            logger.error(string_write("Configure failed: {}", ex))
            is_configured = False
        return is_configured

    def __init__(self, inuithy_cfgpath='config/inuithy.conf', traffic_cfgpath='config/traffics.conf', lg=None):
        self.__initialized = False
        self.__node2host = {}
        if lg != None:
            global logger
            logger = lg
        if self.load_configs(inuithy_cfgpath, traffic_cfgpath):
            self.__do_init()
#    def whohas(self, addr):
#        """Find out which host has node with given address connected
#        """
#        for aid, ainfo in self.available_agents.items():
#            if ainfo.has_node(addr) != None:
#                logger.info(string_write("{} has node {}", aid, addr))
#                return aid
#        return None
    def node_to_host(self):
        logger.info("Map node address to host")
        for agent in self.nwcfg.agents:
            [self.__node2host.__setitem__(node, agent[CFGKW_HOST]) for node in agent[CFGKW_NODES]]


    def config_node_address(self):
        # TODO
        pass

    def config_network(self, nwlayoutname):
        """Configure network by given network layout
        """
        logger.info(string_write("Config network: [{}]", nwlayoutname))

        for subnet in self.nwcfg.config[nwlayoutname].values():
            data = subnet
            for node in subnet[CFGKW_NODES]:
                if not self.__node2host.has_key(node):
                    raise ValueError(string_write("Node [{}] not found on any agent", node))
                target_agent = self.__node2host[node]
                data[CFGKW_CLIENTID]     = target_agent,
                data[CFGKW_NODE]         = node
                data[CFGKW_TRAFFIC_TYPE] = TrafficType.JOIN.name
                pub_traffic(self.subscriber, self.tcfg.mqtt_qos, data)

    def run_traffics(self):
        logger.info(string_write("Run traffics, mode:[{}]", self.tcfg.workmode))
        if self.tcfg.workmode != WorkMode.AUTO.name or not self.initialized:
            return

        self.trgens = create_traffics(self.trcfg, self.nwcfg)
        logger.info(string_write("Total generator: [{}]", len(self.trgens)))
        for tg in self.trgens:
            # configure network layout
            try:
                logger.info(string_write("Current traffic [{}]", str(tg)))
                if self.current_nwlayout != tg.nwlayoutid:
                    self.config_network(getnwlayoutname(tg.nwlayoutid))
            except Exception as ex:
                logger.error(string_write("Exception on configuring network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, ex))

            # start trafngfic
            if self.is_network_layout_done() and self.tcfg.workmode == WorkMode.AUTO.name:
                self.register_traffic(tg)

    def is_network_layout_done(self):
        logger.info("Is network layout done")
        #TODO
        return False

    def register_traffic(self, tg):
        logger.info(string_write("Register traffic: [{}]", str(tg)))
        for tr in tg.traffics:
            try:
                logger.debug(string_write("TRAFFIC: {}", tr))
                data = {
                CFGKW_SENDER:       tr.sender,
                CFGKW_RECIPIENT:    tr.recipient,
                CFGKW_PKGSIZE:      tr.pkgsize,
                }
                pub_traffic(self.subscriber, self.tcfg.mqtt_qos, data)
            except Exception as ex:
                logger.error(string_write("Exception on publishing traffic, network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, ex))


    def start(self):
        if not self.initialized:
            logger.error(string_write("Controller not initialized"))
            return
        try:
            logger.info(string_write("Expected Agents({}): {}", len(self.__expected_agents), self.__expected_agents))
            self.__alive_notification()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            logger.info(string_write("Controller received keyboard interrupt"))
        except Exception as ex:
            logger.error(string_write("Exception on Controller: {}", ex))
        finally:
            self.teardown()
            logger.info(string_write("Controller terminated"))

    def add_agent(self, agentid, host, nodes):
        self.__available_agents[agentid] = AgentInfo(agentid, host, AgentStatus.ONLINE, nodes)
        logger.info(string_write("Agent {} added", agentid))

    def del_agent(self, agentid):
        if self.__available_agents.has_key(agentid):
            del self.__available_agents[agentid]
            logger.info(string_write("Agent {} removed", agentid))

    def is_agents_all_up(self):
        logger.info("Is agent all up")
        logger.debug(string_write("Expected Agents({}): {}", len(self.__expected_agents), self.__expected_agents))
        logger.debug(string_write("Available Agents({}): {}",
            len(self.__available_agents),
            [str(a) for a in self.__available_agents.values()]))

        if len(self.__expected_agents) != len(self.__available_agents):
            return False

        exps = []
        for aname in self.__expected_agents:
            agent = self.nwcfg.agent_by_name(aname)
            exps.append(agent[CFGKW_HOST])
        avails = []
        for ai in self.__available_agents.values():
            if ai.host not in exps: return False
        if self.tcfg.enable_localdebug:
            return True

        return True

    def on_topic_register(self, message):
        """Register message format:
        <agentid>
        """
        logger.info(string_write("On topic register"))
        agentid, host, nodes = extract_register(message.payload)
        if len(agentid) == 0:
            logger.error(string_write("Invalid agent ID"))
            return
        try:
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
        except Exception as ex:
            logger.error(string_write("Exception on registering agent {}: {}", agentid, ex))

        if self.tcfg.workmode == WorkMode.AUTO.name and self.is_agents_all_up():
            self.run_traffics()

    def on_topic_unregister(self, message):
        """Unregister message format:
        <agentid>
        """
        logger.info(string_write("On topic register"))
        agentid = agent_id_from_payload(message.payload)
        if len(agentid) == 0:
            logger.error(string_write("Invalid agent ID"))
            return
        try:
            self.del_agent(agentid)
            logger.info(string_write("Available Agents({}): {}", len(self.__available_agents), self.__available_agents))
        except Exception as ex:
            logger.error(string_write("Exception on unregistering agent {}: {}", agentid, ex))

    def on_topic_status(self, message):
        logger.info(string_write("On topic status"))
        logger.debug(message.payload)

    def on_topic_reportwrite(self, message):
        logger.info(string_write("On topic reportwrite"))
        logger.debug(message.payload)
        #TODO

    def on_topic_notification(self, message):
        logger.info(string_write("On topic notification"))
        logger.debug(message.payload)
        #TODO

    def __alive_notification(self):
        """Broadcast on new controller startup
        """
        logger.info(string_write("New controller notification {}", self.clientid))
        pub_newctrl(self.__subscriber, self.tcfg.mqtt_qos, self.clientid)

def start_controller(tcfg, trcfg):
    controller = Controller(tcfg, trcfg)
    controller.start()

if __name__ == '__main__':
    logger.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Controller"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)

