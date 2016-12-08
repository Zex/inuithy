""" Task manager
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import to_string, INUITHY_LOGCONFIG,\
T_EVERYONE
import os
import multiprocessing as mp
import threading
import logging.config as lconf
import logging

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('TaskManager')

class ProcTaskManager(object):
    """Process task manager
    """
    def __init__(self, lgr=None):
        self.__tasks = []
        self.lgr = lgr
        if self.lgr is None:
           self.lgr = logging

    def waitall(self):
        self.lgr.info(to_string('[{}] tasks running', len(self.__tasks)))
        try:
            [os.waitpid(t.pid, 0) for t in self.__tasks if t.is_alive()]
            self.lgr.info(to_string('[{}] tasks finished', len(self.__tasks)))
        except Exception as ex:
            self.lgr.error(to_string("Exception on to waiting all: {}", ex))

    def create_task(self, proc, args=()):
        """Create one task with args
        """
        try:
            t = mp.Process(target=proc, args=args)
            self.__tasks.append(t)
            t.start()
#            self.lgr.info(to_string('[{}]/{} running', t.pid, len(self.__tasks)))
        except Exception as ex:
            self.lgr.error(to_string("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs, *args):
        """Create task foreach object with args
        """
        self.lgr.info("Tasks creation begin")
#        [self.create_task(proc, (o, *args)) for o in objs]
        [self.create_task(proc, (o,)+args) for o in objs]
        self.lgr.info("Tasks creation end")

class ThrTaskManager(object):
    """Thread task manager
    """
    def __init__(self, lgr=None):
        self.__tasks = []
        self.lgr = lgr
        if self.lgr is None:
           self.lgr = logging

    def waitall(self):
        self.lgr.info(to_string('[{}] tasks running', len(self.__tasks)))
        try:
            [t.join() for t in self.__tasks if t.isAlive()]
            self.lgr.info(to_string('[{}] tasks finished', len(self.__tasks)))
        except Exception as ex:
            self.lgr.error(to_string("Exception on to waiting all: {}", ex))

    def create_task(self, proc, args=()):
        """Create one task with args
        """
        try:
            t = threading.Thread(target=proc, args=args)
            self.__tasks.append(t)
            t.run()
#            self.lgr.info(to_string('[{}]/{} running', t.name, len(self.__tasks)))
        except Exception as ex:
            self.lgr.error(to_string("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs, *args):
        """Create task foreach object with args
        """
        self.lgr.info("Tasks creation begin")
#        [self.create_task(proc, (o, *args)) for o in objs]
        [self.create_task(proc, (o,)+args) for o in objs]
        self.lgr.info("Tasks creation end")

def dummy_task(port):
    logger.info(to_string("[{}:{}]running {}", os.getppid(), os.getpid(), port))
    time.sleep(10)

if __name__ == '__main__':

#    from inuithy.common.node import *
    import glob, time
    DEV_TTYS = '/dev/ttyS1{}'
    ports = enumerate(name for name in glob.glob(DEV_TTYS.format(T_EVERYONE)))
    mng = TaskManager()
    mng.create_task_foreach(dummy_task, ports)
    mng.waitall()


