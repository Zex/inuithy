## Command helper
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.util.helper import *
import json

#            newctrl
# Agent <------------------------ Controller
def pub_newctrl(publisher, qos, clientid):
    payload = string_write("{} {}", CtrlCmds.NEW_CONTROLLER.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

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

def extract_traffic(jpack):
    """
    - Join network traffic
        channel: 15
        gateway: '1122'
        nodes: ['1111', '1112', '1113', '1114', '1122', '1123', '1124', '1134']
        panid: F5F5E6E617171515
        node: '1111'
        traffic_type: JOIN
    - Serial command traffic
        node: '1111'
        <parameters>
    """
    s = json.loads(jpack)
    return s

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

def extract_register(jpack):
    s = json.loads(jpack)
    return s[CFGKW_CLIENTID], s[CFGKW_HOST], s[CFGKW_NODES]

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

def extract_status(jpack):
    #TODO
    return json.loads(jpack)
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

def extract_reportwrite(jpack):
    s = json.loads(jpack)
    return s[CFGKW_CLIENTID], s[CFGKW_HOST], s[CFGKW_NODES]

