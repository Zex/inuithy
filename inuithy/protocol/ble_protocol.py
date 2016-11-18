""" BLE protocol definition
 @author Zex Li <top_zlynch@yahoo.com>
 @reference BLE_Control_Protocol.pdf
"""
from inuithy.common.predef import string_write
from inuithy.protocol.protocol import Protocol

class BleProtocol(Protocol):
    """BLE control protocol
    """
    LIGHTON = "lighton"
    LIGHTOFF = "lightoff"
    JOINGRP = "joingrp"
    LEAVEGRP = "leavegrp"
    SETADDR = "setaddr"
    GETADDR = "getaddr"

    def __init__(self):
        pass

    @staticmethod
    def traffic(*args, **kwargs):
        raddr = args[0]
        return " ".join([BleProtocol.LIGHTON, raddr])

    @staticmethod
    def joingrp(grpid):
        return " ".join([BleProtocol.JOINGRP, grpid, Protocol.EOL])

    @staticmethod
    def leavegrp(grpid):
        return " ".join([BleProtocol.LEAVEGRP, grpid, Protocol.EOL])

    @staticmethod
    def lighton(*args, **kwargs):
        raddr = args[0]
        return " ".join([BleProtocol.LIGHTON, raddr, Protocol.EOL])

    @staticmethod
    def lightoff(*args, **kwargs):
        raddr = args[0]
        return " ".join([BleProtocol.LIGHTOFF, raddr, Protocol.EOL])

    @staticmethod
    def setaddr(self, *args, **kwargs):
        addr = args[0] 
        return " ".join([BleProtocol.SETADDR, raddr, Protocol.EOL])

    @staticmethod
    def getaddr(self, *args, **kwargs):
        return " ".join([BleProtocol.GETADDR, Protocol.EOL])


