""" Common definition for inuithy
 @author: Zex Li <top_zlynch@yahoo.com>
"""
import os
import sys

if os.uname()[-1] == 'armv7l':
    sys.path.insert(0, '/usr/lib/python2.7/site-packages')

from inuithy.common.version import __version__, INUITHY_ROOT
from enum import Enum

# Controller => Agents
# Command for agents
TT_COMMAND = "inuithy/topic/command"
# Configuration for agents
TT_CONFIG = "inuithy/topic/config"
# Traffc data to send via serial port on agent
TT_TRAFFIC = "inuithy/topic/traffic"
# Configure network layout as given configure
TT_NWLAYOUT = "inuithy/topic/nwlayout"
# Message sent via inuithy shell
TT_TSH = "inuithy/topic/tsh"
# Response from agent
TT_REPLY = "inuithy/topic/reply"
# Agents => Controller
# Unregister agent
TT_UNREGISTER = "inuithy/topic/unregister"
# Status of agent/nodes
TT_STATUS = "inuithy/topic/status"
# Heartbeat from agent
TT_HEARTBEAT = "inuithy/topic/heartbeat"
# Report data wriited to serial port
TT_REPORTWRITE = "inuithy/topic/reportwrite"
# Report data read from serial port
TT_NOTIFICATION = "inuithy/topic/notification"
# Sniffer data topic
TT_SNIFFER = "inuithy/topic/sniffer"
# Message sent via inuithy shell
# <topic id>::<message>
INUITHY_MQPAYLOAD_DELEMER = "::>"
INUITHY_MQPAYLOAD_FMT = "{}"+INUITHY_MQPAYLOAD_DELEMER+"{}"

INUITHYAGENT_MSGFMT = "INUITHYAGENT [{}]"
# Agent identity in MQ network: inuithy/agent/<host>"
INUITHYAGENT_CLIENT_ID = "inuithy/agent/{}"
INUITHYNODE_CLIENT_ID = "inuithy/node/{}"

CTRL_MSGFMT = "INUITHYCTRL [{}]"
CTRL_CLIENT_ID = "inuithy/ctrl/{}"

# command message from Controller to Agents
# <command> <parameters>
INUITHY_CTRL_CMD = "{} {}"
# Default paths
INUITHY_NOHUP_OUTPUT = "/tmp/inuithy.nohup"
INUITHY_LOGCONFIG = INUITHY_ROOT+"/config/logging.conf"
INUITHY_CONFIG_PATH = INUITHY_ROOT+"/config/inuithy_config.yaml"
NETWORK_CONFIG_PATH = INUITHY_ROOT+"/config/network_config.yaml"
TRAFFIC_CONFIG_PATH = INUITHY_ROOT+"/config/traffic_config.yaml"
INUITHY_MQLOG_FMT = "MQ.Log: {}"
# Inuithy ver <version> <component>
INUITHY_TITLE = "Inuithy version {} {}"

DEV_TTYACM = '/dev/ttyACM{}'
DEV_TTYUSB = '/dev/ttyUSB{}'
DEV_TTYS = '/dev/ttyS{}'
DEV_TTY = '/dev/tty{}'

IFACEPATH = '/etc/network/interfaces'

# Configure keywords
T_WORKMODE = 'workmode'
T_HEARTBEAT = 'heartbeat'
T_MQTT = 'mqtt'
T_HOST = 'host'
T_PORT = 'port'
T_QOS = 'qos'
T_SNIFFER = 'sniffer'
T_PCAP = 'pcap'
T_TSHARK = 'tshark'
T_BAUD = 'baud'
T_MQTT_VERSION = 'mqtt_version'
T_VERSION = 'version'
T_CONTROLLER = 'controller'
T_AGENTS = 'agents'
T_ENABLED = 'enabled'
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
T_JITTER = 'jitter'
T_DESTS = 'dests'
T_DEST = 'dest'
T_SRCS = 'srcs'
T_SRC = 'src'
T_DURATION = 'duration'
T_TARGET_PHASES = 'target_phases'
T_TARGET_TRAFFICS = 'target_traffics'
T_TARGET_AGENTS = 'target_agents'
T_NWLAYOUT = 'nwlayout'
T_NWCONFIG_PATH = 'network_config'
T_NWLAYOUT_ID_FMT = '{}:{}'
T_TRAFFICS = 'traffics'
T_PANID = 'panid'
T_SPANID = 'spanid'
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
T_SNIFFER_RECORDS = 'sniffer_records'
T_TRAFFIC_STATUS = 'traffic_status'
T_TID = 'tid'
T_TRAFFIC_FINISH_DELAY = 'traffin_delay'
T_EVERYONE = '*'
T_DIAG = '+'
T_NOI = 'noi' # Nodes of interest
T_RLOGBASE = 'rlog_base'

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
    "AGENTFAILED",      # Agent down unexpectly
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
    "SEND",
    "JOINING",
    "UNKNOWN",
    ])

class GenInfo(object):
    """Report generation info"""
    def __init__(self):
        self.header = None
        self.csv_path = None
        self.raw_csv_path = None
        self.pdf_path = None
        self.fig_base = None
        self.genid = None
        self.colormap = 'jet_r' #'brg_r'

    def __str__(self):
        return to_string("header: {}\ncsv: {}\npdf: {}\nfigures: {}\ngenid: {}\n",\
                self.header, self.csv_path, self.pdf_path, self.fig_base, self.genid)

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

def to_string(fmt, *params):
    if params is None or len(params) == 0:
        return fmt
    return fmt.format(*params)

def to_console(fmt, *params):
    if params is None or len(params) == 0:
        print(fmt)
        return
    print(fmt.format(*params))

NodeType = Enum("NodeType", [
    "BLE",
    "Zigbee",
    "BleZbee",
    "UNKNOWN",
])

