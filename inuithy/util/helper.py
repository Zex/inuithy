## Node under test definition
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.predef import *
from inuithy.common.node import *
from inuithy.util.task_manager import *

def getnwlayoutid(nwcfg_path, layout_name):
    return string_write(CFGKW_NWLAYOUT_ID_FMT, nwcfg_path, layout_name)

def getpredefaddr():
    ret = ''
    with open('/etc/network/interfaces', 'r') as fd:
         while True:
             line = fd.readline()
             if line == None or len(line) == 0: break
             line = line.strip('\t ')
             if line.find('inet static') >= 0: continue
             if line.find('address') >= 0:
                 ret = line.split()[1]
                 break

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





