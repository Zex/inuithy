## Common definition for inuithy
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.version import *
import paho.mqtt.client as mqtt
from enum import Enum

INUITHY_MQTTMSGFMT = "dup:{}, info:{}, mid:{}, payload:[{}], qos:{}, retain:{}, state:{}, timestamp:{}, topic:[{}]"
# Controller => Agents
# Command for agents
INUITHY_TOPIC_COMMAND     = "inuithy/topic/command"
# Configuration for agents
INUITHY_TOPIC_CONFIG      = "inuithy/topic/config"
# Traffc data to send via serial port on agent
INUITHY_TOPIC_TRAFFIC     = "inuithy/topic/traffic"
# Agents => Controller
# Register agent with connected nodes
INUITHY_TOPIC_REGISTER    = "inuithy/topic/register"
# Unregister agent
INUITHY_TOPIC_UNREGISTER  = "inuithy/topic/unregister"
# Status of agent/nodes
INUITHY_TOPIC_STATUS      = "inuithy/topic/status"
# Report data wriited to serial port
INUITHY_TOPIC_REPORTWRITE  = "inuithy/topic/reportwrite"
# Report data read from serial port
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
NETWORK_CONFIG_PATH = INUITHY_ROOT+"/config/network_config.yaml"
TRAFFIC_CONFIG_PATH = INUITHY_ROOT+"/config/traffic_config.yaml"
INUITHY_MQLOG_FMT     = "MQ.Log: {}"
# Inuithy ver <version> <component>
INUITHY_TITLE         = "Inuithy version {} {}"

DEV_TTYUSB          = '/dev/ttyUSB{}'
DEV_TTYS            = '/dev/ttyS{}'

# Configure keywords
CFGKW_WORKMODE          = 'workmode'
CFGKW_MQTT              = 'mqtt'
CFGKW_HOST              = 'host'
CFGKW_PORT              = 'port'
CFGKW_QOS               = 'qos'
CFGKW_CONTROLLER        = 'controller'
CFGKW_AGENTS            = 'agents'
CFGKW_ENABLE_LDEBUG     = 'enable_localdebug'
CFGKW_ENABLE_MQDEBUG    = 'enable_mqdebug'
CFGKW_TRAFFIC_STORAGE   = 'traffic_storage'
CFGKW_TYPE              = 'type'
CFGKW_PATH              = 'path'
CFGKW_USER              = 'user'
CFGKW_PASSWD            = 'passwd'
CFGKW_TSH               = 'inuithy_shell'
CFGKW_HISTORY           = 'history'
CFGKW_SUBNET            = 'subnet'
CFGKW_NODES             = 'nodes'
CFGKW_GATEWAY           = 'gateway'
CFGKW_PKGSIZE           = 'pkgsize'
CFGKW_PKGRATE           = 'pkgrate'
CFGKW_RECIPIENTS        = 'recipients'
CFGKW_SENDERS           = 'senders'
CFGKW_SENDER            = 'sender'
CFGKW_RECIPIENT         = 'recipient'
CFGKW_DURATION          = 'duration'
CFGKW_TARGET_TRAFFICS   = 'target_traffics'
CFGKW_TARGET_AGENTS     = 'target_agents'
CFGKW_NWLAYOUT          = 'nwlayout'
CFGKW_NWCONFIG_PATH     = 'network_config'
CFGKW_NWLAYOUT_ID_FMT   = '{}:{}'
CFGKW_TRAFFICS          = 'traffics'
CFGKW_PANID             = 'panid'
CFGKW_CHANNEL           = 'channel'

CFGKW_CLIENTID          = 'clientid'
CFGKW_TRAFFIC_TYPE      = 'traffic_type'
CFGKW_NODE              = 'node'
CFGKW_ADDR              = 'addr'
CFGKW_MSG               = 'msg'

TrafficType = Enum("TrafficType", [
    "JOIN", # Join network
    "SCMD", # Serial command
    "UNKNOWN",
    ])

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
])

def string_write(fmt, *params):
    if params == None or len(params) == 0:
        return(fmt)
    return fmt.format(*params)

def console_write(fmt, *params):
    if params == None or len(params) == 0:
        print(fmt)
        return
    print(fmt.format(*params))


