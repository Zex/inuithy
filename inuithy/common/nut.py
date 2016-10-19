## Node under test definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial, glob
from inuithy.common.node import *
from inuithy.util.task_manager import *

DEV_TTYUSB = '/dev/ttyUSB{}'

class NUT:
    """Node under test"""
    def __init__(self):

    def get_type(self):

    def scan_nodes(self):
         ports = enumerate(name for name in glob.glob(DEV_TTYUSB.format('*')))




