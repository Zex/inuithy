## Agent application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, signal, sys, logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
from inuithy.util.helper import *
from inuithy.util.config_manager import *
from inuithy.common.serial_adapter import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyAgent')

class Agent:
    """
    """
    __mutex     = thrd.Lock()
    __mutex_msg = thrd.Lock()

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
    def enable_heartbeat(self):
        return self.__enable_heartbeat

    @enable_heartbeat.setter
    def enable_heartbeat(self):
        pass

    @property
    def initialized(self):
        return self.__initialized

    @initialized.setter
    def initialized(self, val):
        if Agent.__mutex.acquire_lock():
            if not self.__initialized:
                self.__initialized = True
            Agent.__mutex.release()

    @staticmethod
    def on_connect(client, userdata, rc):
        logger.info(string_write("MQ.Connection client:{} userdata:[{}] rc:{}", client, userdata, rc))

    @staticmethod
    def on_message(client, userdata, message):
        logger.info(string_write("MQ.Message: userdata:[{}]", userdata))
        logger.info(string_write("MQ.Message: message "+INUITHY_MQTTMSGFMT, 
            message.dup, message.info, message.mid, message.payload, 
            message.qos, message.retain, message.state, message.timestamp,
            message.topic))
        userdata.topic_handlers[message.topic](message)

    @staticmethod
    def on_disconnect(client, userdata, rc):
        logger.info(string_write("MQ.Disconnection: client:{} userdata:[{}] rc:{}", client, userdata, rc))

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
        return string_write("subscriber:{}", self.__subscriber)
    
    def register(self):
        """Register an agent to controller
        """
        logger.info(string_write("Registering {}", self.clientid))
        pub_register(self.__subscriber, self.cfgmng.mqtt_qos, self.clientid, self.__sad.nodes)

    def unregister(self):
        """Unregister an agent from controller
        """
        logger.info(string_write("Unregistering {}", self.clientid))
        try:
            pub_unregister(self.__subscriber, self.cfgmng.mqtt_qos, self.clientid)
        except Exception as ex:
            logger.error(string_write("Unregister failed"))

    def create_subscriber(self, host, port):
        self.topic_handlers = {
            INUITHY_TOPIC_COMMAND:  self.on_topic_command,
        }
        self.__subscriber = mqtt.Client(self.clientid, True, self)
        self.__subscriber.on_connect    = Agent.on_connect
        self.__subscriber.on_message    = Agent.on_message
        self.__subscriber.on_disconnect = Agent.on_disconnect
        self.__subscriber.on_log        = Agent.on_log
        self.__subscriber.on_publish    = Agent.on_publish
        self.__subscriber.on_subscribe  = Agent.on_subscribe
        self.__subscriber.connect(host, port)
        self.__subscriber.subscribe([
            (INUITHY_TOPIC_COMMAND, self.cfgmng.mqtt_qos),
        ])
        self.ctrlcmd_handlers = {
            CtrlCmds.NEW_CONTROLLER.name:               self.on_new_controller,
            CtrlCmds.AGENT_RESTART.name:                self.on_agent_restart,
            CtrlCmds.AGENT_STOP.name:                   self.on_agent_stop,
            CtrlCmds.AGENT_ENABLE_HEARTBEAT.name:       self.on_agent_enable_heartbeat,
            CtrlCmds.AGENT_DISABLE_HEARTBEAT.name:      self.on_agent_disable_heartbeat,
            CtrlCmds.TRAFFIC.name:                      self.on_traffic,
        }


    def get_clientid(self):
        rd = ''
        if self.cfgmng.enable_localdebug:
            from random import randint
            rd = string_write('-{}', hex(randint(1000000,10000000))[2:])
        return string_write(INUITHYAGENT_CLIENT_ID, self.host+rd)

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        logger.info(string_write("Do initialization"))
        try:
            self.__host = socket.gethostbyname(socket.gethostname())
            self.__clientid = self.get_clientid()
            self.__sad = SerialAdapter()
            self.create_subscriber(*self.cfgmng.mqtt)
            self.initialized = True
        except Exception as ex:
            logger.error(string_write("Failed to initialize: {}", ex))
    
    def __init__(self, cfgpath='config/inuithy.conf'):
        self.__initialized = False
        self.__cfg_mng = ConfigManager(cfgpath)
        if False == self.__cfg_mng.load():
            logger.error(string_write("Failed to load configure"))
        else:
            self.__do_init()

    def ctrlcmd_dispatch(self, command):
        logger.info(string_write("Receive command [{}]", command))
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            logging.error(string_write('Invalid command [{}]', command))
            return
        ctrlcmd = cmds[0]
        try:
            if self.ctrlcmd_handlers.has_key(ctrlcmd):
                self.ctrlcmd_handlers[ctrlcmd](command[len(ctrlcmd)+1:])
            else:
                logging.error(string_write('Invalid command [{}]', command))
        except Exception as ex:
                logging.error(string_write('Exception on handling command [{}]', command))
#        if Agent.__mutex_msg.acquire():
#            # TODO
#            Agent.__mutex_msg.release()

    def on_topic_command(self, message):
        """Command message format:
        <command> <parameters>
        """
        logger.info(string_write("On topic command"))
        try:
            self.ctrlcmd_dispatch(message.payload.strip())
        except Exception as ex:
            logger.error(string_write("Exception on dispating control command: {}", ex))

    def on_new_controller(self, message):
        logger.info(string_write("New controller"))
        self.register()

    def on_agent_restart(self, message):
        logger.info(string_write("Restart agent"))
        #TODO
        pass

    def on_agent_stop(self, message):
        logger.info(string_write("Stop agent"))
        #TODO
        pass

    def on_agent_enable_heartbeat(self, message):
        logger.info(string_write("Enable heartbeat"))
        self.__enable_heartbeat = True

    def on_agent_disable_heartbeat(self, message):
        logger.info(string_write("Disable heartbeat"))
        self.__enable_heartbeat = False

    def on_traffic(self, message):
        logger.info(string_write("Traffic command"))
        #TODO
        pass

    def start(self):
        if not self.initialized:
            logger.error(string_write("Agent not initialized"))
            return

        try:
            logger.info(string_write("Starting Agent {}", self.clientid))
            self.__sad.scan_nodes()
            logger.info(string_write("Connected nodes: [{}]", self.__sad.nodes))
            self.register()
            self.__subscriber.loop_forever()
        except KeyboardInterrupt:
            self.unregister()
            self.__subscriber.disconnect()
            logger.error(string_write("Agent received keyboard interrupt"))
        finally:
            logger.info(string_write("Agent terminated"))

def start_agent(cfgpath):
    agent = Agent(cfgpath)
    agent.start()

if __name__ == '__main__':
    logger.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Agent"))
    start_agent(INUITHY_CONFIG_PATH)

