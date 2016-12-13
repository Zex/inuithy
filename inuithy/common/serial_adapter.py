""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
import sys
sys.path.append('/opt/inuithy')
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
to_string, T_EVERYONE, INUITHY_LOGCONFIG, T_MSG, NodeType,\
T_CHANNEL, T_PANID,\
T_SPANID, T_NODE                    
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
from random import randint

lconf.fileConfig(INUITHY_LOGCONFIG)

[SupportedProto.register(*proto) for proto in [
    (NodeType.BLE, BleProto, SerialNode),
    (NodeType.Zigbee, ZbeeProto, SerialNode),
    (NodeType.BleZbee, BzProto, SerialNode),
]]

class SerialAdapter:
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
#        self.poll_timeout = 0.5 # seconds
#        self.poller = select.epoll()
#        self.poller_thread = None
#        self.node_reader = Worker(0.5, SerialAdapter.lgr)
        self.node_writer = Worker(0.5, SerialAdapter.lgr)
        self.node_svr = None
#        self.create_node_svr()
        with SerialAdapter._mutex:
            SerialAdapter._initialized = True

    def get_type(self, node):
        """Get firmware type via port"""
#        for proto in SupportedProto.protocols.values():
        proto = next(node.try_proto)
        if proto is not None:
            """[ntype.name] => (ntype, proto, node, report_hdr)
            """
            try:
                req = proto[1].getfwver()
                self.node_writer.add_job(node.write, req)
            except Exception as ex:
                SerialAdapter.lgr.error(to_string(
                "Exception on sending examine msg [{}]: {}", req, ex))

    def get_addr(self, node):
        """Get firmware type via port"""
        SerialAdapter.lgr.info(to_string("Get address via {}", node))
        req = None
        try:
            req = node.proto.getaddr()
            self.node_writer.add_job(node.write, req)
        except Exception as ex:
            SerialAdapter.lgr.error(to_string(
                "Exception on requesting address [{}]: {}", req, ex))

    def register(self, node, data):
        """Register node with details to adapter
            [ntype.name] => (ntype, proto, node, report_hdr)
           callback for nodes
        """
        SerialAdapter.lgr.debug(to_string("Register node {}, {}", node.path, data))
        try:
            if node.proto is None:
                for proto in SupportedProto.protocols.values():
                    if proto[1].isme({T_MSG: data}):
                        node.fwver = data
                        node.ntype = proto[0]
                        node.proto = proto[1]
			break
		if node.proto is None:
                    self.get_type(node)
                else:
                    params = {
                         T_CHANNEL: '17', T_PANID: '1515151515',
                         T_SPANID: '1515', T_NODE: 'A004' }
                    req = node.proto.join(params)
                    self.node_writer.add_job(node.write, req)
#                else:
#                    self.get_addr(node)
                with_proto = [n for n in self.nodes.values() if n.proto is not None]
                if len(with_proto) == len(self.nodes):
                    SerialAdapter.scan_done.set()
#            elif len(node.addr) == 0:
#                node.addr = data
#                with_addr = [n for n in self.nodes.values() if len(n.addr) > 0]
#                if len(with_addr) == len(self.nodes):
#                    SerialAdapter.scan_done.set()
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on register node: {}", ex))

    def yield_proto(self):
        for proto in SupportedProto.protocols.values():
            yield proto

    def add_node(self, node):
        """Add node to fileno-node map"""
        try:
            if node is not None:
                self.nodes[node.dev.fileno()] = node
                node.try_proto = self.yield_proto()
                node.start_listener()
#                self.poller.register(node.dev.fileno(), select.EPOLLIN|select.EPOLLOUT|select.EPOLLET|select.EPOLLERR|select.EPOLLHUP)
                self.get_type(node)
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
            node = SerialNode(path=path, lgr=SerialAdapter.lgr, adapter=self, reporter=self.reporter)
#            node = RawNode(path=RAWNODE_BASE+path, lgr=SerialAdapter.lgr, adapter=self)
            self.add_node(node)
        except KeyboardInterrupt:
            SerialAdapter.lgr.error(to_string("Received keyboard interrupt"))
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on creating node: {}", ex))
        return node

    def scan_nodes(self, targets=None):#[DEV_TTYUSB.format(T_EVERYONE)]):
        SerialAdapter.lgr.info(to_string("Scan for connected nodes {}", targets))
        clear_list(self.nodes)
        if targets is None or len(targets) == 0:
            targets = [to_string(DEV_TTYUSB, T_EVERYONE)]#, to_string(DEV_TTYACM, T_EVERYONE)]
        paths = []
        [paths.extend(glob.glob(target)) for target in targets]
#        self.node_reader.start()
        self.node_writer.start()
        [self.create_node(path) for path in paths]
#        self.start_poll()
        SerialAdapter.scan_done.wait()
        SerialAdapter.scan_done.clear()
        SerialAdapter.lgr.info("Scanning finished")

