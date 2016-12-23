""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
import sys
sys.path.append('/opt/inuithy')
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
to_string, T_EVERYONE, INUITHY_LOGCONFIG, T_MSG, NodeType, DEV_TTYACM
from inuithy.util.helper import clear_list
from inuithy.util.task_manager import ProcTaskManager
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import SerialNode, RawNode, RAWNODE_BASE, RawNodeSvr
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.util.worker import Worker
import multiprocessing as mp
import glob, logging
import threading
import select
import socket
import logging.config as lconf
from random import randint

lconf.fileConfig(INUITHY_LOGCONFIG)

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE, BleProto, SerialNode),
    (NodeType.Zigbee, ZbeeProto, SerialNode),
    (NodeType.BleZbee, BzProto, SerialNode),
]]

#shared_manager = mp.Manager()

class NodeAdapter(object):
    """Serial port adapter
    """
    @property
    def nodes(self):
        return self.__nodes
    @nodes.setter
    def nodes(self, val):
        pass

    _mutex = threading.Lock()

    _initialized = False

    def __init__(self, reporter=None, lgr=None):
        self.__nodes = {}
        self.reporter = reporter
        NodeAdapter.lgr = lgr is None and logging or lgr
        self.run_listener = False
        self.worker = Worker(1, NodeAdapter.lgr)
        with NodeAdapter._mutex:
            NodeAdapter._initialized = True
        self.scan_done = threading.Event()
#        self.shared_nodes = shared_manager.Queue()

    def start_nodes(self):
        NodeAdapter.lgr.info("Start connected nodes")
        [n.start() for n in self.nodes.values()]

    def stop_nodes(self):
        NodeAdapter.lgr.info("Stop connected nodes")
        [n.stop() for n in self.nodes.values()]

    def teardown(self):
        NodeAdapter.lgr.info("Serial adapter teardown")
        with NodeAdapter._mutex:
            if not NodeAdapter._initialized:
                return
        with NodeAdapter._mutex:
            NodeAdapter._initialized = False
#        if not self.scan_done.isSet():
        self.scan_done.set()
        self.stop_nodes()
        self.worker.stop()
        [node.close() for node in self.nodes.values()]

    def register(self, node, data):
        """Register node with details to self
            [ntype.name] => (ntype, proto, node, report_hdr)
           callback for nodes
        """
        NodeAdapter.lgr.info(to_string("Register node {}, {}", node.path, data))
        if node.fwver is None or len(node.fwver) == 0:
            NodeAdapter.lgr.error(to_string("Unknown node {}", node.path))
            return
        try:
    #        if node.proto is None:
             for proto in SupportedProto.protocols.values():
                if proto[1] == node.proto:
                    node.ntype = proto[0]
                    break
             if len(self.expected_paths) != len(self.nodes):
                NodeAdapter.lgr.info(to_string("Register node {}/{}", len(self.nodes), len(self.expected_paths)))
                return
             with_proto = [n for n in self.nodes.values() if n.ntype is not None]
             if len(with_proto) == len(self.nodes):
                self.scan_done.set()
        except Exception as ex:
            NodeAdapter.lgr.error(to_string("Exception on register node: {}", ex))

def yield_proto():
    for proto in SupportedProto.protocols.values():
        yield proto

def get_type(node):
    """Get firmware type via port
      [ntype.name] => (ntype, proto, node, report_hdr)
    """
    if node is not None:
        try:
            proto = next(node.try_proto)
            NodeAdapter.lgr.info(to_string("Examine {}", proto))
            if proto[1].prepare(node) is False:
                get_type(node)
                return
            if proto[1].start(node) is False:
                get_type(node)
        except StopIteration:
            NodeAdapter.lgr.info(to_string("All proto tried"))
        except Exception as ex:
            NodeAdapter.lgr.error(to_string(
            "Exception on examine node[{}]: {}", node, ex))

def add_node(adapter, node):
    """Add node to fileno-node map"""
    try:
        if node is not None:
            adapter.nodes[node.dev.fileno()] = node
            node.try_proto = yield_proto()
            get_type(node)
        else:
            NodeAdapter.lgr.error(to_string("Invalid node"))
    except Exception as ex:
        NodeAdapter.lgr.error(to_string("Exception on adding node: {}", ex))

def create_node(adapter, path, nodes=None):
    """Create node"""
    NodeAdapter.lgr.debug(to_string("Creating node {}", path))
    if not NodeAdapter._initialized:
        return

    path = path.strip()
    node = None

    try:
        node = SerialNode(path=path, lgr=NodeAdapter.lgr, adapter=adapter, reporter=adapter.reporter)
#       node = RawNode(path=RAWNODE_BASE+path, lgr=NodeAdapter.lgr, adapter=adapter.
#        if nodes is not None:
#            nodes.put(node)
#        else:
        add_node(adapter, node)
    except KeyboardInterrupt:
        NodeAdapter.lgr.error(to_string("Received keyboard interrupt"))
    except Exception as ex:
        NodeAdapter.lgr.error(to_string("Exception on creating node: {}", ex))
    return node


def scan_nodes(adapter, targets=None):
    NodeAdapter.lgr.info(to_string("Scan for connected nodes {}", targets))
    clear_list(adapter.nodes)
    if targets is not None and not isinstance(targets, list):
        NodeAdapter.lgr.error(to_string("Expecting a list for targets"))
        return
    if targets is None or len(targets) == 0:
        targets = [to_string(DEV_TTYUSB, T_EVERYONE), to_string(DEV_TTYACM, T_EVERYONE)]
    paths = []
    [paths.extend(glob.glob(target)) for target in targets]

    adapter.worker.start()
#   [adapter.create_node(path) for path in paths]
#   [adapter.worker.add_job(adapter.get_type, node) for node in adapter.nodes.values()]
    adapter.expected_paths = paths
    pool = ProcTaskManager(NodeAdapter.lgr)#, start_on_create=False)
    NodeAdapter.lgr.info("Scanning preparing")
    [pool.create_task(create_node, adapter, path) for path in paths]
#    pool.start()
    NodeAdapter.lgr.info("Scanning started")
    pool.waitall()

    adapter.scan_done.wait()
    adapter.scan_done.clear()
    NodeAdapter.lgr.info("Scanning finished")
#    adapter.start_nodes()

if __name__ == '__main__':

    adapter = NodeAdapter()
    try:
#       NodeAdapter.lgr.debug(NodeAdapter.protocols)
        scan_nodes(adapter, targets=['/dev/ttyUSB*'])
        NodeAdapter.lgr.debug([str(fd)+str(n) for fd, n in adapter.nodes.items()])
        NodeAdapter.lgr.debug(len(adapter.nodes))
    except KeyboardInterrupt:
        NodeAdapter.lgr.error(to_string("Received keyboard interrupt"))
    except Exception as ex:
        NodeAdapter.lgr.error(to_string("Exception: {}", ex))
        raise
    finally:
        adapter.teardown()


