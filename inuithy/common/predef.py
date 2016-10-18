## Common definition for inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
from common.version import *
import paho.mqtt.client as mqtt
from enum import Enum

INUITHY_MQTTMSGFMT = "dup:{}, info:{}, mid:{}, payload:[{}], qos:{}, retain:{}, state:{}, timestamp:{}, topic:[{}]"
INUITHY_TOPIC_COMMAND = "inuithy/topic/command"
INUITHY_TOPIC_STATUS = "inuithy/topic/status"
INUITHY_TOPIC_REGISTER = "inuithy/topic/register"
INUITHY_TOPIC_RESPONSE = "inuithy/topic/response"
# <topic id>::<message>
INUITHY_MQPAYLOAD_DELEMER = "::>"
INUITHY_MQPAYLOAD_FMT = "{}"+INUITHY_MQPAYLOAD_DELEMER+"{}"

INUITHYAGENT_MSGFMT = "INUITHYAGENT [{}]"
# Agent identity in MQ network: inuithy/agent/<host>"
INUITHYAGENT_CLIENT_ID = "inuithy/agent/{}"
#INUITHYAGENT_TOPIC_ID = "inuithy/agent/{}/topic/status"

INUITHYCONTROLLER_MSGFMT = "INUITHYCONTROLLER [{}]"
INUITHYCONTROLLER_CLIENT_ID = "inuithy/controller/{}"

INUITHY_LOGCONFIG = "config/logging.conf"
INUITHY_MQLOG_FMT = "MQ.Log: {}"

def mqlog_map(logger, level, msg):
    if level == mqtt.MQTT_LOG_INFO:
        logger.info(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_ERR:
        logger.error(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_NOTICE or level == mqtt.MQTT_LOG_WARNING:
        logger.warning(INUITHY_MQLOG_FMT.format(msg))
    else: # level == mqtt.MQTT_LOG_DEBUG:
        logger.debug(INUITHY_MQLOG_FMT.format(msg))

AgentStatus = Enum("AgentStatus", [
    "OFFLINE",
    "ONLINE",
    "UNKNOWN",
    ])

class AgentInfo:
    def __init__(self, agentid="", status=AgentStatus.OFFLINE):
        self.agentid = agentid
        self.status = status

    def __str__(self):
        return "agent<{}>: status:{}".format(self.agentid, self.status)

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
    return INUITHY_MQPAYLOAD_FMT.format(agentid, msg)

WorkMode = Enum("WorkMode", [
    "AUTO",
    "MANUAL",
    "MONITOR",
    ])

    
