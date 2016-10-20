## Controller application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
import socket, signal, sys
from inuithy.common.predef import *
from inuithy.common.commands import *
from inuithy.util.config_manager import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyController')

class Controller:
    """
    """
    __mutex = thrd.Lock()

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
    def cfgmng(self):
        return self.__cfg_mng

    @cfgmng.setter
    def cfgmng(self, val):
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

    @staticmethod
    def on_connect(client, userdata, rc):
        logger.info("MQ.Connection client:{} userdata:[{}] rc:{}".format(client, userdata, rc))
        if 0 != rc:
            logger.info("MQ.Connection: connection error")

    @staticmethod
    def on_message(client, userdata, message):
        logger.info("MQ.Message: userdata:[{}]".format(userdata))
        logger.info("MQ.Message: message "+INUITHY_MQTTMSGFMT.format(
            message.dup, message.info, message.mid, message.payload, 
            message.qos, message.retain, message.state, message.timestamp,
            message.topic))
        userdata.topic_handlers[message.topic](message)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        logger.info("MQ.Disconnection: client:{} userdata:[{}] rc:{}".format(client, userdata, rc))
        if 0 != rc:
            logger.info("MQ.Disconnection: disconnection error")

    @staticmethod
    def on_log(client, userdata, level, buf):
        mqlog_map(logger, level, buf)

    @staticmethod
    def on_publish(client, userdata, mid):
        logger.info("MQ.Publish: client:{} userdata:[{}], mid:{}".format(client, userdata, mid))

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        logger.info("MQ.Subscribe: client:{} userdata:[{}], mid:{}, grated_qos:{}".format(client, userdata, mid, granted_qos))

    def teardown(self):
        if self.initialized:
            self.__subscriber.disconnect()

    def __del__(self):
        pass

    def __str__(self):
        return "subscriber:{}".format(self.__subscriber)
    
    def create_mqtt_subscriber(self, host, port):
        self.topic_handlers = {
            INUITHY_TOPIC_REGISTER:  self.on_topic_register,
            INUITHY_TOPIC_STATUS:    self.on_topic_status,
            INUITHY_TOPIC_RESPONSE:  self.on_topic_response,
        }
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect = Controller.on_connect
        self.__subscriber.on_message = Controller.on_message
        self.__subscriber.on_disconnect = Controller.on_disconnect
        self.__subscriber.on_log = Controller.on_log
        self.__subscriber.on_publish = Controller.on_publish
        self.__subscriber.on_subscribe = Controller.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_REGISTER,  self.cfgmng.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER,self.cfgmng.mqtt_qos),
            (INUITHY_TOPIC_STATUS,    self.cfgmng.mqtt_qos),
            (INUITHY_TOPIC_RESPONSE,  self.cfgmng.mqtt_qos),
        ])

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        __expected_agents: list of agents
        __available_agents: agentid => AgentInfo
        """
        logger.info("Do initialization")
        try:
            self.__expected_agents = self.cfgmng.agents
            self.__available_agents = {}
            self.__host = socket.gethostbyname(socket.gethostname())
            self.__clientid = INUITHYCONTROLLER_CLIENT_ID.format(self.host)
            self.create_mqtt_subscriber(*self.cfgmng.mqtt)
            self.initialized = True
        except Exception as ex:
            logger.error("Failed to initialize:{}".format(ex))

    def __init__(self, cfgpath='config/inuithy.conf'):
        self.__initialized = False
        self.__cfg_mng = ConfigManager(cfgpath)
        if False == self.__cfg_mng.load():
            logger.error("Failed to load configure")
        else:
            self.__do_init()

    def add_agent(self, agentid):
        self.__available_agents[agentid] = AgentInfo(agentid, AgentStatus.ONLINE)

    def add_agent(self, agentid):
        del self.__available_agents[agentid]

    def on_topic_register(self, message):
        """Register message format:
        <agentid>
        """
        logger.info("On topic register")
        agentid = agent_id_from_payload(message.payload)
        if len(agentid) == 0:
            logger.error("Invalid agent ID")
            return
        try:
            self.add_agent(agentid)
            logger.info("Agent {} added".format(agentid))
            logger.info("Expected Agents({}): {}".format(len(self.__expected_agents), self.__expected_agents))
            logger.info("Available Agents({}): {}".format(len(self.__available_agents), self.__available_agents))
        except:
            logger.error("Exception on registering agent {}".format(agentid))

    def on_topic_unregister(self, message):
        """Unregister message format:
        <agentid>
        """
        logger.info("On topic register")
        agentid = agent_id_from_payload(message.payload)
        if len(agentid) == 0:
            logger.error("Invalid agent ID")
            return
        try:
            self.remove_agent(agentid)
            logger.info("Agent {} removed".format(agentid))
            logger.info("Available Agents({}): {}".format(len(self.__available_agents), self.__available_agents))
        except:
            logger.error("Exception on unregistering agent {}".format(agentid))

    def on_topic_status(self, message):
        logger.info("On topic status")

    def on_topic_response(self, message):
        logger.info("On topic response")

    def alive_notification(self):
        """Broadcast on new controller startup
        """
        logger.info("New controller notification {}".format(self.clientid))
        self.__subscriber.publish(INUITHY_TOPIC_COMMAND, create_payload(self.clientid), self.cfgmng.mqtt_qos, False)

    def start(self):
        if not self.initialized:
            logger.error("Controller not initialized")
            return

        try:
            logger.info("Expected Agents({}): {}".format(len(self.__expected_agents), self.__expected_agents))
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            self.__subscriber.disconnect()
            logger.info("Controller received keyboard interrupt")
        finally:
            logger.info("Controller terminated")

def start_controller(cfgpath):
    controller = Controller(cfgpath)
    controller.start()

if __name__ == '__main__':
    logger.info(INUITHY_TITLE.format(INUITHY_VERSION, "Controller"))
    start_controller(INUITHY_CONFIG_PATH)

