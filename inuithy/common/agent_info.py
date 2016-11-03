""" Agent info definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TYPE, AgentStatus, T_ADDR, string_write
from inuithy.common.node import NodeBLE, NodeZigbee, NodeType
import json

class AgentInfo(object):
    def __init__(self, agentid ="", host ="", status =AgentStatus.OFFLINE, nodes =[]):
        self.agentid = agentid
        self.status = status
        self.host = host
        self.nodes = []
        self.rebuild_node(nodes)

    def rebuild_node(self, nodes):
        """Rebuild nodes from node infomation
        """
        for n in nodes:
            n = json.loads(n)
            if n[T_TYPE] == NodeType.BLE.name:
                self.nodes.append(NodeBLE(addr =n[T_ADDR]))
            elif n[T_TYPE] == NodeType.Zigbee.name:
                self.nodes.append(NodeZigbee(addr =n[T_ADDR]))
            else:
                pass

    def has_node(self, addr):
        for node in self.nodes:
            if node.addr == addr: return node
        return None

    def __str__(self):
        return string_write("agent<{}>: host:{} status:{} nodes:{} total_node:{}", self.agentid, self.host, self.status, [str(n) for n in self.nodes], len(self.nodes))
    
