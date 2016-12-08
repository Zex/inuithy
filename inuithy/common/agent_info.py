""" Agent info definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TYPE, AgentStatus, T_ADDR, to_string,\
NodeType, INUITHY_LOGCONFIG
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import SerialNode
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.protocol.ble_report import BleReport
from inuithy.protocol.zigbee_report import ZbeeReport
from inuithy.protocol.bzcombo_report import BzReport
import json
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE, BleProto, SerialNode, BleReport),\
    (NodeType.Zigbee, ZbeeProto, SerialNode, ZbeeReport),\
    (NodeType.BleZbee, BzProto, SerialNode, BzReport),\
]]

class AgentInfo(SupportedProto):
    """Agent information block"""
    def __init__(self, agentid="", host="", status=AgentStatus.OFFLINE, nodes=None, lgr=None):
        self.lgr = lgr is None and logging or lgr
        self.agentid = agentid
        self.status = status
        self.host = host
        self.nodes = []
        self.rebuild_node(nodes)

    def rebuild_node(self, nodes):
        """Rebuild nodes from node infomation
            [ntype.name] => (ntype, proto, node, report_hdr)
        """
#        self.lgr.debug(to_string("Rebuild node: {}", nodes))
        if nodes is None:
            return
        for n in nodes:
            try:
                n = json.loads(n)
#                self.lgr.debug(to_string("node: {}", n))
                proto = SupportedProto.protocols.get(n.get(T_TYPE))
                if proto is not None:
                    node = proto[2].create(ntype=proto[0], proto=proto[1], addr=n.get(T_ADDR))
                    if node is not None:
                        self.nodes.append(node)
                else:
                    self.lgr.error(to_string("Unsupported protocol"))
            except Exception as ex:
                    self.lgr.error(to_string("Exception on rebuilding node {}: {}", node, ex))

    def has_node(self, addr):
        for node in self.nodes:
            if node.addr == addr: return node
        return None

    def __str__(self):
        return to_string("agent<{}>: host:{} status:{} nodes:{} total_node:{}",\
            self.agentid, self.host, self.status, [str(n) for n in self.nodes], len(self.nodes))
    
if __name__ == '__main__':
    ai = AgentInfo('123', 'lkfjrj', nodes=[json.dumps({T_TYPE: 'Zigbee', T_ADDR: '1234', 'port': '/dev/ttyHello'})])
    print(ai)

    print(SupportedProto.protocols)
