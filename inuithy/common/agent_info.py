""" Agent info definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TYPE, AgentStatus, T_ADDR, _s,\
NodeType, _l
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import SerialNode
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.protocol.ble_report import BleReport
from inuithy.protocol.zigbee_report import ZbeeReport
from inuithy.protocol.bzcombo_report import BzReport
import json

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE, BleProto, SerialNode, BleReport),\
    (NodeType.Zigbee, ZbeeProto, SerialNode, ZbeeReport),\
    (NodeType.BleZbee, BzProto, SerialNode, BzReport),\
]]

class AgentInfo:#(SupportedProto):
    """Agent information block"""
    def __init__(self, agentid="", host="", status=AgentStatus.OFFLINE, nodes=None):
        self.agentid = agentid
        self.status = status
        self.host = host
        self.nodes = []
        self.rebuild_node(nodes)

    def rebuild_node(self, nodes):
        """Rebuild nodes from node infomation
            [ntype.name] => (ntype, proto, node, report_hdr)
        """
#        _l.debug(_s("Rebuild node: {}", nodes))
        if nodes is None:
            return
        for n in nodes:
            node = None
            try:
                n = json.loads(n)
#                _l.debug(_s("node: {}", n))
                proto = SupportedProto.protocols.get(n.get(T_TYPE))
                if proto is not None:
                    node = proto[2](ntype=proto[0], proto=proto[1], addr=n.get(T_ADDR))
                    if node is not None:
                        self.nodes.append(node)
                else:
                    _l.error(_s("Unsupported protocol"))
            except Exception as ex:
                    _l.error(_s("Exception on rebuilding node {}: {}", node, ex))

    def has_node(self, addr):
        for node in self.nodes:
            if node.addr == addr: return node
        return None

    def __str__(self):
        return _s("agent<{}>: host:{} status:{} nodes:{} total_node:{}",\
            self.agentid, self.host, self.status, [str(n) for n in self.nodes], len(self.nodes))
    
if __name__ == '__main__':
    ai = AgentInfo('123', 'lkfjrj', nodes=[json.dumps({T_TYPE: 'Zigbee', T_ADDR: '1234', 'path': '/dev/ttyHello'})])
    print(ai)

    print(SupportedProto.protocols)
