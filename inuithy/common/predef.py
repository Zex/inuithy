""" Common definition for inuithy
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_VERSION, INUITHY_ROOT
import paho.mqtt.client as mqtt
from enum import Enum

INUITHY_MQTTMSGFMT = "dup:{}, info:{}, mid:{}, payload:[{}], \
qos:{}, retain:{}, state:{}, timestamp:{}, topic:[{}]"
# Controller => Agents
# Command for agents
INUITHY_TOPIC_COMMAND = "inuithy/topic/command"
# Configuration for agents
INUITHY_TOPIC_CONFIG = "inuithy/topic/config"
# Traffc data to send via serial port on agent
INUITHY_TOPIC_TRAFFIC = "inuithy/topic/traffic"
# Agents => Controller
# Unregister agent
INUITHY_TOPIC_UNREGISTER = "inuithy/topic/unregister"
# Status of agent/nodes
INUITHY_TOPIC_STATUS = "inuithy/topic/status"
# Heartbeat from agent
INUITHY_TOPIC_HEARTBEAT = "inuithy/topic/heartbeat"
# Report data wriited to serial port
INUITHY_TOPIC_REPORTWRITE = "inuithy/topic/reportwrite"
# Report data read from serial port
INUITHY_TOPIC_NOTIFICATION = "inuithy/topic/notification"
# <topic id>::<message>
INUITHY_MQPAYLOAD_DELEMER = "::>"
INUITHY_MQPAYLOAD_FMT = "{}"+INUITHY_MQPAYLOAD_DELEMER+"{}"

INUITHYAGENT_MSGFMT = "INUITHYAGENT [{}]"
# Agent identity in MQ network: inuithy/agent/<host>"
INUITHYAGENT_CLIENT_ID = "inuithy/agent/{}"
#INUITHYAGENT_TOPIC_ID = "inuithy/agent/{}/topic/status"

INUITHYCONTROLLER_MSGFMT = "INUITHYCONTROLLER [{}]"
INUITHYCONTROLLER_CLIENT_ID = "inuithy/controller/{}"

# command message from Controller to Agents
# <command> <parameters>
INUITHY_CTRL_CMD = "{} {}"

INUITHY_NOHUP_OUTPUT = "/tmp/inuithy.nohup"
INUITHY_LOGCONFIG = INUITHY_ROOT+"/config/logging.conf"
INUITHY_CONFIG_PATH = INUITHY_ROOT+"/config/inuithy_config.yaml"
NETWORK_CONFIG_PATH = INUITHY_ROOT+"/config/network_config.yaml"
TRAFFIC_CONFIG_PATH = INUITHY_ROOT+"/config/traffic_config.yaml"
INUITHY_MQLOG_FMT = "MQ.Log: {}"
# Inuithy ver <version> <component>
INUITHY_TITLE = "Inuithy version {} {}"

DEV_TTYUSB = '/dev/ttyUSB{}'
DEV_TTYS = '/dev/ttyS{}'
DEV_TTY = '/dev/tty{}'

IFACEPATH = '/etc/network/interfaces'

# Configure keywords
T_WORKMODE = 'workmode'
T_MQTT = 'mqtt'
T_HOST = 'host'
T_PORT = 'port'
T_QOS = 'qos'
T_VERSION = 'version'
T_CONTROLLER = 'controller'
T_AGENTS = 'agents'
T_ENABLE_LDEBUG = 'enable_localdebug'
T_ENABLE_MQDEBUG = 'enable_mqdebug'
T_TRAFFIC_STORAGE = 'traffic_storage'
T_TYPE = 'type'
T_PATH = 'path'
T_USER = 'user'
T_PASSWD = 'passwd'
T_TSH = 'inuithy_shell'
T_HISTORY = 'history'
T_SUBNET = 'subnet'
T_NODES = 'nodes'
T_GATEWAY = 'gateway'
T_PKGSIZE = 'pkgsize'
T_PKGRATE = 'pkgrate'
T_RECIPIENTS = 'recipients'
T_SENDERS = 'senders'
T_SENDER = 'sender'
T_RECIPIENT = 'recipient'
T_DURATION = 'duration'
T_TARGET_TRAFFICS = 'target_traffics'
T_TARGET_AGENTS = 'target_agents'
T_NWLAYOUT = 'nwlayout'
T_NWCONFIG_PATH = 'network_config'
T_NWLAYOUT_ID_FMT = '{}:{}'
T_TRAFFICS = 'traffics'
T_PANID = 'panid'
T_CHANNEL = 'channel'
T_GENID = 'genid'
T_REPORTDIR = 'reportdir'

T_CLIENTID = 'clientid'
T_TRAFFIC_TYPE = 'traffic_type'
T_NODE = 'node'
T_ADDR = 'addr'
T_CTRLCMD = 'ctrlcmd'
T_MSG = 'msg'
T_MSG_TYPE = 'msgtype'
T_INTERVAL = 'interval'
T_TIME = 'time'
T_RECORDS = 'records'
T_TRAFFIC_STATUS = 'traffic_status'
T_TID = 'tid'
T_TRAFFIC_FINISH_DELAY = 'traffin_delay'
T_EVERYONE = '*'

TrafficStatus = Enum("TrafficStatus", [
    "INITFAILED",       # Initialization failure
    "STOPPED",          # Initial status, traffic not yet launched
    "STARTED",          # Traffic routine started
    "NWCONFIGURING",    # Configuring network layout
    "NWCONFIGED",       # Network layout configured
    "REGISTERING",      # Registering traffics
    "REGISTERED",       # Traffics already been registered to agents
    "RUNNING",          # Traffics are fired
    "FINISHED",         # Traffics finished
])

TrafficType = Enum("TrafficType", [
    "JOIN", # Join network
    "SCMD", # Serial command
    "TSH",  # Command from TSH
    "START", # Start execute traffic
    "UNKNOWN",
    ])

MessageType = Enum("MessageType", [
    "RECV",
    "SENT",
    "UNKNOWN",
    ])

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

AgentStatus = Enum("AgentStatus", [
    "OFFLINE",
    "ONLINE",
    "TRAFFIC_COMPLETED",
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

StorageType = Enum("StorageType", [
    "MongoDB",      # Default
    "PostgreSQL",
    "MySQL",
    "SQLite3",
    "Splunk",
    "JSON",
    "Protobuf",
    "CSV",
])

CtrlCmd = Enum("CtrlCmd", [
    "NEW_CONTROLLER",
    "AGENT_RESTART",
    "AGENT_STOP",
    "AGENT_ENABLE_HEARTBEAT",
    "AGENT_DISABLE_HEARTBEAT",
])

def string_write(fmt, *params):
    if params is None or len(params) == 0:
        return fmt
    return fmt.format(*params)

def console_write(fmt, *params):
    if params is None or len(params) == 0:
        print(fmt)
        return
    print(fmt.format(*params))


