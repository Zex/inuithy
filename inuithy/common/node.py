""" General node definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import TrafficType, T_TRAFFIC_TYPE, T_MSG,\
INUITHY_LOGCONFIG, T_MSG_TYPE, MessageType, string_write, T_TYPE,\
T_ADDR, T_PORT, T_PANID, T_TIME, T_NODE, T_SENDER, T_RECIPIENT
from inuithy.util.cmd_helper import pub_reportwrite, pub_notification
from inuithy.protocol.ble_protocol import BleProtocol as BleProt
from inuithy.protocol.zigbee_protocol import ZigbeeProtocol
import logging.config as lconf
import threading as threading
#from datetime import datetime as dt
from copy import deepcopy
from enum import Enum
import logging
import serial
import json
import time

lconf.fileConfig(INUITHY_LOGCONFIG)

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
    "UNKNOWN",
])

class SerialNode(object):
    """Node control via serial port
    """
    def __init__(self, ntype, port="", reporter=None, lgr=None, timeout=2):
        if lgr is None:
            self.lgr = logging
        else:
            self.lgr = lgr
        self.port = port
        self.addr = None
        self.ntype = ntype
        self.reporter = reporter
        # TODO: create serial object
        self.__serial = None #serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.__listener = threading.Thread(target=self.__listener_routine, name="Listener")
        self.run_listener = False

    def read(self, rdbyte=0, report=None):
#        self.lgr.debug(string_write("SerialNode#R: rdbyte:{}", rdbyte))
        rdbuf = ""
        if self.__serial is not None and self.__serial.isOpen():
            if 0 < self.__serial.inWaiting():
                rdbuf = self.__serial.readall()
        #TODO
        if report is not None:
            #TODO parse rdbuf
#            report[T_MSG] = rdbuf
            report[T_NODE] = self.addr
#            report[T_RECIPIENT] = self.addr
            report[T_TIME] = str(int(time.time()))#dt.now())
#            if rdbuf.split(' ')[0] == 'joingrp':
#                report[T_TRAFFIC_TYPE] = TrafficType.JOIN.name
#            else
#                report[T_TRAFFIC_TYPE] = TrafficType.SCMD.name
            import random
            traftype = random.randint(TrafficType.JOIN.value, TrafficType.SCMD.value)
            report[T_TRAFFIC_TYPE] = traftype == TrafficType.JOIN.value and TrafficType.JOIN.name or TrafficType.SCMD.name

            self.report_read(report)
        return rdbuf

    def write(self, data="", report=None):
#        self.lgr.debug(string_write("SerialNode#W: data:[{}], len:{}", data, len(data)))
        written = 0
        if self.__serial is not None and self.__serial.isOpen():
            written = self.__serial.write(data)
        #TODO -->
        if report is not None:
            self.report = deepcopy(report)
            report[T_TIME] = str(int(time.time()))#dt.now())
            report[T_MSG] = data
            self.report_write(report)

    def start_listener(self):
        if self.run_listener is False and self.port is not None and len(self.port) > 0:
            self.run_listener = True
            # TODO if self.__listener is not None and self.__serial is not None: self.__listener.start()
            if self.__listener is not None:
                self.__listener.start()

    def __listener_routine(self):
        while self.run_listener:
            try:
                if self.__serial is None:
                    time.sleep(5)
                report = deepcopy(self.report)
                self.read(report=report)
            except Exception as ex:
                self.lgr.error(string_write("Exception in listener routine: {}", ex))

    def stop_listener(self):
        self.run_listener = False

    def report_write(self, data):
        data.__setitem__(T_MSG_TYPE, MessageType.SENT.name)
        if self.reporter is not None:
            pub_reportwrite(self.reporter, data=data)

    def report_read(self, data):
        data.__setitem__(T_MSG_TYPE, MessageType.RECV.name)
        if self.reporter is not None:
            pub_notification(self.reporter, data=data)

    def __str__(self):
        return jsoin.dumps({T_TYPE:self.ntype.name})

    def __del__(self):
        self.stop_listener()

    def join(self, data):
        pass

    def traffic(self, data):
        pass

class NodeBLE(SerialNode):
    """Bluetooth node definition
    @addr Node address in network
    @port Serial port path
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeBLE, self).__init__(NodeType.BLE, port, reporter)
        self.addr = addr
        self.port = port
        self.prot = BleProt
        self.report = None
#        if port is not None and len(port) > 0:
#            self.start_listener()

    def __str__(self):
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def join(self, data):
        self.report = deepcopy(data)
        self.joingrp(data[T_PANID], data)

    def traffic(self, data):
        self.report = deepcopy(data)
        self.lighton(self, data[T_ADDRS], data)

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

    def getaddr(self, report=None):
        msg = self.prot.getaddr(addr)
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
        return json.dumps({T_TYPE:self.ntype.name, T_ADDR:self.addr, T_PORT: self.port})
    # TODO: Zigbee command

    def join(self, data):
        pass

    def traffic(self, data):
        pass

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyNode')
