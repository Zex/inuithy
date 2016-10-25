## Agent info definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.node import *

class AgentInfo:
    def __init__(self, agentid="", status=AgentStatus.OFFLINE, nodes=[]):
        self.agentid = agentid
        self.status = status
        self.nodes = []

    def rebuild_node(self, nodes):
        """Rebuild nodes from node infomation
        """
        for n in nodes:
            if n['type'] == NodeType.BLE.name:
                self.nodes.append(NodeBLE(addr=n['addr'])
            elif n['type'] == NodeType.Zigbee.name:
                self.nodes.append(NodeZigbee(addr=n['addr'])

    def has_node(self, addr):
        for node in self.nodes:
            if node.addr == addr: return node
        return Node

    def __str__(self):
        return string_write("agent<{}>: status:{} nodes:{}", self.agentid, self.status, self.nodes)
    
