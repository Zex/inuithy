## Configure manager for Inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging
import logging.config as lconf
from inuithy.util.helper import *

# Configure keywords
CFGKW_WORKMODE          = 'workmode'
CFGKW_MQTT              = 'mqtt'
CFGKW_HOST              = 'host'
CFGKW_PORT              = 'port'
CFGKW_QOS               = 'qos'
CFGKW_CONTROLLER        = 'controller'
CFGKW_AGENTS            = 'agents'
CFGKW_ENABLE_LDEBUG     = 'enable_localdebug'
CFGKW_ENABLE_MQDEBUG    = 'enable_mqdebug'
CFGKW_TRAFFIC_STORAGE   = 'traffic_storage'
CFGKW_TYPE              = 'type'
CFGKW_PATH              = 'path'
CFGKW_USER              = 'user'
CFGKW_PASSWD            = 'passwd'
CFGKW_TSH               = 'inuithy_shell'
CFGKW_HISTORY           = 'history'
CFGKW_SUBNET            = 'subnet'
CFGKW_NODES             = 'nodes'
CFGKW_GATEWAY           = 'gateway'
CFGKW_PKGSIZE           = 'pkgsize'
CFGKW_PKGRATE           = 'pkgrate'
CFGKW_RECIPIENTS        = 'recipients'
CFGKW_SENDERS           = 'senders'
CFGKW_DURATION          = 'duration'
CFGKW_TARGET_TRAFFICS   = 'target_traffics'
CFGKW_NWCONFIG          = 'nwconfig'
CFGKW_NWCONFIG_ID_FMT   = '{}:{}'
CFGKW_TRAFFICS          = 'traffics'

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyConfig')

class Config:
    """Basic configure
    """
    @property
    def config_path(self):
        return self.__config_path

    def config_path(self, val):
        if val == None or len(val) == 0:
            logger.error("Invalid config path")
            return
        self.__config_path = val
    
    def __init__(self, path):
        self.config_path = path
        self.config = {}

    def __str__(self):
        return '\n'.join([self.config_path, str(self.config)])

    def load(self):
        logger.info(string_write("Loading configure from [{}]", self.config_path))
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
            logger.error(string_write("dumping yaml config file [{}]: {}", self.config_path, ex))

    def dump_json(self):
        try:
            import json
            with open(self.config_path, 'w') as fd:
                json.dump(self.config, fd)
        except Exception as ex:
            logger.error(string_write("dumping json config file [{}]: {}", self.config_path, ex))

    def load_yaml(self):
        ret = True
        try:
            import yaml
            with open(self.config_path, 'r') as fd:
                self.config = yaml.load(fd)
        except Exception as ex:
            logger.error(string_write("loading yaml config file [{}]: {}", self.config_path, ex))
            ret = False
        return ret

    def load_json(self):
        ret = True
        try:
            import json
            with open(self.config_path, 'r') as fd:
                self.config = json.load(fd)
        except Exception as ex:
            logger.error(string_write("loading json config file [{}]: {}", self.config_path, ex))
            ret = False
        return ret

    def dump_protobuf(self):
        logger.error("Not implemented")
        return False

    def load_protobuf(self):
        logger.error("Not implemented")
        return False

class InuithyConfig(Config):
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
    def enable_localdebug(self):
        return self.config[CFGKW_ENABLE_LDEBUG]

    @enable_localdebug.setter
    def enable_localdebug(self, val):
        pass

    @property
    def enable_mqdebug(self):
        return self.config[CFGKW_ENABLE_MQDEBUG]

    @enable_mqdebug.setter
    def enable_mqdebug(self, val):
        pass

    @property
    def tsh_hist(self):
        return self.config[CFGKW_TSH][CFGKW_HISTORY]

    @tsh_hist.setter
    def tsh_hist(self, val):
        pass

    def create_sample(self):
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
        self.config[CFGKW_ENABLE_LDEBUG] = True
        self.config[CFGKW_ENABLE_MQDEBUG] = False
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
        # Inuithy shell config
        self.config[CFGKW_TSH]  = {
            CFGKW_HISTORY: '/home/lab/.inuithy.cache',
        }

