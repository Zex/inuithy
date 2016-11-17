""" Zigbee protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import string_write
from inuithy.protocol.protocol import Protocol
from enum import Enum

class ZigbeeProtocol(Protocol):
    """Protocol for communication with Zigbee firmware"""
    JOIN = "JOIN"
    WRITEATTRIBUTE2 = "writeAttribute2"
    GETNETWORKADDRESS = 'getNetworkAddress'
    GETUID = 'getUID'
    RESET_CONF = 'minimalDevice'
    DGN = 'Dgn'

    ReqType  = Enum('ReqType', [
        'snd_req',
    ])
    MsgType = Enum('MsgType', [
        'snd',
        'rcv',
        'dgn',
    ])

    def __init__(self):
        pass

    @staticmethod
    def joinnw(ch, ext_panid, panid, addr):
        msg = " ".join([ZigbeeProtocol.JOIN, str(ch), str(ext_panid), str(panid), str(addr), Protocol.EOL])
        return msg

    @staticmethod
    def writeattribute2(dest, psize, rsp=1):
#        msg = 'writeAttribute2 s '+str(destination)+' 20 0 4 0x42 "1" %s '%str(packet_size) + rsp +"\r"
#        data = " ".join([BluetoothDevice.WRITEATTRIBUTE2, "s", "0x%04X"%dest, "0x14 0x00 0x04 0x42", "1", "0x%02X"%psize, "0x%02X"%rsp, BluetoothDevice.EOL])
        msg = " ".join([ZigbeeProtocol.WRITEATTRIBUTE2, "s", "0x"+dest, "20 0 4 42", "1", str(psize), str(rsp), Protocol.EOL])
        return msg

