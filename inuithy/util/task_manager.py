""" Task manager
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import to_string, INUITHY_LOGCONFIG,\
T_EVERYONE
from inuithy.util.helper import clear_list
import os
import multiprocessing as mp
import threading
import logging.config as lconf
import logging
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('TaskManager')

class ProcTaskManager(object):
    """Process task manager
    """
    def __init__(self, lgr=None, with_child=False, daemon=False,\
        start_on_create=True):
        self.__tasks = [] #self.shared_mng.Queue()
        self.lgr = lgr is None and logging or lgr
        self.with_child = with_child
        self.daemon = daemon
        self.start_on_create = start_on_create

    def waitall(self):
        self.lgr.info(to_string('[{}] tasks running', len(self.__tasks)))
        try:
            [t.join() for t in self.__tasks if t.is_alive()]
            self.lgr.info(to_string('[{}] tasks finished', len(self.__tasks)))
            clear_list(self.__tasks)
        except Exception as ex:
            self.lgr.error(to_string("Exception on to waiting all: {}", ex))

    def _start_one(self, task):

        if self.with_child:
            task.start()
        else:
            task.run()

    def start(self):
       
       [self._start_one(t) for t in self.__tasks]

    def create_task(self, proc, *args):
        """Create one task with args
        """
        try:
            t = mp.Process(target=proc, args=args)
            t.daemon = self.daemon
            self.__tasks.append(t)
            if self.start_on_create:
                self._start_one(t)
        except Exception as ex:
            self.lgr.error(to_string("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs, *args):
        """Create task foreach object with args
        foreach `obj` in `objs` execute `proc` with `args`
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
        self.lgr = lgr is None and logging or lgr

    def waitall(self):
        self.lgr.info(to_string('[{}] tasks running', len(self.__tasks)))
        try:
            [t.join() for t in self.__tasks if t.isAlive()]
            self.lgr.info(to_string('[{}] tasks finished', len(self.__tasks)))
            clear_list(self.__tasks)
        except Exception as ex:
            self.lgr.error(to_string("Exception on to waiting all: {}", ex))

    def create_task(self, proc, *args):
        """Create one task with args
        """
        try:
            t = threading.Thread(target=proc, args=args)
            self.__tasks.append(t)
            t.run()
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


