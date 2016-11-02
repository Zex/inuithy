## BLE protocol definition
# Author: Zex Li <top_zlynch@yahoo.com>
# Reference: BLE_Control_Protocol.pdf
#
from inuithy.protocol.protocol import *

class BleProtocol(Protocol):
    """BLE control protocol
    """
    def __init__(self):
        pass

    @staticmethod
    def traffic(*args, **kwargs):
        raddr = arg[0]
        return string_write("lighton {}", raddr)

    @staticmethod
    def joingrp(grpid):
        return string_write("joingrp {}", grpid)

    @staticmethod
    def leavegrp(grpid):
        return string_write("leavegrp {}", grpid)

    @staticmethod
    def lighton(*args, **kwargs):
        raddr = arg[0]
        return string_write("lighton {}", raddr)

    @staticmethod
    def lightoff(*args, **kwargs):
        raddr = arg[0]
        return string_write("lightoff {}", raddr)

    @staticmethod
    def setaddr(self, *args, **kwargs):
        addr = arg[0] 
        return sting_write("addr {}", addr)

    @staticmethod
    def getaddr(self, *args, **kwargs):
        return string_write("addr")


