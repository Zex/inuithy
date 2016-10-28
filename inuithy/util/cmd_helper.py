## Command helper
# Author: Zex Li <top_zlynch@yahoo.com>
#
#from inuithy.util.helper import *
from inuithy.util.trigger import *
import json

#            newctrl
# Agent <------------------------ Controller
def pub_ctrlcmd(publisher, qos, data):
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

def extract_payload(jdata):
    if isinstance(jdata, bytes): jdata = jdata.decode()
    return json.loads(jdata)

#            enable heartbeat
# Agent <------------------------ Controller
def pub_enable_hb(publisher, qos, clientid="*"):
    payload = string_write("{} {}", CtrlCmds.AGENT_ENABLE_HEARTBEAT.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#            disable heartbeat
# Agent <------------------------ Controller
def pub_disable_hb(publisher, qos, clientid="*"):
    payload = string_write("{} {}", CtrlCmds.AGENT_DISABLE_HEARTBEAT.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#            restart agent
# Agent <------------------------ Controller
def pub_restart_agent(publisher, qos, clientid="*"):
    payload = string_write("{} {}", CtrlCmds.AGENT_RESTART.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#            stop agent
# Agent <------------------------ Controller
def pub_stop_agent(publisher, qos, clientid="*"):
    payload = string_write("{} {}", CtrlCmds.AGENT_STOP.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#            traffic
# Agent <------------------------ Controller
def pub_traffic(publisher, qos=0, data={}):
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_TRAFFIC, payload, qos, False)

#            config
# Agent <------------------------ Controller
def pub_config(publisher, qos, config={}, clientid="*"):
    # TODO
    payload = string_write("{} {}", CtrlCmds.TRAFFIC.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#           register
# Agent ------------------> Controller
def pub_register(publisher, qos=0, data={}):
    """
        data = {
            CFGKW_CLIENTID: self.clientid,
            CFGKW_HOST:     self.host,
            CFGKW_NODES:    [str(node) for node in self.__sad.nodes]
        }
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_REGISTER, payload, qos, False)

#           unregister
# Agent ------------------> Controller
def pub_unregister(publisher, qos=0, clientid=''):
    payload = string_write("{}", clientid)
    publisher.publish(INUITHY_TOPIC_UNREGISTER, payload, qos, False)

#           status
# Agent ------------------> Controller
def pub_status(publisher, qos=0, data={}):
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_STATUS, payload, qos, False)

#           notification
# Agent ------------------> Controller
def pub_notification(publisher, qos=0, data={}):
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_NOTIFICATION, payload, qos, False)

#           response
# Agent ------------------> Controller
def pub_reportwrite(publisher, qos=0, data={}):
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_REPORTWRITE, payload, qos, False)

#def extract_reportwrite(jpack):
#    s = json.loads(jpack)
#    return s[CFGKW_CLIENTID], s[CFGKW_HOST], s[CFGKW_NODES]

#           heartbeat
# Agent ------------------> Controller
def pub_heartbeat(publisher, qos=0, data={}):
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_HEARTBEAT, payload, qos, False)

class Heartbeat(threading.Thread):
    """Heartbeat generator
    """
    __mutex = threading.Lock()

    def __init__(self, interval=2, target=None, name="Heartbeat", daemon=True, *args, **kwargs):
        threading.Thread.__init__(self, target=None, name=name, args=args, kwargs=kwargs, daemon=daemon)
        self.__interval = interval    
        self.__running = False
        self.__args = args
        self.__kwargs = kwargs
        self.__target = target

    def run(self):
        if self.__target == None: return # or self.__sender == None: return
        self.__running = True

        while self.__running:
            if Heartbeat.__mutex.acquire():
                self.__target()
                Heartbeat.__mutex.release()
            time.sleep(self.__interval)

    def stop(self):
        self.__running = False

    def __del__(self):
        self.stop()

