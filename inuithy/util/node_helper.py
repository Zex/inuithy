## Node under test definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial, glob
from inuithy.common.node import *
from inuithy.util.task_manager import *

DEV_TTYUSB = '/dev/ttyUSB{}'


def get_type( port):
    pass

def create_node( port):
    pass

def scan_nodes():
    ports = enumerate(name for name in glob.glob(DEV_TTYUSB.format('*')))
    mng = TaskManager()
    mng.create_task_foreach(create_node, ports)
    mng.waitall()




