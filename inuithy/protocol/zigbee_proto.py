""" Zigbee protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import _s, T_TIME, T_TYPE, T_MSG, _l,\
MessageType, TrafficType, T_NODE, T_MSG_TYPE, T_TRAFFIC_TYPE,\
T_GENID, T_CHANNEL, T_PANID, T_SPANID, T_DEST, T_PKGSIZE, T_SRC, NodeType,\
T_DIAG, T_DESTS, T_DELAY, T_TIMEOUT, T_ENABLED
from inuithy.protocol.protocol import Protocol
from enum import Enum
import time
import random
import threading

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
T_SEQ_NR = 'seq_nr'
T_STATUS = 'status'
T_YES = 'yes'
T_NO = 'NO'
T_RSP = 'rsp'
T_ACK = 'ack'
T_CATEGORY0 = 'cat0'
T_CATEGORY1 = 'cat1'
T_CATEGORY2 = 'cat2'
T_COUNTER = 'counter'

def unify_addr(addr):
    if addr is None:
        return ''
    return addr.upper().strip('0X')

class _Lab(Protocol):
    """Zigbee lab version"""
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
    NWUPDATESTATUS = 'Network update status'

    @staticmethod
    def start(node):
        
        try:
            node.start()
            node.writable.set()
            node.uid = None

            while node.running and node.uid is None or len(node.uid) == 0:
                node._write(_Lab.getuid())
                _l.info(_s("{}: NODE UID", node))

#            while node.running and not node.joined:
#                node.write(_Lab.join(
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
#                node.write(_Lab.writeattribute2({ T_DEST: 'A002', T_PKGSIZE: '50', T_RSP: '1'})
#                    + _Lab.getdiag())

            while node.running and node.fwver is None or len(node.fwver) == 0:
                node._write(_Lab.getfwver())
                _l.info(_s("{}: FWVER", node))
#            node.stop()
        except Exception as ex:
            _l.error(_s("Start proto failed: {}", ex))
            return False
        return True

    @staticmethod
    def join(params=None):
        """Join command"""
        return _Lab.joinnw(params) 

    @staticmethod
    def traffic(params=None, node=None):
        """Traffic command"""
        if node is None:
            return 

        if params.get(T_DESTS) is None:
            _l.error("Invalid traffic parameters")
            return

        if T_DIAG in params.get(T_DESTS):
            try:
                msg = _Lab.getdiag(params)
                node.write(msg)
            except Exception as ex:
                _l.error(_s("Traffic failed in protocol: {}", ex))
        else:
            for dest in params.get(T_DESTS):
                try:
                    params[T_DEST] = dest
                    msg = _Lab.writeattribute2(params) 
                    node.write(msg, params)
                except Exception as ex:
                    _l.error(_s("Traffic failed in protocol: {}", ex))

    @staticmethod
    def joinnw(params=None):
        """Join network command builder"""
        ch, ext_panid, panid, addr = \
            params.get(T_CHANNEL), params.get(T_PANID),\
            params.get(T_SPANID), params.get(T_NODE)
        msg = " ".join([_Lab.JOIN, str(ch), '0x'+str(ext_panid), '0x'+str(panid), '0x'+str(addr)]) + _Lab.EOL
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
        msg = " ".join([_Lab.WRITEATTRIBUTE2, "s", "0x"+dest,\
            "20 0 4 42", "1", str(psize), str(rsp)]) + _Lab.EOL
        return msg

    @staticmethod
    def getdiag(params=None):
        """Get diag data"""
        return _Lab.GETDIAGDATA + _Lab.EOL

    @staticmethod
    def getfwver(params=None):
        """Get firmware version command builder"""
        return _Lab.GETFWVER + _Lab.EOL

    @staticmethod
    def getaddr(params=None):
        """Get network address"""
        return _Lab.GETSHORTADDRESS + _Lab.EOL

    @staticmethod
    def getuid(params=None):
        """Get node uid"""
        return _Lab.GETUID + _Lab.EOL

    @staticmethod
    def on_unknown_cmd(node, data, adapter=None):
        _l.debug(_s('{}: got unknown command', node))
        node.started = True
        node.writable.set()
        return

    @staticmethod
    def on_name(node, data, adapter=None):
        node.fwver = data
        node.proto = PROTO
        if adapter is not None:
            _l.debug(_s("Register to adapter"))
            if adapter.sender is not None:
                adapter.sender.send((node.dev.fileno(), node.addr, node.fwver, node.proto, data))
        else:
            _l.error(_s("Failed to register node to adapter: no adapter given"))
        node.started = True
        node.writable.set()
        return

    @staticmethod
    def on_send(node, params, adapter=None):
        """Send 0xc1 0x05 0xa001 0xa004 0x00"""
        report = {
            T_GENID: node.genid,
            T_NODE: unify_addr(node.addr),
            T_TIME: time.time(),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_TYPE: _Lab.MsgType.snd.name,
            T_ZBEE_ZCL_CMD_TSN: params[1],
            T_ZBEE_NWK_SRC: unify_addr(params[3]),
            T_ZBEE_NWK_DST: unify_addr(params[4]),
            T_STATUS: params[5],
            T_SEQ_NR: node.sequence_nr,
        }
        node.sequence_nr += 1
        node.writable.set()
        return report

    @staticmethod
    def on_recv(node, params, adapter=None):
        """Recv 0xc1 0x05 0xa001 0xa004"""
        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_TYPE: _Lab.MsgType.rcv.name,
            T_ZBEE_NWK_SRC: unify_addr(params[3]),
            T_ZBEE_NWK_DST: unify_addr(params[4]),
            T_ZBEE_ZCL_CMD_TSN: params[1],
        }
        return report

    @staticmethod
    def on_join(node, params, adapter=None):
        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.JOIN.name,
            T_MSG_TYPE: MessageType.RECV.name,
        }
        #DEBUG data
        node.joined = True
        node.writable.set()
        return report

    @staticmethod
    def on_getuid(node, params, adapter=None):
        node.uid = params[1]
        node.addr = node.uid[-4:]
        node.writable.set()
        return

    @staticmethod
    def on_resetconf(node, params, adapter=None):
        return None

    @staticmethod
    def on_dgn(node, params, adapter=None):
        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_MSG_TYPE: MessageType.RECV.name,
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_TYPE: _Lab.MsgType.dgn.name,
            T_ZBEE_NWK_ADDR: unify_addr(node.addr),
        }
        report.update(dict(zip(PROTO.DIAG_ITEM, params[1:])))
        node.writable.set()
        return report

    @staticmethod
    def parse_rbuf(data, node, adapter=None):
        """Parse recieved data
        @data Serial command sent
        @node Node object
        @return Dict report for sending to controller
        """
        if data is None or node is None:
            return

        _l.debug(_s('{}: {}', node, data))
        report = {}
        data = data.strip('\t \r\n')
       
        hdr = _Lab.preboot_route.get(data)
        if hdr is not None:
            return hdr(node, data, adapter)

        params = data.split(' ')
        msg_type = params[0].upper()

        hdr = _Lab.postboot_route.get(msg_type)
        if hdr is not None:
            return hdr(node, params, adapter)

        if _Lab.NWUPDATESTATUS in data:
            report.update({\
                T_TRAFFIC_TYPE: TrafficType.JOIN.name,\
                T_MSG_TYPE: MessageType.RECV.name,\
                T_MSG: data,\
                T_GENID: node.genid,\
                T_TIME: time.time(),\
                T_NODE: unify_addr(node.addr),\
            })
            node.joined = True
            node.writable.set()
            return report

        report.update({
            T_MSG_TYPE: MessageType.RECV.name,
            T_UNKNOWN_RESP: T_YES,
            T_ZBEE_NWK_ADDR: ' '.join([unify_addr(node.addr), data]),
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
            T_TYPE: _Lab.MsgType.snd_req.name,
            T_ZBEE_NWK_SRC: request.get(T_SRC),#node.addr,
            T_ZBEE_NWK_DST: request.get(T_DEST),
            T_ACK: request.get(T_RSP) and 'y' or 'n',
        }
        return report


class _Prod(Protocol):
    """Zigbee product version"""
    postboot_route = {}
    preboot_route = {}

    BRIDGE = 'Bridge'
    TH = 'TH'
    CONNECTION = 'Connection'
    SYS = 'SYS'
    LOG = 'Log'
    ZCL = 'Zcl'
    ZDP = 'Zdp'
    TRUSTCENTER = 'TrustCenter'
    # BRIDGE SUBMESSAGE
    GROUPRAGE = 'GroupRange'
    NETWORKSETTINGS = 'NetworkSettings'
    VERSION = 'Version'
    # CONNECTION SUBMESSAGE
    A = 'A'
    ASSOCIATE = 'Associate'
    ASSOCIATEDONE = 'AssociateDone'
    FINDFREEPAN = 'FindFreePan'
    FINDFREEPANDONE = 'FindFreePanDone'
    STARTCOOR = 'StartCoordinator'
    STARTCOORDONE = 'StartCoordinatorDone'
    # MISC MESSAGE
    INFO = 'Info'
    SYS = 'Error'
    # COMMANDS
    BCASTRETR = 'BroadcastRetransmission'
    DUMPINFO = 'DumpInfo'
    MCASTRETR = 'MulticastRetransmission'
    READY = 'Ready'
    ROUTEREQRETR = 'RouteRequestRetransmission'
    SETCHMASK = 'SetChannelMask'
    SETMACADDR = 'SetMacAddress'
    SETPASSACKTHR = 'SetPassiveAckThreshold'
    SETTXPOWER = 'SetTxPower'
    DGN = 'Dgn'
    RECVAPSUPDEV = 'Received_ApsUpdateDevice'
    ADDCLUSTSIMPDESC = 'AddClusterToSimpleDescriptor'
    IND = 'Ind'
    CONF = 'Conf'
    REQ = 'Req'
    REGCLUST = 'RegisterCluster'
    REGENDPOINT = 'RegisterEndpoint'
    JOINPERM = 'JoinPermitted'
    RECVDEVANNO = 'ReceivedDeviceAnnounce'
    SENDMGMTPERMJOIN = 'SendMgmtPermitJoiningReq'
    RESET_FACTORY = 'ResetToFactoryDefaults'
    EOL = '\r'
    END_POINT = '64'
    CLUSTER_ID = '64768'
    MFR_PHILIPS_HIGH = '10'
    MFR_PHILIPS_LOW = '0b'
    MFR_PHILIPS = '0x' + MFR_PHILIPS_HIGH + MFR_PHILIPS_LOW

    @staticmethod
    def __w(cmd):
        """Command payload wrapper"""
        return '[' + cmd + ']' + _Prod.EOL

    @staticmethod
    def start(node):
        
        try:
            node.start()
            node.writable.set()
            node.uid = None
###
            for _ in range(4): 
                if not node.running:
                    break
                _l.info(_s('getdiag ...'))
                node.write(_Prod.getdiag({ T_SEQ_NR: 1, T_COUNTER: 1}))
#            node.stop()
        except Exception as ex:
            _l.error(_s("Start proto failed: {}", ex))
            return False
        return True
    # TH subcommands
    @staticmethod
    def getdiag(params=None):
        """Get diag data"""
        seq, counter = params.get(T_SEQ_NR), params.get(T_COUNTER)
        return _Prod.__w(' '.join([_Prod.TH, _Prod.DGN, str(seq), str(counter)]))

    @staticmethod
    def resetfactory(params=None):
        delay = params.get(T_DELAY)
        if delay is None:
            delay = 0
        return _Prod.__w(' '.join([_Prod.TH, _Prod.RESET_FACTORY, str(delay)]))

    @staticmethod
    def setmacaddr(params=None):
        addr = params.get(T_ADDR)
        if addr is None:
            return ''
        return _Prod.__w(' '.join([_Prod.TH, _Prod.SETMACADDR, 'L=' + addr]))

    @staticmethod
    def setchmask(params=None):
        ch = params.get(T_CHANNEL)
        if ch is None:
            return ''
        return _Prod.__w(' '.join([_Prod.TH, _Prod.SETCHMASK, '0x%08x' % ch]))

    @staticmethod
    def reset(params=None):
        return _Prod.__w(' '.join([_Prod.TH, _Prod.RESET]))

    @staticmethod
    def settxpower(params=None):
        power = params.get(T_POWER)
        if power is None:
            return ''
        return _Prod.__w(' '.join([_Prod.TH, _Prod.SETTXPOWER, power]))

    @staticmethod
    def retransmission(params=None):
        enabled = params.get(T_ENABLED)
        if enabled is None:
            return ''
        return _Prod.__w(' '.join([_Prod.TH, _Prod.RETRANSMISSION, enabled]))

    @staticmethod
    def setpassackthr(params=None):
        thr = params.get(T_THRESHOLD)
        if thr is None:
            return ''
        return _Prod.__w(' '.join([_Prod.TH, _Prod.SETPASSACKTHR, thr]))

    # Connection subcommands
    @staticmethod
    def connassoc(params=None):
        return _Prod.__w(' '.join([_Prod.CONNECTION, _Prod.ASSOCIATE]))

    @staticmethod
    def findfreepan(params=None):
        return _Prod.__w(' '.join([_Prod.CONNECTION, _Prod.FINDFREEPAN]))

    @staticmethod
    def startcoor(params=None):
        spanid = param.get(T_SPANID)
        panid = param.get(T_PANID)
        return _Prod.__w(' '.join([_Prod.CONNECTION, _Prod.STARTCOOR, spanid, panid])) 

    # Zdp subcommands
    @staticmethod
    def sendmgmtpermjoin(params=None):
        seconds = params.get(T_TIMEOUT)
        return _Prod.__w(' '.join([_Prod.ZDP, _Prod.SENDMGMTPERMJOIN,
            'B=0xfffc', seconds, '0']))

    @staticmethod
    def regendpoint(params=None):
        return _Prod.__w(' '.join([_Prod.ZDP, _Prod.REGENDPOINT, _Prod.END_POINT, '260', '7', '0', '4', '2', '6']))
        
    # Zcl subcommands
    @staticmethod
    def regcluster(params=None):
        dire = params.get(T_DIRECTION)
        if dire is None:
            return ''
        return _Prod.__w(' '.join([_Prod.ZCL, _Prod.REGCLUST, _Prod.CLUSTER_ID, _Prod.MFR_PHILIPS, str(dire)]))

    @staticmethod
    def addclustsimpdesc(params=None):
        dire = params.get(T_DIRECTION)
        if dire is None:
            return ''
        return _Prod.__w(' '.join([_Prod.ZCL, _Prod.ADDCLUSTSIMPDESC, _Prod.END_POINT, str(dire), _Prod.CLUSTER_ID]))
        

    @staticmethod
    def unpack(data):
        if data is None or len(data) == 0:
            return None
        ret = data.strip('[]')
        return ret.split(',')
# TODO
    @staticmethod
    def join(params=None):
        return ""

    @staticmethod
    def traffic(params=None):
        return ""

    @staticmethod
    def on_log(node, items, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.writable.set()
        return report

    @staticmethod
    def on_sys(node, items, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.started = True
        node.writable.set()
        return report

    @staticmethod
    def on_th(node, data, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.writable.set()
        return report

    @staticmethod
    def on_connection(node, data, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.writable.set()
        return report

    @staticmethod
    def on_bridge_version(node, data, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.fwver = items[2]
        print("FWVER", node.fwver)
        node.writable.set()
        return report

    @staticmethod
    def on_trustcenter(node, data, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.writable.set()
        return report

    @staticmethod
    def on_zcl(node, data, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.writable.set()
        return report

    @staticmethod
    def on_zdp(node, data, adapter=None):

        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_NODE: unify_addr(node.addr),
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_MSG_TYPE: MessageType.RECV.name,
            T_CATEGORY0: items[0],
            T_CATEGORY1: items[1],
            T_MSG: items,
        }
        node.writable.set()
        return report

    @staticmethod
    def parse_rbuf(data, node, adapter=None):
        """Parse recieved data
        @data Serial command sent
        @node Node object
        @return Dict report for sending to controller
        """
        if data is None or node is None:
            return

        _l.debug(_s('{}: {}', node, data))
        report = {}
        data = data.strip('\t \r\n')
        
        items = _Prod.unpack(data)
        if items is None or len(items) < 2:
            return

        hdr = _Prod.preboot_route.get(items[0])
        if hdr is not None:
            return hdr(node, data, adapter)

        hdr = _Prod.postboot_route.get(items[0])
        if hdr is not None:
            return hdr(node, params, adapter)

#        report.update({
#            T_MSG_TYPE: MessageType.RECV.name,
#            T_UNKNOWN_RESP: T_YES,
#            T_ZBEE_NWK_ADDR: ' '.join([unify_addr(node.addr), data]),
#        })

        return report

    @staticmethod
    def parse_wbuf(data, node, request):
        if request is None or request.get(T_SRC) is None or request.get(T_DEST) is None:
            return None
        report = {
            T_GENID: node.genid,
            T_TIME: time.time(),
            T_MSG_TYPE: MessageType.SEND.name,
            T_TRAFFIC_TYPE: request.get(T_TRAFFIC_TYPE),
            T_NODE: node.addr,
            T_TYPE: _Lab.MsgType.snd_req.name,
            T_ZBEE_NWK_SRC: request.get(T_SRC),
            T_ZBEE_NWK_DST: request.get(T_DEST),
            T_ACK: request.get(T_RSP) and 'y' or 'n',
        }
        return report

class ZigbeeProtocol(Protocol):
    """Protocol for communication with Zigbee firmware"""
    subproto = None
    postboot_route = {}
    preboot_route = {}

    HANDSHAKE_REQ = '\xB2\xA5\x65\x4B'
    HANDSHAKE_RSP = '\x69\xD3\xD2\x26'
    ACK = '\x4D\x5A\x9A\xB4'
    NACK = '\x2D\x59\x5A\xB2'
    POST_HANDSHAKE = 'S9030000FC'
    UNKNOWN_CMD = 'unknown command'
    HELLO = '[hello]'
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
    def check_subproto(node, rdbuf):
        if rdbuf.startswith('['):
            while True:
                buf = node._read_one(1)
                rdbuf += buf
                if rdbuf.endswith(']'):
                    buf = node._read_one(2)
                    break
        return rdbuf

    @staticmethod
    def examine_subproto(node, data):
        if data.startswith('['):
            PROTO.subproto = _Prod
        else:
            PROTO.subproto = _Lab
        _l.debug(_s("Using sub-protocol {}", PROTO.subproto))
        node.started = True

    @staticmethod
    def handshake(node):
        
        try:
            node.proto = PROTO
            retry = 4
            while not node.started and node.running and retry > 0:
                _l.info(_s("{}: [{}] Handshaking", node, retry))
                retry -= 1
    
                node._write((PROTO.HELLO + PROTO.EOL).encode())
#                rdbuf = node._read_one(len(PROTO.UNKNOWN_CMD))
                rdbuf = node._read_one(in_wait=True)
                rdbuf = PROTO.check_subproto(node, rdbuf) 
                node.proto.parse_rbuf(rdbuf, node)
                if node.started:
                     break
                node._write(PROTO.HANDSHAKE_REQ)
                rdbuf = node._read_one(len(PROTO.HANDSHAKE_RSP))
                rdbuf = PROTO.check_subproto(node, rdbuf) 
                node.proto.parse_rbuf(rdbuf, node)
                if node.started:
                     break
                node._write(PROTO.POST_HANDSHAKE)
#                rdbuf = node._read_one(in_wait=True)
                rdbuf = node._read_one(len(PROTO.HANDSHAKE_RSP))
                rdbuf = PROTO.check_subproto(node, rdbuf) 
                node.proto.parse_rbuf(rdbuf, node)
            if retry <= 0 and not node.started:
                node.proto = None
                return False
        except Exception as ex:
            _l.error(_s("Handshake failed: {}", ex))
            return False
        return True
    
    @staticmethod
    def prepare(node):

        if not PROTO.handshake(node):
            node.proto = None
            return False
        return True

    @staticmethod
    def start(node):
        
        if PROTO.subproto:
            return PROTO.subproto.start(node)

    @staticmethod
    def isme(params=None):
        """Message replied to `getfwver` to identify protocol"""
        msg = params.get(T_MSG)
        if msg == _Lab.NAME or msg == _Prod.NAME:
            return True
        return False

    @staticmethod
    def on_handshake_rsp(node, data, adapter=None):
        _l.debug(_s('{}: got handshake response', node))
#        node._write(PROTO.POST_HANDSHAKE)
        return

    @staticmethod
    def on_ack(node, data, adapter=None):
        _l.debug(_s('{}: got ack', node))
        rdbuf = node._read_one()
        _l.debug(_s('{}: post ack', rdbuf))
        PROTO.examine_subproto(node, data)
        return

    @staticmethod
    def parse_rbuf(data, node, adapter=None):

#        if PROTO.subproto:
        if data is None or len(data) == 0:
            return 
        
        if node.started:
            return PROTO.subproto.parse_rbuf(data, node, adapter)
        else:
            _l.debug(str([_s("{}", x) for x in data]))
            if data.startswith('['):
                PROTO.examine_subproto(node, data)
                if node.started:
                    return PROTO.subproto.parse_rbuf(data, node, adapter)
            hdr = PROTO.preboot_route.get(data)
            if hdr is not None:
                return hdr(node, data, adapter)

    @staticmethod
    def parse_wbuf(data, node, request):

        if PROTO.subproto:
            _l.debug(_s("Using sub-protocol {}", PROTO.subproto))
            return PROTO.subproto.parse_wbuf(data, node, request)

PROTO = ZigbeeProtocol

PROTO.preboot_route = {
    PROTO.HANDSHAKE_RSP: PROTO.on_handshake_rsp,
    PROTO.ACK: PROTO.on_ack,
}

_Lab.preboot_route = {
#    PROTO.UNKNOWN_CMD: _Lab.on_unknown_cmd,
}

_Lab.postboot_route = {
    MessageType.SEND.name: _Lab.on_send,
    MessageType.RECV.name: _Lab.on_recv,
    MessageType.JOINING.name: _Lab.on_join,
    _Lab.DGN.upper(): _Lab.on_dgn,
    _Lab.GETUID.upper(): _Lab.on_getuid,
    _Lab.RESET_CONF.upper(): _Lab.on_resetconf,
    _Lab.NAME: _Lab.on_name,
    PROTO.UNKNOWN_CMD: _Lab.on_unknown_cmd,
}

_Prod.preboot_route = {
#   _Prod.NAME: _Prod.on_name,
}

_Prod.postboot_route = {
    _Prod.LOG: _Prod.on_log,
    _Prod.SYS: _Prod.on_sys,
    _Prod.CONNECTION: _Prod.on_connection,
    _Prod.BRIDGE: _Prod.on_bridge_version,
    _Prod.TH: _Prod.on_th,
    _Prod.ZCL: _Prod.on_zcl,
    _Prod.ZDP: _Prod.on_zdp,
    _Prod.TRUSTCENTER: _Prod.on_trustcenter,
}



