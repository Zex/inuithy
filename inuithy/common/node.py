## General node definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial, json
from abc import ABCMeta, abstractmethod
from enum import Enum

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
])

class Node:
    __metaclass__ = ABCMeta

    def __init__(self, ntype):
        self.ntype = ntype

    @abstractmethod
    def read(self, rdbyte=0, **kwargs):
        pass

    @abstractmethod
    def write(self, data="", **kwargs):
        pass

    def __str__(self):
        return json.dumps({'type':self.ntype.name})

class NodeBLE(Node):
    """Bluetooth node definition
    """
    def __init__(self, port):
        super(NodeBLE, self).__init__(NodeType.BLE)
        #TODO
        self.__serial = None
        self.__addr = ''

    def read(self, rdbyte=0, **kwargs):
        pass

    def write(self, data="", **kwargs):
        pass
    
    def __str__(self):
        # TODO: node info
        return json.dumps({'type':self.ntype.name, 'addr':self.__addr})
    # TODO: BLE command

class NodeZigbee(Node):
    """Zigbee node definition
    """
    def __init__(self, port):
        super(NodeBLE, self).__init__(NodeType.Zigbee)
        #TODO
        self.__serial = None

    def read(self, rdbyte=0, **kwargs):
        pass

    def write(self, data="", **kwargs):
        pass

    def __str__(self):
        # TODO: node info
        return json.dumps({'type':self.ntype.name, 'addr':self.__addr})
    # TODO: Zigbee command


