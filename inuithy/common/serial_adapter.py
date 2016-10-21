## Serial port adapter
# Author: Zex Li <top_zlynch@yahoo.com>
#
import glob
from inuithy.common.node import *
from inuithy.util.task_manager import *

class SerialAdapter:
   
    @property
    def nodes(self):
        return self.__nodes

    @nodes.setter
    def nodes(self, val):
        pass

    def __init__(self):
        self.__nodes = []

    @staticmethod
    def get_type(port):
        # TODO
        return NodeType.BLE
    
    def create_node(self, port):
        node = None
        ptype = SerialAdapter.get_type(port)
        if ptype == NodeType.BLE:
            node = NodeBLE(port)
        elif ptype == NodeType.Zigbee:
            node = NodeZigbee(port)
        if node != None:
            self.__nodes.append(node)
        return node
    
    def scan_nodes(self):
        self.__nodes = []
        ports = enumerate(name for name in glob.glob(DEV_TTYS.format('*')))
        mng = ThrTaskManager()
        mng.create_task_foreach(self.create_node, ports)
        mng.waitall()

if __name__ == '__main__':

    sad = SerialAdapter()
    sad.scan_nodes()
    print("#######################################")
    print(sad.nodes)



