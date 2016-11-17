""" AutoController application main thread
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

class AutoController(ControllerBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.on_connect = AutoController.on_connect
        self._mqclient.on_message = AutoController.on_message
        self._mqclient.on_disconnect = AutoController.on_disconnect
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
        if lgr is not None:
            self.lgr = lgr
        else:
            self.lgr = logging

    def start(self):
        """Start controller routine"""
        if not AutoController.initialized:
            self.lgr.error(string_write("AutoController not initialized"))
            return
        try:
            self.lgr.info(string_write("Expected Agents({}): {}",\
                len(self.chk.expected_agents), self.chk.expected_agents))
            self._alive_notification()
            if self._traffic_timer is not None:
                self._traffic_timer.start()
            self._mqclient.loop_forever()
        except KeyboardInterrupt:
            self.lgr.info(string_write("AutoController received keyboard interrupt"))
        except NameError as ex:
            self.lgr.error(string_write("ERR: {}", ex))
        except Exception as ex:
            self.lgr.error(string_write("Exception on AutoController: {}", ex))
        self.teardown()
        self.lgr.info(string_write("AutoController terminated"))

    def teardown(self):
        """Cleanup"""
        try:
            if AutoController.initialized:
                AutoController.initialized = False
                self.lgr.info("Stop agents")
                stop_agents(self._mqclient, self.tcfg.mqtt_qos)
                if self._traffic_state:
                    self._traffic_state.running = False
                if self._traffic_timer:
                    self._traffic_timer.cancel()
                if self.storage:
                    self.storage.close()
                time.sleep(self.shutdown_delay)
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
        if data.get(T_TRAFFIC_STATUS) == TrafficStatus.REGISTERED.name:
            self.lgr.info(string_write("Traffic {} registered on {}",\
                data.get(T_TID), data.get(T_CLIENTID)))
            self.chk.traffic_stat[data.get(T_TID)] = TrafficStatus.REGISTERED
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.RUNNING.name:
            self.lgr.info(string_write("Traffic {} fired on {}",\
                data.get(T_TID), data.get(T_CLIENTID)))
            self.chk.traffic_stat[data.get(T_TID)] = TrafficStatus.RUNNING
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.FINISHED.name:
            self.lgr.info(string_write("Traffic {} finished", data.get(T_TID)))
            self.chk.traffic_stat[data.get(T_TID)] = TrafficStatus.FINISHED
        elif data.get(T_TRAFFIC_STATUS) == TrafficStatus.INITFAILED.name:
            self.lgr.error(string_write("Agent {} failed to initialize: {}",\
                data.get(T_CLIENTID), data.get(T_MSG)))
            self.teardown()
        elif data.get(T_MSG) is not None:
            self.lgr.info(data.get(T_MSG))
        else:
            self.lgr.debug(string_write("Unhandled status message {}", data))

    def on_topic_reportwrite(self, message):
        """Report-written topic handler"""
#        self.lgr.info(string_write("On topic reportwrite"))
        data = extract_payload(message.payload)
        try:
            if data.get(T_TRAFFIC_TYPE) == TrafficType.JOIN.name:
                self.lgr.info(string_write("JOINING: {}", data.get(T_NODE)))
            elif data.get(T_TRAFFIC_TYPE) == TrafficType.SCMD.name:
            # Record traffic only
                self.lgr.debug(string_write("REPORT: {}", data))
                if data.get(T_MSG_TYPE) == MessageType.SEND.name and data.get(T_NODE) is not None:
                    self.storage.insert_record(data)
        except Exception as ex:
            self.lgr.error(string_write("Failed to handle report write message: {}", ex))
            self.teardown()

    def on_topic_notification(self, message):
        """Report-read topic handler"""
#       self.lgr.info(string_write("On topic notification"))
        data = extract_payload(message.payload)
        try:
            self.lgr.debug(string_write("NOTIFY: {}", data))
            if data.get(T_TRAFFIC_TYPE) == TrafficType.JOIN.name:
#                if self.chk.nwlayout.get(data.get(T_PANID)) is not None:
#                    self.chk.nwlayout[data.get(T_PANID)][data.get(T_NODE)] = True
                if self.chk.nwlayout.get(data.get(T_NODE)) is not None:
                    self.chk.nwlayout[data.get(T_NODE)] = True
            elif data.get(T_TRAFFIC_TYPE) == TrafficType.SCMD.name:
            # Record traffic only
                if data.get(T_MSG_TYPE) == MessageType.RECV.name and data.get(T_NODE) is not None:
                    self.storage.insert_record(data)
            else:
                self.storage.insert_record(data)
        except Exception as ex:
            self.lgr.error(string_write("Failed to handle notification message: {}", ex))
            self.teardown()

def start_controller(tcfg, trcfg, lgr=None):
    """Shortcut to start controller"""
    controller = AutoController(tcfg, trcfg, lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyAutoController')
    lgr.info(string_write(INUITHY_TITLE, INUITHY_VERSION, "AutoController"))
    start_controller(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, lgr)

