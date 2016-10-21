## Common definition for inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.version import *
import paho.mqtt.client as mqtt
from enum import Enum

INUITHY_MQTTMSGFMT = "dup:{}, info:{}, mid:{}, payload:[{}], qos:{}, retain:{}, state:{}, timestamp:{}, topic:[{}]"
# Controller => Agents
INUITHY_TOPIC_COMMAND = "inuithy/topic/command"
# Agents => Controller
INUITHY_TOPIC_STATUS = "inuithy/topic/status"
INUITHY_TOPIC_RESPONSE = "inuithy/topic/response"
INUITHY_TOPIC_REGISTER = "inuithy/topic/register"
INUITHY_TOPIC_UNREGISTER = "inuithy/topic/unregister"
INUITHY_TOPIC_NOTIFICATION = "inuithy/topic/notification"
# <topic id>::<message>
INUITHY_MQPAYLOAD_DELEMER = "::>"
INUITHY_MQPAYLOAD_FMT = "{}"+INUITHY_MQPAYLOAD_DELEMER+"{}"

INUITHYAGENT_MSGFMT = "INUITHYAGENT [{}]"
# Agent identity in MQ network: inuithy/agent/<host>"
INUITHYAGENT_CLIENT_ID = "inuithy/agent/{}"
#INUITHYAGENT_TOPIC_ID = "inuithy/agent/{}/topic/status"

INUITHYCONTROLLER_MSGFMT      = "INUITHYCONTROLLER [{}]"
INUITHYCONTROLLER_CLIENT_ID   = "inuithy/controller/{}"

# command message from Controller to Agents
# <command> <parameters>
INUITHY_CTRL_CMD       = "{} {}"

INUITHY_ROOT          = "inuithy"
INUITHY_LOGCONFIG     = INUITHY_ROOT+"/config/logging.conf"
INUITHY_CONFIG_PATH   = INUITHY_ROOT+"/config/inuithy_config.yaml"
INUITHY_MQLOG_FMT     = "MQ.Log: {}"
# Inuithy ver <version> <component>
INUITHY_TITLE         = "Inuithy version {} {}"

DEV_TTYUSB          = '/dev/ttyUSB{}'
DEV_TTYS            = '/dev/ttyS{}'

def mqlog_map(logger, level, msg):
    if level == mqtt.MQTT_LOG_INFO:
        logger.info(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_ERR:
        logger.error(INUITHY_MQLOG_FMT.format(msg))
    elif level == mqtt.MQTT_LOG_NOTICE or level == mqtt.MQTT_LOG_WARNING:
        logger.warning(INUITHY_MQLOG_FMT.format(msg))
    else: # level == mqtt.MQTT_LOG_DEBUG:
        #logger.debug(INUITHY_MQLOG_FMT.format(msg))
        pass

AgentStatus = Enum("AgentStatus", [
    "OFFLINE",
    "ONLINE",
    "UNKNOWN",
    ])


WorkMode = Enum("WorkMode", [
    "AUTO",
    "MANUAL",
    "MONITOR",
    ])

TrafficStorage = Enum("TrafficStorage", [
    "DB",      # Database
    "FILE",    # Local file
    ])

CtrlCmds = Enum("CtrlCmds", [
    "NEW_CONTROLLER",
    "AGENT_RESTART",
    "AGENT_STOP",
    "AGENT_ENABLE_HEARTBEAT",
    "AGENT_DISABLE_HEARTBEAT",
    "TRAFFIC",
])

class AgentInfo:
    def __init__(self, agentid="", status=AgentStatus.OFFLINE):
        self.agentid = agentid
        self.status = status

    def __str__(self):
        return string_write("agent<{}>: status:{}", self.agentid, self.status)
    

