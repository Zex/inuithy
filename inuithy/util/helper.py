""" Node under test definition
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_NWLAYOUT_ID_FMT, IFACEPATH
from inuithy.common.predef import string_write 
import subprocess as sp
import os

def runonremote(user, host, cmd):
    """Run command on remote host
    """
    fmt = 'ssh -f {}@{} '#"{}"'
    rcmd = string_write(fmt, user, host)#, cmd)
    rcmd += "\"" + cmd + "\""
    sp.call(rcmd, shell=True)

def delimstr(delim, *args):
    if delim is None or not isinstance(delim, str):
        delim = ''
    return delim.join(list(args))

def getnwlayoutid(nwcfg_path, layout_name):
    return string_write(T_NWLAYOUT_ID_FMT, nwcfg_path, layout_name)

def getnwlayoutname(nwlayoutid):
    return nwlayoutid.split(':')[1]

def getpredefaddr():
    """Get predefined network address
    """
    ret = ''
    if not os.path.exists(IFACEPATH): return ret
    with open(IFACEPATH, 'r') as fd:
        while True:
            line = fd.readline()
            if line is None or len(line) == 0:
                break
            line = line.strip('\t ')
            if line.find('inet static') >= 0:
                continue
            if line.find('address') >= 0:
                ret = line.split()[1]
                break
    return ret

def is_number(s, base=16):
    """Is this a number
    """
    try:
        int(s, base)
    except ValueError:
        return False
    return True

def valid_cmds(command):
    """Extract command and parameters from string
    """
    command = command.strip()
    return [c.strip() for c in command.split(' ') if len(c) != 0]


