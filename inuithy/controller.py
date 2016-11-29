""" Controller application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
TRAFFIC_CONFIG_PATH, INUITHY_TITLE, INUITHY_VERSION, string_write,\
WorkMode
from inuithy.util.config_manager import create_inuithy_cfg
import inuithy.mode.auto_mode as auto
import inuithy.mode.monitor_mode as moni
import inuithy.util.console as tsh
from inuithy.util.task_manager import ProcTaskManager
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)

def auto_mode_handler(tcfg, trcfg):
    """Handler for automatic mode
    """
    global controller
    controller = auto.AutoController(tcfg, trcfg)
    controller.start()

def manual_mode_handler(tcfg, trcfg):
    """Handler for manual mode
    """
    tsh.start_console()

def monitor_mode_handler(tcfg, trcfg):
    """Handler for monitoring mode
    """
    controller = moni.MonitorController(tcfg, trcfg)
    controller.start()

mode_route = {
    WorkMode.AUTO.name:     auto_mode_handler,
    WorkMode.MANUAL.name:   manual_mode_handler,
    WorkMode.MONITOR.name:  monitor_mode_handler,
}

def start_controller(tcfg, trcfg):
    lgr.info(string_write("Start controller"))
    cfg = create_inuithy_cfg(tcfg)
    if cfg is None:
        lgr.error("Preload failed")
        return
    if mode_route.get(cfg.workmode) is None:
        lgr.error("Unknown work mode")
        return
    try:
        procs = ProcTaskManager()
        procs.create_task(mode_route[cfg.workmode], (tcfg, trcfg))
        procs.waitall()
    except KeyboardInterrupt:
        lgr.info(string_write("Controller received keyboard interrupt"))
        controller.teardown()
    except Exception as ex:
        lgr.error(string_write("Exception on Controller: {}", ex))
#    finally:
    lgr.info("Bye~")

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyController')
    lgr.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Controller"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)

