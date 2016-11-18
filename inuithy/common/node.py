""" General node definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import TrafficType, T_TRAFFIC_TYPE, T_MSG,\
INUITHY_LOGCONFIG, T_MSG_TYPE, MessageType, string_write, T_TYPE, T_SPANID,\
T_ADDR, T_PORT, T_PANID, T_TIME, T_NODE, T_SRC, T_DEST, T_ACK, T_CHANNEL,\
T_ZBEE_NWK_SRC, T_ZBEE_NWK_DST, T_ZBEE_NWK_ADDR, T_AVGMACRETRY, T_RSP,\
T_LASTMSGLQI, T_LASTMSGRSSI, T_PKGBUFALLOCFAIL, T_RTDISCINIT, T_YES,\
T_APSRXBCAST, T_APSTXBCAST, T_APSTXUCASTRETRY, T_RELAYEDUCAST, T_STATUS,\
T_APSRXUCAST, T_NEIGHBORADDED, T_NEIGHBORRMED, T_NEIGHBORSTALE, T_GENID,\
T_MACRXUCAST, T_MACTXUCAST, T_MACTXUCASTFAIL, T_MACTXUCASTRETRY,\
T_MACRXBCAST, T_MACTXBCAST, T_APSTXUCASTSUCCESS, T_APSTXUCASTFAIL,\
T_UNKNOWN_RESP, T_PKGSIZE, T_ZBEE_ZCL_CMD_TSN, T_SND_SEQ_NR
from inuithy.util.cmd_helper import pub_reportwrite, pub_notification
from inuithy.protocol.ble_protocol import BleProtocol as BleProt
from inuithy.protocol.zigbee_protocol import ZigbeeProtocol as ZbeeProt
import logging.config as lconf
from enum import Enum
import threading
import logging
import serial
import json
import time
import random

lconf.fileConfig(INUITHY_LOGCONFIG)

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
    "UNKNOWN",
])

class SerialNode(object):
    """Node control via serial port
    """
    def __init__(self, ntype, port="", reporter=None, lgr=None, timeout=2):
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging
        self.port = port
        self.addr = None
        self.ntype = ntype
        self.reporter = reporter
        # TODO: create serial object
        self.__serial = None #serial.Serial(port, baudrate=baudrate, timeout=timeout)
        self.__listener = threading.Thread(target=self.__listener_routine, name="Listener")
        self.run_listener = False
        self.genid = None
        self.done = threading.Event()

    def read(self, rdbyte=0):
        """Read data ultility"""
#        self.lgr.debug(string_write("SerialNode#R: rdbyte:{}", rdbyte))
        rdbuf = ""
        if self.__serial is not None and self.__serial.isOpen():
            if 0 < self.__serial.inWaiting():
                rdbuf = self.__serial.readall()
        #TODO
        self.report_read(rdbuf)
        return rdbuf

    def write(self, data="", request=None):
        """Write data ultility"""
#       self.lgr.debug(string_write("SerialNode#W: data:[{}], len:{}", data, len(data)))
        written = 0
        if self.__serial is not None and self.__serial.isOpen():
            written = self.__serial.write(data)
        #TODO -->
        self.report_write(data, request)

    def start_listener(self):
        """Start listening incoming package"""
        if self.run_listener is False and self.port is not None and len(self.port) > 0:
            self.run_listener = True
            if self.__listener is not None:
                self.__listener.start()

    def __listener_routine(self):
        """Listen for incoming packages"""
        while self.run_listener:
            try:
                if self.__serial is None: #DEBUG
                    self.done.wait(random.randint(1, 5))#30, 50))
                self.read()
                self.done.clear()
            except Exception as ex:
                self.lgr.error(string_write("Exception in listener routine: {}", ex))

    def stop_listener(self):
        """Stop running listener"""
        self.run_listener = False

    def report_write(self, data=None, request=None):
        """Report written data"""
        pass

    def report_read(self, data=None):
        """Report read data"""
        pass

    def __str__(self):
        return json.dumps({T_TYPE:self.ntype.name})

    def __del__(self):
        self.stop_listener()

    def join(self, data):
        """General join adapter"""
        pass

    def traffic(self, data):
        """General traffic adapter"""
        pass

class NodeBLE(SerialNode):
    """Bluetooth node definition
    @addr Node address in network
    @port Serial port path
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeBLE, self).__init__(NodeType.BLE, port, reporter)
        self.addr = addr
        self.port = port
        self.prot = BleProt
#        if port is not None and len(port) > 0:
#            self.start_listener()

    def __str__(self):
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def report_write(self, data=None, request=None):
        """"Report writen data"""
        if self.reporter is None or self.genid is None:
            return
