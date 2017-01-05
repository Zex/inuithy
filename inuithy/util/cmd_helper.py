""" Command helper
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT, PROJECT_PATH, INUITHY_AGENT_INTERPRETER
from inuithy.common.predef import T_CLIENTID, TT_CONFIG, TT_COMMAND, _l,\
T_CTRLCMD, CtrlCmd, TT_UNREGISTER, TT_STATUS, TT_SNIFFER,\
TT_NOTIFICATION, TT_REPORTWRITE, INUITHY_NOHUP_OUTPUT,\
TT_HEARTBEAT, TT_TRAFFIC, TT_NWLAYOUT, _s, TT_REPLY
from inuithy.util.helper import runonremote
import paho.mqtt.client as mqtt
import json
import threading

#            newctrl
# Agent <------------------------ Controller
def pub_ctrlcmd(publisher, target='all', qos=0, data=None):
    """Publish control command
    """
    payload = json.dumps(data)
    publisher.publish(_s(TT_COMMAND, target), payload, qos, False)

def extract_payload(jdata):
    """Extract data from payload
    """
    if isinstance(jdata, bytes):
        jdata = jdata.decode()
    return json.loads(jdata)

#            enable heartbeat
# Agent <------------------------ Controller
def pub_enable_hb(publisher, target='all', qos=0):
    """Publish disable heartbeat command
    """
    data = {
        T_CTRLCMD:  CtrlCmd.AGENT_ENABLE_HEARTBEAT.name,
    }
    pub_ctrlcmd(publisher, target, qos, data)

#            disable heartbeat
# Agent <------------------------ Controller
def pub_disable_hb(publisher, target='all', qos=0):
    """Publish disable heartbeat command
    """
    data = {
        T_CTRLCMD:  CtrlCmd.AGENT_DISABLE_HEARTBEAT.name,
    }
    pub_ctrlcmd(publisher, target, qos, data)

#             network layout
# Agent <------------------------ Controller
def pub_nwlayout(publisher, target='all', qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(_s(TT_NWLAYOUT, target), payload, qos, False)

#             tsh command
# Agent <------------------------ Controller
def pub_tsh(publisher, target='all', qos=0, data=None):
    """Publish tsh message
    """
    payload = json.dumps(data)
    publisher.publish(_s(TT_TSH, target), payload, qos, False)

#         reply to tsh command
# Agent -------------------------> Controller
def pub_reply(publisher, qos=0, data=None):
    """Publish reply message
    """
    payload = json.dumps(data)
    publisher.publish(TT_REPLY, payload, qos, False)

#            traffic
# Agent <------------------------ Controller
def pub_traffic(publisher, target='all', qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(_s(TT_TRAFFIC, target), payload, qos, False)

def pub_sniffer(publisher, qos=0, data=None):
    """Publish traffic message
    """
    payload = json.dumps(data)
    publisher.publish(TT_SNIFFER, payload, qos, False)

#            config
# Agent <------------------------ Controller
def pub_config(publisher, target='all', qos=0, config=None):
    """Publish configure message
    """
    # TODO
    payload = json.dumps(config)
    publisher.publish(_s(TT_CONFIG, target), payload, qos, False)

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
#    cmd = _s('pushd {};nohup python {}/agent.py &>> {}',
#    cmd = _s('pushd {} > /dev/null;> {};python {}/agent.py &>> {};exit',
#            PROJECT_PATH, '\"/var/log/inuithy/inuithy.log\"', INUITHY_ROOT, INUITHY_NOHUP_OUTPUT)
    cmd = _s('pushd {} > /dev/null;{} {}/agent.py &>> {};exit',
            PROJECT_PATH, INUITHY_AGENT_INTERPRETER, INUITHY_ROOT, INUITHY_NOHUP_OUTPUT)
    [runonremote('root', host, cmd) for host in hosts]

def stop_agents(publisher, target='all', qos=0):
    """Stop agent remotely"""
    data = {
        T_CTRLCMD: CtrlCmd.AGENT_STOP.name,
    }
    pub_ctrlcmd(publisher, target, qos, data)

def force_stop_agents(hosts):
    """Force agent stop remotely"""
#    cmd = 'kill `ps aux|grep inuithy/agent.py|awk \'{print $2,\"@\"$11,$12}\'|grep @python|awk \'{printf \" \"$1}\'` &> /dev/null'
    cmd = _s('kill `ps aux|grep \" {}.*inuithy/agent.py\"|awk \'{printf \" \"$2}\'` &> /dev/null', INUITHY_AGENT_INTERPRETER)
    [runonremote('root', host, cmd) for host in hosts]

def mqlog_map(level, msg):
    if level == mqtt.MQTT_LOG_INFO:
        _l.info(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_ERR:
        _l.error(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_NOTICE or level == mqtt.MQTT_LOG_WARNING:
        _l.warning(INUITHY_MQLOG_FMT.format(msg))
    else: # level == mqtt.MQTT_LOG_DEBUG:
        _l.debug(INUITHY_MQLOG_FMT.format(msg))
        pass

def subscribe(client, topic, callback=None, qos=0):
    if topic is None or len(topic) == 0:
        return
    client.subscribe(topic, qos)
    if callback:
        client.message_callback_add(topic, callback)

