## BLE protocol definition
# Author: Zex Li <top_zlynch@yahoo.com>
# Reference: BLE_Control_Protocol.pdf
#
from inuithy.protocol.protocol import *

class BleProtocol(Protocol):
    
    def __init__(self):
        pass
    @staticmethod
    def joingrp(grpid):
        return string_write("joingrp {}", grpid)

    @staticmethod
    def leavegrp(grpid):
        return string_write("leavegrp {}", grpid)

    @staticmethod
    def traffic(*arg, **kwargs):
        raddr = arg[0]
        return string_write("lighton {}", raddr)

