## Controller application main thread
# Author: Zex Li <top_zlynch@yahoo.com>
#
#from inuithy.util.config_manager import *
import logging
import logging.config as lconf
from inuithy.util.config_manager import *

lconf.fileConfig(INUITHY_LOGCONFIG)
lg = logging.getLogger('InuithyController')

import inuithy.mode.auto_mode as auto
import inuithy.mode.monitor_mode as moni
import inuithy.util.console as tsh

def auto_mode_handler(tcfg, trcfg):
    controller = auto.AutoController(tcfg, trcfg)
    controller.start()

def manual_mode_handler(tcfg, trcfg):
    tsh.start_console()

def monitor_mode_handler(tcfg, trcfg):
    controller = moni.MonitorController(tcfg, trcfg)
    controller.start()

mode_route = {
    WorkMode.AUTO.name:     auto_mode_handler,
    WorkMode.MANUAL.name:   manual_mode_handler,
    WorkMode.MONITOR.name:  monitor_mode_handler,
}

def preload(inuithy_cfgpath):
    inuithy_cfg    = InuithyConfig(inuithy_cfgpath)
    if False == inuithy_cfg.load():
        logger.error(string_write("Failed to load inuithy configure"))
        return None
    return inuithy_cfg

def start_controller(tcfg, trcfg):
    lg.info(string_write("Start controller"))
    cfg = preload(tcfg)
    if cfg == None:
        logger.error("Preload failed")
        return
    if None == mode_route.get(cfg.workmode):
        logger.error("Unknown work mode")
        return
    try:
        mode_route[cfg.workmode](tcfg, trcfg)
    except KeyboardInterrupt:
        logger.info(string_write("AutoController received keyboard interrupt"))
    except Exception as ex:
        self.lg.error(string_write("Exception on AutoController: {}", ex))
    finally:
        return

if __name__ == '__main__':
    lg.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "Controller"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)

