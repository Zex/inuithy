""" Console for manual mode
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT, INUITHY_VERSION
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_TITLE,\
INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, console_write, string_write
from inuithy.agent import Agent
from inuithy.mode.manual_mode import ManualController 
from inuithy.common.command import TSH_ERR_GENERAL, TSH_ERR_HANDLING_CMD
from inuithy.util.helper import valid_cmds, runonremote
import multiprocessing as mp
import socket, threading, logging, signal, sys, glob, os, os.path
import logging.config as lconf
from random import randint

DEFAULT_PROMPT = "inuithy@{}>"
# Inuithy shell commands
TSH_CMD_AGENT = "agent"
TSH_CMD_TRAFFIC = "traffic"
TSH_CMD_CONFIG = "config"
TSH_CMD_CTRL = "ctrl"
TSH_CMD_HELP = "help"
TSH_CMD_QUIT = "quit"
TSH_CMD_EXCLAM = "!"
TSH_CMD_AT = "@"

TSH_CMD_RESTART = "restart"
TSH_CMD_START = "start"
TSH_CMD_STOP = "stop"
TSH_CMD_LIST = "list"
TSH_CMD_HOST = "host"
TSH_CMD_DEPLOY = "deploy"
TSH_CMD_RUN = "run"
TSH_CMD_REGTRAF = "regtraf"
TSH_CMD_WHOHAS = "whohas"

console_reader = hasattr(__builtins__, 'raw_input') and raw_input or input

lconf.fileConfig(INUITHY_LOGCONFIG)

class Dispatcher(object):
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
            if banners is None or len(banners) == 0:
                return
            self.__banner_path = banners[randint(0, len(banners)-1)]
            with open(self.__banner_path, 'r') as fd:
                self.__banner = fd.read()
        except Exception as ex:
            console_write("Setup banner failed: {}", ex)

    def __register_routes(self):
        # TODO
        self.usages = {
            "usage": self.__title + "\n"\
            "Usage:\n"\
            "  help                  Print inuithy shell usage\n"\
            "  help <command>        Print usage for <command>\n"\
            "  quit                  Leave me\n"\
            "  agent                 Operations on agents\n"\
            #"  config                Configure items\n"\
            "  ! <system command>    Execute shell command\n"\
            "  @ <host> <system command> Execute shell command on remote host\n",
            "usage_agent":  self.__title + "\n"\
            "  agent list            Print available agents\n"\
            "  agent restart <host>  Restart agent on <host>\n"\
            "                        '*' for all connected hosts\n"\
            "  agent stop <host>     Stop agent on <host>\n"\
            "                        '*' for all connected hosts\n",
            "usage_traffic": self.__title + "\n"\
            "  traffic host <host>:<node addr> <serial command>\n"\
            "                        Send serial command to agent on <host>\n"\
            "                        '*' for all connected hosts\n"\
            "  traffic deploy <traffic name>\n"\
            "                       Deploy network layout based on given traffic configure\n"\
            "  traffic regtraf      Register preconfigred traffic to agents\n"\
            "  traffic run          Run registed traffic\n",
            "usage_config": self.__title + "\n"\
"  config nw <network_config_file>\n"\
"                        Create network layout based on <network_config_file>\n",
            "usage_quit":   self.__title + "\n"\
            "  quit                  Leave me\n",
            "usage_help":   self.__title + "\n"\
            "  help                  Print inuithy shell usage\n",
        }
        self.__cmd_routes = {
            TSH_CMD_AGENT:      self.on_cmd_agent,
            TSH_CMD_TRAFFIC:    self.on_cmd_traffic,
#            TSH_CMD_CONFIG:     self.on_cmd_config,
            TSH_CMD_HELP:       self.on_cmd_help,
            TSH_CMD_QUIT:       self.on_cmd_quit,
            TSH_CMD_EXCLAM:     self.on_cmd_sys,
            TSH_CMD_AT:         self.on_cmd_rsys,
        }
        self.__cmd_agent_routes = {
            TSH_CMD_START:    self.on_cmd_agent_start,
            TSH_CMD_STOP:       self.on_cmd_agent_stop,
            TSH_CMD_LIST:       self.on_cmd_agent_list,
        }
        self.__cmd_traffic_routes = {
            TSH_CMD_HOST:       self.on_cmd_traffic_host,
            TSH_CMD_DEPLOY:     self.on_cmd_traffic_deploy,
            TSH_CMD_RUN:        self.on_cmd_traffic_run,
            TSH_CMD_REGTRAF:    self.on_cmd_traffic_regtraf,
        }

    def __init__(self, group=None, target=None, name=None, args =(), kwargs=None, verbose=None):
        self.__title = INUITHY_TITLE.format(INUITHY_VERSION, "Shell")
        self.__running = True
        self.__banner = ""
        self.__host = socket.gethostname()#socket.gethostbyname(socket.gethostname())
        self.__setup_banner()
        self.__register_routes()
        self.create_controller()

    def create_controller(self):
        self.__ctrl = ManualController(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)
        self.__ctrl_proc = threading.Thread(target =self.__ctrl.start, name ="Ctrl@InuithyShell")
        self.__ctrl_proc.daemon = False

    def on_cmd_agent_start(self, *args, **kwargs):
        print(args)
        agents = list(args)
        start_agents(agents)

    def on_cmd_agent_stop(self, *args, **kwargs):
        if args is None or len(args) < 1:
            return
        clientid = args[0]
        data = {
            T_CTRLCMD:  CtrlCmd.AGENT_STOP.name,
            T_CLIENTID: clientid,
            T_HOST:     clientid,
        }
        pub_ctrlcmd(self.__ctrl.subscriber, self.__ctrl.tcfg.mqtt_qos, data)

    def on_cmd_agent_list(self, *args, **kwargs):
        [console_write("AGENT[{}]:{}", k, str(v)) for k,v in self.__ctrl.available_agents.items()] 

    def on_cmd_agent(self, *args, **kwargs):
        """Operation on agent"""
        if args is None or len(args) == 0:  return
        params = args[1:]
        if self.__cmd_agent_routes.get(args[0]):
            self.__cmd_agent_routes[args[0]](*(params))
        else:
            console_write(self.usages['usage_agent'])

    def on_cmd_traffic(self, *args, **kwargs):
        if args is None or len(args) == 0:
            return
        params = args[1:]
        if self.__cmd_traffic_routes.get(args[0]):
            self.__cmd_traffic_routes[args[0]](*(params))
        else:
            console_write(self.usages['usage_traffic'])
            
    def on_cmd_traffic_host(self, *args, **kwargs):
        """
        traffic host 127.0.0.1:1111 lighton 1112
        ['traffic', 'host', '127.0.0.1', 'lighton', '1112']
        ('127.0.0.1', 'lighton', '1112')
        """
        if len(args) < 3:
            console_write(self.usages['usage_traffic'])
            return
        if len(self.__ctrl.host2aid) == 0:
            console_write("No available agent")
            return
        host, node = args[0].split(':')
        data = {
            T_TRAFFIC_TYPE: TrafficType.TSH.name,
            T_HOST:         host,
            T_NODE:         node,
            T_CLIENTID:     self.__ctrl.host2aid.get(host),
            T_MSG:          ' '.join(list(args[1:])),
        }
        pub_traffic(self.__ctrl.subscriber, self.__ctrl.tcfg.mqtt_qos, data)

    def on_cmd_traffic_deploy(self, *args, **kwargs):
        print(args)
        if args is None or len(args) < 2:
            return
        self.__ctrl.traffic_state.start()
        self.__ctrl.traffic_state.wait_agent()
        self.__ctrl.traffic_state.deploy()
        console_write("Deploying network layout")

    def on_cmd_traffic_regtraf(self, *args, **kwargs):
        if args is None or len(args) < 2:
            return
        self.__ctrl.traffic_state.wait_nwlayout()
        self.__ctrl.traffic_state.register()
        console_write("Traffic registerd")
        
    def on_cmd_traffic_run(self, *args, **kwargs):
        if args is None or len(args) < 2:
            return
        self.__ctrl.traffic_state.wait_traffic()
        self.__ctrl.traffic_state.fire()
        console_write("Traffic fired")

    def on_cmd_help(self, *args, **kwargs):
        if args is None or len(args) == 0 or len(args[0]) == 0:
            console_write(self.usages['usage'])
            return
        command = args[0].strip()
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(self.usages['usage'])
            return
        subhelp = 'usage_{}'.format(cmds[0])
        if self.usages.get(subhelp):
            console_write(self.usages[subhelp])
            return
        console_write(TSH_ERR_INVALID_CMD, command, 'help')

    def on_cmd_quit(self, *args, **kwargs):
        """FORMAT: quit
        """
        try:
            self.__ctrl.subscriber.disconnect()
            self.__ctrl_proc.join()
        except Exception as ex:
            pass
        self.running = False

    def on_cmd_rsys(self, *args, **kwargs):
        """FORMAT: @ <host> <system command>
        """
        print(args)
        if args is None or len(args) < 2:
            return
        runonremote('root', args[0], ' '.join(args[1:]))

    def on_cmd_sys(self, *args, **kwargs):
        """FORMAT: ! <system command>
        """
        if args is None or len(args) == 0:
            return
        os.system(args[0])

    def start(self): 
        console_write(self.__title)
        console_write(self.__banner)
        self.__ctrl_proc.start()
        mod = os.path.exists(self.__ctrl.tcfg.tsh_hist) and 'a+' or 'w+'
        with open(self.__ctrl.tcfg.tsh_hist, mod) as tshhist:
            while self.running:
                try:
                    command = console_reader(DEFAULT_PROMPT.format(self.__host))
                    command = command.strip()
                    if len(command) == 0: continue
                    tshhist.write(str(command)+'\n')
                    self.dispatch(command)
                except Exception as ex:
                    console_write(TSH_ERR_GENERAL, ex)
                except KeyboardInterrupt:
                    self.on_cmd_quit()

    def dispatch(self, command):
        if command is None or len(command) == 0:
            return
        cmds = valid_cmds(command)
        if len(cmds) == 0 or len(cmds[0]) == 0:
            console_write(TSH_ERR_INVALID_CMD, command, 'help')
        params = cmds[1:]
        try:
            if self.__cmd_routes.get(cmds[0]):
                self.__cmd_routes[cmds[0]](*(params))
            else:
                self.on_cmd_help()
        except Exception as ex:
            console_write(TSH_ERR_HANDLING_CMD, command, ex)

def start_console(logger=None):
    term = Console()
    term.start()
    console_write("\nBye~\n")

if __name__ == '__main__':
    start_console()