#        self.start_nodes()

    def create_node_svr(self):
        """Similator"""
        self.node_svr = RawNodeSvr(adapter=self)
        self.poller.register(self.node_svr.dev.fileno(), select.EPOLLIN|select.EPOLLOUT|select.EPOLLET|select.EPOLLERR|select.EPOLLHUP)

    def close_node_svr(self):
        """Similator"""
        if self.node_svr is None:
            return
        self.node_svr.close()

    def start_nodes(self):
        SerialAdapter.lgr.info("Start connected nodes")
        [n.start_listener() for n in self.nodes.values()]

    def stop_nodes(self):
        SerialAdapter.lgr.info("Stop connected nodes")
        [n.stop_listener() for n in self.nodes.values()]

#    def __listener_routine(self):
#        """Node listener routine"""
#        try:
#            while self.run_listener:
#                events = self.poller.poll(self.poll_timeout)
#                for fileno, event in events:
#                    node = self.nodes.get(fileno)
#                    if self.nodes.get(fileno) is not None:
#                        if event & select.EPOLLIN:
#                            SerialAdapter.lgr.debug(to_string("NODE|EPOLLIN: {}", node.path))
#                            self.node_reader.add_job(node.read)
#                        elif event & select.EPOLLOUT:
#                            SerialAdapter.lgr.debug(to_string("NODE|EPOLLOUT: {}", node.path))
#                            if not node.msgs.empty():
#                                msg = node.msgs.get()
#                                if len(msg) == 1:
#                                    node.write(msg[0])
#                                elif len(msg) == 2:
#                                    node.write(msg[0], msg[1])
#                        elif event & select.EPOLLHUP:
#                            SerialAdapter.lgr.debug(to_string("HUP: {}, {}", fileno, event))
#                        elif event & select.EPOLLERR:
#                            SerialAdapter.lgr.debug(to_string("ERR: {}, {}", fileno, event))
#                        else:
#                            SerialAdapter.lgr.debug(to_string("OTHER: {}, {}", fileno, event))
#                    elif self.node_svr is not None and fileno == self.node_svr.dev.fileno():
#                        if event & select.EPOLLIN:
#                            self.node_svr.read()
#                    else:
#                        SerialAdapter.lgr.debug(to_string("OTHER: {}, {}", fileno, event))
##                    elif event & select.EPOLLIN:
##                        SerialAdapter.lgr.debug(to_string("IN: {}, {}", fileno, event))
##                    elif event & select.EPOLLOUT:
##                        SerialAdapter.lgr.debug(to_string("OUT: {}, {}", fileno, event))
##                    elif event & select.EPOLLHUP:
##                        SerialAdapter.lgr.debug(to_string("HUP: {}, {}", fileno, event))
##                    elif event & select.EPOLLERR:
##                        SerialAdapter.lgr.debug(to_string("ERR: {}, {}", fileno, event))
##                if len(events) == 0:
##                    SerialAdapter.lgr.debug("GOT NOTHING on TIMEOUT")
#        except KeyboardInterrupt:
#            SerialAdapter.lgr.error(to_string("Received keyboard interrupt"))
#        except Exception as ex:
#            SerialAdapter.lgr.error(to_string("Exception on listener routine: {}", ex))
#        self.teardown()
#
#    def start_poll(self):
#        """Start poller for node IO events"""
#        SerialAdapter.lgr.info("Start poller")
#        if self.poller is None or self.node_reader is None:
#            SerialAdapter.lgr.error("Invalid poller or worker")
#            return
#        self.run_listener = True
#        self.poller_thread = threading.Thread(target=self.__listener_routine)
#        self.poller_thread.start()
#
#    def stop_poll(self):
#        """Stop polling node IO events"""
#        SerialAdapter.lgr.info("Stop poller")
#        if self.poller is None or self.poller.closed:
#            return
#        self.run_listener = False
#        [self.poller.unregister(node.dev.fileno()) for node in self.nodes.values()]
#        self.poller.close()

    def teardown(self):
        SerialAdapter.lgr.info("Serial adapter teardown")
        with SerialAdapter._mutex:
            if not SerialAdapter._initialized:
                return
        SerialAdapter._initialized = False
        if not SerialAdapter.scan_done.isSet():
            SerialAdapter.scan_done.set()
        self.stop_nodes()
#        self.stop_poll()
        [node.close() for node in self.nodes.values()]
        self.close_node_svr()
#        self.node_reader.stop()
        self.node_writer.stop()

if __name__ == '__main__':

    sad = SerialAdapter()
    try:
#       SerialAdapter.lgr.debug(SerialAdapter.protocols)
        sad.scan_nodes(targets=['/dev/ttyUSB*'])
        SerialAdapter.lgr.debug([str(fd)+str(n) for fd, n in sad.nodes.items()])
        SerialAdapter.lgr.debug(len(sad.nodes))
    except KeyboardInterrupt:
        SerialAdapter.lgr.error(to_string("Received keyboard interrupt"))
    except Exception as ex:
        SerialAdapter.lgr.error(to_string("Exception: {}", ex))
    finally:
        sad.teardown()


