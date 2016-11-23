""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY,\
string_write, T_EVERYONE
from inuithy.common.node import NodeBLE, NodeZigbee, NodeType
from inuithy.protocol.ble_proto import BleProtocol as BleProt
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProt
from inuithy.protocol.bzcombo_proto import BzProtocol as BZProt
from inuithy.util.task_manager import ThrTaskManager
import glob, logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

class SerialAdapter(object):
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
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging

    @staticmethod
    def exam_msg(msg):
        """Send examine message"""
        buf = ''
        dev.write(msg)

        if dev.inWaiting():
            buf = dev.readall()
        if len(buf) != 0:
            buf = buf.strip('\t \r\n')
# TODO Examine reply
#        return NodeType.BLE
#        return NodeType.Zigbee
#        return NodeType.BleZbee
        return None

    @staticmethod
    def get_type(port):
        """Get firmware type via port"""
        # TODO
#        return NodeType.BLE
        return NodeType.Zigbee
#        return NodeType.BleZbee

        supported_proto = [BleProt, ZbeeProt, BZProt]
        for msg in supported_proto:
            try:
                ptype = SerialAdapter.exam_msg(msg)
                if ptype is not None and len(ptype) > 0:
                    return ptype
            except Exception as ex:
                self.lgr(string_write(
                    "Exception on sending examine msg [{}]: {}",
                    msg, ex))

    def create_node(self, port):
        if isinstance(port, tuple):
            port = port[1]
        if not isinstance(port, str) or port is None or len(port) == 0:
            return
        port = port.strip()
        node = None
        try:
            ptype = SerialAdapter.get_type(port)
            if ptype is NodeType.BLE:
                node = NodeBLE(port, reporter=self.reporter, lgr=self.lgr)
            elif ptype is NodeType.Zigbee:
                node = NodeZigbee(port, reporter=self.reporter, lgr=self.lgr)
            elif ptype is NodeType.BleZbee:
                node = NodeBz(port, reporter=self.reporter, lgr=self.lgr)
            if node is not None:
                self.__nodes.append(node)
                node.start_listener()
        except Exception as ex:
            logging.error(string_write("Exception on creating node: {}", ex))

        return node

    def scan_nodes(self, targets=DEV_TTYUSB.format(T_EVERYONE)):
        self.lgr.info("Scan for connected nodes")
        self.__nodes = []
        ports = enumerate(name for name in glob.glob(targets))
        mng = ThrTaskManager()
        mng.create_task_foreach(self.create_node, ports)
        mng.waitall()

    def stop_nodes(self):
        self.lgr.info("Stop connected nodes")
        [n.stop_listener() for n in self.nodes]

if __name__ == '__main__':

    sad = SerialAdapter()
    sad.scan_nodes()
    print(sad.nodes)



