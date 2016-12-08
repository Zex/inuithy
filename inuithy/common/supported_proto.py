""" Supported proto definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
#from inuithy.common.predef import T_TYPE, AgentStatus, T_ADDR, to_string
#from inuithy.protocol.ble_proto import BleProtocol as BleProto
#from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
#from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
#from inuithy.protocol.ble_report import BleReport
#from inuithy.protocol.zigbee_report import ZbeeReport
#from inuithy.protocol.bzcombo_report import BzReport

class SupportedProto(object):
    """Supported protocols"""
    protocols = {}

    @staticmethod
    def register(ntype, proto, node=None, report_hdr=None):
        """
        @ntype Name of NodeType value fore referencing to protocol
        Ex:
            - NodeType.BLE
            - NodeType.Zigbee
            - NodeType.BleZbee
        @proto Protocol class
        @node Node class
        @report_hdr Report handler
        """
        SupportedProto.protocols[ntype.name] = (ntype, proto, node, report_hdr)

#[SupportedProto.register(*proto) for proto in [
#    (NodeType.BLE.name, BleProto, NodeBLE, BleReport),\
#    (NodeType.Zigbee.name, ZbeeProto, NodeZigbee, ZbeeReport),\
#    (NodeType.BleZbee.name, BzProto, NodeBz, BzReport),\
#]]
