""" Configure manager for Inuithy
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, string_write,\
INUITHY_TITLE, INUITHY_VERSION, INUITHY_CONFIG_PATH, T_ENABLE_LDEBUG,\
T_MQTT, T_WORKMODE, T_ENABLE_MQDEBUG, T_TSH, T_HISTORY, T_QOS,\
T_TARGET_AGENTS, T_NODES, T_PANID, T_NODE, T_NWCONFIG_PATH, T_TYPE,\
T_AGENTS, T_CONTROLLER, T_USER, T_TRAFFIC_STORAGE, T_GENID, T_PATH,\
T_PORT, WorkMode, TrafficStorage, StorageType, T_PASSWD, T_CHANNEL,\
T_GATEWAY, T_TARGET_TRAFFICS, T_DURATION, T_PKGSIZE, T_PKGRATE,\
T_RECIPIENTS, T_SENDERS, T_NWLAYOUT, NETWORK_CONFIG_PATH,\
TRAFFIC_CONFIG_PATH, T_HOST
from abc import ABCMeta, abstractmethod
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

class Config(object):
    """Basic configure
    """
    @property
    def config_path(self):
        return self.__config_path
    @config_path.setter
    def config_path(self, val):
        if val is None or len(val) == 0:
            self.lgr.error("Invalid config path")
            return
        self.__config_path = val

    def __init__(self, path, lgr=None):
        __metaclass__ = ABCMeta
        if lgr is not None:
            self.lgr = lgr
        else:
            self.lgr = logging
        self.config_path = path
        self.config = {}

    def __str__(self):
        return '\n'.join([self.config_path, str(self.config)])

    def load(self):
        self.lgr.info(string_write("Loading configure from [{}]", self.config_path))
        ret = True
        if self.config_path.endswith('yaml'):
            ret = self.load_yaml()
        elif self.config_path.endswith('json'):
            ret = self.load_json()
        else:
            if self.load_yaml() == False and self.load_json == False:
                self.lgr.error("Unsupported format for config file")
                ret = False
        return ret

    def dump_yaml(self):
        try:
            import yaml
            with open(self.config_path, 'w') as fd:
                yaml.dump(self.config, fd)
        except Exception as ex:
            self.lgr.error(string_write("dumping yaml config file [{}]: {}", self.config_path, ex))

    def dump_json(self):
        try:
            import json
            with open(self.config_path, 'w') as fd:
                json.dump(self.config, fd)
        except Exception as ex:
            self.lgr.error(string_write("dumping json config file [{}]: {}", self.config_path, ex))

    def load_yaml(self):
        ret = True
        try:
            import yaml
            with open(self.config_path, 'r') as fd:
                self.config = yaml.load(fd)
        except Exception as ex:
            self.lgr.error(string_write("loading yaml config file [{}]: {}", self.config_path, ex))
            ret = False
        return ret

    def load_json(self):
        ret = True
        try:
            import json
            with open(self.config_path, 'r') as fd:
                self.config = json.load(fd)
        except Exception as ex:
            self.lgr.error(string_write("loading json config file [{}]: {}", self.config_path, ex))
            ret = False
        return ret

    def dump_protobuf(self):
        self.lgr.error("Not implemented")
        return False

    def load_protobuf(self):
        self.lgr.error("Not implemented")
        return False

class InuithyConfig(Config):
    """Configure for Inuithy framework
    """
    def __init__(self, path, lgr=None):
        Config.__init__(self, path, lgr=None)

    @property
    def mqtt(self):
        """MQTT server address"""
        return self.config[T_MQTT][T_HOST], self.config[T_MQTT][T_PORT]
    @mqtt.setter
    def mqtt(self, val):
        pass

    @property
    def mqtt_qos(self):
        """MQTT QOS"""
        return self.config[T_MQTT][T_QOS]
    @mqtt_qos.setter
    def mqtt_qos(self):
        pass

    @property
    def workmode(self):
        """Work mode"""
        return self.config[T_WORKMODE]
    @workmode.setter
    def workmode(self, val):
        pass

    @property
    def controller(self):
        """Controller host"""
        return self.config[T_CONTROLLER][HOST]

    @controller.setter
    def controller(self, val):
        pass

    @property
    def enable_localdebug(self):
        """Enable local debug"""
        return self.config[T_ENABLE_LDEBUG]
    @enable_localdebug.setter
    def enable_localdebug(self, val):
        pass

    @property
    def enable_mqdebug(self):
        """Enable message queue debug"""
        return self.config[T_ENABLE_MQDEBUG]

    @enable_mqdebug.setter
    def enable_mqdebug(self, val):
        pass

    @property
    def tsh_hist(self):
        return self.config[T_TSH][T_HISTORY]
    @tsh_hist.setter
    def tsh_hist(self, val):
        pass

    @property
    def genid_path(self):
        """Path to traffic generator ID file"""
        return self.config[T_GENID][T_PATH]
    @genid_path.setter
    def genid_path(self, val):
        pass
    @property
    def storagetype(self):
        """Storage type"""
        return self.config[T_TRAFFIC_STORAGE][T_TYPE].split(':')
    @storagetype.setter
    def storagetype(self, val):
        pass

    def create_sample(self):
        """Create sample confgigure"""
        self.config[T_MQTT] = {
            T_HOST: '192.168.100.131',
            T_PORT: 1883,
            T_QOS:  0
        }
        # Work mode the framework should run in
        # - WorkMode.AUTO
        # - WorkMode.MANUAL
        # - WorkMode.MONITOR
        self.config[T_WORKMODE] = WorkMode.AUTO.name
        self.config[T_CONTROLLER] = {
            T_HOST:'192.168.100.131',
        }
        self.config[T_ENABLE_LDEBUG] = True
        self.config[T_ENABLE_MQDEBUG] = False
        self.config[T_TRAFFIC_STORAGE] = {
            # Storage types:
            # <TrafficStorage>:<StorageType>
            # - TrafficStorage.DB
            # - TrafficStorage.FILE
            T_TYPE:     string_write("{}:{}", TrafficStorage.DB.name, StorageType.MongoDB.name),
            # Path to traffic database
            # - For database storage, the path is host and port
            #   combination formated as <host>:<port>
            # - For local file storage, the path is absolute or
            #   relative path to storage file on local machine
            T_PATH:     '192.168.100.131:19713',
            # Authentication for storage access if required
            T_USER:     '',
            T_PASSWD:   '',
        }
        # Inuithy shell config
        self.config[T_TSH] = {
            T_HISTORY: '.inuithy.cache',
        }
        self.config[T_GENID] = {
            T_PATH: '.inuithy.genid',
        }

class NetworkConfig(Config):
    """Network layout definition
    General format:
    @code
    <agents> => <agent_name> => <host>
                                <nodes>
             => <agent_name> => <host>
                                <nodes>
    <network_name> => <subnet_name> => <channel>
                                    => <gateway>
                                    => <nodes>
                                    => <panid>
                                    => <subnet_name> => <channel>
                                    => <gateway>
                                    => <nodes>
                                    => <panid>
                                       <network_name> => <subnet_name> => <channel>
                                    => <gateway>
                                    => <nodes>
                                    => <panid>
    @endcode
    - host      IP address
    - panid     PAN ID, hex
    - gateway   Node address, hex
    - channel   Channel, 10-based integer
    - nodes     List of node addresses
    - network_name  Network layout identification
    - subnet_name   Subnet identification
    - agent_name    Agent identification
    """
    @property
    def agents(self):
        return self.config[T_AGENTS].values()

    @agents.setter
    def agents(self, val):
        pass

    def agent_by_name(self, name):
        return self.config[T_AGENTS].get(name)

    def subnet(self, nwlayout_name, subnet_name):
        return self.config[nwlayout_name].get(subnet_name)

    def whohas(self, addr):
        """Find out which host has node with given address connected
        """
        for agent in self.nwcfg.config.agents:
            if addr in agent[T_NODES]:
                self.lgr.info(string_write("Found [{}] on agent [{}]", addr, agent[T_HOST]))
                return agent
        return None

    def create_sample(self):
        # Expected agent list
        self.config[T_AGENTS] = {
            'agent_0': {
                T_HOST:     '192.168.100.131',
                T_NODES:    [
                    '1111', '1112', '1113', '1114',
                ],
            },
            'agent_1': {
                T_HOST:     '192.168.100.132',
                T_NODES:    [
                    '1121', '1122', '1123', '1124',
                ],
            },
            'agent_2': {
                T_HOST:     '192.168.100.133',
                T_NODES:    [
                    '1131', '1132', '1133', '1134',
                    ],
            },
            'agent_3': {
                T_HOST:     '192.168.100.134',
                T_NODES:    [
                    '1141', '1142', '1143', '1144',
                ],
            },
        }
        # Expected network layout
        self.config['network_0'] = {
            'subnet_0': {
                T_PANID     : 'F5F5E6E617171515',
                T_CHANNEL   : 15,
                T_GATEWAY   : '1122',
                T_NODES     : [
                    '1111', '1112', '1113', '1114',
                    '1122', '1123', '1124', '1134',
                ],
            },
            'subnet_1': {
                T_PANID     : 6262441166221516,
                T_CHANNEL   : 16,
                T_GATEWAY   : '1144',
                T_NODES     : [
                    '1121', '1131', '1132', '1133',
                    '1141', '1142', '1143', '1144',
                ],
            },
        }
        self.config['network_1'] = {
            'subnet_0': {
                T_PANID     : '2021313515101517',
                T_CHANNEL   : 17,
                T_GATEWAY   : '1122',
                T_NODES     : [
                    '1111', '1112', '1113', '1114',
                    '1122', '1123', '1124', '1134',
                    '1121', '1131', '1132', '1133',
                    '1141', '1142', '1143', '1144',
                ],
            },
        }
        self.config['network_2'] = {
            'subnet_0': {
                T_PANID     : '1717909012121522',
                T_CHANNEL   : 22,
                T_GATEWAY   : '1122',
                T_NODES     : [
                    '1111', '1112', '1113', '1114',
                    '1122', '1123', '1124', '1134',
                ],
            },
            'subnet_1': {
                T_PANID     : '4040101033441513',
                T_CHANNEL   : 13,
                T_GATEWAY   : '1121',
                T_NODES     : [
                    '1121', '1131', '1132', '1133',
                ]
            },
            'subnet_2': {
                T_PANID     : '5151131320201516',
                T_CHANNEL   : 16,
                T_GATEWAY   : '1144',
                T_NODES     : [
                    '1141', '1142', '1143', '1144',
                ],
            },
        }

class TrafficConfig(Config):
    """Wireless network traffic configure
    Sender/Recipient are indecated by
    - *               All nodes in a network layout
    - <subnet_name>   All nodes in a subnet
    - <node_address>  Node with given address
    """
    @property
    def nw_cfgpath(self):
        return self.config[T_NWCONFIG_PATH]

    @nw_cfgpath.setter
    def nw_cfgpath(self, val):
        pass

    @property
    def target_traffics(self):
        return self.config[T_TARGET_TRAFFICS]

    @target_traffics.setter
    def target_traffics(self, val):
        pass

    @property
    def target_agents(self):
        return self.config[T_TARGET_AGENTS]

    @target_agents.setter
    def target_agents(self, val):
        pass

    def create_sample(self):
        # Network config to use
        self.config["traffic_0"] = {
            T_NWLAYOUT  : 'network_2',
            T_SENDERS   : [
                '1111', '1112', '1113', '1114',
            ],
            T_RECIPIENTS: [
                '1122', '1123', '1124', '1134',
            ],
            # package / seconds
            T_PKGRATE   : 0.5,
            T_PKGSIZE   : 1,
            # seconds
            T_DURATION  : 180,
        }
        self.config["traffic_1"] = {
            T_NWLAYOUT  : 'network_0',
            T_SENDERS   : [
                '1114'
            ],
            T_RECIPIENTS: [
                '1122', '1123', '1124', '1134'
            ],
            # package / seconds
            T_PKGRATE   : 0.5,
            T_PKGSIZE   : 2,
            # seconds
            T_DURATION  : 180,
        }
        self.config["traffic_2"] = {
            T_NWLAYOUT  : 'network_1',
            T_SENDERS   : [
                '1123',
            ],
            T_RECIPIENTS: [
                '1122',
            ],
            # package / seconds
            T_PKGRATE   : 0.2,
            T_PKGSIZE   : 2,
            # seconds
            T_DURATION  : 360,
        }
        self.config["traffic_3"] = {
            T_NWLAYOUT  : 'network_1',
            T_SENDERS   : [
                '1111',
            ],
            T_RECIPIENTS: [
                '*',
            ],
            # package / seconds
            T_PKGRATE   : 0.2,
            T_PKGSIZE   : 2,
            # seconds
            T_DURATION  : 360,
        }
        self.config["traffic_4"] = {
            T_NWLAYOUT  : 'network_2',
            T_SENDERS   : [
                '*',
            ],
            T_RECIPIENTS: [
                '1144',
            ],
            # package / seconds
            T_PKGRATE   : 0.2,
            T_PKGSIZE   : 2,
            # seconds
            T_DURATION  : 360,
        }
        # Network layout configure path
        self.config[T_NWCONFIG_PATH] = NETWORK_CONFIG_PATH
        # Traffics to run
        self.config[T_TARGET_TRAFFICS] = [
            "traffic_0", "traffic_2",
        ]
        self.config[T_TARGET_AGENTS] = [
            "agent_0", "agent_1",
        ]

def create_inuithy_cfg(cfgpath):
    """Create inuithy config object and load configure from given path
    """
    cfg = InuithyConfig(cfgpath)
    if False == cfg.load(): return None
    return cfg

def create_traffic_cfg(cfgpath):
    cfg = TrafficConfig(cfgpath)
    if False == cfg.load(): return None
    return cfg

def create_network_cfg(cfgpath):
    cfg = NetworkConfig(cfgpath)
    if False == cfg.load(): return None
    return cfg

if __name__ == '__main__':
    lgr = logging.getLogger("InuithyConfig")
    lgr.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "InuithyConfig"))

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

    cfg = TrafficConfig(TRAFFIC_CONFIG_PATH)
#   print(dir(cfg))

