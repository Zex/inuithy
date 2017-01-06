""" ManualCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import TT_HEARTBEAT, TT_STATUS,\
TT_REPORTWRITE, TT_NOTIFICATION, TT_UNREGISTER, TT_REPLY,\
INUITHY_TITLE, _s, _c, _l, TT_SNIFFER
from inuithy.mode.base import CtrlBase
from inuithy.util.cmd_helper import subscribe
from inuithy.util.console import Console
from inuithy.common.runtime import Runtime as rt
import paho.mqtt.client as mqtt
import time
import threading

class ManualCtrl(CtrlBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.on_connect = ManualCtrl.on_connect
        self._mqclient.on_message = ManualCtrl.on_message
        self._mqclient.on_disconnect = ManualCtrl.on_disconnect
        self._mqclient.connect(host, port)
        subscribe(self.mqclient, TT_HEARTBEAT, ManualCtrl.on_topic_heartbeat)
        subscribe(self.mqclient, TT_UNREGISTER, ManualCtrl.on_topic_unregister)
        subscribe(self.mqclient, TT_STATUS, ManualCtrl.on_topic_status)
        subscribe(self.mqclient, TT_REPORTWRITE, ManualCtrl.on_topic_reportwrite)
        subscribe(self.mqclient, TT_NOTIFICATION, ManualCtrl.on_topic_notification)
        subscribe(self.mqclient, TT_REPLY, ManualCtrl.on_topic_reply)
        subscribe(self.mqclient, TT_SNIFFER, ManualCtrl.on_topic_sniffer)

    def __init__(self, delay=4):
        CtrlBase.__init__(self, delay)
        self.term = Console(self)

    def keep_looping(self):
        _l.info("Manual controller working")
        while ManualCtrl.initialized:
            self.mqclient.loop()

    def start(self):
        """Start controller routine"""
        if not ManualCtrl.initialized:
            _l.error(_s("ManualCtrl not initialized"))
            return

        try:
            _l.info(_s("Expected Agents({}): {}",\
                len(self.expected_agents), self.expected_agents))
            if self.worker is not None:
                self.worker.start()
            self.alive_notification()
            ret = mqtt.MQTT_ERR_SUCCESS
            for retry_cnt in range(1, 4):
                ret = self.mqclient.loop_start()
                if ret is None or ret == mqtt.MQTT_ERR_SUCCESS:
                    break
                self.mqclient.loop_stop()
                _l.warning(_s('Retry [{}] ...', retry_cnt))
            if ret is not None and ret != mqtt.MQTT_ERR_SUCCESS:
                raise RuntimeError("Start MQTT loop failed")
            self.term.start()
            _c("\nBye~\n")
            self.mqclient.loop_stop()
        except KeyboardInterrupt:
            _l.info(_s("ManualCtrl received keyboard interrupt"))
            self.term.on_cmd_quit()
        except NameError as ex:
            _l.error(_s("ERR: {}", ex))
        except Exception as ex:
            _l.error(_s("Exception on ManualCtrl: {}", ex))
        self.teardown()
        _l.info(_s("ManualCtrl terminated"))

def start_controller(args=None):
    """Shortcut to start controller"""
    rt.handle_args(args)
    controller = ManualCtrl()
    controller.start()

if __name__ == '__main__':
    import logging
    _l = logging.getLogger('InuithyManualCtrl')
    _l.info(_s(INUITHY_TITLE, __version__, "ManualCtrl"))
    start_controller()

