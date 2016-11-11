""" Command helper
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT, PROJECT_PATH
from inuithy.common.predef import T_CLIENTID, INUITHY_TOPIC_COMMAND,\
T_CTRLCMD, CtrlCmd, INUITHY_TOPIC_UNREGISTER, INUITHY_TOPIC_STATUS,\
INUITHY_TOPIC_NOTIFICATION, INUITHY_TOPIC_REPORTWRITE, INUITHY_NOHUP_OUTPUT,\
INUITHY_TOPIC_HEARTBEAT, INUITHY_TOPIC_TRAFFIC, string_write
from inuithy.util.helper import runonremote
import json
import threading

#            newctrl
# Agent <------------------------ Controller
def pub_ctrlcmd(publisher, qos, data):
    """Publish control command
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

def extract_payload(jdata):
    """Extract data from payload
    """
    if isinstance(jdata, bytes):
        jdata = jdata.decode()
    return json.loads(jdata)

#            enable heartbeat
# Agent <------------------------ Controller
def pub_enable_hb(publisher, qos=0, clientid="*"):
    """Publish disable heartbeat command
    """
    data = {
        T_CTRLCMD:  CtrlCmd.AGENT_ENABLE_HEARTBEAT.name,
        T_CLIENTID: clientid,
    }
    pub_ctrlcmd(publisher, qos, data)

#            disable heartbeat
# Agent <------------------------ Controller
def pub_disable_hb(publisher, qos=0, clientid="*"):
    """Publish disable heartbeat command
    """
    data = {
        T_CTRLCMD:  CtrlCmd.AGENT_DISABLE_HEARTBEAT.name,
        T_CLIENTID: clientid,
    }
    pub_ctrlcmd(publisher, qos, data)


#            traffic
# Agent <------------------------ Controller
def pub_traffic(publisher, qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_TRAFFIC, payload, qos, False)

#            config
# Agent <------------------------ Controller
def pub_config(publisher, qos, config=None, clientid="*"):
    """Publish configure message
    """
    # TODO
    payload = json.dumps(config)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#           unregister
# Agent ------------------> Controller
def pub_unregister(publisher, qos=0, clientid=''):
    """
    """
    payload = json.dumps({T_CLIENTID : clientid})
    publisher.publish(INUITHY_TOPIC_UNREGISTER, payload, qos, False)

#           status
# Agent ------------------> Controller
def pub_status(publisher, qos=0, data=None):
    """Publish status message
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_STATUS, payload, qos, False)

#           notification
# Agent ------------------> Controller
def pub_notification(publisher, qos=0, data=None):
    """Publish notification message
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_NOTIFICATION, payload, qos, False)

#           response
# Agent ------------------> Controller
def pub_reportwrite(publisher, qos=0, data=None):
    """Publish report message written message
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_REPORTWRITE, payload, qos, False)

#           heartbeat
# Agent ------------------> Controller
def pub_heartbeat(publisher, qos=0, data=None):
    """Publish heartbeat message
    """
    payload = json.dumps(data)
    publisher.publish(INUITHY_TOPIC_HEARTBEAT, payload, qos, False)

class Heartbeat(threading.Thread):
    """Heartbeat generator
    """
    __mutex = threading.Lock()

    def __init__(self, interval=2, target=None, name="Heartbeat",\
        daemon=True, *args, **kwargs):
        threading.Thread.__init__(self, target=None, name=name,\
        args=args, kwargs=kwargs, daemon=daemon)
        self.__interval = interval
        self.__running = False
        self.__args = args
        self.__kwargs = kwargs
        self.__target = target

    def run(self):
        if self.__target is None:
            return # or self.__sender is None: return
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

def start_agents(hosts):
    """Start agent remotely"""
    cmd = string_write('pushd {};nohup python3 {}/agent.py &>> {}',\
        PROJECT_PATH, INUITHY_ROOT, INUITHY_NOHUP_OUTPUT)
    [runonremote('root', host, cmd) for host in hosts]

def stop_agents(publisher, qos=0, clientid="*"):
    """Stop agent remotely"""
    data = {
        T_CTRLCMD: CtrlCmd.AGENT_STOP.name,
        T_CLIENTID: clientid,
    }
    pub_ctrlcmd(publisher, qos, data)

def force_stop_agents(hosts):
    """Force agent stop remotely"""
    cmd = 'kill `ps aux|grep inuithy/agent.py|awk \'{print $2,\"@\"$11,$12}\'|grep @python|awk \'{printf \" \"$1}\'` &> /dev/null'
    [runonremote('root', host, cmd) for host in hosts]

