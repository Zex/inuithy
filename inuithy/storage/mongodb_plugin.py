""" Mongodb plugin
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import MessageType, T_HOST, StorageType,\
T_RECORDS, T_MSG_TYPE, to_string, T_TIME, T_GENID, T_CLIENTID,\
T_SRC, T_DEST, T_PKGSIZE, to_console
from pymongo import MongoClient
#from bson.objectid import ObjectId
#from datetime import datetime as dt
import time

class MongodbStorage(object):
    """MongoDB adapter
    Provide:
    - Traffic Storage - Runtime traffic records
                      - Inuithy config
                      - Network config
                      - Traffic config

    """
    @property
    def cli(self):
        return self.__cli
    @cli.setter
    def cli(self, val):
        pass

    @property
    def storage_name(self):
        return self.__storage_name
    @storage_name.setter
    def storage_name(self, val):
        pass

    @property
    def host(self):
        return self.__host
    @host.setter
    def host(self, val):
        pass

    @property
    def port(self):
        return self.__port
    @port.setter
    def port(self, val):
        pass

    @property
    def localpath(self):
        return None
    @localpath.setter
    def localpath(self, val):
        pass

    @property
    def storage_path(self):
        return self.localpath or to_string("{}:{}", self.host, self.port)
    @storage_path.setter
    def storage_path(self, val):
        pass

    @property
    def db(self):
        return self.__db
    @db.setter
    def db(self, val):
        pass

    @property
    def trafrec(self):
        return self.__coll_trafrec
    @trafrec.setter
    def trafrec(self, val):
        pass

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
        return str(to_string("cli:{} host:{} port:{} name:{}", self.cli, self.host, self.port, self.storage_name))

    def insert_config(self, data):
        """
        Storage structure
        - T_GENID      : <connect configure and records> => string
        - T_TARGET_NWLAYOUT : <network layout>  => dict
        - T_TARGET_TRAFFIC  : <traffic layout>  => dict
        - T_RECORDS      : [                    => list
        -- T_TIME        : <recored datetime string>      => string---+
        -- T_MSG         : <string from/to serial port>   => string   |
        -- T_CLIENTID    : <agentid>             => string            |
        -- T_HOST        : <agent host>          => string            +->record
        -- T_SRC      : <src node addr>    => string            |
        -- T_DEST   : <dest node addr> => string            |
        -- T_PKGSIZE     : <package size>        => integer-----------+
           ]
        Data sample - initial state
        - T_TARGET_NWLAYOUT : <network layout>  => dict
        - T_TARGET_TRAFFIC  : <traffic layout>  => dict
        - T_RECORDS         : []                => list
        Return
        - T_GENID           : <connect configure and records> => string
        """
        data[T_GENID] = str(int(time.time()))
        data[T_RECORDS]     = []
        self.__coll_trafrec.insert_one(data)
        return data[T_GENID]
#        return str(self.__coll_trafrec.insert_one(data).inserted_id)

    def insert_record(self, data):
        """
        Storage structure
        - T_GENID      : <connect configure and records> => string
        - T_TARGET_NWLAYOUT : <network layout>  => dict
        - T_TARGET_TRAFFIC  : <traffic layout>  => dict
        - T_RECORDS      : [                    => list
        -- T_TIME        : <recored datetime string>      => string---+
        -- T_MSG         : <string from/to serial port>   => string   |
        -- T_MSG_TYPE    : Message type          => string   |
        -- T_CLIENTID    : <agentid>             => string            |
        -- T_HOST        : <agent host>          => string            +->record
        -- T_SRC      : <src node addr>    => string            |
        -- T_DEST   : <dest node addr> => string            |
        -- T_PKGSIZE     : <package size>        => integer-----------+
           ]
        Data sample - on record
        {
        -- T_GENID       : <connect configure and records> => string--+
        -- T_MSG         : <string from/to serial port>   => string   |
        -- T_CLIENTID    : <agentid>             => string            |
        -- T_HOST        : <agent host>          => string            +->record
        -- T_SRC      : <src node addr>    => string            |
        -- T_DEST   : <dest node addr> => string            |
        -- T_PKGSIZE     : <package size>        => integer-----------+
        }
        Additional field
        -- T_TIME        : <recored datetime string>      => string
        """
#        data[T_TIME] = str(dt.now())
        self.trafrec.update(
#            {"_id": ObjectId(data[T_GENID])},
            {T_GENID: data.get(T_GENID)},
            {'$push': {T_RECORDS: data}})

# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    def update_test(host, port):

        sto = MongodbStorage(host, port)
        to_console(sto.trafrec)
        for r in sto.trafrec.find():
            oid = r.get('_id')
            to_console("------------------------{}---------------------".format(oid))
            to_console(r)
            rec = {
                T_GENID:    str(r.get('_id')),
                T_MSG:      "lignton 1122",
                T_CLIENTID: "HAHAHAH333111MARS",
                T_HOST:     "PLUTO",
                T_SRC:   "1111",
                T_DEST:"1122",
                T_PKGSIZE:  "10",
            }
            sto.insert_record(rec)
            to_console(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
#        to_console(sto.trafrec.find_one({"_id": ObjectId(oid)}))
            to_console("{}", sto.trafrec.find_one({T_GENID: oid}))

    def check_records(host, port):
        sto = MongodbStorage(host, port)
        to_console(sto.trafrec)
        for r in sto.trafrec.find():
            oid = r.get('_id')
            to_console("------------------------{}---------------------", oid)
            to_console(r)

    def check_recv(host, port, genid):
        sto = MongodbStorage(host, port)
        for r in sto.trafrec.find({
#            "_id": ObjectId(genid),
                T_GENID: genid,
                #"records": { "$elemMatch": {"msgtype": "RECV"} }
            }):
            [to_console(v) for v in r[T_RECORDS] if v[T_MSG_TYPE] == MessageType.RECV.name]

    def check_sent(host, port, genid):
        sto = MongodbStorage(host, port)
        for r in sto.trafrec.find({
#            "_id": ObjectId(genid),
                T_GENID: genid,
            }):
            [to_console(v) for v in r[T_RECORDS] if v[T_MSG_TYPE] == MessageType.SEND.name]

    def cleanup(host, name):
        sto = MongodbStorage(host, name)
        sto.trafrec.delete_many({})

    def export(host, name, genid):

        sto = MongodbStorage(host, name)
        with open(gid+'.log', 'w') as fd:
            for r in sto.trafrec.find({T_GENID: genid,}):
                [fd.writelines(str(l)+'\n') for l in r[T_RECORDS]]

#    oid = '581fdfe3362ac719d1c96eb3'
#    check_recv('192.168.1.185', 19713, oid)
    gid = '1481793953'
    export('127.0.0.1', 19713, gid)


