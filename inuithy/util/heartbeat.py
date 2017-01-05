""" Heartbeart over UDP
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import T_CLIENTID, T_HOST,\
T_VERSION, T_ADDR, _s, _l
import json
import threading
import socket

class Heartbeat(threading.Thread):
    """Heartbeat generator
    @interval Seconds between two heartbeat
    @name Routine name
    @info Information block to send
    """
    PORT = 13972
    __mutex = threading.Lock()

    def __init__(self, interval=2, name="Heartbeat", info=None,\
        daemon=False, *args, **kwargs):
        threading.Thread.__init__(self, target=None, name=name,\
            args=args, kwargs=kwargs, daemon=daemon)
        self.__interval = interval
        self.__running = False
        self.__args = args
        self.__kwargs = kwargs
        self.__sock = None
        self.done = threading.Event()
        self.create_sock()
        self.info = info

    def create_sock(self):
        _l.info("Create heartbeat socket")
        self.__sock = socket.socket(type=socket.SocketKind.SOCK_DGRAM)
#        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        _l.info(_s("Heartbeat routine started"))
        if self.__target is None or self.info is None:
            _l.error(_s("Heartbeat routine not defined or hearbeat info block empty"))
            return # or self.__src is None: return
        self.__running = True

        while self.__running:
            with Heartbeat.__mutex:
                self.__target()
            self.done.wait(self.__interval)
            self.done.clear()

    def stop(self):
        self.__running = False

    def __del__(self):
        self.stop()
        if self.__sock is not None:
            self.__sock.close()

    def __target(self):
        _l.info(_s("Heartbeat routine"))
        try:
            addr = (self.info.get(T_ADDR), Heartbeat.PORT)
            data = {
                T_CLIENTID: self.info.get(T_CLIENTID),
                T_HOST: self.info.get(T_HOST),
                T_VERSION: __version__,
            }
            self.__sock.sendto(json.dumps(data), addr)
        except Exception as ex:
            _l.info(_s("Heartbeat exception:{}", ex))


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
