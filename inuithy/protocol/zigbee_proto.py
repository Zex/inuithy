""" Zigbee protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import to_string, T_TIME, T_TYPE, T_MSG,\
MessageType, TrafficType, T_NODE, T_MSG_TYPE, T_TRAFFIC_TYPE,\
T_GENID, T_CHANNEL, T_PANID, T_SPANID, T_DEST, T_PKGSIZE, T_SRC, NodeType
from inuithy.protocol.protocol import Protocol
from enum import Enum
import time
import random

T_ZBEE_NWK_SRC = 'zbee_nwk_src'
T_ZBEE_NWK_DST = 'zbee_nwk_dst'
T_ZBEE_NWK_ADDR = 'zbee_nwk_addr'
T_ZBEE_ZCL_CMD_TSN = 'zbee_zcl_cmd_tsn'
T_UNKNOWN_RESP = 'unknown_resp'
T_AVGMACRETRY = 'averageMACRetryPerAPSMessageSent'
T_LASTMSGLQI = 'lastMessageLQI'
T_LASTMSGRSSI = 'lastMessageRSSI'
T_PKGBUFALLOCFAIL = 'packetBufferAllocateFailure'
T_RTDISCINIT = 'routeDiscInitiated'
T_APSRXBCAST = 'apsRxBcast'
T_APSTXBCAST = 'apsTxBcast'
T_APSTXUCASTRETRY = 'apsTxUcastRetry'
T_RELAYEDUCAST = 'relayedUcast'
T_APSRXUCAST = 'apsRxUcast'
T_NEIGHBORADDED = 'neighborAdded'
T_NEIGHBORRMED = 'neighborRemoved'
T_NEIGHBORSTALE = 'neighborStale'
T_MACRXUCAST = 'macRxUcast'
T_MACTXUCAST = 'macTxUcast'
T_MACTXUCASTFAIL = 'macTxUcastFail'
T_MACTXUCASTRETRY = 'macTxUcastRetry'
T_MACRXBCAST = 'macRxBcast'
T_MACTXBCAST = 'macTxBcast'
T_APSTXUCASTSUCCESS = 'apsTxUcastSuccess'
T_APSTXUCASTFAIL = 'apsTxUcastFail'
T_SND_SEQ_NR = 'snd_seq_nr'
T_STATUS = 'status'
T_YES = 'yes'
T_NO = 'NO'
T_RSP = 'rsp'
T_ACK = 'ack'

class ZigbeeProtocol(Protocol):
    """Protocol for communication with Zigbee firmware"""
    NAME = 'minimalDevice'
    JOIN = "join"
    WRITEATTRIBUTE2 = "writeAttribute2"
    GETNETWORKADDRESS = 'getNetworkAddress'
    GETSHORTADDRESS = "getShortAddress"
    GETUID = 'getUID'
    GETDIAGDATA = 'getDiagnosticsData'
    RESET_CONF = 'minimalDevice'
    DGN = 'Dgn'
    GETFWVER = "getFWName"
    HANDSHAKE_REQ = '\xB2\xA5\x65\x4B'
    HANDSHAKE_RSP = '\x69\xD3\xD2\x26'
    ACK = '\x4D\x5A\x9A\xB4'
    NACK = '\x2D\x59\x5A\xB2'
    POST_HANDSHAKE = 'S9030000FC'
    UNKNOWN_CMD = 'unknown command'
    NWUPDATESTATUS = 'Network update status'
    HELLO = 'hello'
    DIAG_ITEM = [
        T_AVGMACRETRY, T_LASTMSGLQI, T_LASTMSGRSSI, T_PKGBUFALLOCFAIL, T_RTDISCINIT,
        T_APSRXBCAST,  T_APSTXBCAST, T_APSTXUCASTRETRY, T_RELAYEDUCAST, T_APSRXUCAST,
        T_NEIGHBORADDED, T_NEIGHBORRMED, T_NEIGHBORSTALE, T_MACRXUCAST, T_MACTXUCAST,
        T_MACTXUCASTFAIL, T_MACTXUCASTRETRY, T_MACRXBCAST, T_MACTXBCAST, T_APSTXUCASTSUCCESS,
        T_APSTXUCASTFAIL
    ]

    MsgType = Enum('MsgType', [\
        'snd',\
        'rcv',\
        'dgn',\
        'snd_req',\
    ])

    @staticmethod
    def start(node):
        
        try:
            node.proto = PROTO
            while not node.started and node.running:
                PROTO.lgr.info(to_string("{}: Handshaking", node))
    
                node._write((PROTO.HELLO + PROTO.EOL).encode())
                rdbuf = node._read_one(len(PROTO.UNKNOWN_CMD))
                node.proto.parse_rbuf(rdbuf, node)
    
                node._write(PROTO.HANDSHAKE_REQ)
                rdbuf = node._read_one(len(PROTO.HANDSHAKE_RSP))
                node.proto.parse_rbuf(rdbuf, node)
    
                node._write(PROTO.POST_HANDSHAKE)
    
                rdbuf = node._read_one(in_wait=True)
                node.proto.parse_rbuf(rdbuf, node)
    
            node.start()
            node.writable.set()
            node.uid = None

            while node.running and node.uid is None or len(node.uid) == 0:
                node.write(PROTO.getuid())
                PROTO.lgr.info(to_string("{}: NODE UID", node))

#            while node.running and not node.joined:
#                node.write(PROTO.join(
#                    {
#                    T_CHANNEL: '17', T_PANID: '4321432143214321',
#                    T_SPANID: '4321', T_NODE: node.uid[-4:],
#                    }))
#
#            for _ in range(4): 
#                if not node.running:
#                    break
#                if node.addr == 'A002':
#                    break
#                node.write(PROTO.writeattribute2({ T_DEST: 'A002', T_PKGSIZE: '50', T_RSP: '1'})
#                    + PROTO.getdiag())

            while node.running and node.fwver is None or len(node.fwver) == 0:
                node.write(PROTO.getfwver())
                PROTO.lgr.info(to_string("{}: FWVER", node))

        except Exception as ex:
            PROTO.lgr.error(to_string("Start proto failed: {}", ex))
            return False
        return True

    @staticmethod
    def join(params=None):
        """Join command"""
        return PROTO.joinnw(params) 

    @staticmethod
    def traffic(params=None, node=None):
        """Traffic command"""
        if node is None:
            msg = PROTO.writeattribute2(params) 
            msg += PROTO.getdiag(params)

            return msg
        else:
            msg = PROTO.writeattribute2(params) 
            node.write(msg, params)

            node.in_traffic = False
            msg = PROTO.getdiag(params)
            node.write(msg, params)
            node.in_traffic = True

    @staticmethod
    def joinnw(params=None):
        """Join network command builder"""
        ch, ext_panid, panid, addr = \
            params.get(T_CHANNEL), params.get(T_PANID),\
            params.get(T_SPANID), params.get(T_NODE)
        msg = " ".join([PROTO.JOIN, str(ch), '0x'+str(ext_panid), '0x'+str(panid), '0x'+str(addr)]) + Protocol.EOL
        return msg

    @staticmethod
    def writeattribute2(params=None):
        """Write attribute command builder"""
# msg = 'writeAttribute2 s '+str(destination)+
#    ' 20 0 4 0x42 "1" %s '%str(packet_size) + rsp +"\r"
# data = " ".join([BluetoothDevice.WRITEATTRIBUTE2, "s",
#   "0x%04X"%dest, "0x14 0x00 0x04 0x42", "1", "0x%02X"%psize, "0x%02X"%rsp, BluetoothDevice.EOL])
        dest, psize, rsp = params.get(T_DEST),\
            params.get(T_PKGSIZE), params.get(T_RSP) is None and '0' or '1'
        msg = " ".join([PROTO.WRITEATTRIBUTE2, "s", "0x"+dest,\
            "20 0 4 42", "1", str(psize), str(rsp)]) + Protocol.EOL
        return msg

    @staticmethod
    def getdiag(params=None):
        """Get diag data"""
        return PROTO.GETDIAGDATA + Protocol.EOL

    @staticmethod
    def getfwver(params=None):
        """Get firmware version command builder"""
        return PROTO.GETFWVER + Protocol.EOL

    @staticmethod
    def getaddr(params=None):
        """Get network address"""
        return PROTO.GETSHORTADDRESS + Protocol.EOL

    @staticmethod
    def getuid(params=None):
        """Get node uid"""
        return PROTO.GETUID + Protocol.EOL

    @staticmethod
    def isme(params=None):
        """Message replied to `getfwver` to identify protocol"""
        #TODO
        msg = params.get(T_MSG)
        return msg == PROTO.NAME

    @staticmethod
    def parse_rbuf(data, node, adapter=None):
        """Parse recieved data
        @data Serial command sent
        @node Node object
        @return Dict report for sending to controller
        """
        if data is None or node is None:
            return

#        PROTO.lgr.debug(to_string('{}: {}', node, data))
        report = {}
        data = data.strip('\t \r\n')
       
        # DEBUG data
#        rand = random.randint(MessageType.RECV.value, MessageType.UNKNOWN.value)
#        if node.joined is False:
#            params = []
#            params.append(MessageType.JOINING.name)
#        else:
#            if rand == MessageType.RECV.value:
#                params = []
#                params.append(MessageType.RECV.name)
#                params.append(str(random.randint(0, 10)))
#                params.append(str(random.randint(0, 10)))
#                params.append(str(random.randint(1100, 1144)))
#            elif rand == MessageType.SEND.value:
#                params = []
#                params.append(MessageType.SEND.name)
#                params.append(str(random.randint(0, 10)))
#                params.append(str(random.randint(0, 10)))
#                params.append(str(random.randint(0, 10)))
#                params.append(str(random.randint(1100, 1144)))
#                params.append(str(random.randint(10, 100)))
#            else:
#                params = [PROTO.DGN]
#                params.extend([str(random.randint(0, 2000)) for _ in range(21)])
        #------------end debug data--------------

        if data == PROTO.HANDSHAKE_RSP:
            PROTO.lgr.debug(to_string('{}: got handshake response', node))
            node._write(PROTO.POST_HANDSHAKE)
            return

        if data == PROTO.ACK:
            PROTO.lgr.debug(to_string('{}: got ack', node))
            rdbuf = node._read_one()
            PROTO.lgr.debug(to_string('{}: post ack', rdbuf))
            node.started = True
            return

        if data == PROTO.UNKNOWN_CMD:
            PROTO.lgr.debug(to_string('{}: got unknown command', node))
            node.started = True
            return

        if data == PROTO.NAME:
            node.fwver = data
            node.proto = PROTO
            if adapter is not None:
                PROTO.lgr.debug(to_string("Register to adapter"))
                adapter.register(node, data)
            else:
                PROTO.lgr.error(to_string("Failed to register node to adapter: no adapter given"))
            node.started = True
            node.writable.set()
            return

        report[T_GENID] = node.genid
        report[T_TIME] = time.time()
        report[T_NODE] = node.addr

        if PROTO.NWUPDATESTATUS in data:
            report.update({\
                T_TRAFFIC_TYPE: TrafficType.JOIN.name,\
                T_MSG_TYPE: MessageType.RECV.name,\
                T_MSG: data,\
            })
            node.joined = True
            return report

        params = data.split(' ')
        msg_type = params[0].upper()

        if msg_type == MessageType.SEND.name:
            if len(params) == 6:
                report.update({
                    T_TIME: time.time(),
                    T_TRAFFIC_TYPE: TrafficType.SCMD.name,
                    T_MSG_TYPE: MessageType.RECV.name,
                    T_TYPE: PROTO.MsgType.snd.name,
                    T_ZBEE_NWK_SRC: node.addr,
                    T_ZBEE_NWK_DST: params[4],
                    T_ZBEE_ZCL_CMD_TSN: params[1],
                    T_STATUS: params[5],
                    T_SND_SEQ_NR: node.sequence_nr,
                })
                node.sequence_nr += 1
#                if status == '0x00':
#                    node.nr_messages_sent += 1
            else:
                PROTO.lgr.error(to_string('Incorrect send confirm: {}', data))
            node.writable.set()
        elif msg_type == MessageType.RECV.name:
            report.update({
                T_TRAFFIC_TYPE: TrafficType.SCMD.name,
                T_MSG_TYPE: MessageType.RECV.name,
                T_TYPE: PROTO.MsgType.rcv.name,
                T_ZBEE_NWK_SRC: params[3],
                T_ZBEE_NWK_DST: node.addr,
                T_ZBEE_ZCL_CMD_TSN: params[1],
            })
            node.writable.set()
        elif msg_type == MessageType.JOINING.name:
            report = {
                T_TRAFFIC_TYPE: TrafficType.JOIN.name,
                T_MSG_TYPE: MessageType.RECV.name,
            }
            #DEBUG data
            node.joined = True
            node.writable.set()
        elif params[0] == 'Trying':
            return None
        elif params[0] == 'Network':
            return None
        elif params[0] == PROTO.GETUID:
            node.uid = params[1]
            node.addr = node.uid[-4:]
            node.writable.set()
        elif params[0] == PROTO.GETNETWORKADDRESS:
            node.addr = data[-6:]
        elif params[0] == PROTO.RESET_CONF:
            return None
        elif params[0] == PROTO.DGN:
            report.update({
                T_MSG_TYPE: MessageType.RECV.name,
                T_TRAFFIC_TYPE: TrafficType.SCMD.name,
                T_TYPE: PROTO.MsgType.dgn.name,
                T_ZBEE_NWK_ADDR: node.addr,
            })
            report.update(dict(zip(PROTO.DIAG_ITEM, params[1:])))
            node.writable.set()
        else:
            report.update({
                T_MSG_TYPE: MessageType.RECV.name,
                T_UNKNOWN_RESP: T_YES,
                T_ZBEE_NWK_ADDR: ' '.join([node.addr, data]),
            })
  
        return report

    @staticmethod
    def parse_wbuf(data, node, request):
        """Parse written buffer
        @data Serial command sent
        @node Node object
        @request Dict request information
        @return Dict report for sending to controller
        """
        if request is None or request.get(T_SRC) is None or request.get(T_DEST) is None:
            return None

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_MSG_TYPE: MessageType.SEND.name,
            T_TRAFFIC_TYPE: request.get(T_TRAFFIC_TYPE),#TrafficType.SCMD.name,
            T_NODE: node.addr,
            T_TYPE: PROTO.MsgType.snd_req.name,
            T_ZBEE_NWK_SRC: request.get(T_SRC),#node.addr,
            T_ZBEE_NWK_DST: request.get(T_DEST),
            T_ACK: request.get(T_RSP) and 'y' or 'n',
        }
        return report

PROTO = ZigbeeProtocol

