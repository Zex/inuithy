""" Heartbeart over UDP
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import T_CLIENTID, T_HOST,\
T_VERSION, T_ADDR, to_string, INUITHY_LOGCONFIG
import json
import threading
import socket
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

class Heartbeat(threading.Thread):
    """Heartbeat generator
    @interval Seconds between two heartbeat
    @name Routine name
    @info Information block to send
    """
    PORT = 13972
    __mutex = threading.Lock()

    def __init__(self, interval=2, name="Heartbeat", info=None,\
        daemon=False, lgr=None, *args, **kwargs):
        threading.Thread.__init__(self, target=None, name=name,\
            args=args, kwargs=kwargs, daemon=daemon)
        self.__interval = interval
        self.__running = False
        self.__args = args
        self.__kwargs = kwargs
        self.__sock = None
        self.done = threading.Event()
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging
        self.create_sock()
        self.info = info

    def create_sock(self):
        self.lgr.info("Create heartbeat socket")
        self.__sock = socket.socket(type=socket.SocketKind.SOCK_DGRAM)
#        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        self.lgr.info(to_string("Heartbeat routine started"))
        if self.__target is None or self.info is None:
            self.lgr.error(to_string("Heartbeat routine not defined or hearbeat info block empty"))
            return # or self.__src is None: return
        self.__running = True

        while self.__running:
            if Heartbeat.__mutex.acquire():
                self.__target()
                Heartbeat.__mutex.release()
            self.done.wait(self.__interval)
            self.done.clear()

    def stop(self):
        self.__running = False

    def __del__(self):
        self.stop()
        if self.__sock is not None:
            self.__sock.close()

    def __target(self):
        self.lgr.info(to_string("Heartbeat routine"))
        try:
            addr = (self.info.get(T_ADDR), Heartbeat.PORT)
            data = {
                T_CLIENTID: self.info.get(T_CLIENTID),
                T_HOST: self.info.get(T_HOST),
                T_VERSION: INUITHY_VERSION,
            }
            print(json.dumps(data))
            self.__sock.sendto(json.dumps(data), addr)
        except Exception as ex:
            self.lgr.info(to_string("Heartbeat exception:{}", ex))


if __name__ == '__main__':
    data = {
        T_CLIENTID: "2342hj42i34",
        T_HOST: "192.168.1.123",
        T_ADDR: "192.168.1.18",
        }
    hb = Heartbeat(info=data)
    hb.start()

    input("What next ...")
    hb.stop()
