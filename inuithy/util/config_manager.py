## Configure manager for Inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging
import logging.config as lconf
from inuithy.common.predef import *

# Configure keywords
CFGKW_WORKMODE          = 'workmode'
CFGKW_MQTT              = 'mqtt'
CFGKW_HOST              = 'host'
CFGKW_PORT              = 'port'
CFGKW_QOS               = 'qos'
CFGKW_CONTROLLER        = 'controller'
CFGKW_AGENTS            = 'agents'
CFGKW_ENABLE_LDEBUG     = 'enable_localdebug'
CFGKW_TRAFFIC_STORAGE   = 'traffic_storage'
CFGKW_TYPE              = 'type'
CFGKW_PATH              = 'path'
CFGKW_USER              = 'user'
CFGKW_PASSWD            = 'passwd'

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('ConfigManager')

class ConfigManager:
    """Configure manager
    """
    @property
    def config_path(self):
        return self.__config_path

    def config_path(self, val):
        if val == None or len(val) == 0:
            logger.error("Invalid config path")
            return
        self.__config_path = val

    @property
    def mqtt(self):
        return self.config[CFGKW_MQTT][CFGKW_HOST], self.config[CFGKW_MQTT][CFGKW_PORT]

    @mqtt.setter
    def mqtt(self, val):
        pass

    @property
    def mqtt_qos(self):
        return self.config[CFGKW_MQTT][CFGKW_QOS]
      
    @mqtt_qos.setter
    def mqtt_qos(self):
        pass

    @property
    def workmode(self):
        return self.config[CFGKW_WORKMODE]

    @workmode.setter
    def workmode(self, val):
        pass

    @property
    def controller(self):
        return self.config[CFGKW_CONTROLLER][HOST]

    @controller.setter
    def controller(self, val):
        pass

    @property
    def agents(self):
        return self.config[CFGKW_AGENTS].values()

    @agents.setter
    def agents(self, val):
        pass

    @property
    def enable_localdebug(self):
        return self.config[CFGKW_ENABLE_LDEBUG]

    @enable_localdebug.setter
    def enable_localdebug(self, val):
        pass

    def __init__(self, path):
        self.config_path = path
        self.config = {}

    def create_dummy_config(self):
        self.config[CFGKW_MQTT] = {
            CFGKW_HOST: '127.0.0.1',
            CFGKW_PORT: 1883,
            CFGKW_QOS:  0
        }
        # Work mode the framework should run in
        # - WorkMode.AUTO
        # - WorkMode.MANUAL
        # - WorkMode.MONITOR
        self.config[CFGKW_WORKMODE] = WorkMode.AUTO.name
        self.config[CFGKW_CONTROLLER] = {
            CFGKW_HOST:'127.0.0.1',
        }
        # Expected agent list
        self.config[CFGKW_AGENTS] = {
            'agent_0':{
                CFGKW_HOST:'127.0.0.1',
            },
            'agent_1':{
                CFGKW_HOST:'127.0.0.2',
            },
            'agent_2':{
                CFGKW_HOST:'127.0.0.3',
            }
        }
        self.config[CFGKW_ENABLE_LDEBUG] = False
        self.config[CFGKW_TRAFFIC_STORAGE] = {
            # Storage types:
            # - TrafficStorage.DB
            # - TrafficStorage.FILE
            CFGKW_TYPE:     TrafficStorage.DB.name,
            # Path to traffic database
            # - For database storage, the path is host and port combination formated as <host>:<port>
            # - For local file storage, the path is absolute or relative path to storage file on local machine
            CFGKW_PATH:     '127.0.0.1:7671',
            # Authentication for storage access if required
            CFGKW_USER:     '',
            CFGKW_PASSWD:   '',
        }

    def load(self):
        logger.info("Loading configure from [{}]".format(self.config_path))
        ret = True
        if self.config_path.endswith('yaml'):
            ret  = self.load_yaml()
        elif self.config_path.endswith('json'):
            ret = self.load_json()
        else:
            if self.load_yaml() == False and self.load_json == False:
                logger.error("Unsupported format for config file")
                ret = False
        return ret

    def dump_yaml(self):
        try:
            import yaml
            with open(self.config_path, 'w') as fd:
                yaml.dump(self.config, fd)
        except Exception as ex:
            logger.error("dumping yaml config file [{}]: {}".format(self.config_path, ex))

    def dump_json(self):
        try:
            import json
            with open(self.config_path, 'w') as fd:
                json.dump(self.config, fd)
        except Exception as ex:
            logger.error("dumping json config file [{}]: {}".format(self.config_path, ex))

    def load_yaml(self):
        ret = True
        try:
            import yaml
            with open(self.config_path, 'r') as fd:
                self.config = yaml.load(fd)
        except Exception as ex:
            logger.error("loading yaml config file [{}]: {}".format(self.config_path, ex))
            ret = False
        return ret

    def load_json(self):
        ret = True
        try:
            import json
            with open(self.config_path, 'r') as fd:
                self.config = json.load(fd)
        except Exception as ex:
            logger.error("loading json config file [{}]: {}".format(self.config_path, ex))
            ret = False
        return ret

if __name__ == '__main__':
    logger.info(INUITHY_TITLE.format(INUITHY_VERSION, "ConfigManager"))
    cfg = ConfigManager(INUITHY_CONFIG_PATH)
    cfg.create_dummy_config()
    cfg.dump_yaml()
    cfg.config_path = INUITHY_CONFIG_PATH.replace('yaml', 'json')
    cfg.dump_json()



