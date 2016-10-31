## High-level Storage definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging
import logging.config as lconf
from inuithy.common.predef import *
from inuithy.storage.mongodb_plugin import MongodbStorage
from abc import ABCMeta, abstractmethod

lconf.fileConfig(INUITHY_LOGCONFIG)
lg = logging.getLogger('InuithyStorage')

class Storage:
    """High-level storage
    @trafrec    Traffic records
    """
    @property
    def storage_name(self): return self.__dbplugin.storage_name
    @storage_name.setter
    def storage_name(self, val): pass

    @property
    def host(self): return self.__dbplugin.host   
    @host.setter
    def host(self, val): pass

    @property
    def port(self): return self.__dbplugin.port
    @port.setter
    def port(self, val): pass

    @property
    def localpath(self): return self.__dbplugin.localpath
    @localpath.setter
    def localpath(self, val): pass

    @property
    def storage_path(self):
        return self.localpath or string_write("{}:{}", self.host, self.port)
    @storage_path.setter
    def storage_path(self, val): pass

    @property
    def trafrec(self): return self.__dbplugin.trafrec
    @trafrec.setter
    def trafrec(self, val): pass

    def __init__(self, tcfg, lg=None):
        self.tcfg = tcfg
        if lg == None: self.lg = logging
        else: self.lg = lg
        self.load_plugin(*self.tcfg.storagetype)

    def load_plugin(self, sttype, stname):
        self.lg.info(string_write("Load plugin: {}:{}", sttype, stname))
        s = self.tcfg.config[CFGKW_TRAFFIC_STORAGE]
        if sttype == TrafficStorage.DB.name:
            if stname == StorageType.MongoDB.name:
                self.__dbplugin = MongodbStorage(
                    *(s[CFGKW_PATH].split(":"))
                ) 
        else: #TODO TrafficStorage.FILE.name
            pass

    def insert_record(self, data):
        """Insert one traffic record
        @data Traffic data, dict
        @return Inserted id
        """
        try:
            self.__dbplugin.insert_record(data)
        except Exception as ex:
            self.lg.error(string_write("Insert record failed: {}", ex))

    def insert_config(self, data):
        """Insert current configure
        @data Configure data, dict
        """
        try:
            return self.__dbplugin.insert_config(data)
        except Exception as ex:
            self.lg.error(string_write("Insert record failed: {}", ex))
            return None
    
    def close(self):
        self.lg.info("Close storage")
        self.__dbplugin.close()

