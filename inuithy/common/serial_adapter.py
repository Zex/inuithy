""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
to_string, T_EVERYONE, INUITHY_LOGCONFIG, T_MSG
from inuithy.common.supported_proto import SupportedProto
from inuithy.protocol.ble_proto import BleProtocol as BleProto
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
from inuithy.protocol.bzcombo_proto import BzProtocol as BZProto
from inuithy.util.task_manager import ThrTaskManager
import glob, logging
import logging.config as lconf
from multiprocessing import Queue as JQ

lconf.fileConfig(INUITHY_LOGCONFIG)

class SerialAdapter(SupportedProto):
    """Serial port adapter
    """
    @property
    def nodes(self):
        return self.__nodes
    @nodes.setter
    def nodes(self, val):
        pass

    def __init__(self, reporter=None, lgr=None):
        self.__nodes = []
        self.reporter = reporter
        SerialAdapter.lgr = lgr
        if SerialAdapter.lgr is None:
            SerialAdapter.lgr = logging

    @staticmethod
    def exam_msg(msg):
        """Send examine message"""
# TODO
#        return ZbeeProto.NAME
        return BleProto.NAME
#        return BZProto.NAME

        buf = ''
        dev.write(msg)

        if dev.inWaiting():
            buf = dev.readall()
        if len(buf) != 0:
            buf = buf.strip('\t \r\n')
        return buf

    @staticmethod
    def get_type(port):
        """Get firmware type via port"""
        for proto in SerialAdapter.protocols.values():
            """name => (proto, node)"""
            try:
                req = proto[0].getfwver()
                rep = SerialAdapter.exam_msg(req)
                if rep is not None and len(rep) > 0:
                    SerialAdapter.lgr.info(to_string("Reply {}", rep))
                    if proto[0].isme({T_MSG: rep}):
                        SerialAdapter.lgr.info(to_string("Found protocol {}", proto[0]))
                        return proto[1]
            except Exception as ex:
                SerialAdapter.lgr.error(to_string(
                "Exception on sending examine msg [{}]: {}", req, ex))
        return None

    def create_node(self, port):
        """Create node"""
        SerialAdapter.lgr.info(to_string("Creating node {}", port))
        if isinstance(port, tuple):
            port = port[1]
        if not isinstance(port, str) or port is None or len(port) == 0:
            return
        port = port.strip()
        node = None
        try:
            ptype = SerialAdapter.get_type(port)
            if ptype is not None:
                node = ptype.create(port, reporter=self.reporter, lgr=SerialAdapter.lgr)
            else: 
                SerialAdapter.lgr.error(to_string("Unsupported protocol {}", ptype))
            if node is not None:
                self.__nodes.append(node)
        except Exception as ex:
            SerialAdapter.lgr.error(to_string("Exception on creating node: {}", ex))
#        SerialAdapter.lgr.debug("Creation finished " + port)
        return node

    def scan_nodes(self, targets=DEV_TTYUSB.format(T_EVERYONE)):
        SerialAdapter.lgr.info(to_string("Scan for connected nodes {}", targets))
        self.__nodes = []
        ports = enumerate(name for name in glob.glob(targets))
        mng = ThrTaskManager(SerialAdapter.lgr)
        mng.create_task_foreach(self.create_node, ports)
        mng.waitall()
        self.start_nodes()
    
    def start_nodes(self):
        SerialAdapter.lgr.info("Start connected nodes")
        [n.start_listener() for n in self.__nodes]

    def stop_nodes(self):
        SerialAdapter.lgr.info("Stop connected nodes")
        [n.stop_listener() for n in self.nodes]

if __name__ == '__main__':

    sad = SerialAdapter()

#    print(SerialAdapter.protocols)
    sad.scan_nodes(targets='/dev/ttyS1*')
    print(sad.nodes)
    sad.stop_nodes()


