## Commands between controller and agents
# Author: Zex Li <top_zlynch@yahoo.com>
#

from enum import Enum

CtrlCmds = Enum("CtrlCmds", [
    "CMD_NEW_CONTROLLER",
    "CMD_AGENT_RESTART",
    "CMD_AGENT_STOP",
    "CMD_AGENT_ENABLE_HEARTBEAT",
    "CMD_AGENT_DISABLE_HEARTBEAT",
    "CMD_TRAFFIC_SEND",
])



