""" Agent info definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TYPE, AgentStatus, T_ADDR, to_string
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import NodeBLE, NodeZigbee, NodeBz, NodeType
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.protocol.ble_report import BleReport
from inuithy.protocol.zigbee_report import ZbeeReport
from inuithy.protocol.bzcombo_report import BzReport
import json

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE.name, BleProto, NodeBLE, BleReport),\
    (NodeType.Zigbee.name, ZbeeProto, NodeZigbee, ZbeeReport),\
    (NodeType.BleZbee.name, BzProto, NodeBz, BzReport),\
]]

class AgentInfo(SupportedProto):
    """Agent information block"""
    def __init__(self, agentid="", host="", status=AgentStatus.OFFLINE, nodes=None):
        self.agentid = agentid
        self.status = status
        self.host = host
        self.nodes = []
        self.rebuild_node(nodes)

    def rebuild_node(self, nodes):
        """Rebuild nodes from node infomation
        """
        if nodes is None:
            return
        for n in nodes:
            node = None
            n = json.loads(n)
            proto = SupportedProto.protocols.get(T_TYPE)
            if proto is not None:
                node = proto[1].create(addr=n.get(T_ADDR))
            
            if node is not None:
                self.nodes.append(proto[1].create(addr=n.get(T_ADDR)))

    def has_node(self, addr):
        for node in self.nodes:
            if node.addr == addr: return node
        return None

    def __str__(self):
        return to_string("agent<{}>: host:{} status:{} nodes:{} total_node:{}",\
            self.agentid, self.host, self.status, [str(n) for n in self.nodes], len(self.nodes))
    
if __name__ == '__main__':
    ai = AgentInfo('123', 'lkfjrj', nodes=[json.dumps(6)])
    print(ai)

