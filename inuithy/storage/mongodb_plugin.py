## Mongodb plugin
# Author: Zex Li <top_zlynch@yahoo.com>
#
from datetime import datetime as dt
from inuithy.common.predef import *
from pymongo import MongoClient
from bson.objectid import ObjectId

class MongodbStorage:
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
    def localpath(self): return None
    @localpath.setter
    def localpath(self, val): pass

    @property
    def storage_path(self):
        return self.localpath or string_write("{}:{}", self.host, self.port)
    @storage_path.setter
    def storage_path(self, val): pass

    @property
    def db(self): return self.__db
    @db.setter
    def db(self, val): pass

    @property
    def trafrec(self): return self.__coll_trafrec
    @trafrec.setter
    def trafrec(self, val): pass

    def __init__(self, host, port): 
        self.__storage_name = StorageType.MongoDB.name
        self.__host = host
        self.__port = int(port)
        self.__cli = MongoClient(self.host, self.port)
        self.__db = self.cli.inuithy
        self.__coll_trafrec = self.db.traffic_records
   
    def close(self):
        self.cli.close()

    def __str__(self):
        return str(string_write("cli:{} host:{} port:{} name:{}", self.__cli, self.host, self.port, self.storage_name))

    def insert_config(self, data):
        """
        Storage structure
        - CFGKW_GENID      : <connect configure and records> => string
        - CFGKW_TARGET_NWLAYOUT : <network layout>  => dict
        - CFGKW_TARGET_TRAFFIC  : <traffic layout>  => dict
        - CFGKW_RECORDS      : [                    => list
        -- CFGKW_TIME        : <recored datetime string>      => string---+
        -- CFGKW_MSG         : <string from/to serial port>   => string   | 
        -- CFGKW_CLIENTID    : <agentid>             => string            |
        -- CFGKW_HOST        : <agent host>          => string            +->record
        -- CFGKW_SENDER      : <sender node addr>    => string            |
        -- CFGKW_RECIPIENT   : <recipient node addr> => string            |
        -- CFGKW_PKGSIZE     : <package size>        => integer-----------+
           ]
        Data sample - initial state
        - CFGKW_TARGET_NWLAYOUT : <network layout>  => dict
        - CFGKW_TARGET_TRAFFIC  : <traffic layout>  => dict
        - CFGKW_RECORDS         : []                => list
        Return
        - CFGKW_GENID           : <connect configure and records> => string
        """
        data[CFGKW_RECORDS]     = []
        return str(self.__coll_trafrec.insert_one(data).inserted_id)

    def insert_record(self, data):
        """
        Storage structure
        - CFGKW_GENID      : <connect configure and records> => string
        - CFGKW_TARGET_NWLAYOUT : <network layout>  => dict
        - CFGKW_TARGET_TRAFFIC  : <traffic layout>  => dict
        - CFGKW_RECORDS      : [                    => list
        -- CFGKW_TIME        : <recored datetime string>      => string---+
        -- CFGKW_MSG         : <string from/to serial port>   => string   | 
        -- CFGKW_MSG_TYPE    : Message type          => string   | 
        -- CFGKW_CLIENTID    : <agentid>             => string            |
        -- CFGKW_HOST        : <agent host>          => string            +->record
        -- CFGKW_SENDER      : <sender node addr>    => string            |
        -- CFGKW_RECIPIENT   : <recipient node addr> => string            |
        -- CFGKW_PKGSIZE     : <package size>        => integer-----------+
           ]
        Data sample - on record
        {
        -- CFGKW_GENID       : <connect configure and records> => string--+
        -- CFGKW_MSG         : <string from/to serial port>   => string   | 
        -- CFGKW_CLIENTID    : <agentid>             => string            |
        -- CFGKW_HOST        : <agent host>          => string            +->record
        -- CFGKW_SENDER      : <sender node addr>    => string            |
        -- CFGKW_RECIPIENT   : <recipient node addr> => string            |
        -- CFGKW_PKGSIZE     : <package size>        => integer-----------+
        }
        Additional field
        -- CFGKW_TIME        : <recored datetime string>      => string
        """
        data[CFGKW_TIME] = str(dt.now())
        self.trafrec.update(
            {"_id": ObjectId(data[CFGKW_GENID])},
            {'$push': {CFGKW_RECORDS: data}})

# -----------------------------------------------------------------------------------------

def update_test():

    sto = MongodbStorage('127.0.0.1', 19713)
    print(sto.trafrec)
    for r in sto.trafrec.find():
        oid = r.get('_id')
        print("------------------------{}---------------------".format(oid))
        print(r)
        rec = {
            CFGKW_GENID:    str(r.get('_id')),
            CFGKW_MSG:      "lignton 1122",
            CFGKW_CLIENTID: "HAHAHAH333111MARS",
            CFGKW_HOST:     "PLUTO",
            CFGKW_SENDER:   "1111",
            CFGKW_RECIPIENT:"1122",
            CFGKW_PKGSIZE:  "10",
        }
        sto.insert_record(rec)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(sto.trafrec.find_one({"_id": ObjectId(oid)}))

def check_records():
    sto = MongodbStorage('127.0.0.1', 19713)
    print(sto.trafrec)
    for r in sto.trafrec.find():
        oid = r.get('_id')
        print("------------------------{}---------------------".format(oid))
        print(r)

def check_recv(host, port, genid):
    sto = MongodbStorage(host, port)
    for r in sto.trafrec.find({
            "_id": ObjectId(genid),
            #"records": { "$elemMatch": {"msgtype": "RECV"} }
        }):
        [print(v) for v in r[CFGKW_RECORDS] if v[CFGKW_MSG_TYPE] == MessageType.RECV.name]

def check_sent(host, port, genid):
    sto = MongodbStorage(host, port)
    for r in sto.trafrec.find({
            "_id": ObjectId(genid),
        }):
        [print(v) for v in r[CFGKW_RECORDS] if v[CFGKW_MSG_TYPE] == MessageType.SENT.name]

def cleanup():
    sto = MongodbStorage('127.0.0.1', 19713)
    sto.trafrec.delete_many({})

if __name__ == '__main__':
#    check_records() 
#    check_fields()
#    cleanup()
    oid = '581776fa362ac737abefe32e'
    check_recv('127.0.0.1', 19713, oid)
#    check_sent('127.0.0.1', 19713, oid)
