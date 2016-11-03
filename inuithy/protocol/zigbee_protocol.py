""" Zigbee protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import string_write
from inuithy.protocol.protocol import Protocol

class ZigbeeProtocol(Protocol):
    
    def __init__(self):
        pass

    def joinnw(self, ch):
        return string_write("join {}", ch)


