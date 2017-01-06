""" Task manager
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import _s, _l, T_EVERYONE
from inuithy.util.helper import clear_list
from inuithy.util.cmd_helper import gen_pidfile
from inuithy.common.runtime import Runtime as rt
import os
import multiprocessing as mp
import threading
import logging.config as lconf
import logging
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty

class ProcTaskManager(object):
    """Process task manager
    """
    def __init__(self, with_child=False, daemon=False,\
        start_on_create=True):
        self.__tasks = [] #self.shared_mng.Queue()
        self.with_child = with_child
        self.daemon = daemon
        self.start_on_create = start_on_create

    def waitall(self):
        _l.info(_s('[{}] tasks running', len(self.__tasks)))
        try:
            [t.join() for t in self.__tasks if t.is_alive()]
            _l.info(_s('[{}] tasks finished', len(self.__tasks)))
            clear_list(self.__tasks)
        except Exception as ex:
            _l.error(_s("Exception on to waiting all: {}", ex))

    def _start_one(self, task):

        if self.with_child:
            task.start()
            pidfile = rt.tcfg.config.get(T_PIDFILE)
            if pidfile:
                gen_pidfile(pidfile, task.pid)
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
            _l.error(_s("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs, *args):
        """Create task foreach object with args
        foreach `obj` in `objs` execute `proc` with `args`
        """
        _l.info("Tasks creation begin")
#        [self.create_task(proc, (o, *args)) for o in objs]
        [self.create_task(proc, (o,)+args) for o in objs]
        _l.info("Tasks creation end")

class ThrTaskManager(object):
    """Thread task manager
    """
    def __init__(self):
        self.__tasks = []

    def waitall(self):
        _l.info(_s('[{}] tasks running', len(self.__tasks)))
        try:
            [t.join() for t in self.__tasks if t.isAlive()]
            _l.info(_s('[{}] tasks finished', len(self.__tasks)))
            clear_list(self.__tasks)
        except Exception as ex:
            _l.error(_s("Exception on to waiting all: {}", ex))

    def create_task(self, proc, *args):
        """Create one task with args
        """
        try:
            t = threading.Thread(target=proc, args=args)
            self.__tasks.append(t)
            t.run()
        except Exception as ex:
            _l.error(_s("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs, *args):
        """Create task foreach object with args
        """
        _l.info("Tasks creation begin")
#        [self.create_task(proc, (o, *args)) for o in objs]
        [self.create_task(proc, (o,)+args) for o in objs]
        _l.info("Tasks creation end")

def dummy_task(port):
    logger.info(_s("[{}:{}]running {}", os.getppid(), os.getpid(), port))
    time.sleep(10)

if __name__ == '__main__':

    pass

