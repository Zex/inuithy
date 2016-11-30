""" BLE protocol definition
 @author Zex Li <top_zlynch@yahoo.com>
 @reference BLE_Control_Protocol.pdf
"""
from inuithy.common.predef import to_string, MessageType,\
TrafficType, T_SRC, T_DEST, T_CHANNEL, T_MSG_TYPE, T_TRAFFIC_TYPE,\
T_GENID, T_ADDR, T_TIME, T_NODE, T_PANID
from inuithy.protocol.protocol import Protocol
import time

class BleProtocol(Protocol):
    """BLE control protocol
    """
    LIGHTON = "lighton"
    LIGHTOFF = "lightoff"
    JOINGRP = "joingrp"
    LEAVEGRP = "leavegrp"
    SETADDR = "setaddr"
    GETADDR = "getaddr"
    GETFWVER = "getfwver"

    @staticmethod
    def joingrp(params=None):
        """Join group command builder"""
        grpid = params.get(T_PANID)
        return " ".join([BleProtocol.JOINGRP, grpid, Protocol.EOL])

    @staticmethod
    def leavegrp(params=None):
        """Leave group command builder"""
        grpid = params.get(T_PANID)
        return " ".join([BleProtocol.LEAVEGRP, grpid, Protocol.EOL])

    @staticmethod
    def lighton(params=None):
        """Light on command builder"""
        raddr = params.get(T_DEST)
        return " ".join([BleProtocol.LIGHTON, raddr, Protocol.EOL])

    @staticmethod
    def lightoff(params=None):
        """Light off command builder"""
        raddr = params.get(T_DEST)
        return " ".join([BleProtocol.LIGHTOFF, raddr, Protocol.EOL])

    @staticmethod
    def setaddr(params=None):
        """Set address command builder"""
        raddr = params.get(T_ADDR)
        return " ".join([BleProtocol.SETADDR, raddr, Protocol.EOL])

    @staticmethod
    def getaddr(params=None):
        """Get address command builder"""
        return " ".join([BleProtocol.GETADDR, Protocol.EOL])

    @staticmethod
    def parse_rbuf(data, node):
        """Parse recieved data
        @data Serial command sent
        @node Node object
        @return Dict report for sending to controller
        """
        #TODO parse data
        report = {
            T_GENID: node.genid,\
            T_TIME: time.time(),\
            T_MSG_TYPE: MessageType.RECV.name,\
            T_NODE: node.addr,\
#            T_MSG: data,
            T_SRC: hex(random.randint(4096, 65535))[2:], #TODO
            T_DEST: node.addr,
        }
#        if data.split(' ')[0] == 'joingrp':
#            report[T_TRAFFIC_TYPE] = TrafficType.JOIN.name
#        else
#            report[T_TRAFFIC_TYPE] = TrafficType.SCMD.name
        msg_type = random.randint(TrafficType.JOIN.value, TrafficType.SCMD.value)
        report[T_TRAFFIC_TYPE] = msg_type == TrafficType.JOIN.value\
            and TrafficType.JOIN.name or TrafficType.SCMD.name
        return report

    @staticmethod
    def getfwver(params=None):
        """Get firmware version command builder"""
        return " ".join([PROTO.GETFWVER, Protocol.EOL])

    @staticmethod
    def parse_wbuf(data, node, request):
        """Parse written buffer
        @data Serial command sent
        @node Node object
        @request Dict request information
        @return Dict report for sending to controller
        """
        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_MSG_TYPE: MessageType.SEND.name,
            T_NODE: node.addr,
#            T_MSG: data,
            T_SRC: request.get(T_SRC),
            T_DEST: request.get(T_DEST),
        }
        return report

PROTO = BleProtocol

