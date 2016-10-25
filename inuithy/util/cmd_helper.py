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
def pub_traffic(publisher, qos, data, clientid="*"):
    # TODO
    payload = string_write("{} {}", clientid, clientid)
    publisher.publish(INUITHY_TOPIC_TRAFFIC, payload, qos, False)

#            config
# Agent <------------------------ Controller
def pub_config(publisher, qos, config={}, clientid="*"):
    # TODO
    payload = string_write("{} {}", CtrlCmds.TRAFFIC.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#           register
# Agent ------------------> Controller
def pub_register(publisher, qos, clientid, nodes=[]):
    payload = json.dumps({
        CFGKW_CLIENTID: clientid,
        CFGKW_NODES:    [str(node) for node in nodes]
    })
    publisher.publish(INUITHY_TOPIC_REGISTER, payload, qos, False)

def extract_register(jpack):
    s = json.loads(jpack)
    return s[CFGKW_CLIENTID], s[CFGKW_NODES]

#           unregister
# Agent ------------------> Controller
def pub_unregister(publisher, qos, clientid):
    payload = string_write("{}", clientid)
    publisher.publish(INUITHY_TOPIC_UNREGISTER, payload, qos, False)

#           status
# Agent ------------------> Controller
def pub_status(publisher, qos, clientid, data):
    payload = string_write("{} {}", clientid, data)
    publisher.publish(INUITHY_TOPIC_STATUS, payload, qos, False)

#           notification
# Agent ------------------> Controller
def pub_notification(publisher, qos, clientid, data):
    payload = string_write("{} {}", clientid, data)
    publisher.publish(INUITHY_TOPIC_NOTIFICATION, payload, qos, False)

#           response
# Agent ------------------> Controller
def pub_response(publisher, qos, clientid, data):
    payload = string_write("{} {}", clientid, data)
    publisher.publish(INUITHY_TOPIC_RESPONSE, payload, qos, False)

