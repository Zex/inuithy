""" Splunk adapter for Inuithy
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import MessageType, T_HOST, StorageType,\
T_RECORDS, T_MSG_TYPE, string_write, T_TIME, T_GENID, T_CLIENTID,\
T_SRC, T_DEST, T_PKGSIZE, T_TYPE, T_MSG
import socket, time

#import thirdparty.splunklib.client as client
#print(dir(client))

#conn = client.connect(host='127.0.0.1', port=1737, username='admin', password='elapstic1024')
#conn = client.connect(host='127.0.0.1', port=1379)
#print(dir(conn))

class SplunkStorage(object):
    """Splunk adapter
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
        return self.localpath or string_write("{}:{}", self.host, self.port)
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
        self.__storage_name = StorageType.Splunk.name
        self.__host = host
        self.__port = int(port)
        self.__cli = socket.socket()
        self.__db = None
        self.__coll_trafrec = None
#        self.__running = False
        self.connect()

    def connect(self):
        self.cli.connect((self.host, self.port))

    def close(self):
#        self.__running = False
#        self.cli.shutdown(socket.SHUT_RDWR)
        self.cli.close()

    def __str__(self):
        return str(string_write("cli:{} host:{} port:{} name:{}", self.cli, self.host, self.port, self.storage_name))

    def insert_config(self, data):
    
        data[T_GENID] = str(int(time.time()))
        msg = ' '.join(['{}={}'.format(k, v) for k, v in data.items()])
        msg += '\r\n'
        self.cli.send(msg.encode())
        return data[T_GENID]

    def insert_record(self, data):
        msg = ' '.join(['{}={}'.format(k, v) for k, v in data.items() if k != T_MSG])
        msg += ' '.join(['{}="{}"'.format(T_MSG, data.get(T_MSG))])
        msg += '\r\n'
        self.cli.send(msg.encode())

def insert_test():

    sto = SplunkStorage('127.0.0.1', 1737)
    data = {
        T_GENID: str(int(time.time())),
        T_TIME: str(dt.now()),
        T_TYPE: 'configurEEEEEEEEEEEEEEEEEEEEEEEEEEEEE',
    }
    gid = sto.insert_config(data)
    data = {
        T_GENID: gid,
        T_TIME: str(dt.now()),
        T_TYPE: 'GUTENTAG',
    }
    [sto.insert_record(data) for i in range(30)]
    input("Waiting...")
    sto.close()

if __name__ == '__main__':

    from datetime import datetime as dt
    insert_test()


