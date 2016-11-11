""" Serial port adapter
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import DEV_TTYUSB, DEV_TTYS, DEV_TTY, string_write
from inuithy.common.node import NodeBLE, NodeZigbee, NodeType
from inuithy.util.task_manager import ThrTaskManager
import glob, logging

class SerialAdapter(object):
    """Serial port adapter
    """
    @property
    def nodes(self):
        return self.__nodes
    @nodes.setter
    def nodes(self, val):
        pass

    def __init__(self, reporter=None):
        self.__nodes = []
        self.reporter = reporter

    @staticmethod
    def get_type(port):
        # TODO
        return NodeType.BLE
        dev = serial.Serial(port, baudrate=115200, timeout=2)
#TODO   dev.write(candidates)
        buf = ''
        if dev.inWaiting():
            buf = dev.readall()
        if len(buf) != 0:
            buf = buf.strip('\t \r\n')
            # TODO 
        return NodeType.BLE

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
                node = NodeBLE(port, reporter=self.reporter)
            elif ptype is NodeType.Zigbee:
                node = NodeZigbee(port, reporter=self.reporter)
            if node is not None:
                self.__nodes.append(node)
                node.start_listener()
        except Exception as ex:
            logging.error(string_write("Exception on creating node: {}", ex))

        return node

    def scan_nodes(self, targets=DEV_TTYUSB.format('*')):
        self.__nodes = []
        # TODO DEV_TTYS => DEV_TTYUSB
        ports = enumerate(name for name in glob.glob(targets))
        mng = ThrTaskManager()
        mng.create_task_foreach(self.create_node, ports)
        mng.waitall()

    def stop_nodes(self):
        [n.stop_listener() for n in self.nodes]

if __name__ == '__main__':

    sad = SerialAdapter()
    sad.scan_nodes()
    print(sad.nodes)