#       if data is None or len(data) == 0:
#           return
        report = {
            T_TIME: str(time.time()),
            T_GENID: self.genid,
            T_MSG_TYPE: MessageType.SEND.name,
            T_NODE: self.addr,
            T_MSG: data,
            T_SRC: request.get(T_SRC),
            T_DEST: request.get(T_DEST),
        }
        pub_reportwrite(self.reporter, data=report)

    def report_read(self, data=None):
        """"Report received data"""
        if self.reporter is None or self.genid is None:
            return
#       if data is None or len(data) == 0:
#           return
        #TODO parse data
        report = {
            T_TIME: str(time.time()),
            T_GENID: self.genid,
            T_MSG_TYPE: MessageType.RECV.name,
            T_NODE: self.addr,
            T_MSG: data,
            T_SRC: 'SOMEONE', #TODO
            T_DEST: self.addr,
        }
#        if data.split(' ')[0] == 'joingrp':
#            report[T_TRAFFIC_TYPE] = TrafficType.JOIN.name
#        else
#            report[T_TRAFFIC_TYPE] = TrafficType.SCMD.name
        msg_type = random.randint(TrafficType.JOIN.value, TrafficType.SCMD.value)
        report[T_TRAFFIC_TYPE] = msg_type == TrafficType.JOIN.value\
            and TrafficType.JOIN.name or TrafficType.SCMD.name

        report.__setitem__(T_MSG_TYPE, MessageType.RECV.name)
        pub_notification(self.reporter, data=report)

    def join(self, data):
        """General join request adapter"""
        self.genid = data.get(T_GENID)
        self.joingrp(data.get(T_PANID), request=data)

    def traffic(self, data):
        """General traffic request adapter"""
        self.genid = data.get(T_GENID)
        self.lighton(data.get(T_DEST), request=data)

    def joingrp(self, grpid, request=None):
        """Send joingrp command"""
        msg = self.prot.joingrp(grpid)
        self.write(msg, request)

    def leavegrp(self, grpid, request=None):
        """Send leavegrp command"""
        msg = self.prot.leavegrp(grpid)
        self.write(msg, request)

    def lighton(self, raddr, request=None):
        """Send lighton command"""
        msg = self.prot.lighton(raddr)
        self.write(msg, request)

    def lightoff(self, raddr, request=None):
        """Send lightoff command"""
        msg = self.prot.lightoff(raddr)
        self.write(msg, request)

    def setaddr(self, addr, request=None):
        """Send setaddr command"""
        msg = self.prot.setaddr(addr)
        self.write(msg, request)

    def getaddr(self, request=None):
        """Send getaddr command"""
        msg = self.prot.getaddr()
        self.write(msg, request)
#        self.addr = addr

class NodeZigbee(SerialNode):
    """Zigbee node definition
    """
    def __init__(self, port='', addr='', reporter=None):
        super(NodeZigbee, self).__init__(NodeType.Zigbee, port, reporter)
        #TODO
        self.addr = addr
        self.uid = None
        self.port = port
        self.prot = ZbeeProt()
        self.sequence_nr = 0
        self.joined = False # DEBUG data

    def __str__(self):
        return json.dumps({
            T_TYPE:self.ntype.name,
            T_ADDR:self.addr,
            T_PORT:self.port})

    def join(self, data):
        """General join request adapter"""
        self.genid = data.get(T_GENID)
        self.joinnw(data.get(T_CHANNEL), data.get(T_PANID), data.get(T_SPANID), data.get(T_NODE), request=data)

    def traffic(self, data):
        """General traffic request adapter"""
        self.genid = data.get(T_GENID)
        self.writeattribute2(data.get(T_DEST), data.get(T_PKGSIZE), 1, request=data)

    def joinnw(self, ch, ext_panid, panid, addr, request=None):
        """Send join command"""
        msg = self.prot.joinnw(ch, ext_panid, panid, addr)
        self.write(msg, request)

    def writeattribute2(self, dest, psize, rsp, request=None):
        """Send writeattribute2 command"""
        msg = self.prot.writeattribute2(dest, psize, rsp)
        request[T_RSP] = rsp
        self.write(msg, request)

    def report_write(self, data=None, request=None):
        """"Report writen data"""
        if self.reporter is None or self.genid is None:
            return
#       if data is None or len(data) == 0:
#           return
        report = {
            T_TIME: time.time(),
            T_GENID: self.genid,
            T_MSG_TYPE: MessageType.SEND.name,
            T_NODE: self.addr,
            T_TYPE: self.prot.ReqType.snd_req.name,
            T_ZBEE_NWK_SRC: request.get(T_SRC),#self.addr,
            T_ZBEE_NWK_DST: request.get(T_DEST),
            T_ACK: request.get(T_RSP) == 1 and 'y' or 'n',
        }
        pub_reportwrite(self.reporter, data=report)

    def report_read(self, data=None):
        """"Report received data"""
        if self.reporter is None or self.genid is None:
            return
#       if data is None or len(data) == 0:
#           return
        report = {}
        params = data.split(' ')

        # DEBUG data
        rand = random.randint(MessageType.RECV.value, MessageType.UNKNOWN.value)
        if self.joined is False:
