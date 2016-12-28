""" ManualCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import TT_HEARTBEAT, TT_STATUS,\
TT_REPORTWRITE, TT_NOTIFICATION, TT_UNREGISTER, TT_REPLY,\
INUITHY_TITLE, INUITHY_LOGCONFIG, to_string, to_console, TT_SNIFFER
from inuithy.mode.base import CtrlBase
from inuithy.util.cmd_helper import stop_agents
from inuithy.util.console import Console
from inuithy.common.runtime import Runtime as rt
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time
import threading

lconf.fileConfig(INUITHY_LOGCONFIG)

class ManualCtrl(CtrlBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.on_connect = ManualCtrl.on_connect
        self._mqclient.on_message = ManualCtrl.on_message
        self._mqclient.on_disconnect = ManualCtrl.on_disconnect
        self._mqclient.connect(host, port)
        self._mqclient.subscribe([
            (TT_HEARTBEAT, rt.tcfg.mqtt_qos),
            (TT_UNREGISTER, rt.tcfg.mqtt_qos),
            (TT_STATUS, rt.tcfg.mqtt_qos),
            (TT_REPORTWRITE, rt.tcfg.mqtt_qos),
            (TT_NOTIFICATION, rt.tcfg.mqtt_qos),
            (TT_REPLY, rt.tcfg.mqtt_qos),
            (TT_SNIFFER, rt.tcfg.mqtt_qos),
        ])
        self.mqclient.message_callback_add(TT_HEARTBEAT, ManualCtrl.on_topic_heartbeat)
        self.mqclient.message_callback_add(TT_UNREGISTER, ManualCtrl.on_topic_unregister)
        self.mqclient.message_callback_add(TT_STATUS, ManualCtrl.on_topic_status)
        self.mqclient.message_callback_add(TT_REPORTWRITE, ManualCtrl.on_topic_reportwrite)
        self.mqclient.message_callback_add(TT_NOTIFICATION, ManualCtrl.on_topic_notification)
        self.mqclient.message_callback_add(TT_REPLY, ManualCtrl.on_topic_reply)
        self.mqclient.message_callback_add(TT_SNIFFER, ManualCtrl.on_topic_sniffer)

    def __init__(self, lgr=None, delay=4):
        CtrlBase.__init__(self, lgr, delay)
        self.lgr = lgr is None and logging or lgr
        self.term = Console(self)

    def keep_looping(self):
        self.lgr.info("Manual controller working")
        while ManualCtrl.initialized:
            self.mqclient.loop()

    def start(self):
        """Start controller routine"""
        if not ManualCtrl.initialized:
            self.lgr.error(to_string("ManualCtrl not initialized"))
            return

        try:
            self.lgr.info(to_string("Expected Agents({}): {}",\
                len(self.expected_agents), self.expected_agents))
            if self.worker is not None:
                self.worker.start()
#            self.mqworker.start()
#            stop_agents(self.mqclient)
            self.alive_notification()
            ret = mqtt.MQTT_ERR_SUCCESS
            for retry_cnt in range(1, 4):
                ret = self.mqclient.loop_start()
                if ret is None or ret == mqtt.MQTT_ERR_SUCCESS:
                    break
                self.mqclient.loop_stop()
                self.lgr.warning(to_string('Retry [{}] ...', retry_cnt))
            if ret is not None and ret != mqtt.MQTT_ERR_SUCCESS:
                raise Exception("Start MQTT loop failed")
            self.term.start()
            to_console("\nBye~\n")
            self.mqclient.loop_stop()
        except KeyboardInterrupt:
            self.lgr.info(to_string("ManualCtrl received keyboard interrupt"))
            self.term.on_cmd_quit()
        except NameError as ex:
            self.lgr.error(to_string("ERR: {}", ex))
        except Exception as ex:
            self.lgr.error(to_string("Exception on ManualCtrl: {}", ex))
        self.teardown()
        self.lgr.info(to_string("ManualCtrl terminated"))

def start_controller(args=None, lgr=None):
    """Shortcut to start controller"""
    rt.handle_args(args)
    controller = ManualCtrl(lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyManualCtrl')
    lgr.info(to_string(INUITHY_TITLE, __version__, "ManualCtrl"))
    start_controller(lgr=lgr)

