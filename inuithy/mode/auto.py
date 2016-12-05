""" AutoCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import INUITHY_TOPIC_HEARTBEAT, INUITHY_TOPIC_STATUS,\
INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION, INUITHY_TOPIC_UNREGISTER,\
TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE, INUITHY_LOGCONFIG,\
to_string
from inuithy.mode.base import CtrlBase
from inuithy.util.cmd_helper import stop_agents
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time

lconf.fileConfig(INUITHY_LOGCONFIG)

class AutoCtrl(CtrlBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self.lgr.info("Create MQTT client")
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self.mqclient.on_connect = AutoCtrl.on_connect
        self.mqclient.on_message = AutoCtrl.on_message
        self.mqclient.on_disconnect = AutoCtrl.on_disconnect
        self.mqclient.connect(host, port)
        self.mqclient.subscribe([
            (INUITHY_TOPIC_HEARTBEAT, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION, self.tcfg.mqtt_qos),
        ])
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_HEARTBEAT, AutoCtrl.on_topic_heartbeat)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_UNREGISTER, AutoCtrl.on_topic_unregister)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_STATUS, AutoCtrl.on_topic_status)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_REPORTWRITE, AutoCtrl.on_topic_reportwrite)
        self.mqclient.message_callback_add(\
            INUITHY_TOPIC_NOTIFICATION, AutoCtrl.on_topic_notification)

    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        CtrlBase.__init__(self, inuithy_cfgpath, traffic_cfgpath, lgr, delay)
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging

    def start(self):
        """Start controller routine"""
        if not AutoCtrl.initialized:
            self.lgr.error(to_string("AutoCtrl not initialized"))
            return
        try:
            self.lgr.info(to_string("Expected Agents({}): {}",\
                len(self.expected_agents), self.expected_agents))
            if self._traffic_timer is not None:
                self._traffic_timer.start()
            if self.worker is not None:
                self.worker.start()
            stop_agents(self.mqclient)
            self.alive_notification()
            self._mqclient.loop_forever()
        except KeyboardInterrupt:
            self.lgr.info(to_string("AutoCtrl received keyboard interrupt"))
            if self.traffic_state is not None:
                self.traffic_state.traf_running = False
                self.traffic_state.chk.set_all()
        except NameError as ex:
            self.lgr.error(to_string("NameError: {}", ex))
            if self.traffic_state is not None:
                self.traffic_state.traf_running = False
                self.traffic_state.chk.set_all()
            raise
        except Exception as ex:
            self.lgr.error(to_string("Exception on AutoCtrl: {}", ex))
#        self.teardown()
        self.lgr.info(to_string("AutoCtrl terminated"))

def start_controller(tcfg, trcfg, lgr=None):
    """Shortcut to start controller"""
    controller = AutoCtrl(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyAutoCtrl')
    lgr.info(to_string(INUITHY_TITLE, INUITHY_VERSION, "AutoCtrl"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

