""" ManualController application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import T_CLIENTID, T_TRAFFIC_TYPE, T_PANID,\
T_NODE, T_HOST, T_NODES, INUITHY_TOPIC_HEARTBEAT, T_TID, T_MSG, T_SPANID,\
T_TRAFFIC_STATUS, TrafficStatus, TrafficType, to_string, to_console,\
MessageType, TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE, T_SRC,\
INUITHY_TOPIC_UNREGISTER, INUITHY_LOGCONFIG, T_DEST, T_MSG_TYPE, T_VERSION,\
INUITHY_TOPIC_STATUS, INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION
from inuithy.mode.base import ControllerBase
from inuithy.util.cmd_helper import stop_agents, extract_payload
from inuithy.util.console import start_console
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time

lconf.fileConfig(INUITHY_LOGCONFIG)

class ManualController(ControllerBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.on_connect = ManualController.on_connect
        self._mqclient.on_message = ManualController.on_message
        self._mqclient.on_disconnect = ManualController.on_disconnect
        self._mqclient.connect(host, port)
        self._mqclient.subscribe([
            (INUITHY_TOPIC_HEARTBEAT, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION, self.tcfg.mqtt_qos),
        ])

    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        ControllerBase.__init__(self, inuithy_cfgpath, traffic_cfgpath, lgr, delay)
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging

    def start(self):
        """Start controller routine"""
        if not ManualController.initialized:
            self.lgr.error(to_string("ManualController not initialized"))
            return
        try:
            self.lgr.info(to_string("Expected Agents({}): {}",\
                len(self.expected_agents), self.expected_agents))
#            if self._traffic_timer is not None:
#                self._traffic_timer.start()
            self.alive_notification()
#            self._mqclient.loop_forever()
            ret = mqtt.MQTT_ERR_SUCCESS
            for retry_cnt in range(1, 4):
                ret = self.mqclient.loop_start()
                if ret == mqtt.MQTT_ERR_SUCCESS:
                    break
                self.mqclient.loop_stop()
                self.lgr.warning(to_string('Retry [{}] ...', retry_cnt))
            if ret != mqtt.MQTT_ERR_SUCCESS:
                raise Exception("Start MQTT loop failed")

            start_console(self)
            self.mqclient.loop_stop()
        except KeyboardInterrupt:
            self.lgr.info(to_string("ManualController received keyboard interrupt"))
        except NameError as ex:
            self.lgr.error(to_string("ERR: {}", ex))
        except Exception as ex:
            self.lgr.error(to_string("Exception on ManualController: {}", ex))
        self.teardown()
        self.lgr.info(to_string("ManualController terminated"))

def start_controller(tcfg, trcfg, lgr=None):
    """Shortcut to start controller"""
    controller = ManualController(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyManualController')
    lgr.info(to_string(INUITHY_TITLE, INUITHY_VERSION, "ManualController"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

