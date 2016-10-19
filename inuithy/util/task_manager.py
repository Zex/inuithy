## Task manager
# Author: Zex Li <top_zlynch@yahoo.com>
#

import os, multiprocessing, logging
from inuithy.common.predef import *

class TaskManager:

    def __init__(self):
        self.__tasks = []

    def waitall(self):
        logging.debug('Waitall: {} running'.format(len(self.__tasks)))
        try:
            [os.waitpid(p.pid, 0) for p in self.__tasks if p.is_alive()]
        except Exception as ex:
            logging.error("Waitall: failed to wait all: {}".format(ex))

    def create_task(self, proc, args=()):
        try:
            p = multiprocessing.Process(target=proc, args=args)
            self.__tasks.append(p)
            p.start()
            logging.debug('[{}]/{} running'.format(p.pid, len(self.__tasks)))
        except Exception as ex:
            logging.error("Create task for [{}] failed: {}".format(args, ex))

    def create_task_foreach(self, proc, objs):
        logging.debug("---creation begin---")
        [self.create_task(proc, (o,)) for o in objs]
        logging.debug("---creation end---")

def dummy_task(port):
    logging.debug("[{}:{}]running {}".format(os.getppid(), os.getpid(), port))
    time.sleep(10)

if __name__ == '__main__':

    import glob, time
    import logging.config as lconf
    lconf.fileConfig(INUITHY_LOGCONFIG)
    DEV_TTYUSB = '/dev/ttyS1{}'
    logger = logging.getLogger('InuithyTask')
    ports = enumerate(name for name in glob.glob(DEV_TTYUSB.format('*')))
    mng = TaskManager()
    mng.create_task_foreach(dummy_task, ports)
    mng.waitall()


