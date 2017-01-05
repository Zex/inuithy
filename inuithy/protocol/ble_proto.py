""" BLE protocol definition
 @author Zex Li <top_zlynch@yahoo.com>
 @reference BLE_Control_Protocol.pdf
"""
from inuithy.common.predef import _s, MessageType, T_MSG,\
TrafficType, T_SRC, T_DEST, T_CHANNEL, T_MSG_TYPE, T_TRAFFIC_TYPE,\
T_GENID, T_ADDR, T_TIME, T_NODE, T_PANID, NodeType
from inuithy.protocol.protocol import Protocol
import time
from random import randint

class BleProtocol(Protocol):
    """BLE control protocol
    """
    NAME = "Bluetooth Lower Energy"
    LIGHTON = "lighton"
    LIGHTOFF = "lightoff"
    JOINGRP = "joingrp"
    LEAVEGRP = "leavegrp"
    SETADDR = "setaddr"
    GETADDR = "getaddr"
    GETFWVER = "getfwver"

    @staticmethod
    def prepare(node):
        # TODO
        return True

    @staticmethod
    def start(node):
        # TODO
        return False

    @staticmethod
    def join(params=None):
        """Join command"""
        return PROTO.joingrp(params) 

    @staticmethod
    def traffic(params=None):
        """Traffic command"""
        return PROTO.lighton(params) 

    @staticmethod
    def joingrp(params=None):
        """Join group command builder"""
        grpid = params.get(T_PANID)
        return " ".join([PROTO.JOINGRP, grpid]) + Protocol.EOL

    @staticmethod
    def leavegrp(params=None):
        """Leave group command builder"""
        grpid = params.get(T_PANID)
        return " ".join([PROTO.LEAVEGRP, grpid]) + Protocol.EOL

    @staticmethod
    def lighton(params=None):
        """Light on command builder"""
        raddr = params.get(T_DEST)
        return " ".join([PROTO.LIGHTON, raddr]) + Protocol.EOL

    @staticmethod
    def lightoff(params=None):
        """Light off command builder"""
        raddr = params.get(T_DEST)
        return " ".join([PROTO.LIGHTOFF, raddr]) + Protocol.EOL

    @staticmethod
    def setaddr(params=None):
        """Set address command builder"""
        raddr = params.get(T_ADDR)
        return " ".join([PROTO.SETADDR, raddr]) + Protocol.EOL

    @staticmethod
    def getaddr(params=None):
        """Get address command builder"""
        return " ".join([PROTO.GETADDR]) + Protocol.EOL

    @staticmethod
    def getuid(params=None):
        """Get node uid"""
        return Protocol.EOL

    @staticmethod
    def parse_rbuf(data, node):
        """Parse recieved data
        @data Serial command sent
        @node Node object
        @return Dict report for sending to controller
        """
        data = data.strip('\t \r\n')
        #TODO parse data
        report = {
            T_GENID: node.genid,\
            T_TIME: time.time(),\
            T_MSG_TYPE: MessageType.RECV.name,\
            T_NODE: node.addr,\
#            T_MSG: data,
        }
#        if data.split(' ')[0] == 'joingrp':
        if node.joined is False:
            report[T_TRAFFIC_TYPE] = TrafficType.JOIN.name
            node.joined = True
        else:
            report[T_SRC] = hex(randint(4096, 65535))[2:] #TODO
            report[T_DEST] = node.addr
            report[T_TRAFFIC_TYPE] = TrafficType.SCMD.name
            
        return report

    @staticmethod
    def getfwver(params=None):
        """Get firmware version command builder"""
        return " ".join([PROTO.GETFWVER, Protocol.EOL])

    @staticmethod
    def isme(params=None):
        """Message replied to `getfwver` to identify protocol"""
        #TODO
        msg = params.get(T_MSG)
        return msg == PROTO.NAME

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
            T_TRAFFIC_TYPE: request.get(T_TRAFFIC_TYPE),#TrafficType.SCMD.name,
            T_NODE: node.addr,
#            T_MSG: data,
            T_SRC: request.get(T_SRC),
            T_DEST: request.get(T_DEST),
        }
        return report

PROTO = BleProtocol

