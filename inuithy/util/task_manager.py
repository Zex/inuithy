## Task manager
# Author: Zex Li <top_zlynch@yahoo.com>
#

import os, multiprocessing, logging
import logging.config as lconf
from inuithy.common.predef import *

lconf.fileConfig(INUITHY_LOGCONFIG)
logger = logging.getLogger('TaskManager')

class TaskManager:

    def __init__(self):
        self.__tasks = []

    def waitall(self):
        logger.info('[{}] tasks running'.format(len(self.__tasks)))
        try:
            [os.waitpid(p.pid, 0) for p in self.__tasks if p.is_alive()]
            logger.info('[{}] tasks finished'.format(len(self.__tasks)))
        except Exception as ex:
            logger.error("Exception on to waiting all: {}".format(ex))

    def create_task(self, proc, args=()):
        try:
            p = multiprocessing.Process(target=proc, args=args)
            self.__tasks.append(p)
            p.start()
            logger.info('[{}]/{} running'.format(p.pid, len(self.__tasks)))
        except Exception as ex:
            logger.error("Create task with [{}] failed: {}".format(args, ex))

    def create_task_foreach(self, proc, objs):
        logger.info("Tasks creation begin")
        [self.create_task(proc, (o,)) for o in objs]
        logger.info("Tasks creation end")

def dummy_task(port):
    logger.info("[{}:{}]running {}".format(os.getppid(), os.getpid(), port))
    time.sleep(10)

if __name__ == '__main__':

    import glob, time
    DEV_TTYS = '/dev/ttyS1{}'
    ports = enumerate(name for name in glob.glob(DEV_TTYUSB.format('*')))
    mng = TaskManager()
    mng.create_task_foreach(dummy_task, ports)
    mng.waitall()


