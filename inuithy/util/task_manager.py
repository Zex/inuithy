## Task manager
# Author: Zex Li <top_zlynch@yahoo.com>
#

import os, multiprocessing, logging, threading
import logging.config as lconf
from inuithy.util.helper import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('TaskManager')

class ProcTaskManager:

    def __init__(self):
        self.__tasks = []

    def waitall(self):
        logger.info(string_write('[{}] tasks running', len(self.__tasks)))
        try:
            [os.waitpid(t.pid, 0) for p in self.__tasks if t.is_alive()]
            logger.info('[{}] tasks finished'.format(len(self.__tasks)))
        except Exception as ex:
            logger.error(string_write("Exception on to waiting all: {}", ex))

    def create_task(self, proc, args=()):
        try:
            p = multiprocessing.Process(target=proc, args=args)
            self.__tasks.append(p)
            t.start()
            logger.info(string_write('[{}]/{} running', t.pid, len(self.__tasks)))
        except Exception as ex:
            logger.error(string_write("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs):
        logger.info("Tasks creation begin")
        [self.create_task(proc, (o,)) for o in objs]
        logger.info("Tasks creation end")

class ThrTaskManager:

    def __init__(self):
        self.__tasks = []

    def waitall(self):
        logger.info('[{}] tasks running'.format(len(self.__tasks)))
        try:
            [t.join() for t in self.__tasks if t.isAlive()]
            logger.info('[{}] tasks finished'.format(len(self.__tasks)))
        except Exception as ex:
            logger.error(string_write("Exception on to waiting all: {}", ex))

    def create_task(self, proc, args=()):
        try:
            t = threading.Thread(target=proc, args=args)
            self.__tasks.append(t)
            t.start()
            logger.info('[{}]/{} running'.format(t.name, len(self.__tasks)))
        except Exception as ex:
            logger.error(string_write("Create task with [{}] failed: {}", args, ex))

    def create_task_foreach(self, proc, objs):
        logger.info("Tasks creation begin")
        [self.create_task(proc, (o,)) for o in objs]
        logger.info("Tasks creation end")

def dummy_task(port):
    logger.info("[{}:{}]running {}".format(os.getppid(), os.getpid(), port))
    time.sleep(10)

if __name__ == '__main__':

    import glob, time
    from inuithy.common.node import *
    DEV_TTYS = '/dev/ttyS1{}'
    ports = enumerate(name for name in glob.glob(DEV_TTYUSB.format('*')))
    mng = TaskManager()
    mng.create_task_foreach(dummy_task, ports)
    mng.waitall()


