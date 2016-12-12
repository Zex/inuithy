""" General worker
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, to_string
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty
import threading
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

class Worker(object):
    """General worker
    jobs = Queue()
    keep_working = True
    
    def work():
        while keep_working and not jobs.empty():
            print('working')
            j = jobs.get()
            j[0](j[1])
    
    def add_job():
        while keep_working:
            jobs.put((print, (time.time(),)))
    
    def stop_worker():
        global keep_working
        keep_working = False
    
    newjob = threading.Thread(target=add_job)
    worker = threading.Thread(target=work)
    stopper = threading.Timer(5, stop_worker)
    
    newjob.start()
    worker.start()
    stopper.start()
"""
    def __init__(self, get_timeout=None, lgr=None):
        self.lgr = lgr is None and logging or lgr
        self.jobs = Queue()
        self.get_timeout = get_timeout
        self._keep_working = True

    def add_job(self, func, *args):
        if self._keep_working:
            self.jobs.put((func, args))

    def _do_start(self):
        while self._keep_working:# and not self.jobs.empty():
            try:
                job = self.jobs.get(timeout=self.get_timeout)
#                self.lgr.debug(to_string("job:{}", job))
                if len(job) > 1 and job[0] is not None:
                    job[0](*job[1])
            except Empty:
                pass

    def start(self):
        self.lgr.info("Start worker")
        self.workline = threading.Thread(target=self._do_start)
        self.workline.start()
    
    def stop(self):
        self.lgr.info("Stop worker")
        self._keep_working = False

if __name__ == '__main__':
    import time
    work = Worker(2)
    work.start()
#    for i in range(10000):
#        threading.Thread(target=work.add_job, args=(print, time.time(), "morning",)).start()
#    input("Working ...")
    work.stop()

