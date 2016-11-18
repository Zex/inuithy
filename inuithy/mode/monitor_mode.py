""" MonitorController application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION
from inuithy.common.predef import T_CLIENTID, T_TRAFFIC_TYPE, T_PANID,\
T_NODE, T_HOST, T_NODES, INUITHY_TOPIC_HEARTBEAT, T_TID, T_MSG, T_SPANID,\
T_TRAFFIC_STATUS, TrafficStatus, TrafficType, string_write, MessageType,\
TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE, T_SRC,\
INUITHY_TOPIC_UNREGISTER, INUITHY_LOGCONFIG, T_DEST, T_MSG_TYPE,\
INUITHY_TOPIC_STATUS, INUITHY_TOPIC_REPORTWRITE, INUITHY_TOPIC_NOTIFICATION
from inuithy.mode.base import ControllerBase
from inuithy.util.cmd_helper import stop_agents, extract_payload
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time

lconf.fileConfig(INUITHY_LOGCONFIG)

class MonitorController(ControllerBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.on_connect = MonitorController.on_connect
        self._mqclient.on_message = MonitorController.on_message
        self._mqclient.on_disconnect = MonitorController.on_disconnect
        self._mqclient.connect(host, port)
        self._mqclient.subscribe([
            (INUITHY_TOPIC_HEARTBEAT, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_UNREGISTER, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_STATUS, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_REPORTWRITE, self.tcfg.mqtt_qos),
            (INUITHY_TOPIC_NOTIFICATION, self.tcfg.mqtt_qos),
        ])

    def register_routes(self):
        self.topic_routes = {
            INUITHY_TOPIC_HEARTBEAT:      self.on_topic_heartbeat,
            INUITHY_TOPIC_UNREGISTER:     self.on_topic_unregister,
            INUITHY_TOPIC_STATUS:         self.on_topic_status,
            INUITHY_TOPIC_REPORTWRITE:    self.on_topic_reportwrite,
            INUITHY_TOPIC_NOTIFICATION:   self.on_topic_notification,
        }

    def __init__(self, inuithy_cfgpath='config/inuithy.conf',\
        traffic_cfgpath='config/traffics.conf', lgr=None, delay=4):
        ControllerBase.__init__(self, inuithy_cfgpath, traffic_cfgpath, lgr, delay)
        self.lgr = lgr
        if lgr is None:
            self.lgr = logging

    def start(self):
        """Start controller routine"""
        if not MonitorController.initialized:
            self.lgr.error(string_write("MonitorController not initialized"))
            return
        try:
            self.lgr.info(string_write("Expected Agents({}): {}",\
                len(self.chk.expected_agents), self.chk.expected_agents))
#            if self._traffic_timer is not None:
#                self._traffic_timer.start()
            self.alive_notification()
            pub_enable_hb(self.mqclient)
            self._mqclient.loop_forever()
        except KeyboardInterrupt:
            self.lgr.info(string_write("MonitorController received keyboard interrupt"))
        except NameError as ex:
            self.lgr.error(string_write("ERR: {}", ex))
        except Exception as ex:
            self.lgr.error(string_write("Exception on MonitorController: {}", ex))
        self.teardown()
        self.lgr.info(string_write("MonitorController terminated"))

    def teardown(self):
        """Cleanup"""
        try:
            if MonitorController.initialized:
                MonitorController.initialized = False
                pub_disable_hb(self.mqclient)
                self.lgr.info("Stop agents")
                stop_agents(self._mqclient, self.tcfg.mqtt_qos)
                if self.traffic_state:
                    self.traffic_state.running = False
                if self._traffic_timer:
                    self._traffic_timer.cancel()
                if self.storage:
                    self.storage.close()
                if self.mqclient:
                    self.mqclient.disconnect()
        except Exception as ex:
            self.lgr.error(string_write("Exception on teardown: {}", ex))

    def on_topic_heartbeat(self, message):
        """Heartbeat message format:
        """
        self.lgr.info(string_write("On topic heartbeat"))
        data = extract_payload(message.payload)
        agentid, host, nodes = data[T_CLIENTID], data[T_HOST], data[T_NODES]
        try:
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
        except Exception as ex:
            self.lgr.error(string_write("Exception on registering agent {}: {}", agentid, ex))

    def on_topic_unregister(self, message):
        """Unregister message format:
        <agentid>
        """
        self.lgr.info(string_write("On topic unregister"))
        data = extract_payload(message.payload)
        agentid = data[T_CLIENTID]
        try:
            self.del_agent(agentid)
            self.lgr.info(string_write("Available Agents({}): {}",\
                len(self.chk.available_agents), self.chk.available_agents))
        except Exception as ex:
            self.lgr.error(string_write("Exception on unregistering agent {}: {}", agentid, ex))

    def on_topic_status(self, message):
        """Status topic handler"""
        self.lgr.info(string_write("On topic status"))
        data = extract_payload(message.payload)
        self.lgr.info(string_write("STATUS: {}", data))

    def on_topic_reportwrite(self, message):
        """Report-written topic handler"""
        self.lgr.info(string_write("On topic reportwrite"))
        data = extract_payload(message.payload)
        self.lgr.info(string_write("REPORT: {}", data))

    def on_topic_notification(self, message):
        """Report-read topic handler"""
        self.lgr.info(string_write("On topic notification"))
        data = extract_payload(message.payload)
        self.lgr.info(string_write("NOTIFY: {}", data))

def start_controller(tcfg, trcfg, lgr=None):
    """Shortcut to start controller"""
    controller = MonitorController(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyMonitorController')
    lgr.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "MonitorController"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

