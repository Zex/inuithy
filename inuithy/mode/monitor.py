""" MoniCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import TT_HEARTBEAT, TT_STATUS,\
TT_REPORTWRITE, TT_NOTIFICATION, TT_UNREGISTER,\
TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE, INUITHY_LOGCONFIG,\
to_string, T_CLIENTID, T_HOST, T_NODES, T_VERSION
from inuithy.common.runtime import Runtime as rt
from inuithy.mode.base import CtrlBase
from inuithy.util.cmd_helper import pub_enable_hb, pub_disable_hb,\
extract_payload
import paho.mqtt.client as mqtt
import logging
import logging.config as lconf
import time

lconf.fileConfig(INUITHY_LOGCONFIG)

class MoniCtrl(CtrlBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self.mqclient.on_connect = MoniCtrl.on_connect
        self.mqclient.on_message = MoniCtrl.on_message
        self.mqclient.on_disconnect = MoniCtrl.on_disconnect
        self.mqclient.connect(host, port)
        self.mqclient.subscribe([
            (TT_HEARTBEAT, rt.tcfg.mqtt_qos),
            (TT_UNREGISTER, rt.tcfg.mqtt_qos),
            (TT_STATUS, rt.tcfg.mqtt_qos),
            (TT_REPORTWRITE, rt.tcfg.mqtt_qos),
            (TT_NOTIFICATION, rt.tcfg.mqtt_qos),
        ])
        self.mqclient.message_callback_add(TT_HEARTBEAT, MoniCtrl.on_topic_heartbeat)
        self.mqclient.message_callback_add(TT_UNREGISTER, MoniCtrl.on_topic_unregister)
        self.mqclient.message_callback_add(TT_STATUS, MoniCtrl.on_topic_status)
        self.mqclient.message_callback_add(TT_REPORTWRITE, MoniCtrl.on_topic_reportwrite)
        self.mqclient.message_callback_add(TT_NOTIFICATION, MoniCtrl.on_topic_notification)

    def __init__(self, lgr=None, delay=4):
        CtrlBase.__init__(self, lgr, delay)
        self.lgr = lgr is None and logging or lgr

    @staticmethod
    def on_topic_heartbeat(client, userdata, message):
        """Heartbeat message format:
        """
        self = userdata
        self.lgr.info(to_string("On topic heartbeat"))
        data = extract_payload(message.payload)
        agentid, host, nodes, version = data.get(T_CLIENTID), data.get(T_HOST),\
                data.get(T_NODES), data.get(T_VERSION)
        try:
            self.lgr.info(to_string("On topic heartbeat: Agent Version {}", version))
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
#            self.traffic_state.check("is_agents_up")
            self.lgr.info(to_string("Found Agents({}): {}",\
                len(self.available_agents), self.available_agents))
            pub_enable_hb(self.mqclient, clientid=agentid)
        except Exception as ex:
            self.lgr.error(to_string("Exception on registering agent {}: {}", agentid, ex))

    def start(self):
        """Start controller routine"""
        if not MoniCtrl.initialized:
            self.lgr.error(to_string("MoniCtrl not initialized"))
            return
        try:
#            if self._traffic_timer is not None:
#                self._traffic_timer.start()
            if self.worker is not None:
                self.worker.start()
            self.alive_notification()
#            for agent in self.available_agents:
#                self.lgr.debug(to_string("Enable heartbeat on {}", agent))
#                pub_enable_hb(self.mqclient, clientid=agent.agentid)
            self._mqclient.loop_forever()
        except KeyboardInterrupt:
            self.lgr.info(to_string("MoniCtrl received keyboard interrupt"))
        except NameError as ex:
            self.lgr.error(to_string("ERR: {}", ex))
        except Exception as ex:
            self.lgr.error(to_string("Exception on MoniCtrl: {}", ex))
        pub_disable_hb(self.mqclient)
        self.teardown()
        self.lgr.info(to_string("MoniCtrl terminated"))

def start_controller(args=None, lgr=None):
    """Shortcut to start controller"""
    rt.handle_args(args)
    controller = MoniCtrl(lgr)
    controller.start()

if __name__ == '__main__':
    lgr = logging.getLogger('InuithyMoniCtrl')
    lgr.info(to_string(INUITHY_TITLE, __version__, "MoniCtrl"))
    start_controller(lgr=lgr)

