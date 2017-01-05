""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
import sys
import os

if os.uname()[-1] == 'armv7l':
    sys.path.insert(0, '/usr/lib/python2.7/site-packages')
    sys.path.append('/opt/inuithy')

from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
_s, _l, T_EVERYONE, T_MSG, NodeType, DEV_TTYACM
from inuithy.util.helper import clear_list
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import SerialNode, RawNode, RAWNODE_BASE, RawNodeSvr
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.util.worker import Worker
from inuithy.util.task_manager import ProcTaskManager
import multiprocessing as mp
import glob
import threading
import select
import socket
from random import randint

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

    def __init__(self, reporter=None):
        self.__nodes = {}
        self.reporter = reporter
        self.run_listener = False
        self.worker = Worker(1)
        with NodeAdapter._mutex:
            NodeAdapter._initialized = True
        self.scan_done = threading.Event()
#        self.shared_nodes = shared_manager.Queue()
        self.expected_paths = []
        self.sender = None
        self.recver = None

    def start_nodes(self):
        _l.info("Start connected nodes")
        [n.start() for n in self.nodes.values()]

    def stop_nodes(self):
        _l.info("Stop connected nodes")
        [n.stop() for n in self.nodes.values()]

    def teardown(self):
        _l.info("Serial adapter teardown")
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
        _l.info(_s("Register node {}, {}", node.path, data))
        if node.fwver is None or len(node.fwver) == 0:
            _l.error(_s("Unknown node {}", node.path))
            return
        try:
    #        if node.proto is None:
             for proto in SupportedProto.protocols.values():
                if proto[1] == node.proto:
                    node.ntype = proto[0]
                    break
             if len(self.expected_paths) != len(self.nodes):
                _l.info(_s("Register node {}/{}", len(self.nodes), len(self.expected_paths)))
                return
             with_proto = [n for n in self.nodes.values() if n.ntype is not None]
             if len(with_proto) == len(self.nodes):
                self.scan_done.set()
        except Exception as ex:
            _l.error(_s("Exception on register node: {}", ex))

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
            _l.info(_s("Examine {}", proto))
            if proto[1].prepare(node) is False:
                get_type(node)
                return
            if proto[1].start(node) is False:
                get_type(node)
        except StopIteration:
            _l.info(_s("All proto tried"))
            if not node.started:
                raise RuntimeError(_s("No proto found for node {}", node))
        except Exception as ex:
            _l.error(_s(
            "Exception on examine node[{}]: {}", node, ex))

def create_node(adapter, path):#, sender=None):
    """Create node"""
    _l.debug(_s("Creating node {}", path))
    if not NodeAdapter._initialized:
        return

    path = path.strip()
    node = None

    try:
        node = SerialNode(path=path, adapter=adapter)#, reporter=adapter.reporter)
#       node = RawNode(path=RAWNODE_BASE+path, adapter=adapter.
        if node is not None:
            adapter.nodes[node.dev.fileno()] = node
            node.try_proto = yield_proto()
        else:
            _l.error(_s("Invalid node"))
    except KeyboardInterrupt:
        _l.error(_s("Received keyboard interrupt"))
    except Exception as ex:
        _l.error(_s("Exception on creating node: {}", ex))
    return node


def scan_nodes(adapter, targets=None):
    _l.info(_s("Scan for connected nodes {}", targets))
    clear_list(adapter.nodes)
    if targets is not None and not isinstance(targets, list):
        _l.error(_s("Expecting a list for targets"))
        return
    if targets is None or len(targets) == 0:
        targets = [_s(DEV_TTYUSB, T_EVERYONE), _s(DEV_TTYACM, T_EVERYONE)]
    paths = []
    [paths.extend(glob.glob(target)) for target in targets]
    if len(paths) == 0:
        raise RuntimeError("No node connected")
    adapter.worker.start()
    adapter.expected_paths = paths

    pipe = mp.Pipe()
    adapter.sender = pipe[0]
    adapter.recver = pipe[1]
    adapter.register_mutex = mp.Lock()

    try:
        _l.info("Scanning preparing")
        pool = ProcTaskManager(with_child=True)
        [create_node(adapter, path) for path in paths]
        [pool.create_task(get_type, node) for node in adapter.nodes.values()]
        while not adapter.scan_done.isSet():
            if adapter.recver.poll(2):
                fd, addr, fwver, proto, data = adapter.recver.recv()
                node = adapter.nodes.get(fd)
                if node:
                    node.addr, node.fwver, node.proto = addr, fwver, proto
                    with adapter.register_mutex:
                        adapter.register(node, data)
                else:
                    _l.error(_s("Unexpected node try to register ({})", (fd, fwver, proto, data)))
        pool.waitall()
    except Exception as ex:
        _l.error(_s("Scanning failed: {}", ex))
        [p.close() for p in pipe]
        raise

    adapter.scan_done.wait()
    adapter.scan_done.clear()
    [p.close() for p in pipe]
    adapter.sender = None
    adapter.recver = None
    _l.info("Scanning finished")

    adapter.start_nodes()

if __name__ == '__main__':

    from inuithy.common.runtime import Runtime as rt
    from inuithy.common.runtime import load_tcfg

    rt.handle_args()
    load_tcfg(rt.tcfg_path)
    adapter = NodeAdapter()
    try:
#       _l.debug(NodeAdapter.protocols)
        scan_nodes(adapter, targets=['/dev/ttyUSB*'])
        _l.debug([str(fd)+str(n) for fd, n in adapter.nodes.items()])
        _l.debug(len(adapter.nodes))
    except KeyboardInterrupt:
        _l.error(_s("Received keyboard interrupt"))
    except Exception as ex:
        _l.error(_s("Exception: {}", ex))
        raise
    finally:
        adapter.teardown()


