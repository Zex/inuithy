## Command helper
# Author: Zex Li <top_zlynch@yahoo.com>
#
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
    payload = string_write("{} {}", CtrlCmd.AGENT_ENABLE_HEARTBEAT.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#            disable heartbeat
# Agent <------------------------ Controller
def pub_disable_hb(publisher, qos, clientid="*"):
    payload = string_write("{} {}", CtrlCmd.AGENT_DISABLE_HEARTBEAT.name, clientid)
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
    payload = json.dumps(config)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#           unregister
# Agent ------------------> Controller
def pub_unregister(publisher, qos=0, clientid=''):
    payload = json.dumps({ CFGKW_CLIENTID : clientid })
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

def start_agents(agents):
    cmd = string_write('"pushd {};nohup python3 {}/agent.py"', PROJECT_PATH, INUITHY_ROOT)
    [runonremote('root', host, cmd) for host in agents]

def stop_agents(publisher, qos=0, clientid="*"):
    data = {
        CFGKW_CTRLCMD:  CtrlCmd.AGENT_STOP.name,
        CFGKW_CLIENTID: clientid,
    }
    pub_ctrlcmd(publisher, qos, data)

