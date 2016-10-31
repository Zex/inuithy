## General node definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial, json, time
from copy import deepcopy
from abc import ABCMeta, abstractmethod
from inuithy.util.cmd_helper import *
from inuithy.protocol.ble_protocol import BleProtocol as BleProt
import threading as thrd
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)
lg = logging.getLogger('InuithyNode')

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
    "UNKNOWN",
])

class SerialNode:
    __metaclass__ = ABCMeta

    def __init__(self, ntype, port="", reporter=None, lg=None, baudrate=115200, timeout=2):
        if lg == None: self.lg = logging
        else: self.lg = lg
        self.ntype = ntype
        self.reporter = reporter
        # TODO: create serial object 
        self.__serial = None #serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.__listener = thrd.Thread(target=self.__listener_routine, name="Listener")
        self.run_listener = False

    def read(self, rdbyte=0, report=None):
        self.lg.debug(string_write("SerialNode#R: rdbyte:{}", rdbyte))
        rdbuf = ""
        if self.__serial != None and self.__serial.isOpen():
            if 0 < self.__serial.inWaiting(): 
                rdbuf = self.__serial.readall()
#                self.lg.debug(string_write("SerialNode: rdbuf:[{}], len:[{}]", rdbuf, len(rdbuf)))
        if report != None:
            #TODO DEBUG
#            report[CFGKW_MSG] = rdbuf
            self.report_read(report)
        return rdbuf

    def write(self, data="", report=None):
        self.lg.debug(string_write("SerialNode#W: data:[{}], len:{}", data, len(data)))
        written = 0
        if self.__serial != None and self.__serial.isOpen():
            written = self.__serial.write(data)
#            self.lg.debug(string_write("SerialNode: writebuf:[{}], len:[{}], written:[{}]", data, len(data), written))
        if report != None:
            report[CFGKW_MSG] = data
            self.report_write(report)

    def start_listener(self):
        if self.run_listener == False:
            self.run_listener = True
            if self.__listener != None: self.__listener.start()

    def __listener_routine(self):
        while self.run_listener:
            try:
                if self.__serial == None: time.sleep(5)
                report = deepcopy(self.report)
                self.read(report=report)
            except Exception as ex:
                self.lg.error(string_write("Exception in listener routine: {}", ex))

    def stop_listener(self):
        self.run_listener = False

    def report_write(self, data):
        data.__setitem__(CFGKW_MSG_TYPE, MessageType.SENT.name)
        if self.reporter != None:
            pub_reportwrite(self.reporter, data=data)

    def report_read(self, data):
        data.__setitem__(CFGKW_MSG_TYPE, MessageType.RECV.name)
        if self.reporter != None:
            pub_notification(self.reporter, data=data)

    def __str__(self):
        return jsoin.dumps({CFGKW_TYPE:self.ntype.name})

    def __del__(self):
        self.stop_listener()

    @abstractmethod
    def join(self, data):
        pass

    @abstractmethod
    def traffic(self, data):
        pass

class NodeBLE(SerialNode):
    """Bluetooth node definition
    @addr Node address in network
    @port Serial port path
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeBLE, self).__init__(NodeType.BLE, port, reporter)
        #TODO
        self.addr = addr
        self.port = port
        self.prot = BleProt
        self.start_listener()
        self.report = None

    def __str__(self):
        return json.dumps({
            CFGKW_TYPE:self.ntype.name,
            CFGKW_ADDR:self.addr,
            CFGKW_PORT:self.port})
    # TODO: BLE control protocol
    def join(self, data):
        self.report = data
        self.joingrp(data[CFGKW_PANID], data)

    def traffic(self, data):
        self.lighton(self, data[CFGKW_ADDRS], data)

    def joingrp(self, grpid, report=None):
        msg = self.prot.joingrp(grpid)
        self.write(msg, report)

    def leavegrp(self, grpid, report=None):
        msg = self.prot.leavegrp(grpid)
        self.write(msg, report)

    def lighton(self, raddr, report=None):
        msg = self.prot.lighton(raddr)
        self.write(msg, report)

    def lightoff(self, raddr, report=None):
        msg = self.prot.lightoff(raddr)
        self.write(msg, report)

    def setaddr(self, addr, report=None):
        msg = self.prot.setaddr(addr)
        self.write(msg, report)
        self.addr = addr


class NodeZigbee(SerialNode):
    """Zigbee node definition
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeZigbee, self).__init__(NodeType.Zigbee, port, reporter)
        #TODO
        self.addr = addr
        self.port = port
        self.prot = ZigbeeProtocol()

#    def read(self, rdbyte=0, **kwargs):
#        pass

#    def write(self, data="", **kwargs):
#        pass

    def __str__(self):
        # TODO: node info
        return json.dumps({CFGKW_TYPE:self.ntype.name, CFGKW_ADDR:self.addr, CFGKW_PORT: self.port})
    # TODO: Zigbee command

    def join(self, data):
        pass

    def traffic(self, data):
        pass

