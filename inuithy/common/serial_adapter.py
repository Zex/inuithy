""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
to_string, T_EVERYONE, INUITHY_LOGCONFIG, T_MSG, NodeType
from inuithy.util.helper import clear_list
from inuithy.util.task_manager import ProcTaskManager
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import SerialNode
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
import glob, logging
import threading
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE, BleProto, SerialNode),
    (NodeType.Zigbee, ZbeeProto, SerialNode),
    (NodeType.BleZbee, BzProto, SerialNode),
]]

class SerialAdapter(SupportedProto):
    """Serial port adapter
    """
    @property
    def nodes(self):
        return self.__nodes
    @nodes.setter
    def nodes(self, val):
        pass

    resp_timeout = threading.Event()
    scan_done = threading.Event()

    def __init__(self, reporter=None, lgr=None):
        self.__nodes = []
        self.reporter = reporter
        SerialAdapter.lgr = lgr
        if SerialAdapter.lgr is None:
            SerialAdapter.lgr = logging

    @staticmethod
    def get_type(node):
        """Get firmware type via port"""
        for proto in SerialAdapter.protocols.values():
            """[ntype.name] => (ntype, proto, node, report_hdr)
            """
            try:
                req = proto[1].getfwver()
                node.write(req)
            except Exception as ex:
                SerialAdapter.lgr.error(to_string(
                "Exception on sending examine msg [{}]: {}", req, ex))
        return None

    def register(self, node, data):
        """Register node to adapter
            [ntype.name] => (ntype, proto, node, report_hdr)
        """
#        SerialAdapter.lgr.debug(to_string("Register node {}, {}", node.port, data))
        try:
            for proto in SerialAdapter.protocols.values():
                if proto[1].isme({T_MSG: data}):
#                    SerialAdapter.lgr.debug(to_string("Found protocol {}", proto[0]))
                    node.fwver = data
                    node.ntype = proto[0]
                    node.proto = proto[1]
                    node.reporter = self.reporter
#        node.lgr = SerialAdapter.lgr
#        if node is not None:
#            self.nodes.append(node)
            reg = [n for n in self.nodes if n.proto is not None]
            node.stop_listener()
            if len(reg) == len(self.nodes):
                SerialAdapter.scan_done.set()
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on register node"))

    def create_node(self, port):
        """Create node"""
#        SerialAdapter.lgr.debug(to_string("Creating node {}", port))
        if isinstance(port, tuple):
            port = port[1]
        if not isinstance(port, str) or port is None or len(port) == 0:
            return

        port = port.strip()
        node = None

        try:
            node = SerialNode.create(port=port, lgr=SerialAdapter.lgr, adapter=self)
            node.start_listener()
            SerialAdapter.get_type(node)
            self.nodes.append(node)
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on creating node: {}", ex))
        return node

    def scan_nodes(self, targets=DEV_TTYUSB.format(T_EVERYONE)):
        SerialAdapter.lgr.info(to_string("Scan for connected nodes {}", targets))
#        self.nodes.clear()
        clear_list(self.nodes)
        ports = enumerate(name for name in glob.glob(targets))
        [self.create_node(port) for port in ports]
#        mng = ProcTaskManager(SerialAdapter.lgr)
#        mng.create_task_foreach(self.create_node, ports)
#        mng.waitall()
#TODO
        SerialAdapter.scan_done.wait()
        SerialAdapter.scan_done.clear()
        SerialAdapter.lgr.info("Scanning finished")
        self.start_nodes()
    #TODO: epoll    
    def start_nodes(self):
        SerialAdapter.lgr.info("Start connected nodes")
        [n.start_listener() for n in self.nodes]

    def stop_nodes(self):
        SerialAdapter.lgr.info("Stop connected nodes")
        [n.stop_listener() for n in self.nodes]

if __name__ == '__main__':

    sad = SerialAdapter()
#    print(SerialAdapter.protocols)

    sad.scan_nodes(targets='/dev/ttyS1*')
    print([str(n) for n in sad.nodes])
    sad.stop_nodes()


