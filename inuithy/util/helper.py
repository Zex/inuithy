## Node under test definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import serial, glob
from inuithy.common.predef import *
from inuithy.common.node import *
from inuithy.util.task_manager import *


def string_write(fmt, *params):
    if params == None or len(params) == 0:
        return(fmt)
    return fmt.format(*params)

def console_write(fmt, *params):
    if params == None or len(params) == 0:
        print(string_write(fmt))
        return
    print(string_write(fmt, params))

def agent_id_from_payload(msg):
    msgitems = msg.split(INUITHY_MQPAYLOAD_DELEMER)
    if 0 < len(msgitems):
        return msgitems[0]
    return ""

def message_from_payload(msg):
    msgitems = msg.split(INUITHY_MQPAYLOAD_DELEMER)
    if 1 < len(msgitems):
        return msgitems[1]
    return ""

def create_payload(agentid, msg=""):
    return string_write(INUITHY_MQPAYLOAD_FMT, agentid, msg)

def valid_cmds(command):
    command = command.strip()
    return [c for c in command.split(' ') if len(c) != 0]

#            newctrl
# Agent <----------------- Controller
def pub_newctrl(publisher, qos, clientid):
    payload = string_write("{} {}", CtrlCmds.NEW_CONTROLLER.name, clientid)
    publisher.publish(INUITHY_TOPIC_COMMAND, payload, qos, False)

#           register
# Agent ------------------> Controller
def pub_register(publisher, qos, clientid, nodes=[]):
    payload = string_write("{} {}", clientid, ' '.join([str(node) for node in nodes]))
    publisher.publish(INUITHY_TOPIC_REGISTER, payload, qos, False)

#           unregister
# Agent ------------------> Controller
def pub_unregister(publisher, qos, clientid):
    payload = string_write("{}", clientid)
    publisher.publish(INUITHY_TOPIC_UNREGISTER, payload, qos, False)



