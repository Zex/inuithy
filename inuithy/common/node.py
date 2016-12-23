""" General node definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import TrafficType, T_MSG, T_GENID, T_TRAFFIC_STATUS,\
INUITHY_LOGCONFIG, to_string, T_TYPE, T_ADDR, T_PATH, NodeType, TrafficStatus
from inuithy.util.cmd_helper import pub_reportwrite, pub_notification, pub_status, pub_reply
from inuithy.util.worker import Worker
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
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

RAWNODE_BASE = '/tmp'
RAWNODE_SVR = RAWNODE_BASE+'/dev/svr'
RAWNODE_RBUF_MAX = 1024

lconf.fileConfig(INUITHY_LOGCONFIG)

class Node(object):
    """Node control via serial port
    """
    def __init__(self, ntype=None, proto=None, path="", addr="", reporter=None,\
        lgr=None, adapter=None):
        self.lgr = lgr is None and logging or lgr
        self.path = path
        self.addr = addr
        self.ntype = ntype
        self.reporter = reporter
        self.proto = proto
        self.genid = None
        self.joined = False #DEBUG
        self.fwver = ''
        self.adapter = adapter
        self.sequence_nr = 0
        self.dev = None
        self.mutex = threading.Lock()
        self.reader = None#Worker(lgr=self.lgr)
        self.running = True
        self.writer = Worker(1, lgr=self.lgr)
        self.writable = threading.Event()
        self.started = False # Indicate whether firmware is ready
        self.in_traffic = False # Indicate traffic started or not
        self.tsh_on = False

    def __str__(self):
        if self.ntype is None:
            ntype = ''
        else:
            ntype = self.ntype.name
        return json.dumps({
            T_TYPE:ntype,
            T_ADDR:self.addr,
            T_PATH:self.path})

    def read(self, rdbyte=0):
        """Read data ultility"""
        pass

    def write(self, data="", request=None):
        """Write data ultility"""
        pass

    def start(self):
        """Start node workers"""
#        self.reader.start()
        self.running = True
        self.reader = threading.Thread(target=self._read)
        self.reader.start()
        if self.writer:
            self.writer.start()

    def stop(self):
        """Stop node workers"""
        if self.writer:
            self.writer.stop()
        self.running = False
        if self.reader:
            self.reader.join()

    def join(self, data):
        """General join adapter for joining a node to network"""
        self.genid = data.get(T_GENID)
        msg = self.proto.join(data)
        self.write(msg, data)

    def traffic(self, data):
        """General traffic adapter for sending network traffic"""
        self.genid = data.get(T_GENID)
#        msg = self.proto.traffic(data)
#        self._write(msg, data)
        self.proto.traffic(data, self)

    def report_read(self, data=None):
        """Report received data
        Ex:
               data = ZbeeProto.NAME
               data = BleProto.NAME
               date = BzProto.NAME
        """
        try:
            if data is None or len(data) == 0:
                return
            if self.proto is None:
                return
            report = self.proto.parse_rbuf(data, self, self.adapter)

            if self.reporter is not None and report is not None and len(report) > 2:
                pub_notification(self.reporter, data=report)
        except Exception as ex:
            self.lgr.error(to_string("Exception on report read: {}", ex))

    def report_write(self, data=None, request=None):
        """Report writen data"""
        try:
            if self.proto is None or data is None or len(data) == 0:
                return

            report = self.proto.parse_wbuf(data, self, request)
            if self.reporter is not None and report is not None and len(report) > 2:
                pub_reportwrite(self.reporter, data=report)
        except Exception as ex:
            self.lgr.error(to_string("Exception on report write: {}", ex))

    def close(self):

        if self.dev is not None:
            self.dev.close()

class SerialNode(Node):

    def __init__(self, ntype=None, proto=None, path="", addr="", reporter=None,\
        lgr=None, timeout=3, baudrate=115200, adapter=None):
        Node.__init__(self, ntype=ntype, proto=proto, path=path, addr=addr,\
            reporter=reporter, lgr=lgr, adapter=adapter)
        if path is not None and exists(path):
            self.dev = serial.Serial(path, baudrate=baudrate, timeout=timeout)
#        self.writer = None
        self.wait_timeout = 2.0

    def _read_one(self, rdbyte=0, in_wait=False):
        rdbuf = ''
        rlen = 0

        if rdbyte > 0:
            return self.dev.read(rdbyte)
        
        if in_wait:
            rlen = self.dev.inWaiting()
            if rlen == 0:
                return rdbuf

        while self.running:
            c = self.dev.read()
            if not c or len(c) == 0 or c == '\r' or c == '\n':
                break
            rdbuf += c
        return rdbuf

    def _read(self, rdbyte=0):
        """Read data ultility"""
#        rdsize = rdbyte == 0 and self.dev.inWaiting() or rdbyte
        rdbuf = ''
        try:
            while self.running:
                rdbuf = self._read_one()
                if self.tsh_on:
                    pub_reply(self.reporter, data={
                        T_NODE: self,
                        T_MSG: rdbuf,
                    })
                    self.tsh_on = False
                if len(rdbuf) > 0:
                    self.report_read(rdbuf)
        except serial.SerialException as ex:
            self.lgr.error(to_string("Serial exception on reading: {}", ex))
            pub_status(self.reporter, data={
                T_TRAFFIC_STATUS: TrafficStatus.AGENTFAILED.name,
                T_NODE: self,
                T_MSG: str(ex),
            })

    def _write(self, data="", request=None):
        """Write data ultility"""
        try:
            if not self.in_traffic:
                self.writable.wait(self.wait_timeout)
            else:
                self.writable.wait()
            written = self.dev.write(data)
            self.writable.clear()
            self.report_write(data, request)
            self.lgr.info(to_string("NODE|W: {}, {}({})", self.path, data, written))
        except serial.SerialException as ex:
            self.lgr.error(to_string("Serial exception on writting: {}", ex))
            raise

    def write(self, data="", request=None):
        if data is None or len(data) == 0:
            return
#        if not self.in_traffic:
#        self._write(data, request)
        self.writer.add_job(self._write, data, request)

    def read(self, request=None):
#        self.reader.add_job(self._read)
        self._read_one()

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
        self.dev.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.dev.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.dev.bind(path)

    def read(self, rdbyte=0):
        """Read data ultility"""
        rdbuf = ""
        rdbuf, sender = self.dev.recvfrom(RAWNODE_RBUF_MAX)
        self.lgr.info(to_string("NODE|R: {}, {}, {}", self.path, rdbuf, sender))
        rdbuf = rdbuf.decode()
        self.report_read(rdbuf)
        return rdbuf

    def write(self, data="", request=None):
        """Write data ultility"""
        self.dev.sendto(data.encode(), 0, RAWNODE_SVR)
        self.report_write(data, request)
        self.lgr.info(to_string("NODE|W: {}, {}", self.path, data))

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
        self.lgr.info(to_string("SVR|R: {}, {}, {}", self.path, rdbuf, sender))
        self.dev.sendto(rdbuf, 0, sender)
        return rdbuf.decode()

    def write(self, data="", request=None):
        """Write data ultility"""
        pass

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyNode')
    node = SerialNode(path='/dev/tty2')
    node.close()
