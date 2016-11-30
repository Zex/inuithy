""" MoniCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import INUITHY_TOPIC_HEARTBEAT, INUITHY_TOPIC_STATUS,\
INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION, INUITHY_TOPIC_UNREGISTER,\
TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE, INUITHY_LOGCONFIG,\
to_string
from inuithy.mode.base import ControllerBase
from inuithy.util.cmd_helper import stop_agents, extract_payload
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time

lconf.fileConfig(INUITHY_LOGCONFIG)

class MoniCtrl(ControllerBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self.mqclient.on_connect = MoniCtrl.on_connect
        self.mqclient.on_message = MoniCtrl.on_message
        self.mqclient.on_disconnect = MoniCtrl.on_disconnect
        self.mqclient.connect(host, port)
        self.mqclient.subscribe([
            (INUITHY_TOPIC_HEARTBEAT, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION, self.tcfg.mqtt_qos),
        ])
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_HEARTBEAT, MoniCtrl.on_topic_heartbeat)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_UNREGISTER, MoniCtrl.on_topic_unregister)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_STATUS, MoniCtrl.on_topic_status)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_REPORTWRITE, MoniCtrl.on_topic_reportwrite)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_NOTIFICATION, MoniCtrl.on_topic_notification)

    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        ControllerBase.__init__(self, inuithy_cfgpath, traffic_cfgpath, lgr, delay)
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging

    def start(self):
        """Start controller routine"""
        if not MoniCtrl.initialized:
            self.lgr.error(to_string("MoniCtrl not initialized"))
            return
        try:
            self.lgr.info(to_string("Expected Agents({}): {}",\
                len(self.expected_agents), self.expected_agents))
#            if self._traffic_timer is not None:
#                self._traffic_timer.start()
            if self.worker is not None:
                self.worker.start()
            stop_agents(self.mqclient)
            self.alive_notification()
            self._mqclient.loop_forever()
        except KeyboardInterrupt:
            self.lgr.info(to_string("MoniCtrl received keyboard interrupt"))
#            self.traffic_state.chk.done.set()
        except NameError as ex:
            self.lgr.error(to_string("ERR: {}", ex))
            self.teardown()
        except Exception as ex:
            self.lgr.error(to_string("Exception on MoniCtrl: {}", ex))
            raise
        self.lgr.info(to_string("MoniCtrl terminated"))

def start_controller(tcfg, trcfg, lgr=None):
    """Shortcut to start controller"""
    controller = MoniCtrl(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyMoniCtrl')
    lgr.info(to_string(INUITHY_TITLE, INUITHY_VERSION, "MoniCtrl"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

