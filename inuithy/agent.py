## Agent application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
import socket, signal, sys
from common.predef import *
from util.config_manager import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyAgent')

class Agent:
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
        if __mutex.acquire_lock():
            if not self.__initialized:
                self.__initialized = True
            __mutex.release()

    @staticmethod
    def on_connect(client, userdata, rc):
        logger.info("MQ.Connection client:{} userdata:[{}] rc:{}".format(client, userdata, rc))

    @staticmethod
    def on_message(client, userdata, message):
        logger.info("MQ.Message: userdata:[{}]".format(userdata))
        logger.info("MQ.Message: message "+INUITHY_MQTTMSGFMT.format(
            message.dup, message.info, message.mid, message.payload, 
            message.qos, message.retain, message.state, message.timestamp,
            message.topic))
        userdata.topic_handlers[message.topic](userdata, message)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        logger.info("MQ.Disconnection: client:{} userdata:[{}] rc:{}".format(client, userdata, rc))

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
    
    def register(self):
        """Register an agent to controller
        """
        logger.info("Register {}".format(self.clientid))
        self.__subscriber.publish(INUITHY_TOPIC_REGISTER, create_payload(self.clientid), 2, False)

    def create_subscriber(self, host, port):
        self.__topic_handlers = {
            INUITHY_TOPIC_COMMAND:  self.on_topic_command,
        }
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect = Agent.on_connect
        self.__subscriber.on_message = Agent.on_message
        self.__subscriber.on_disconnect = Agent.on_disconnect
        self.__subscriber.on_log = Agent.on_log
        self.__subscriber.on_publish = Agent.on_publish
        self.__subscriber.on_subscribe = Agent.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_COMMAND, 2),
        ])

    def get_clientid(self):
        return INUITHYAGENT_CLIENT_ID.format(self.host)

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        logger.info("Do initialization")
        try:
            self.__host = socket.gethostbyname(socket.gethostname())
            self.__clientid = self.get_clientid()
            self.create_subscriber(*self.cfgmng.mqtt)
            self.register()
            self.initialized = True
        except Exception as ex:
            logging.error("Failed to initialize")
    
    def __init__(self, cfgpath='config/inuithy.conf'):
        self.__initialized = False
        self.__cfg_mng = ConfigManager(cfgpath)
        if False == self.__cfg_mng.load():
            logger.error("Failed to load configure")
        else:
            self.__do_init()

    def on_topic_command(self, message):
        """Command message format:
        <agentid>::><command message>
        """
        logger.info("On topic command")
        agentid = agent_id_from_payload(message.payload)
        if len(agentid) == 0 or agentid != self.clientid:
            return
        parse_command(message_from_payload)

    def parse_command(msg):
        logger.info("Receive command [{}]".format(msg))

    def start(self):
        if not self.initialized:
            logger.error("Agent not initialized")
            return

        try:
            logger.info("Starting Agent {}".format(self.clientid))
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            self.__subscriber.disconnect()
            logger.error("Agent received keyboard interrupt")
        finally:
            logger.info("Agent terminated")

def start_agent(cfgpath):
    agent = Agent(cfgpath)
    agent.start()

if __name__ == '__main__':
    logger.info("Inuithy ver {} Agent".format(INUITHY_VERSION))
    start_agent("config/inuithy_config.yaml")

