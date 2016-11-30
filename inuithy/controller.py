""" Controller application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
TRAFFIC_CONFIG_PATH, INUITHY_TITLE, INUITHY_VERSION, to_string,\
WorkMode
from inuithy.util.config_manager import create_inuithy_cfg
import inuithy.mode.auto as auto
import inuithy.mode.monitor as moni
from inuithy.util.task_manager import ProcTaskManager
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)
controller = None

def auto_mode_handler(tcfg, trcfg):
    """Handler for automatic mode
    """
    global controller
    controller = auto.AutoController(tcfg, trcfg)
    controller.start()

def manual_mode_handler(tcfg, trcfg):
    """Handler for manual mode
    """
    global controller
    controller = auto.ManualController(tcfg, trcfg)
    controller.start()

def monitor_mode_handler(tcfg, trcfg):
    """Handler for monitoring mode
    """
    global controller
    controller = moni.MonitorController(tcfg, trcfg)
    controller.start()

mode_route = {
    WorkMode.AUTO.name:     auto_mode_handler,
    WorkMode.MANUAL.name:   manual_mode_handler,
    WorkMode.MONITOR.name:  monitor_mode_handler,
}

def start_controller(tcfg, trcfg):
    global controller
    lgr.info(to_string("Start controller"))
    cfg = create_inuithy_cfg(tcfg)
    if cfg is None:
        lgr.error("Preload failed")
        return
    if mode_route.get(cfg.workmode) is None:
        lgr.error("Unknown work mode")
        return
    try:
        mode_route[cfg.workmode], (tcfg, trcfg)
    except KeyboardInterrupt:
        lgr.info(to_string("Controller received keyboard interrupt"))
        controller.teardown()
    except Exception as ex:
        lgr.error(to_string("Exception on Controller: {}", ex))
#    finally:
    lgr.info("Bye~")

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyController')
    lgr.info(to_string(INUITHY_TITLE, INUITHY_VERSION, "Controller"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)

