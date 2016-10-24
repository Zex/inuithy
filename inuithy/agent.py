## Agent application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, signal, sys, logging
import logging.config as lconf
import paho.mqtt.client as mqtt
import threading as thrd
from inuithy.util.cmd_helper import *
from inuithy.util.config_manager import *
from inuithy.common.serial_adapter import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyAgent')

class Agent:
    """
    Message Flow:
                        register
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
    def traffic(self):
        return self.__traffic

    @traffic.setter
    def traffic(self, val):
        pass

    @property
    def tcfg(self):
        return self.__inuithy_cfg

    @tcfg.setter
    def tcfg(self, val):
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
        userdata.topic_routes[message.topic](message)

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
            self.unregister()
            self.__subscriber.disconnect()

    def __del__(self):
        pass

    def __str__(self):
        return string_write("clientid:[{}] host:[{}] heartbeat:[{}]", self.clientid, self.host, self.enable_heartbeat)
    
    def register(self):
        """Register an agent to controller
        """
        logger.info(string_write("Registering {}", self.clientid))
        pub_register(self.__subscriber, self.tcfg.mqtt_qos, self.clientid, self.__sad.nodes)

    def unregister(self):
        """Unregister an agent from controller
        """
        logger.info(string_write("Unregistering {}", self.clientid))
        try:
            pub_unregister(self.__subscriber, self.tcfg.mqtt_qos, self.clientid)
        except Exception as ex:
            logger.error(string_write("Unregister failed"))

    def create_subscriber(self, host, port):
        self.topic_routes = {
            INUITHY_TOPIC_COMMAND:  self.on_topic_command,
            INUITHY_TOPIC_CONFIG:   self.on_topic_config,
            INUITHY_TOPIC_TRAFFIC:  self.on_topic_traffic,
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
            (INUITHY_TOPIC_COMMAND, self.tcfg.mqtt_qos),
        ])
        self.ctrlcmd_routes = {
            CtrlCmds.NEW_CONTROLLER.name:               self.on_new_controller,
            CtrlCmds.AGENT_RESTART.name:                self.on_agent_restart,
            CtrlCmds.AGENT_STOP.name:                   self.on_agent_stop,
            CtrlCmds.AGENT_ENABLE_HEARTBEAT.name:       self.on_agent_enable_heartbeat,
            CtrlCmds.AGENT_DISABLE_HEARTBEAT.name:      self.on_agent_disable_heartbeat,
        }

    def get_clientid(self):
        rd = ''
        if self.tcfg.enable_localdebug:
            from random import randint
            rd = string_write('-{}', hex(randint(1000000,10000000))[2:])
        return string_write(INUITHYAGENT_CLIENT_ID, self.host+rd)

    def set_host(self):
        try:
            self.__host = getpredefaddr()
        except Exception as ex:
            logger.error(string_write("Failed to get predefined static address: {}", ex))
            try:
                self.__host = socket.gethostname() #socket.gethostbyname(socket.gethostname())
            except Exception as ex:
                logger.error(string_write("Failed to get host by name: {}", ex))

    def __do_init(self):
        """
        __host: IP address of agent
        __clientid: identity in MQ network
        """
        logger.info(string_write("Do initialization"))
        try:
            self.set_host()
            self.__clientid = self.get_clientid()
            self.__sad = SerialAdapter()
            self.create_subscriber(*self.tcfg.mqtt)
            self.__traffics = []
            if self.tcfg.workmode == WorkMode.MONITOR.name:
                self.__enable_heartbeat = True
            self.initialized = True
        except Exception as ex:
            logger.error(string_write("Failed to initialize: {}", ex))
    
    def __init__(self, cfgpath='config/inuithy.conf', lg=None):
        self.__initialized = False
        self.__enable_heartbeat = False
        self.__inuithy_cfg = InuithyConfig(cfgpath)
        if lg != None:
            global logger
            logger = lg
        if False == self.__inuithy_cfg.load():
            logger.error(string_write("Failed to load configure"))
        else:
            self.__do_init()

    def ctrlcmd_dispatch(self, command):
        logger.info(string_write("Receive command [{}]", command))
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            logger.error(string_write('Invalid command [{}]', command))
            return
        ctrlcmd = cmds[0]
        try:
            if self.ctrlcmd_routes.has_key(ctrlcmd):
                self.ctrlcmd_routes[ctrlcmd](command[len(ctrlcmd)+1:])
            else:
                logger.error(string_write('Invalid command [{}]', command))
        except Exception as ex:
                logger.error(string_write('Exception on handling command [{}]:{}', command, ex))
#        if Agent.__mutex_msg.acquire():
#            # TODO
#            Agent.__mutex_msg.release()


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
            self.teardown()
            logger.error(string_write("Agent received keyboard interrupt"))
        finally:
            logger.info(string_write("Agent terminated"))

    def on_topic_command(self, message):
        """Command message format:
        <command> <parameters>
        """
        logger.info(string_write("On topic command"))
        try:
            self.ctrlcmd_dispatch(message.payload.strip())
        except Exception as ex:
            logger.error(string_write("Exception on dispating control command: {}", ex))

    def on_topic_config(self, message):
        """Config message format:
        <key> <value>
        """
        logger.info(string_write("On topic config"))
        try:
            # TODO
            pass
        except Exception as ex:
            logger.error(string_write("Exception on updating config: {}", ex))

    def on_topic_traffic(self, message):
        logger.info(string_write("On topic traffic"))
        command = message.payload.strip()
        cmds = valid_cmds(message.payload)
        if len(cmds) == 0:
            logger.error(string_write('Invalid command [{}]', command))
            return
        ctrlcmd = cmds[0]
        if ctrlcmd == 'start':
            self.start_traffic
            return
        self.__traffic.append(command)

    def start_traffic(self):
        try:
            #TODO
            #[t.run for t in self.traffic]
            pass
        except Exception as ex:
            logger.error(string_write("Exception on running traffic [{}]: {}", t, ex))

    def on_new_controller(self, message):
        logger.info(string_write("New controller"))
        self.register()

    def on_agent_restart(self, message):
        logger.info(string_write("Restart agent"))
        #TODO
        pass

    def on_agent_stop(self, message):
        if message == None or len(message) == 0:
            return
        if message in ['*', self.__host, self.__clientid]:
            logger.info(string_write("Stop agent"))
            self.teardown()

    def on_agent_enable_heartbeat(self, message):
        logger.info(string_write("Enable heartbeat"))
        self.__enable_heartbeat = True

    def on_agent_disable_heartbeat(self, message):
        logger.info(string_write("Disable heartbeat"))
        self.__enable_heartbeat = False

def start_agent(cfgpath):
    agent = Agent(cfgpath)
    agent.start()

if __name__ == '__main__':
    logger.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Agent"))
    start_agent(INUITHY_CONFIG_PATH)

