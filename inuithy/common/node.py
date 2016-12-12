""" General node definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import TrafficType, T_MSG, T_GENID,\
INUITHY_LOGCONFIG, to_string, T_TYPE, T_ADDR, T_PATH, NodeType
from inuithy.util.cmd_helper import pub_reportwrite, pub_notification
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto

import logging.config as lconf
import threading
import logging
import serial
import socket
import json
from os.path import dirname, isdir, exists
from os import makedirs, unlink
from random import randint

RAWNODE_BASE = '/tmp'
RAWNODE_SVR = RAWNODE_BASE+'/dev/svr'
RAWNODE_RBUF_MAX = 1024

lconf.fileConfig(INUITHY_LOGCONFIG)

class Node(object):
    """Node control via serial port
    """
    def __init__(self, ntype=None, proto=None, path="", addr="", reporter=None,\
        lgr=None, adapter=None):
        self.lgr = logging#lgr is None and logging or lgr
        self.path = path
        self.addr = addr
        self.ntype = ntype
        self.reporter = reporter
        self.proto = proto
        self.run_listener = False
        self.genid = None
        self.read_event = threading.Event()
        self.joined = False #DEBUG
        self.fwver = ''
        self.adapter = adapter
        self.sequence_nr = 0
        self.dev = None

    def __str__(self):
        if self.ntype is None:
            ntype = ''
        else:
            ntype = self.ntype.name
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PATH:self.path})

    def read(self, rdbyte=0):
        """Read data ultility"""
#        self.lgr.debug(to_string("SerialNode#R: rdbyte:{}", rdbyte))
        pass

    def write(self, data="", request=None):
        """Write data ultility"""
#        self.lgr.debug(to_string("SerialNode#W: data:[{}], len:{}", data, len(data)))
        pass

    def start_listener(self):
        """Start listening incoming package"""
        if self.run_listener is False and self.path is not None and len(self.path) > 0:
            self.run_listener = True
            self.__listener = threading.Thread(target=self.__listener_routine, name="Listener")
            if self.__listener is not None:
                self.__listener.start()

    def __listener_routine(self):
        """Listen for incoming packages"""
        while self.run_listener:
            try:
                if self.dev is None: #DEBUG
                    self.read_event.wait()  # triggered by writer
                    self.read_event.clear()
                    self.read_event.wait(randint(1, 3)) #TODO remove
                self.read()
                self.read_event.clear()
            except Exception as ex:
                self.lgr.error(to_string("Exception in listener routine: {}", ex))

    def stop_listener(self):
        """Stop running listener"""
        self.run_listener = False
        self.read_event.set()

    def join(self, data):
        """General join adapter for joining a node to network"""
        self.genid = data.get(T_GENID)
        msg = self.proto.join(data)
        self.write(msg, data)

    def traffic(self, data):
        """General traffic adapter for sending network traffic"""
        self.genid = data.get(T_GENID)
        msg = self.proto.traffic(data)
        self.write(msg, data)

    def report_read(self, data=None):
        """Report received data"""
#        self.lgr.debug(to_string("Report read"))
        try:
#TODO: uncomment
#       if data is None or len(data) == 0:
#           return
            if self.proto is None:
#TODO: use actual data
                data = ZbeeProto.NAME
#               data = BleProto.NAME
#               date = BzProto.NAME
                data = data.strip('\t \r\n')
                if self.adapter is not None:
                    self.adapter.register(self, data)
                else:
                    self.lgr.error(to_string("Failed to register node to adapter: no adapter given"))
                return

            if self.run_listener is False:
                return
            if self.reporter is None or self.genid is None:
                self.lgr.error(to_string("R: Invalid reporter or genid: {}, {}", self.reporter, self.genid))
                return
            report = self.proto.parse_rbuf(data, self)
            if report is not None and len(report) > 2:
                pub_notification(self.reporter, data=report)
        except Exception as ex:
            self.lgr.error(to_string("Exception on report read: {}", ex))

    def report_write(self, data=None, request=None):
        """Report writen data"""
#        self.lgr.debug(to_string("Report write"))
        try:
            if self.proto is None:
                return
            if self.reporter is None or self.genid is None or request is None:
                self.lgr.error(to_string("W: Invalid reporter or genid: {}, {}", self.reporter, self.genid))
                return
#TODO: uncomment
#       if data is None or len(data) == 0:
#           return
            report = self.proto.parse_wbuf(data, self, request)
            if report is not None and len(report) > 2:
                pub_reportwrite(self.reporter, data=report)
        except Exception as ex:
            self.lgr.error(to_string("Exception on report write: {}", ex))

    def close(self):

        if self.dev is not None:
            self.dev.close()

    @staticmethod
    def create(ntype=None, proto=None, path='', addr='', repather=None, lgr=None, adapter=None):
        """ntype=None, proto=None, path="", addr="", repather=None, lgr=None, timeout=2, adapter=None
        """
        try:
            return Node(ntype=ntype, proto=proto, port=port,\
                addr=addr, reporter=reporter, lgr=lgr, adapter=adapter)
        except Exception as ex:
            lgr.error(to_string("Exception on node creation: {}", ex))

class SerialNode(Node):

    def __init__(self, ntype=None, proto=None, path="", addr="", reporter=None,\
        lgr=None, timeout=2, baudrate=115200, adapter=None):
        Node.__init__(self, ntype=ntype, proto=proto, path=path, addr=addr,\
            reporter=reporter, lgr=lgr, adapter=adapter)
        self.dev = serial.Serial(port, baudrate=baudrate, timeout=timeout)

    def read(self, rdbyte=0):
        """Read data ultility"""
#        self.lgr.debug(to_string("SerialNode#R: rdbyte:{}", rdbyte))
        rdbuf = ""
        if isinstance(self.dev, serial.Serial) and self.dev.isOpen():
            if 0 < self.dev.inWaiting():
                rdbuf = self.dev.readall()
                if isinstance(rdbuf, bytes):
                    rdbuf = rdbuf.decode()
        #TODO -->
        self.report_read(rdbuf)
        return rdbuf

    def write(self, data="", request=None):
        """Write data ultility"""
#        self.lgr.debug(to_string("SerialNode#W: data:[{}], len:{}", data, len(data)))
        written = 0
        if isinstance(self.dev, serial.Serial) and self.dev.isOpen():
            if isinstance(data, str):
                written = self.dev.write(data.encode())
            else:
                written = self.dev.write(data)
        #TODO -->
        self.report_write(data, request)
        if self.run_listener:
            self.read_event.set()

class RawNode(Node):
    """Raw socket node for simulation"""
    def __init__(self, ntype=None, proto=None, path="", addr="", reporter=None,\
        lgr=None, adapter=None):
        Node.__init__(self, ntype=ntype, proto=proto, path=path, addr=addr,\
            reporter=reporter, lgr=lgr, adapter=adapter)
        if not isdir(dirname(path)):
            makedirs(dirname(path))
        if exists(path):
            unlink(path)
        self.dev = socket.socket(socket.AF_UNIX, socket.SOCK_RAW)
        self.dev.bind(path)

    def read(self, rdbyte=0):
        """Read data ultility"""
        rdbuf = ""
        rdbuf, sender = self.dev.recvfrom(RAWNODE_RBUF_MAX)
        print("NODE|R:", self.path, rdbuf, sender)
        rdbuf = rdbuf.decode()
        self.report_read(rdbuf)
        return rdbuf

    def write(self, data="", request=None):
        """Write data ultility"""
        self.dev.sendto(data.encode(), socket.MSG_DONTWAIT, RAWNODE_SVR)
        self.report_write(data, request)
        print("NODE|W:", self.path, data)
        if self.run_listener:
            self.read_event.set()

    def close(self):

        if self.dev is not None:
            self.dev.close()
        if len(self.path) > 0 and exists(self.path):
            unlink(self.path)

class RawNodeSvr(RawNode):
    """Raw node server"""
    def __init__(self, ntype=None, proto=None, path=RAWNODE_SVR, addr="", reporter=None,\
        lgr=None, adapter=None):
        RawNode.__init__(self, ntype=ntype, proto=proto, path=path, addr=addr,\
            reporter=reporter, lgr=lgr, adapter=adapter)

    def read(self, rdbyte=0):
        """Read data ultility"""
        rdbuf, sender = self.dev.recvfrom(RAWNODE_RBUF_MAX)
        print("SVR|R:", self.path, rdbuf, sender)
        self.dev.sendto(rdbuf, socket.MSG_DONTWAIT, sender)
        return rdbuf.decode()

    def write(self, data="", request=None):
        """Write data ultility"""
        pass
#        written = 0
#        if isinstance(self.dev, socket.socket): #DEBUG
#            self.dev.sendto(data, socket.MSG_DONTWAIT, RAWNODE_SVR)
#        #TODO -->
#        self.report_write(data, request)
#        if self.run_listener:
#            self.read_event.set()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyNode')
    node = SerialNode(path='/dev/tty2')
    node.close()