#        if rand == MessageType.JOINING.value
            params = []
            params.append(MessageType.JOINING.name)
        else:
            if rand == MessageType.RECV.value:
                params = []
                params.append(MessageType.RECV.name)
                params.append(str(random.randint(0, 10)))
                params.append(str(random.randint(0, 10)))
                params.append(str(random.randint(1100, 1144)))
            elif rand == MessageType.SEND.value:
                params = []
                params.append(MessageType.SEND.name)
                params.append(str(random.randint(0, 10)))
                params.append(str(random.randint(0, 10)))
                params.append(str(random.randint(0, 10)))
                params.append(str(random.randint(1100, 1144)))
                params.append(str(random.randint(10, 100)))
            else:
                params = [self.prot.DGN]
                params.extend([str(random.randint(0, 2000)) for _ in range(21)])
        #------------end debug data--------------
        msg_type = params[0].upper()

        if msg_type == MessageType.SEND.name:
            if len(params) == 6:
                report = {\
                    T_TIME: time.time(),\
                    T_GENID: self.genid,\
                    T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
                    T_NODE: self.addr,
                    T_MSG_TYPE: MessageType.RECV.name,
                    T_ZBEE_NWK_SRC: self.addr,\
                    T_ZBEE_NWK_DST: params[4],\
                    T_TYPE: self.prot.MsgType.snd.name,\
                    T_ZBEE_ZCL_CMD_TSN: params[1],\
                    T_STATUS: params[5],\
                    T_SND_SEQ_NR: self.sequence_nr,\
                }
                self.sequence_nr += 1
#                if status == '0x00':
#                    self.nr_messages_sent += 1
            else:
                self.lgr.error(string_write('Incorrect send confirm: {}', data))
        elif msg_type == MessageType.RECV.name:
            report = {\
                    T_TIME: time.time(),\
                    T_GENID: self.genid,\
                    T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
                    T_MSG_TYPE: MessageType.RECV.name,
                    T_NODE: self.addr,
                    T_TYPE: self.prot.MsgType.rcv.name,\
                    T_ZBEE_NWK_SRC: params[3],\
                    T_ZBEE_NWK_DST: self.addr,\
                    T_ZBEE_ZCL_CMD_TSN: params[1],\
            }
        elif msg_type == MessageType.JOINING.name:
            report = {\
                T_TIME: time.time(),\
                T_GENID: self.genid,\
                T_TRAFFIC_TYPE: TrafficType.JOIN.name,\
                T_MSG_TYPE: MessageType.RECV.name,\
                T_NODE: self.addr,\
            }
            #DEBUG data
            self.joined = True
        elif params[0] == 'Trying':
            pass
        elif params[0] == 'Network':
            pass
        elif params[0] == self.prot.GETUID:
            self.uid = params[1]
        elif params[0] == self.prot.GETNETWORKADDRESS:
            self.addr = data[-6:]
        elif params[0] == self.prot.RESET_CONF:
            pass
        elif params[0] == self.prot.DGN:
            report = {
                T_TIME: time.time(),\
                T_GENID: self.genid,\
                T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
                T_MSG_TYPE: MessageType.RECV.name,\
                T_NODE: self.addr,\
                T_TYPE: self.prot.MsgType.dgn.name,
                T_ZBEE_NWK_ADDR: self.addr,\
                T_AVGMACRETRY: params[1],\
                T_LASTMSGLQI: params[2],\
                T_LASTMSGRSSI: params[3],\
                T_PKGBUFALLOCFAIL: params[4],\
                T_RTDISCINIT: params[5],\
                T_APSRXBCAST: params[6],\
                T_APSTXBCAST: params[7],\
                T_APSTXUCASTRETRY: params[8],\
                T_RELAYEDUCAST: params[9],\
                T_APSRXUCAST: params[10],\
                T_NEIGHBORADDED: params[11],\
                T_NEIGHBORRMED: params[12],\
                T_NEIGHBORSTALE: params[13],\
                T_MACRXUCAST: params[14],\
                T_MACTXUCAST: params[15],\
                T_MACTXUCASTFAIL: params[16],\
                T_MACTXUCASTRETRY: params[17],\
                T_MACRXBCAST: params[18],\
                T_MACTXBCAST: params[19],\
                T_APSTXUCASTSUCCESS: params[20],\
                T_APSTXUCASTFAIL: params[21],\
            }
        else:
            report = {\
                T_TIME: time.time(),\
                T_GENID: self.genid,\
                T_MSG_TYPE: MessageType.RECV.name,\
                T_NODE: self.addr,\
                T_UNKNOWN_RESP: T_YES,\
                T_ZBEE_NWK_ADDR: ' '.join([self.addr, data]),\
            }
        pub_notification(self.reporter, data=report)

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyNode')

