""" High-level Storage definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, T_PATH, T_TRAFFIC_STORAGE,\
string_write, TrafficStorage, StorageType
from inuithy.storage.mongodb_plugin import MongodbStorage
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

class Storage(object):
    """High-level storage
    @trafrec    Traffic records
    """
    @property
    def storage_name(self):
        return self.__dbplugin.storage_name
    @storage_name.setter
    def storage_name(self, val):
        pass

    @property
    def host(self):
        return self.__dbplugin.host   
    @host.setter
    def host(self, val):
        pass

    @property
    def port(self):
        return self.__dbplugin.port
    @port.setter
    def port(self, val):
        pass

    @property
    def localpath(self):
        return self.__dbplugin.localpath
    @localpath.setter
    def localpath(self, val):
        pass

    @property
    def storage_path(self):
        return self.localpath or string_write("{}:{}", self.host, self.port)
    @storage_path.setter
    def storage_path(self, val):
        pass

    @property
    def trafrec(self):
        return self.__dbplugin.trafrec
    @trafrec.setter
    def trafrec(self, val):
        pass

    def __init__(self, tcfg, lgr=None):
        self.tcfg = tcfg
        if lgr is None:
            self.lgr = logging
        else:
            self.lgr = lgr
        self.load_plugin(*self.tcfg.storagetype)

    def load_plugin(self, sttype, stname):
        self.lgr.info(string_write("Load plugin: {}:{}", sttype, stname))
        s = self.tcfg.config[T_TRAFFIC_STORAGE]
        if sttype == TrafficStorage.DB.name:
            if stname == StorageType.MongoDB.name:
                self.__dbplugin = MongodbStorage(
                    *(s[T_PATH].split(":"))
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
            self.lgr.error(string_write("Insert record failed: {}", ex))

    def insert_config(self, data):
        """Insert current configure
        @data Configure data, dict
        """
        try:
            return self.__dbplugin.insert_config(data)
        except Exception as ex:
            self.lgr.error(string_write("Insert config failed: {}", ex))
            return None

    def close(self):
        self.lgr.info("Close storage")
        self.__dbplugin.close()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyStorage')
    pass
