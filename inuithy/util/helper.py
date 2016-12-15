""" Node under test definition
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_NWLAYOUT_ID_FMT, IFACEPATH
from inuithy.common.predef import to_string 
import subprocess as sp
import os
import sys

def runonremote(user, host, cmd):
    """Run command on remote host
    """
    fmt = 'ssh -f {}@{} '#"{}"'
    rcmd = to_string(fmt, user, host)#, cmd)
    rcmd += "\"" + cmd + "\""
    sp.call(rcmd, shell=True)

def isprocrunning(name):
    try:
        r = sp.check_output(['pidof', name])
        if r is None or len(r) == 0:
            return False
        return True
    except sp.CalledProcessError:
        return False
    return False

def delimstr(delim, *args):
    if delim is None or not isinstance(delim, str):
        delim = ''
    return delim.join(list(args))

def getnwlayoutid(nwcfg_path, layout_name):
    return to_string(T_NWLAYOUT_ID_FMT, nwcfg_path, layout_name)

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

def clear_list(l):
#    l.clear()
    while len(l) > 0: l.pop()

def console_reader(promt=''):
    sys.stdout.write(promt)
    sys.stdout.flush()
    return sys.stdin.readline()

