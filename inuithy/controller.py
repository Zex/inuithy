""" Controller application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_TITLE, __version__, to_string,\
WorkMode, to_console
from inuithy.common.runtime import Runtime as rt
from inuithy.common.runtime import load_tcfg
import inuithy.mode.auto as auto
import inuithy.mode.manual as manu
import inuithy.mode.monitor as moni
from inuithy.util.task_manager import ProcTaskManager
import logging
import logging.config as lconf

lconf.fileConfig(INUITHY_LOGCONFIG)
controller = None

def auto_mode_handler():
    """Handler for automatic mode
    """
    global controller
    controller = auto.AutoCtrl()
    controller.start()

def manual_mode_handler():
    """Handler for manual mode
    """
    global controller
    controller = manu.ManualCtrl()
    controller.start()

def monitor_mode_handler():
    """Handler for monitoring mode
    """
    global controller
    controller = moni.MoniCtrl()
    controller.start()

mode_route = {
    WorkMode.AUTO.name:     auto_mode_handler,
    WorkMode.MANUAL.name:   manual_mode_handler,
    WorkMode.MONITOR.name:  monitor_mode_handler,
}

def handle_args(in_args = None):
    """Arguments handler"""    
    args = None
    try:
        rt.parser.description = 'Inuithy Controller'
        rt.parser.add_argument('-m', '--work-mode', help='Mode for framework to run in', choices=WorkMode.__members__.keys())
        args = rt.handle_args()
        load_tcfg(rt.tcfg_path)
        if args.work_mode is not None:
            rt.tcfg.workmode = args.work_mode
        to_console("Starting {} Controller", rt.tcfg.workmode)
    except Exception as ex:
        to_console("Exception on handlin report arguments: {}", ex)
        return None
    return args

def start_controller():
    global controller
    lgr.info(to_string("Start controller"))
    
    handle_args()

    if mode_route.get(rt.tcfg.workmode) is None:
        lgr.error("Unknown work mode")
        return
    try:
        mode_route[rt.tcfg.workmode]()
    except KeyboardInterrupt:
        lgr.info(to_string("Controller received keyboard interrupt"))
        controller.teardown()
    except Exception as ex:
        lgr.error(to_string("Exception on Controller: {}", ex))
#    finally:
    lgr.info("Bye~")

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyController')
    lgr.info(to_string(INUITHY_TITLE, __version__, "Controller"))
    start_controller()

