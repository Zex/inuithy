""" Command helper
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT, PROJECT_PATH
from inuithy.common.predef import T_CLIENTID, TT_COMMAND,\
T_CTRLCMD, CtrlCmd, TT_UNREGISTER, TT_STATUS, TT_SNIFFER,\
TT_NOTIFICATION, TT_REPORTWRITE, INUITHY_NOHUP_OUTPUT,\
TT_HEARTBEAT, TT_TRAFFIC, TT_NWLAYOUT, to_string, TT_REPLY
from inuithy.util.helper import runonremote
import paho.mqtt.client as mqtt
import json
import threading

#            newctrl
# Agent <------------------------ Controller
def pub_ctrlcmd(publisher, qos=0, data=None):
    """Publish control command
    """
    payload = json.dumps(data)
    publisher.publish(TT_COMMAND, payload, qos, False)

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

#             network layout
# Agent <------------------------ Controller
def pub_nwlayout(publisher, qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(TT_NWLAYOUT, payload, qos, False)

#             tsh command
# Agent <------------------------ Controller
def pub_tsh(publisher, qos=0, data=None):
    """Publish tsh message
    """
    payload = json.dumps(data)
    publisher.publish(TT_TSH, payload, qos, False)

#         reply to tsh command
# Agent -------------------------> Controller
def pub_reply(publisher, qos=0, data=None):
    """Publish reply message
    """
    payload = json.dumps(data)
    publisher.publish(TT_REPLY, payload, qos, False)

#            traffic
# Agent <------------------------ Controller
def pub_traffic(publisher, qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(TT_TRAFFIC, payload, qos, False)

def pub_sniffer(publisher, qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(TT_SNIFFER, payload, qos, False)

#            config
# Agent <------------------------ Controller
def pub_config(publisher, qos, config=None, clientid="*"):
    """Publish configure message
    """
    # TODO
    payload = json.dumps(config)
    publisher.publish(TT_COMMAND, payload, qos, False)

#           unregister
# Agent ------------------> Controller
def pub_unregister(publisher, qos=0, clientid='*'):
    """Publish unregister message
    """
    payload = json.dumps({T_CLIENTID : clientid})
    publisher.publish(TT_UNREGISTER, payload, qos, False)

#           status
# Agent ------------------> Controller
def pub_status(publisher, qos=0, data=None):
    """Publish status message
    """
    payload = json.dumps(data)
    publisher.publish(TT_STATUS, payload, qos, False)

#           notification
# Agent ------------------> Controller
def pub_notification(publisher, qos=0, data=None):
    """Publish notification message
    """
    payload = json.dumps(data)
    publisher.publish(TT_NOTIFICATION, payload, qos, False)

#           response
# Agent ------------------> Controller
def pub_reportwrite(publisher, qos=0, data=None):
    """Publish report message written message
    """
    payload = json.dumps(data)
    publisher.publish(TT_REPORTWRITE, payload, qos, False)

#           heartbeat
# Agent ------------------> Controller
def pub_heartbeat(publisher, qos=0, data=None):
    """Publish heartbeat message
    """
    payload = json.dumps(data)
    publisher.publish(TT_HEARTBEAT, payload, qos, False)

class Heartbeat(threading.Thread):
    """Heartbeat generator
    """
    __mutex = threading.Lock()

    def __init__(self, interval=5, target=None, daemon=True, *args, **kwargs):
        threading.Thread.__init__(self, target=None, daemon=daemon, args=args, kwargs=kwargs)
        self.__interval = interval
        self.__running = False
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.done = threading.Event()

    def run(self):
        if self.__target is None:
            return # or self.__src is None: return
        self.__running = True

        while self.__running:
            with Heartbeat.__mutex:
#                pub_heartbeat(self.__publisher, qos=0, data=None):
                self.__target(*self.__args, **self.__kwargs)
            self.done.wait(self.__interval)
            self.done.clear()

    def stop(self):
        self.__running = False

    def __del__(self):
        self.stop()

def start_agents(hosts):
    """Start agent remotely"""
#    cmd = to_string('pushd {};nohup python {}/agent.py &>> {}',
#    cmd = to_string('pushd {} > /dev/null;> {};python {}/agent.py &>> {};exit',
#            PROJECT_PATH, '\"/var/log/inuithy/inuithy.log\"', INUITHY_ROOT, INUITHY_NOHUP_OUTPUT)
    cmd = to_string('pushd {} > /dev/null;python {}/agent.py &>> {};exit',
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
#    cmd = 'kill `ps aux|grep inuithy/agent.py|awk \'{print $2,\"@\"$11,$12}\'|grep @python|awk \'{printf \" \"$1}\'` &> /dev/null'
    cmd = 'kill `ps aux|grep \" python.*inuithy/agent.py\"|awk \'{printf \" \"$2}\'` &> /dev/null'
    [runonremote('root', host, cmd) for host in hosts]

def mqlog_map(lgr, level, msg):
    if level == mqtt.MQTT_LOG_INFO:
        lgr.info(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_ERR:
        lgr.error(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_NOTICE or level == mqtt.MQTT_LOG_WARNING:
        lgr.warning(INUITHY_MQLOG_FMT.format(msg))
    else: # level == mqtt.MQTT_LOG_DEBUG:
        lgr.debug(INUITHY_MQLOG_FMT.format(msg))
        pass

