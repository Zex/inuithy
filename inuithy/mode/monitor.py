""" MoniCtrl application main thread
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import __version__
from inuithy.common.predef import TT_HEARTBEAT, TT_STATUS, _l,\
TT_REPORTWRITE, TT_NOTIFICATION, TT_UNREGISTER, TT_SNIFFER,\
TRAFFIC_CONFIG_PATH, INUITHY_CONFIG_PATH, INUITHY_TITLE,\
_s, T_CLIENTID, T_HOST, T_NODES, T_VERSION
from inuithy.common.runtime import Runtime as rt
from inuithy.mode.base import CtrlBase
from inuithy.util.cmd_helper import pub_enable_hb, pub_disable_hb,\
extract_payload, subscribe
import paho.mqtt.client as mqtt
import time

class MoniCtrl(CtrlBase):
    """Controller in automatic mode
    """
    def create_mqtt_client(self, host, port):
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self.mqclient.on_connect = MoniCtrl.on_connect
        self.mqclient.on_message = MoniCtrl.on_message
        self.mqclient.on_disconnect = MoniCtrl.on_disconnect
        self.mqclient.connect(host, port)
        subscribe(self.mqclient, TT_HEARTBEAT, MoniCtrl.on_topic_heartbeat)
        subscribe(self.mqclient, TT_UNREGISTER, MoniCtrl.on_topic_unregister)
        subscribe(self.mqclient, TT_STATUS, MoniCtrl.on_topic_status)
        subscribe(self.mqclient, TT_REPORTWRITE, MoniCtrl.on_topic_reportwrite)
        subscribe(self.mqclient, TT_NOTIFICATION, MoniCtrl.on_topic_notification)
        subscribe(self.mqclient, TT_SNIFFER, MoniCtrl.on_topic_sniffer)

    def __init__(self, delay=4):
        CtrlBase.__init__(self, delay)

    @staticmethod
    def on_topic_heartbeat(client, userdata, message):
        """Heartbeat message format:
        """
        self = userdata
        _l.info(_s("On topic heartbeat"))
        data = extract_payload(message.payload)
        agentid, host, nodes, version = data.get(T_CLIENTID), data.get(T_HOST),\
                data.get(T_NODES), data.get(T_VERSION)
        try:
            _l.info(_s("On topic heartbeat: Agent Version {}", version))
            agentid = agentid.strip('\t\n ')
            self.add_agent(agentid, host, nodes)
#            self.traffic_state.check("is_agents_up")
            _l.info(_s("Found Agents({}): {}",\
                len(self.available_agents), self.available_agents))
            pub_enable_hb(self.mqclient, clientid=agentid)
        except Exception as ex:
            _l.error(_s("Exception on registering agent {}: {}", agentid, ex))

    def start(self):
        """Start controller routine"""
        if not MoniCtrl.initialized:
            _l.error(_s("MoniCtrl not initialized"))
            return
        try:
            if self.worker is not None:
                self.worker.start()
            self.alive_notification()
#            for agent in self.available_agents:
#                _l.debug(_s("Enable heartbeat on {}", agent))
#                pub_enable_hb(self.mqclient, clientid=agent.agentid)
            self._mqclient.loop_forever()
        except KeyboardInterrupt:
            _l.info(_s("MoniCtrl received keyboard interrupt"))
        except NameError as ex:
            _l.error(_s("ERR: {}", ex))
        except Exception as ex:
            _l.error(_s("Exception on MoniCtrl: {}", ex))
        pub_disable_hb(self.mqclient)
        self.teardown()
        _l.info(_s("MoniCtrl terminated"))

def start_controller(args=None):
    """Shortcut to start controller"""
    rt.handle_args(args)
    controller = MoniCtrl()
    controller.start()

if __name__ == '__main__':
    import logging
    _l = logging.getLogger('InuithyMoniCtrl')
    _l.info(_s(INUITHY_TITLE, __version__, "MoniCtrl"))
    start_controller()

