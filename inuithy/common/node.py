## General node definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial
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

class NodeBLE(Node):
    """Bluetooth node definition
    """
    def __init__(self):
        super.__init__(self, NoteType.BLE)

    def read(self, rdbyte=0, **kwargs):
        pass

    def write(self, data="", **kwargs):
        pass

    # TODO: BLE command

class NodeZigbee(Node):
    """Zigbee node definition
    """
    def __init__(self):
        super.__init__(self, NoteType.Zigbee)

    def read(self, rdbyte=0, **kwargs):
        pass

    def write(self, data="", **kwargs):
        pass

    # TODO: Zigbee command


