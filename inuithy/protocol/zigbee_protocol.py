## Zigbee protocol definition
# Author: Zex Li <top_zlynch@yahoo.com>
# Reference: Zigbee_Control_Protocol.pdf
#
from inuithy.protocol.protocol import *

class ZigbeeProtocol(Protocol):
    
    def __init__(self):
        pass

    def joinnw(self, ch):
        return string_write("join {}", ch)


