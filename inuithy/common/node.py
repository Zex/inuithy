""" General node definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import TrafficType, T_MSG, T_GENID,\
INUITHY_LOGCONFIG, to_string, T_TYPE, T_ADDR, T_PORT
from inuithy.util.cmd_helper import pub_reportwrite, pub_notification
from inuithy.protocol.ble_proto import BleProtocol as BleProt
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProt
from inuithy.protocol.zigbee_proto import T_RSP
from inuithy.protocol.bzcombo_proto import BzProtocol as BZProt

import logging.config as lconf
from enum import Enum
import threading
import logging
import serial
import json
import random

lconf.fileConfig(INUITHY_LOGCONFIG)

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
    "BleZbee",
    "UNKNOWN",
])

class SerialNode(object):
    """Node control via serial port
    """
    def __init__(self, ntype, port="", reporter=None, lgr=None, timeout=2):
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging
        self.port = port
        self.addr = None
        self.ntype = ntype
        self.reporter = reporter
        self.prot = None
        # TODO: create serial object
        self.__serial = None #serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.__listener = threading.Thread(target=self.__listener_routine, name="Listener")
        self.run_listener = False
        self.genid = None
        self.done = threading.Event()

    def __str__(self):
        return json.dumps({T_TYPE:self.ntype.name})

    def __del__(self):
        self.stop_listener()

    def read(self, rdbyte=0):
        """Read data ultility"""
#        self.lgr.debug(to_string("SerialNode#R: rdbyte:{}", rdbyte))
        rdbuf = ""
        if self.__serial is not None and self.__serial.isOpen():
            if 0 < self.__serial.inWaiting():
                rdbuf = self.__serial.readall()
        #TODO
        self.report_read(rdbuf)
        return rdbuf

    def write(self, data="", request=None):
        """Write data ultility"""
#       self.lgr.debug(to_string("SerialNode#W: data:[{}], len:{}", data, len(data)))
        written = 0
        if self.__serial is not None and self.__serial.isOpen():
            written = self.__serial.write(data)
        #TODO -->
        self.report_write(data, request)
        self.done.set()

    def start_listener(self):
        """Start listening incoming package"""
        if self.run_listener is False and self.port is not None and len(self.port) > 0:
            self.run_listener = True
            if self.__listener is not None:
                self.__listener.start()

    def __listener_routine(self):
        """Listen for incoming packages"""
        while self.run_listener:
            try:
                if self.__serial is None: #DEBUG
                    self.done.wait()#random.randint(30, 50))
                self.read()
                self.done.clear()
            except Exception as ex:
                self.lgr.error(to_string("Exception in listener routine: {}", ex))

    def stop_listener(self):
        """Stop running listener"""
        self.run_listener = False
        self.done.set()

    def join(self, data):
        """General join adapter"""
        pass

    def traffic(self, data):
        """General traffic adapter"""
        pass

    def report_read(self, data=None):
        """"Report received data"""
        if self.reporter is None or self.genid is None:
            return
#TODO: uncomment
#       if data is None or len(data) == 0:
#           return
        report = self.prot.parse_rbuf(data, self)
        if report is not None and len(report) > 2:
            pub_notification(self.reporter, data=report)

    def report_write(self, data=None, request=None):
        """"Report writen data"""
        if self.reporter is None or self.genid is None or request is None:
            return
#TODO: uncomment
#       if data is None or len(data) == 0:
#           return
        report = self.prot.parse_wbuf(data, self, request)
        if report is not None and len(report) > 2:
            pub_reportwrite(self.reporter, data=report)

class NodeBLE(SerialNode):
    """Bluetooth node definition
    @addr Node address in network
    @port Serial port path
    """
    def __init__(self, port='', addr='', reporter=None, lgr=None):
        super(NodeBLE, self).__init__(NodeType.BLE, port, reporter, lgr)
        self.addr = addr
        self.port = port
        self.prot = BleProt
        self.prot.lgr = self.lgr
#        if port is not None and len(port) > 0:
#            self.start_listener()

    def __str__(self):
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def join(self, data):
        """General join request adapter"""
        self.genid = data.get(T_GENID)
        self.joingrp(data)

    def traffic(self, data):
        """General traffic request adapter"""
        self.genid = data.get(T_GENID)
        self.lighton(data)

    def joingrp(self, request):
        """Send joingrp command"""
        msg = self.prot.joingrp(request)
        self.write(msg, request)

    def leavegrp(self, request):
        """Send leavegrp command"""
        msg = self.prot.leavegrp(request)
        self.write(msg, request)

    def lighton(self, request):
        """Send lighton command"""
        msg = self.prot.lighton(request)
        self.write(msg, request)

    def lightoff(self, raddr, request=None):
        """Send lightoff command"""
        msg = self.prot.lightoff(raddr)
        self.write(msg, request)

    def setaddr(self, addr, request=None):
        """Send setaddr command"""
        msg = self.prot.setaddr(addr)
        self.write(msg, request)

    def getaddr(self, request=None):
        """Send getaddr command"""
        msg = self.prot.getaddr()
        self.write(msg, request)
#        self.addr = addr

class NodeZigbee(SerialNode):
    """Zigbee node definition
    """
    def __init__(self, port='', addr='', reporter=None, lgr=None):
        super(NodeZigbee, self).__init__(NodeType.Zigbee, port, reporter, lgr)
        #TODO
        self.addr = addr
        self.uid = None
        self.port = port
        self.sequence_nr = 0
        self.joined = False # DEBUG data
        self.prot = ZbeeProt
        self.prot.lgr = self.lgr

    def __str__(self):
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def join(self, data):
        """General join request adapter"""
        self.genid = data.get(T_GENID)
        self.joinnw(data)

    def traffic(self, data):
        """General traffic request adapter"""
        self.genid = data.get(T_GENID)
        data[T_RSP] = 1
        self.writeattribute2(data)

    def joinnw(self, request):
        """Send join command"""
        msg = self.prot.joinnw(request)
        self.write(msg, request)

    def writeattribute2(self, request):
        """Send writeattribute2 command"""
        msg = self.prot.writeattribute2(request)
        self.write(msg, request)

class NodeBz(SerialNode):
    """BLE-Zigbee node definition
    """
    def __init__(self, port='', addr='', reporter=None, lgr=None):
        super(NodeBz, self).__init__(NodeType.Zigbee, port, reporter, lgr)
        #TODO
        self.addr = addr
        self.uid = None
        self.port = port
        self.sequence_nr = 0
        self.joined = False # DEBUG data
        self.prot = ZbeeProt
        self.prot.lgr = self.lgr

    def __str__(self):
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def join(self, data):
        """General join request adapter"""
        self.genid = data.get(T_GENID)
        self.joinnw(data)

    def traffic(self, data):
        """General traffic request adapter"""
        self.genid = data.get(T_GENID)
        data[T_RSP] = 1
        self.writeattribute2(data)

    def joinnw(self, request):
        """Send join command"""
        msg = self.prot.joinnw(request)
        self.write(msg, request)

    def writeattribute2(self, request):
        """Send writeattribute2 command"""
        msg = self.prot.writeattribute2(request)
        self.write(msg, request)

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyNode')

