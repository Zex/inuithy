## Serial port adapter
# Author: Zex Li <top_zlynch@yahoo.com>
#
import glob, logging
from inuithy.common.node import *
from inuithy.util.task_manager import *

class SerialAdapter:
   
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
        dev.write(candidates)
        buf = ''
        if dev.inWaiting():
            buf = dev.readall()
        if len(buf) != 0:
            buf = buf.strip('\t \r\n')
            # TODO 
        return NodeType.BLE
    
    def create_node(self, port):
        if isinstance(port, tuple): port = port[1]
        if not isinstance(port, str) or port == None or len(port) == 0:
            return
        port = port.strip()
        node = None
        try:
            ptype = SerialAdapter.get_type(port)
            if ptype == NodeType.BLE:
                node = NodeBLE(port, reporter=self.reporter)
            elif ptype == NodeType.Zigbee:
                node = NodeZigbee(port, reporter=self.reporter)
            if node != None:
                self.__nodes.append(node)
        except Exception as ex:
            logging.error(string_write("Exception on creating node: {}", ex))
            
        return node
    
    def scan_nodes(self):
        self.__nodes = []
        # TODO DEV_TTYS => DEV_TTYUSB
        ports = enumerate(name for name in glob.glob(DEV_TTYS.format('*')))
        mng = ThrTaskManager()
        mng.create_task_foreach(self.create_node, ports)
        mng.waitall()

if __name__ == '__main__':

    sad = SerialAdapter()
    sad.scan_nodes()
    print(sad.nodes)



