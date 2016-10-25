## Controller application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, signal, sys, logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
from inuithy.util.cmd_helper import *
from inuithy.util.config_manager import *
from inuithy.common.traffic import *

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
        userdata.topic_routes[message.topic](message)

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
        if self.initialized:
            self.__subscriber.disconnect()

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
        self.__subscriber.on_publish    = Controller.on_publish
        self.__subscriber.on_subscribe  = Controller.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_REGISTER,  self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER,self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS,    self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_RESPONSE,  self.tcfg.mqtt_qos),
        ])

    def register_routes(self):
        self.topic_routes = {
            INUITHY_TOPIC_REGISTER:       self.on_topic_register,
            INUITHY_TOPIC_UNREGISTER:     self.on_topic_unregister,
            INUITHY_TOPIC_STATUS:         self.on_topic_status,
            INUITHY_TOPIC_RESPONSE:       self.on_topic_response,
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
            self.__expected_agents = self.nwcfg.agents
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
            is_configured = True
        except Exception as ex:
            logger.error(string_write("Configure failed", ex))
            is_configured = False
        return is_configured

    def __init__(self, inuithy_cfgpath='config/inuithy.conf', traffic_cfgpath='config/traffics.conf', lg=None):
        self.__initialized = False
        self.trgens = []
        if lg != None:
            global logger
            logger = lg
        if self.load_configs(inuithy_cfgpath, traffic_cfgpath):
            self.__do_init()
        if self.tcfg.workmode == WorkMode.AUTO and self.initialized:
            self.trgens = create_traffics(self.trcfg, self.nwcfg)

    def config_network(self, tg):
        """Configure network for given traffic generator
        """
        logger.info(string_write("Config network: [{}] for [{}]", tg.nwlayout, tg.traffic_name))
        #TODO
        #pub_traffic()

    def run_traffics(self):
        logger.info(string_write("Run traffics"))
        if self.trgens == None or len(self.trgens) == 0: return
        logger.info("Total generator: [{}]", len(self.trgens))
        for tg in tgs:
            logger.info(str(tg))
#            logger.info(string_write('\n'.join([str(traffic) for traffic in tg.traffics])))
            if self.current_nwlayout != tg.nwlayoutid:
                self.config_network(tg)

            pub_traffic(self.subscriber, self.tcfg.mqtt_qos, data, "*")

    def start(self):
        if not self.initialized:
            logger.error(string_write("Controller not initialized"))
            return
        try:
            logger.info(string_write("Expected Agents({}): {}", len(self.__expected_agents), self.__expected_agents))
            self.__alive_notification()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            self.__subscriber.disconnect()
            logger.info(string_write("Controller received keyboard interrupt"))
        finally:
            logger.info(string_write("Controller terminated"))

    def add_agent(self, agentid, nodes):
        self.__available_agents[agentid] = AgentInfo(agentid, AgentStatus.ONLINE, nodes)
        logger.info(string_write("Agent {} added", agentid))

    def del_agent(self, agentid):
        if self.__available_agents.has_key(agentid):
            del self.__available_agents[agentid]
            logger.info(string_write("Agent {} removed", agentid))

    def whohas(self, addr):
        """Find out which host has node with given address connected
        """
        for aid, ainfo in self.available_agents.items():
            if ainfo.has_node(addr) != None:
                logger.info(string_write("{} has node {}", aid, addr))
                return aid
        return None

    def on_topic_register(self, message):
        """Register message format:
        <agentid>
        """
        logger.info(string_write("On topic register"))
        agentid, nodes = extract_register(message.payload)
        if len(agentid) == 0:
            logger.error(string_write("Invalid agent ID"))
            return
        try:
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, nodes)
            logger.info(string_write("Expected Agents({}): {}", len(self.__expected_agents), self.__expected_agents))
            logger.info(string_write("Available Agents({}): {}", len(self.__available_agents), 
                        [str(a) for a in self.__available_agents.values()]))
        except Exception as ex:
            logger.error(string_write("Exception on registering agent {}: {}", agentid, ex))

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

    def on_topic_response(self, message):
        logger.info(string_write("On topic response"))

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

