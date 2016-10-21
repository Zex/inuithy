## Console for manual mode
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.predef import *
from inuithy.util.helper import *
from random import randint
import socket, argparse, threading
import signal, sys, glob
import os, multiprocessing, logging, os.path

DEFAULT_PROMPT = "inuithy@{}>"
# Inuithy shell commands
TSH_CMD_AGENT       = "agent"
TSH_CMD_CTRL        = "ctrl"
TSH_CMD_HELP        = "help"
TSH_CMD_QUIT        = "quit"
TSH_CMD_EXCLAM      = "!"

TSH_CMD_RESTART     = "restart"
TSH_CMD_STOP        = "stop"
TSH_CMD_LIST        = "list"

TSH_ERR_GENERAL      = "ERROR: {}"
TSH_ERR_INVALID_CMD  = "Invalid command [{}], type `{}` for the usages."
TSH_ERR_HANDLING_CMD = "Exception on handling command [{}]: {}"

console_reader = hasattr(__builtins__, 'raw_input') and raw_input or input

class Command:
    """
    - name: name of the command
    - desc: command description
    - handler: handler to the command
    """
    def __init__(self, name, desc, handler):
        self.name = name
        self.desc = desc
        self.handler = handler

    def run(self, *args, **kwargs):
        if self.handler != None:
            try:
                self.handler(args, kwargs)
            except Exception as ex:
                console_write(TSH_ERR_HANDLING_CMD, self.name, ex)
    def __str__(self):
        return "{}  {}".format(self.name, self.desc)

class Dispatcher:
    # TODO
    pass

class Console(threading.Thread):
    """
    """
    __mutex = threading.Lock() 

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, val):
        if Console.__mutex.acquire():
            self.__running = val
            Console.__mutex.release()

    def __setup_banner(self):
        try:
            self.__banner_path = os.path.abspath(INUITHY_ROOT+'/banner/*')
            banners = glob.glob(self.__banner_path)
            if banners == None or len(banners) == 0:
                return
            self.__banner_path = banners[randint(0, len(banners)-1)]
            with open(self.__banner_path, 'r') as fd:
                self.__banner = fd.read()
        except Exception as ex:
            console_write("Setup banner failed: {}", ex)

    def __register_handlers(self):
        self.usages = {
        "usage":        self.__title + "\n" \
         + "Usage:\n"\
         + "  help                  Print inuithy shell usage\n"\
         + "  help <command>        Print usage for <command>\n"\
         + "  quit                  Leave me\n"\
         + "  agent                 Operations on agents\n"\
         + "  ctrl                  Operation on controller\n"\
         + "  ! <system command>    Excute shell command\n",
        "usage_agent":  self.__title + "\n"\
         + "  agent list            Print available agents\n"\
         + "  agent restart <host>  Restart agent on <host>\n"\
         + "                        '*' for all connected hosts"\
         + "  agent stop <host>     Stop agent on <host>\n"
         + "                        '*' for all connected hosts",
        "usage_ctrl":   self.__title + "\n"\
         + "  ctrl restart          Restart controller\n"\
         + "  ctrl stop             Stop controller\n",
        "usage_quit":   self.__title + "\n"\
         + "  quit                  Leave me\n",
        "usage_help":   self.__title + "\n"\
         + "  help                  Print inuithy shell usage\n",
        }
        self.__cmd_handlers = {
            TSH_CMD_AGENT:      self.on_cmd_agent,
            TSH_CMD_CTRL:       self.on_cmd_ctrl,
            TSH_CMD_HELP:       self.on_cmd_help,
            TSH_CMD_QUIT:       self.on_cmd_quit,
            TSH_CMD_EXCLAM:     self.on_cmd_sys,
        }
        self.__cmd_agent_handlers = {
            TSH_CMD_RESTART:    self.on_cmd_agent_start,
            TSH_CMD_STOP:       self.on_cmd_agent_stop,
            TSH_CMD_LIST:       self.on_cmd_agent_list,
        }
        self.__cmd_ctrl_handlers = {
            TSH_CMD_RESTART:    self.on_cmd_ctrl_start,
            TSH_CMD_STOP:       self.on_cmd_ctrl_stop,
        }

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(Console, self).__init__(group, target, name, args, kwargs, verbose)
        self.__title = INUITHY_TITLE.format(INUITHY_VERSION, "Shell")
        self.__running = True
        self.__banner = ""
        self.__host = socket.gethostbyname(socket.gethostname())
        self.__setup_banner()
        self.__register_handlers()

    def on_cmd_agent_start(self, *args, **kwargs):
        pass
    def on_cmd_agent_stop(self, *args, **kwargs):
        pass
    def on_cmd_agent_list(self, *args, **kwargs):
        pass

    def on_cmd_agent(self, *args, **kwargs):
        """FORMAT:
        - agent[SP]restart[SP][host]
        - agent[SP]stop[SP][host]
        
        """
        if args == None or len(args) == 0:
            return
        command = args[0].strip()
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(TSH_ERR_INVALID_CMD, command, 'help agent')
        try:
            if self.__cmd_agent_handlers.has_key(cmds[0]):
                self.__cmd_agent_handlers[cmds[0]](command[len(cmds[0])+1:])
            else:
                console_write(self.usages['usage_agent'])
        except Exception as ex:
            console_write(TSH_ERR_HANDLING_CMD, command, ex)

    def on_cmd_ctrl_start(self, *args, **kwargs):
        pass
    def on_cmd_ctrl_stop(self, *args, **kwargs):
        pass
    def on_cmd_ctrl(self, *args, **kwargs):
        pass

    def on_cmd_help(self, *args, **kwargs):
        """FORMAT: help
        """
        if args == None or len(args) == 0:
            console_write(self.usages['usage'])
            return
        command = args[0].strip()
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(self.usages['usage'])
            return
        subhelp = 'usage_{}'.format(cmds[0])
        if self.usages.has_key(subhelp):
            console_write(self.usages[subhelp])
            return
        console_write(TSH_ERR_INVALID_CMD, command, 'help')

    def on_cmd_quit(self, *args, **kwargs):
        """FORMAT: quit
        """
        self.running = False

    def on_cmd_sys(self, *args, **kwargs):
        """FORMAT: ![SP][system command]
        """
        if args == None or len(args) == 0:
            return
        os.system(args[0])

    def start(self): 
        console_write(self.__title)
        console_write(self.__banner)
        while self.running:
            try:
                command = console_reader(DEFAULT_PROMPT.format(self.__host))
                self.dispatch(command)
            except Exception as ex:
                console_write(TSH_ERR_GENERAL, ex)
            except KeyboardInterrupt:
                self.on_cmd_quit()

    def dispatch(self, command):
        if command == None or len(command) == 0:
            return
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(TSH_ERR_INVALID_CMD, command, 'help')
        try:
            if self.__cmd_handlers.has_key(cmds[0]):
                self.__cmd_handlers[cmds[0]](command[len(cmds[0])+1:])
            else:
                self.on_cmd_help()
        except Exception as ex:
            console_write(TSH_ERR_HANDLING_CMD, command, ex)

if __name__ == '__main__':
    term = Console()
    term.start()
    console_write("\nBye~\n")

