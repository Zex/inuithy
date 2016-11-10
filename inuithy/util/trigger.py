""" Trigger
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import console_write
import logging, threading, time
import logging.config as lconf

class Duration(object):
    """Duration indicator
    """
    def __init__(self):
        pass

    def __enter__(self):
        console_write(">> {}", time.ctime(time.clock_gettime(time.CLOCK_REALTIME)))

    def __exit__(self, cls, message, traceback):
        console_write("<< {}", time.ctime(time.clock_gettime(time.CLOCK_REALTIME)))


class TrafficTrigger(threading.Thread):
    """Fire a network traffic repeately
    @interval   Fire each @interval seconds
    @duration   Stop after @duration seconds
    """

    def __init__(self, interval=0, duration=0, target=None,\
        name="Trigger", daemon=False, *args, **kwargs):
        threading.Thread.__init__(self, target=target,\
            name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.stop_timer = threading.Timer(duration, self._stop_trigger)
        self.__interval = interval
        self.running = False
        self.__args = args
        self.__kwargs = kwargs
        self._target = target

    def run(self):
        if self._target is None:
            return
        self.running = True
        self.stop_timer.start()

#       with Duration() as dur:
        while self.running:
            self._target(self.__args, self.__kwargs)
            time.sleep(self.__interval)

    def _stop_trigger(self):
        console_write("{}: ========Stopping trgger============", self)
        self.running = False
        self.stop_timer.cancel()

    def __del__(self):
        self._stop_trigger()

    def _target(self):
        pass

def dummy_handler(*data):
    console_write("DUMMY: {} {}", time.clock_gettime(time.CLOCK_REALTIME), data)

if __name__ == '__main__':

    console_write("==========beg=============")
#    tt = TrafficTrigger(1/0.2, 20, dummy_handler, "DummyTrigger", args=(time.localtime()))
#    tt = TrafficTrigger(1/0.5, 25, dummy_handler, "DummyTrigger", args=(time.localtime()))
    tt = TrafficTrigger(1/0.9, 10, dummy_handler, "DummyTrigger", args=(time.localtime()))
#    tt = TrafficTrigger(1/30, 5, dummy_handler, "DummyTrigger", args=(time.localtime()))
    with Duration() as dur:
        tt.run()
    console_write("==========end=============")


