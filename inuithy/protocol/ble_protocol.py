## BLE protocol definition
# Author: Zex Li <top_zlynch@yahoo.com>
# Reference: BLE_Control_Protocol.pdf
#
from inuithy.protocol.protocol import *

class BleProtocol(Protocol):
    
    def __init__(self):
        pass

    def joingrp(self, grpid):
        return string_write("joingrp {}", grpid)

    def leavegrp(self, grpid):
        return string_write("leavegrp {}", grpid)

