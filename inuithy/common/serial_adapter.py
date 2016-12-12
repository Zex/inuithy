""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
to_string, T_EVERYONE, INUITHY_LOGCONFIG, T_MSG, NodeType
from inuithy.util.helper import clear_list
from inuithy.util.task_manager import ProcTaskManager
from inuithy.common.supported_proto import SupportedProto
from inuithy.common.node import SerialNode, RawNode, RAWNODE_BASE, RawNodeSvr
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BzProto
from inuithy.util.worker import Worker
import glob, logging
import threading
import select
import socket
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
    register_mutex = threading.Lock()
    _mutex = threading.Lock()

    _initialized = False

    def __init__(self, reporter=None, lgr=None):
        self.__nodes = {}
        self.reporter = reporter
        SerialAdapter.lgr = lgr is None and logging or lgr
        self.run_listener = False
        self.poll_timeout = 2 # seconds
        self.poller = select.epoll()
        self.poller_thread = None
        self.worker = Worker(2, SerialAdapter.lgr)
        self.node_svr = None
        self.create_node_svr()
        with SerialAdapter._mutex:
            SerialAdapter._initialized = True
#        self.start_poll()

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
        """Register node with details to adapter
            [ntype.name] => (ntype, proto, node, report_hdr)
           callback for nodes
        """
        SerialAdapter.lgr.debug(to_string("Register node {}, {}", node.path, data))
        try:
            for proto in SerialAdapter.protocols.values():
                if proto[1].isme({T_MSG: data}):
                    node.fwver = data
                    node.ntype = proto[0]
                    node.proto = proto[1]
                    node.reporter = self.reporter
#            with SerialAdapter.register_mutex:
            if True:
                reg = [n for n in self.nodes.values() if n.proto is not None]
#            node.stop_listener()
                if len(reg) == len(self.nodes):
                    SerialAdapter.scan_done.set()
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on register node: {}", ex))

    def add_node(self, node):
        """Add node to fileno-node map"""
        try:
            if node is not None:
#            node.start_listener()
                self.poller.register(node.dev.fileno(), select.EPOLLIN|select.EPOLLOUT|select.EPOLLET)
                self.nodes[node.dev.fileno()] = node
                SerialAdapter.get_type(node)
            else:
                SerialAdapter.lgr.error(to_string("Invalid node"))
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on adding node: {}", ex))

    def create_node(self, path):
        """Create node"""
#        SerialAdapter.lgr.debug(to_string("Creating node {}", path))
        if isinstance(path, tuple):
            path = path[1]
        if not isinstance(path, str) or path is None or len(path) == 0:
            return

        path = path.strip()
        node = None

        try:
#            node = SerialNode(path=path, lgr=SerialAdapter.lgr, adapter=self)
            node = RawNode(path=RAWNODE_BASE+path, lgr=SerialAdapter.lgr, adapter=self)
            self.add_node(node)
        except KeyboardInterrupt:
            SerialAdapter.lgr.error(to_string("Received keyboard interrupt"))
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on creating node: {}", ex))
        return node

    def scan_nodes(self, targets=DEV_TTYUSB.format(T_EVERYONE)):
        SerialAdapter.lgr.info(to_string("Scan for connected nodes {}", targets))
        clear_list(self.nodes)
        paths = enumerate(name for name in glob.glob(targets))
        print("start_worker")
        self.worker.start()
        print("start_poll")
        self.start_poll()
        print("start_add job")
        [self.worker.add_job(self.create_node, path) for path in paths]
        print('start ... ')
#        SerialAdapter.scan_done.wait()
        input("waiting...")
        print('quit ...')
        SerialAdapter.scan_done.clear()
        SerialAdapter.lgr.info("Scanning finished")
#        self.start_nodes()

    def create_node_svr(self):
        """Similator"""
        self.node_svr = RawNodeSvr(adapter=self)
        self.poller.register(self.node_svr.dev.fileno(), select.EPOLLIN|select.EPOLLOUT|select.EPOLLET)

    def close_node_svr(self):
        """Similator"""
        self.node_svr.close()

    def start_nodes(self):
        SerialAdapter.lgr.info("Start connected nodes")
        [n.start_listener() for n in self.nodes]

    def stop_nodes(self):
        SerialAdapter.lgr.info("Stop connected nodes")
        [n.stop_listener() for n in self.nodes]

    def __listener_routine(self):
        """Node listener routine"""
        try:
            while self.run_listener:
                events = self.poller.poll(0.1)#self.poll_timeout)
                for fileno, event in events:
                    if self.nodes.get(fileno) is not None:
                        node = self.nodes.get(fileno)
                        if event & select.EPOLLIN:
                            self.worker.add_job(node.read)
                    elif self.node_svr is not None and fileno == self.node_svr.dev.fileno():
                        if event & select.EPOLLIN:
                            self.worker.add_job(self.node_svr.read, self.worker)
#                    elif event & select.EPOLLIN:
#                       pass
#                    elif event & select.EPOLLOUT:
#                       pass
#                    elif event & select.EPOLLHUP:
#                       pass
#                if len(events) == 0:
#                    print("GOT NOTHING on TIMEOUT")
        except KeyboardInterrupt:
            SerialAdapter.lgr.error(to_string("Received keyboard interrupt"))
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on listener routine: {}", ex))
        self.teardown()

    def start_poll(self):
        """Start poller for node IO events"""
        SerialAdapter.lgr.info("Start poller")
        if self.poller is None or self.worker is None:
            SerialAdapter.lgr.error("Invalid poller or worker")
            return
        self.run_listener = True
        self.poller_thread = threading.Thread(target=self.__listener_routine)
        self.poller_thread.start()

    def stop_poll(self):
        """Stop polling node IO events"""
        SerialAdapter.lgr.info("Stop poller")
        if self.poller is None or self.poller.closed:
            return
        self.run_listener = False
        [self.poller.unregister(node.dev.fileno()) for node in self.nodes.values()]
        self.poller.close()

    def teardown(self):
        SerialAdapter.lgr.info("Serial adapter teardown")
        with SerialAdapter._mutex:
            if not SerialAdapter._initialized:
                return
        SerialAdapter._initialized = False
        if not SerialAdapter.scan_done.isSet():
            SerialAdapter.scan_done.set()
#        self.stop_nodes()
        self.stop_poll()
        [node.close() for node in self.nodes.values()]
        self.close_node_svr()
        self.worker.stop()

if __name__ == '__main__':

    sad = SerialAdapter()
    try:
#       print(SerialAdapter.protocols)

        sad.scan_nodes(targets='/dev/tty2*')
        print([str(fd)+str(n) for fd, n in sad.nodes.items()])
#       sad.stop_nodes()
    except KeyboardInterrupt:
        SerialAdapter.lgr.error(to_string("Received keyboard interrupt"))
    except Exception as ex:
        SerialAdapter.lgr.error(to_string("Exception: {}", ex))
    finally:
        sad.teardown()


