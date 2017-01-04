""" AutoCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import TT_HEARTBEAT, TT_STATUS,\
TT_REPORTWRITE, TT_NOTIFICATION, TT_UNREGISTER, TT_SNIFFER,\
INUITHY_TITLE, INUITHY_LOGCONFIG, to_string, to_console
from inuithy.mode.base import CtrlBase
from inuithy.util.cmd_helper import stop_agents, subscribe
from inuithy.common.runtime import Runtime as rt
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
        subscribe(self.mqclient, TT_HEARTBEAT, AutoCtrl.on_topic_heartbeat, rt.tcfg.mqtt_qos)
        subscribe(self.mqclient, TT_UNREGISTER, AutoCtrl.on_topic_unregister, rt.tcfg.mqtt_qos)
        subscribe(self.mqclient, TT_STATUS, AutoCtrl.on_topic_status, rt.tcfg.mqtt_qos)
        subscribe(self.mqclient, TT_REPORTWRITE, AutoCtrl.on_topic_reportwrite, rt.tcfg.mqtt_qos)
        subscribe(self.mqclient, TT_NOTIFICATION, AutoCtrl.on_topic_notification, rt.tcfg.mqtt_qos)
        subscribe(self.mqclient, TT_SNIFFER, AutoCtrl.on_topic_sniffer, rt.tcfg.mqtt_qos)

    def __init__(self, lgr=None, delay=4):
        CtrlBase.__init__(self, lgr, delay)
        self.lgr = lgr is None and logging or lgr

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
#            self.teardown()
            if len(self.traffic_state.chk.available_agents) > 0:
                self.lgr.info("Wait for last notifications")
                self.traffic_state.chk._is_agents_unregistered.wait()#T_TRAFFIC_FINISH_DELAY)
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
        to_console(to_string("AutoCtrl terminated"))

def start_controller(args=None, lgr=None):
    """Shortcut to start controller"""
    rt.handle_args(args)
    controller = AutoCtrl(lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyAutoCtrl')
    lgr.info(to_string(INUITHY_TITLE, __version__, "AutoCtrl"))
    start_controller(lgr=lgr)

