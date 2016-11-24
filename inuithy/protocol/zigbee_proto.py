""" Zigbee protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import string_write, T_TIME, T_TYPE,\
MessageType, TrafficType, T_NODE, T_MSG_TYPE, T_TRAFFIC_TYPE,\
T_GENID, T_CHANNEL, T_PANID, T_SPANID, T_DEST, T_PKGSIZE, T_SRC
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
    JOIN = "join"
    WRITEATTRIBUTE2 = "writeAttribute2"
    GETNETWORKADDRESS = 'getNetworkAddress'
    GETUID = 'getUID'
    RESET_CONF = 'minimalDevice'
    DGN = 'Dgn'
    GETFWVER = "getFWName"

    ReqType = Enum('ReqType', [\
        'snd_req',\
    ])
    MsgType = Enum('MsgType', [\
        'snd',\
        'rcv',\
        'dgn',\
    ])

    @staticmethod
    def joinnw(params=None):
        """Join network command builder"""
        ch, ext_panid, panid, addr = \
            params.get(T_CHANNEL), params.get(T_PANID),\
            params.get(T_SPANID), params.get(T_NODE)
        msg = " ".join([PROTO.JOIN, str(ch), str(ext_panid), str(panid), str(addr), Protocol.EOL])
        return msg

    @staticmethod
    def writeattribute2(params=None):
        """Write attribute command builder"""
# msg = 'writeAttribute2 s '+str(destination)+
#    ' 20 0 4 0x42 "1" %s '%str(packet_size) + rsp +"\r"
# data = " ".join([BluetoothDevice.WRITEATTRIBUTE2, "s",
#   "0x%04X"%dest, "0x14 0x00 0x04 0x42", "1", "0x%02X"%psize, "0x%02X"%rsp, BluetoothDevice.EOL])
        dest, psize, rsp = params.get(T_DEST),\
            params.get(T_PKGSIZE), params.get(T_RSP)
        msg = " ".join([PROTO.WRITEATTRIBUTE2, "s", "0x"+dest,\
            "20 0 4 42", "1", str(psize), str(rsp), Protocol.EOL])
        return msg

    @staticmethod
    def getfwver(params=None):
        """Get firmware version command builder"""
        return " ".join([PROTO.GETFWVER, Protocol.EOL])

    @staticmethod
    def parse_rbuf(data, node):
        """Parse recieved data
        @data Serial command sent
        @node Node object
        @return Dict report for sending to controller
        """
        report = {}
        params = data.split(' ')

        # DEBUG data
        rand = random.randint(MessageType.RECV.value, MessageType.UNKNOWN.value)
        if node.joined is False:
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
                params = [PROTO.DGN]
                params.extend([str(random.randint(0, 2000)) for _ in range(21)])
        #------------end debug data--------------
        msg_type = params[0].upper()

        if msg_type == MessageType.SEND.name:
            if len(params) == 6:
                report = {\
                    T_TIME: time.time(),\
                    T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
                    T_NODE: node.addr,
                    T_MSG_TYPE: MessageType.RECV.name,
                    T_ZBEE_NWK_SRC: node.addr,\
                    T_ZBEE_NWK_DST: params[4],\
                    T_TYPE: PROTO.MsgType.snd.name,\
                    T_ZBEE_ZCL_CMD_TSN: params[1],\
                    T_STATUS: params[5],\
                    T_SND_SEQ_NR: node.sequence_nr,\
                }
                node.sequence_nr += 1
#                if status == '0x00':
#                    node.nr_messages_sent += 1
            else:
                PROTO.lgr.error(string_write('Incorrect send confirm: {}', data))
        elif msg_type == MessageType.RECV.name:
            report = {\
                T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
                T_MSG_TYPE: MessageType.RECV.name,
                T_NODE: node.addr,
                T_TYPE: PROTO.MsgType.rcv.name,\
                T_ZBEE_NWK_SRC: params[3],\
                T_ZBEE_NWK_DST: node.addr,\
                T_ZBEE_ZCL_CMD_TSN: params[1],\
            }
        elif msg_type == MessageType.JOINING.name:
            report = {\
                T_TRAFFIC_TYPE: TrafficType.JOIN.name,\
                T_MSG_TYPE: MessageType.RECV.name,\
                T_NODE: node.addr,\
            }
            #DEBUG data
            node.joined = True
        elif params[0] == 'Trying':
            return None
        elif params[0] == 'Network':
            return None
        elif params[0] == PROTO.GETUID:
            node.uid = params[1]
        elif params[0] == PROTO.GETNETWORKADDRESS:
            node.addr = data[-6:]
        elif params[0] == PROTO.RESET_CONF:
            return None
        elif params[0] == PROTO.DGN:
            report = {
                T_MSG_TYPE: MessageType.RECV.name,\
                T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
                T_NODE: node.addr,\
                T_TYPE: PROTO.MsgType.dgn.name,
                T_ZBEE_NWK_ADDR: node.addr,\
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
                T_MSG_TYPE: MessageType.RECV.name,\
                T_NODE: node.addr,\
                T_UNKNOWN_RESP: T_YES,\
                T_ZBEE_NWK_ADDR: ' '.join([node.addr, data]),\
            }

        report[T_GENID] = node.genid
        report[T_TIME] = time.time()
        return report

    @staticmethod
    def parse_wbuf(data, node, request):
        """Parse written buffer
        @data Serial command sent
        @node Node object
        @request Dict request information
        @return Dict report for sending to controller
        """
        if request.get(T_SRC) is None or request.get(T_DEST) is None:
            return None

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_MSG_TYPE: MessageType.SEND.name,
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,\
            T_NODE: node.addr,
            T_TYPE: PROTO.ReqType.snd_req.name,
            T_ZBEE_NWK_SRC: request.get(T_SRC),#node.addr,
            T_ZBEE_NWK_DST: request.get(T_DEST),
            T_ACK: request.get(T_RSP) == 1 and 'y' or 'n',
        }
        return report

PROTO = ZigbeeProtocol

