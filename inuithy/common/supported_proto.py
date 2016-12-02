""" Supported proto definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TYPE, AgentStatus, T_ADDR, to_string
from inuithy.common.node import NodeBLE, NodeZigbee, NodeBz, NodeType
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.protocol.ble_report import BleReport
from inuithy.protocol.zigbee_report import ZbeeReport
from inuithy.protocol.bzcombo_report import BzReport
import json

class SupportedProto(object):
    """Supported protocols"""
    protocols = {}

    @staticmethod
    def register(name, proto, node, report_hdr=None):
        """
        @name Name of NodeType value fore referencing to protocol
        Ex:
            - NodeType.BLE.name
            - NodeType.Zigbee.name
            - NodeType.BleZbee.name
        @proto Protocol class
        @node Node class
        @report_hdr Report handler
        """
        SupportedProto.protocols[name] = (proto, node, report_hdr)

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE.name, BleProto, NodeBLE, BleReport),\
    (NodeType.Zigbee.name, ZbeeProto, NodeZigbee, ZbeeReport),\
    (NodeType.BleZbee.name, BzProto, NodeBz, BzReport),\
]]

