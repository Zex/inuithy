## Mongodb plugin
# Author: Zex Li <top_zlynch@yahoo.com>
#
from datetime import datetime as dt
from inuithy.common.predef import *

class MongodbStorge:
    """MongoDB adapter
    Provide:
    - Traffic Storage - Runtime traffic records
                      - Inuithy config
                      - Network config
                      - Traffic config
     
    """
    @property
    def cli(self): return self.__cli
    @cli.setter
    def cli(self, val): pass

    def __init__(self, host, port) 
        super(MongodbStorage, self).__init__("MongoDB", host, port)
        self.__cli = MongoClient(self.host, self.port)
        self.db = self.cli.inuithy_traffic_records
   
    
    def __del__(self):
        self.cli.close()

    def __str__(self):
        return str(string_write("cli:{} host:{} port:{} name:{}", self.__cli, self.host, self.port, self.storage_name)

    def insert_config(self, data):
        """
        data
        - CFGKW_GENID      : <connect configure and records> => string
        - CFGKW_TARGET_NWLAYOUT : <network layout>  => dict
        - CFGKW_TARGET_TRAFFIC  : <traffic layout>  => dict
        - CFGKW_RECORDS      : [                    => list
        - CFGKW_GENID       : <connect configure and records> => string
        -- CFGKW_TIME        : <datetime string>            => string +
        -- CFGKW_MSG         : <string from/to serial port> => string | 
        -- CFGKW_CLIENTID    : <agentid>             => string        |
        -- CFGKW_HOST        : <agent host>          => string        +->record
        -- CFGKW_SENDER      : <sender node addr>    => string        |
        -- CFGKW_RECIPIENT   : <recipient node addr> => string        |
        -- CFGKW_PKGSIZE     : <package size>        => integer-------+
           ]
        """
        self.__cli.inser_one(data)

    def insert_record(self, data):
        """
        - CFGKW_GENID      : <connect configure and records> => string
        - CFGKW_TARGET_NWLAYOUT : <network layout>  => dict
        - CFGKW_TARGET_TRAFFIC  : <traffic layout>  => dict
        - CFGKW_RECORDS      : [                    => list
        -- CFGKW_GENID      : <connect configure and records> => string
        -- CFGKW_TIME        : <recored datetime string>       => string +
        -- CFGKW_MSG         : <string from/to serial port> => string | 
        -- CFGKW_CLIENTID    : <agentid>             => string        |
        -- CFGKW_HOST        : <agent host>          => string        +->record
        -- CFGKW_SENDER      : <sender node addr>    => string        |
        -- CFGKW_RECIPIENT   : <recipient node addr> => string        |
        -- CFGKW_PKGSIZE     : <package size>        => integer-------+
           ]
        """
        data[CFGKW_TIME] = datatime.now() 
        self.__cli.insert_one(data)

