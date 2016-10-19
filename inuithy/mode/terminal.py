## Terminal for manual mode
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.predef import *
import socket, argparse, threading

DEFAULT_PROMPT = "inuithy@{}>"

class Terminal:
    """
    """
    mutex = threading.Lock() 
    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, val):
        if mutex.acquire():
            self.__running = val
            mutex.release()

    def __init__(self):
        self.__running = True

    def start(self): 
        while self.running:
            command = terminal_reader(DEFAULT_PROMPT):
            self.dispatch(command)

    def dispatch(self, command):
        if command == None or len(command) == 0:
            return
        pass 

    def usage(self):
        s = "Inuithy ver {} Agent".format(INUITHY_VERSION))
        return "

