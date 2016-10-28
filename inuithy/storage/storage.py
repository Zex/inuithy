## High-level Storage definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.storage.mongodb_plugin import MongodbStorge
from abc import ABCMeta, abstractmethod

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('InuithyStorage')

class Storage:

    @property
    def storage_name(self): return self.__storage_name
    @storage_name.setter
    def storage_name(self, val): pass

    @property
    def host(self): return self.__host
    @host.setter
    def host(self, val): pass

    @property
    def port(self): return self.__port
    @port.setter
    def port(self, val): pass

    @property
    def localpath(self): return self.__localpath
    @localpath.setter
    def localpath(self, val): pass

    @property
    def storage_path(self):
        return self.localpath or string_write("{}:{}", self.host, self.port)
    @storage_path.setter
    def storage_path(self, val): pass

    def __init__(self, tcfg, lg=None)
        self.tcfg = tcfg
        self.__host = host   
        self.__port = port
        self.__localpath = localpath   
        if lg == None: self.lg = logging
        else: self.lg = lg
        self.load_plugin(*self.tcfg.storagetype)

    def load_plugin(self, sttype, stname):
        s = self.tcfg.config[CFGKW_TRAFFIC_STORAGE]
        if sttype == TrafficStorage.DB.name:
            if stname == StorageType.MongoDB.name:
                self.__dbplugin = MongodbPlugin(
                    *(s[CFGKW_PATH]split(":"))
                ) 
        else: #TODO TrafficStorage.FILE.name
            pass

    def insert_record(self, data):
        """Insert one traffic record
        @data Traffic data, dict
        """
        self.__dbplugin.insert_record(data)

    def insert_config(self, data):
        """Insert current configure
        @data Configure data, dict
        """

        self.__dbplugin.insert_config(data)

