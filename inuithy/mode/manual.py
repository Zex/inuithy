""" ManualCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import INUITHY_TOPIC_HEARTBEAT, INUITHY_TOPIC_STATUS,\
INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION, INUITHY_TOPIC_UNREGISTER,\
TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE, INUITHY_LOGCONFIG,\
to_string, to_console
from inuithy.mode.base import ControllerBase
from inuithy.util.cmd_helper import stop_agents, extract_payload
from inuithy.util.console import Console
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time
import threading

lconf.fileConfig(INUITHY_LOGCONFIG)

class ManualCtrl(ControllerBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.on_connect = ManualCtrl.on_connect
        self._mqclient.on_message = ManualCtrl.on_message
        self._mqclient.on_disconnect = ManualCtrl.on_disconnect
        self._mqclient.connect(host, port)
        self._mqclient.subscribe([
            (INUITHY_TOPIC_HEARTBEAT, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION, self.tcfg.mqtt_qos),
        ])
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_HEARTBEAT, ManualCtrl.on_topic_heartbeat)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_UNREGISTER, ManualCtrl.on_topic_unregister)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_STATUS, ManualCtrl.on_topic_status)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_REPORTWRITE, ManualCtrl.on_topic_reportwrite)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_NOTIFICATION, ManualCtrl.on_topic_notification)

    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        ControllerBase.__init__(self, inuithy_cfgpath, traffic_cfgpath, lgr, delay)
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging
#        self.mqworker = threading.Thread(target=self._mqclient.loop_forever)
#        self.mqworker = threading.Thread(target=self.keep_looping)
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
            stop_agents(self.mqclient)
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

def start_controller(tcfg, trcfg, lgr=None):
    """Shortcut to start controller"""
    controller = ManualCtrl(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyManualCtrl')
    lgr.info(to_string(INUITHY_TITLE, INUITHY_VERSION, "ManualCtrl"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

