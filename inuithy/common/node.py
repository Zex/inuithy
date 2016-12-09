""" General node definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import TrafficType, T_MSG, T_GENID,\
INUITHY_LOGCONFIG, to_string, T_TYPE, T_ADDR, T_PORT, NodeType
from inuithy.util.cmd_helper import pub_reportwrite, pub_notification
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
#from inuithy.protocol.zigbee_proto import T_RSP

import logging.config as lconf
import threading
import logging
import serial
import json
from random import randint

lconf.fileConfig(INUITHY_LOGCONFIG)


class SerialNode(object):
    """Node control via serial port
    """
    def __init__(self, ntype=None, proto=None, port="", addr="", reporter=None, lgr=None, timeout=2, adapter=None):
        self.lgr = lgr is None and logging or lgr
        self.port = port
        self.addr = addr
        self.ntype = ntype
        self.reporter = reporter
        self.proto = proto
        # TODO: create serial object
        self.__serial = None #serial.Serial(port, baudrate=baudrate, timeout=timeout)
#        self.__listener = threading.Thread(target=self.__listener_routine, name="Listener")
        self.run_listener = False
        self.genid = None
        self.read_event = threading.Event()
        self.joined = False #DEBUG
        self.fwver = ''
        self.adapter = adapter
        self.sequence_nr = 0

    def __str__(self):
        if self.ntype is None:
            ntype = ''
        else:
            ntype = self.ntype.name
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def read(self, rdbyte=0):
        """Read data ultility"""
#        self.lgr.debug(to_string("SerialNode#R: rdbyte:{}", rdbyte))
        rdbuf = ""
        if self.__serial is not None and self.__serial.isOpen():
            if 0 < self.__serial.inWaiting():
                rdbuf = self.__serial.readall()
        #TODO -->
        self.report_read(rdbuf)
        return rdbuf

    def write(self, data="", request=None):
        """Write data ultility"""
#        self.lgr.debug(to_string("SerialNode#W: data:[{}], len:{}", data, len(data)))
        written = 0
        if self.__serial is not None and self.__serial.isOpen():
            written = self.__serial.write(data)
        #TODO -->
        self.report_write(data, request)
        self.read_event.set()

    def start_listener(self):
        """Start listening incoming package"""
        if self.run_listener is False and self.port is not None and len(self.port) > 0:
            self.run_listener = True
            self.__listener = threading.Thread(target=self.__listener_routine, name="Listener")
            if self.__listener is not None:
                self.__listener.start()

    def __listener_routine(self):
        """Listen for incoming packages"""
        while self.run_listener:
            try:
                if self.__serial is None: #DEBUG
                    self.read_event.wait()
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
        """General join adapter"""
        self.genid = data.get(T_GENID)
        msg = self.proto.join(data)
        self.write(msg, data)

    def traffic(self, data):
        """General traffic adapter"""
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
#TODO: remove
            if self.proto is None:
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

    @staticmethod
    def create(ntype=None, proto=None, port='', addr='', reporter=None, lgr=None, adapter=None):
        """ntype=None, proto=None, port="", addr="", reporter=None, lgr=None, timeout=2, adapter=None
        """
        return SerialNode(ntype=ntype, proto=proto, port=port,\
            addr=addr, reporter=reporter, lgr=lgr, adapter=adapter)

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyNode')