class NetworkConfig(Config):
    """
    """
    @property
    def agents(self):
        return self.config[CFGKW_AGENTS].values()

    @agents.setter
    def agents(self, val):
        pass

    def create_sample(self):
        # Expected agent list
        self.config[CFGKW_AGENTS] = {
        'agent_0': {
            CFGKW_HOST:     '127.0.0.1',
            CFGKW_NODES:    [
                '0x1111', '0x1112', '0x1113', '0x1114',
            ],
        },
        'agent_1': {
            CFGKW_HOST:     '127.0.0.2',
            CFGKW_NODES:    [
                '0x1121', '0x1122', '0x1123', '0x1124',
            ],
        },
        'agent_2': {
            CFGKW_HOST:     '127.0.0.3',
            CFGKW_NODES:    [
                '0x1131', '0x1132', '0x1133', '0x1134',
                ],
        },
        'agent_3': {
            CFGKW_HOST:     '127.0.0.4',
            CFGKW_NODES:    [
                '0x1141', '0x1142', '0x1143', '0x1144',
            ],
        },
        }
        # Expected network layout
        self.config['network_0'] = {
            'subnet_0': {
                CFGKW_GATEWAY   : '0x1122',
                CFGKW_NODES     : [
                    '0x1111', '0x1112', '0x1113', '0x1114',
                    '0x1122', '0x1123', '0x1124', '0x1134',
                ],
            },
            'subnet_1': {
                CFGKW_GATEWAY   : '0x1144',
                CFGKW_NODES     : [
                    '0x1121', '0x1131', '0x1132', '0x1133',
                    '0x1141', '0x1142', '0x1143', '0x1144',
                ],
            },
        }
        self.config['network_1'] = {
            'subnet_0': {
                CFGKW_GATEWAY   : '0x1122',
                CFGKW_NODES     : [
                    '0x1111', '0x1112', '0x1113', '0x1114',
                    '0x1122', '0x1123', '0x1124', '0x1134',
                    '0x1121', '0x1131', '0x1132', '0x1133',
                    '0x1141', '0x1142', '0x1143', '0x1144',
                ],
            },
        }
        self.config['network_2'] = {
            'subnet_0': {
                CFGKW_GATEWAY   : '0x1122',
                CFGKW_NODES     : [
                    '0x1111', '0x1112', '0x1113', '0x1114',
                    '0x1122', '0x1123', '0x1124', '0x1134',
                ],
            },
            'subnet_1': {
                CFGKW_GATEWAY   : '0x1121',
                CFGKW_NODES     : [
                    '0x1121', '0x1131', '0x1132', '0x1133',
                ]
            },
            'subnet_2': {
                CFGKW_GATEWAY   : '0x1144',
                CFGKW_NODES     : [
                    '0x1141', '0x1142', '0x1143', '0x1144',
                ],
            },
        }
        
class TrafficConfig(Config):
    """
    """
    def create_sample(self):
        # Network config to use
        self.config["traffic_0"] = {
            CFGKW_NWCONFIG  : string_write(CFGKW_NWCONFIG_ID_FMT, NETWORK_CONFIG_PATH, 'network_2'),
            CFGKW_SENDERS   : [
                '0x1111', '0x1112', '0x1113', '0x1114',
            ],
            CFGKW_RECIPIENTS: [
                '0x1122', '0x1123', '0x1124', '0x1134',
            ],
            # package / seconds
            CFGKW_PKGRATE   : 0.5,
            CFGKW_PKGSIZE   : 1,
            # seconds
            CFGKW_DURATION  : 180,
        }
        self.config["traffic_1"] = {
            CFGKW_NWCONFIG  : string_write(CFGKW_NWCONFIG_ID_FMT, NETWORK_CONFIG_PATH, 'network_0'),
            CFGKW_SENDERS   : [
                '0x1114'
            ],
            CFGKW_RECIPIENTS: [
                '0x1122', '0x1123', '0x1124', '0x1134'
            ],
            # package / seconds
            CFGKW_PKGRATE   : 0.5,
            CFGKW_PKGSIZE   : 2,
            # seconds
            CFGKW_DURATION  : 180,
        }
        self.config["traffic_2"] = {
            CFGKW_NWCONFIG  : string_write(CFGKW_NWCONFIG_ID_FMT, NETWORK_CONFIG_PATH, 'network_1'),
            CFGKW_SENDERS   : [
                '0x1123',
            ],
            CFGKW_RECIPIENTS: [
                '0x1122',
            ],
            # package / seconds
            CFGKW_PKGRATE   : 0.2,
            CFGKW_PKGSIZE   : 2,
            # seconds
            CFGKW_DURATION  : 360,
        }
        # Traffics to run
        self.config[CFGKW_TARGET_TRAFFICS] = [
            "traffic_0", "traffic_2",
        ]

if __name__ == '__main__':
    logger.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "InuithyConfig"))

    cfg = InuithyConfig(INUITHY_CONFIG_PATH)
    cfg.create_sample()
    cfg.dump_yaml()
    cfg.config_path = INUITHY_CONFIG_PATH.replace('yaml', 'json')
    cfg.dump_json()

    cfg = NetworkConfig(NETWORK_CONFIG_PATH)
    cfg.create_sample()
    cfg.dump_yaml()
    cfg.config_path = NETWORK_CONFIG_PATH.replace('yaml', 'json')
    cfg.dump_json()

    cfg = TrafficConfig(TRAFFIC_CONFIG_PATH)
    cfg.create_sample()
    cfg.dump_yaml()
    cfg.config_path = TRAFFIC_CONFIG_PATH.replace('yaml', 'json')
    cfg.dump_json()


