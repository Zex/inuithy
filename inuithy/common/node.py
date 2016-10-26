## General node definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial, json
from abc import ABCMeta, abstractmethod
from inuithy.util.cmd_helper import *

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
    "UNKNOWN",
])

class SerialNode:
    __metaclass__ = ABCMeta

    def __init__(self, ntype, reporter=None):
        self.ntype = ntype
        self.reporter = reporter

    def read(self, rdbyte=0, **kwargs):
        # TODO
        console_write("R: rdbyte:{}", rdbyte)
        pass

    def write(self, data="", **kwargs):
        # TODO
        console_write("W: data:[{}], len:{}", data, len(data))
        pass

    def report_write(self, data):
        if self.reporter != None:
           pub_reportwrite(self.reporter, data=data)

    def __str__(self):
        return json.dumps({CFGKW_TYPE:self.ntype.name})

class NodeBLE(SerialNode):
    """Bluetooth node definition
    @addr Node address in network
    @port Serial port path
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeBLE, self).__init__(NodeType.BLE, reporter)
        #TODO
        self.__serial = None
        self.addr = addr
        self.port = port

    def __str__(self):
        return json.dumps({
            CFGKW_TYPE:self.ntype.name,
            CFGKW_ADDR:self.addr,
            CFGKW_PORT:self.port})
    # TODO: BLE control protocol
    def joingrp(self, grpid):
        msg = string_write("joingrp {}", grpid)
        self.write(msg)
        self.report_write(msg)

    def leavegrp(self, grpid):
        msg = string_write("leavegrp {}", grpid)
        self.write(msg)
        self.report_write(msg)

    def lighton(self, raddr):
        msg = string_write("lighton {}", raddr)
        self.write(msg)
        self.report_write(msg)

    def lightoff(self, raddr):
        msg = string_write("lightoff {}", raddr)
        self.write(msg)
        self.report_write(msg)

    def setaddr(self, addr):
        msg = string_write("addr {}", addr)
        self.write(msg)
        self.addr = addr
        self.report_write(msg)



class NodeZigbee(SerialNode):
    """Zigbee node definition
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeZigbee, self).__init__(NodeType.Zigbee, reporter)
        #TODO
        self.__serial = None
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


