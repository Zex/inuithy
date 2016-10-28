## Console for manual mode
# Author: Zex Li <top_zlynch@yahoo.com>
#
import socket, threading, signal, sys, glob, os, logging, os.path
import multiprocessing as mp
from random import randint
from inuithy.common.command import *
from inuithy.agent import *
from inuithy.mode.manual_mode import *

DEFAULT_PROMPT = "inuithy@{}>"
# Inuithy shell commands
TSH_CMD_AGENT       = "agent"
TSH_CMD_TRAFFIC     = "traffic"
TSH_CMD_CONFIG      = "config"
TSH_CMD_CTRL        = "ctrl"
TSH_CMD_HELP        = "help"
TSH_CMD_QUIT        = "quit"
TSH_CMD_EXCLAM      = "!"

TSH_CMD_RESTART     = "restart"
TSH_CMD_START       = "start"
TSH_CMD_STOP        = "stop"
TSH_CMD_LIST        = "list"
TSH_CMD_HOST        = "host"
TSH_CMD_LOAD        = "load"
TSH_CMD_RUN         = "run"
TSH_CMD_WHOHAS      = "whohas"

console_reader = hasattr(__builtins__, 'raw_input') and raw_input or input


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

    def __register_routes(self):
        # TODO
        self.usages = {
        "usage":        self.__title + "\n" \
         + "Usage:\n"\
         + "  help                  Print inuithy shell usage\n"\
         + "  help <command>        Print usage for <command>\n"\
         + "  quit                  Leave me\n"\
         + "  agent                 Operations on agents\n"\
 #       + "  ctrl                  Operation on controller\n"\
         + "  config                Configure items\n"\
         + "  ! <system command>    Excute shell command\n",
        "usage_agent":  self.__title + "\n"\
         + "  agent list            Print available agents\n"\
         + "  agent restart <host>  Restart agent on <host>\n"\
         + "                        '*' for all connected hosts\n"\
         + "  agent stop <host>     Stop agent on <host>\n"\
         + "                        '*' for all connected hosts\n",
        "usage_traffic": self.__title + "\n"\
         + "  traffic host <host> <serial command>\n"\
         + "                        Send serial command to agent on <host>\n"\
         + "                        '*' for all connected hosts\n"\
         + "  traffic load <traffic_config_file>\n"\
         + "                        Load predefined traffic from <traffic_config_file>\n"
         + "  traffic run <traffic_name>\n"\
         + "                        Run predefined traffic by name\n",
        "usage_config": self.__title + "\n"\
         + "  config nw <network_config_file>\n"\
         + "                        Create network layout based on <network_config_file>\n",
#        "usage_ctrl":   self.__title + "\n"\
#         + "  ctrl start            Restart controller\n"\
#         + "  ctrl stop             Stop controller\n"\
#         + "  ctrl whohas <address> Query specific owner of short address\n",
        "usage_quit":   self.__title + "\n"\
         + "  quit                  Leave me\n",
        "usage_help":   self.__title + "\n"\
         + "  help                  Print inuithy shell usage\n",
        }
        self.__cmd_routes = {
            TSH_CMD_AGENT:      self.on_cmd_agent,
#            TSH_CMD_CTRL:       self.on_cmd_ctrl,
            TSH_CMD_TRAFFIC:    self.on_cmd_traffic,
            TSH_CMD_CONFIG:     self.on_cmd_config,
            TSH_CMD_HELP:       self.on_cmd_help,
            TSH_CMD_QUIT:       self.on_cmd_quit,
            TSH_CMD_EXCLAM:     self.on_cmd_sys,
        }
        self.__cmd_agent_routes = {
            TSH_CMD_RESTART:    self.on_cmd_agent_restart,
            TSH_CMD_STOP:       self.on_cmd_agent_stop,
            TSH_CMD_LIST:       self.on_cmd_agent_list,
        }
        self.__cmd_ctrl_routes = {
            TSH_CMD_START:      self.on_cmd_ctrl_start,
            TSH_CMD_STOP:       self.on_cmd_ctrl_stop,
            TSH_CMD_WHOHAS:     self.on_cmd_ctrl_whohas,
        }
        self.__cmd_traffic_routes = {
            TSH_CMD_HOST:       self.on_cmd_traffic_host,
            TSH_CMD_LOAD:       self.on_cmd_traffic_load,
            TSH_CMD_RUN:        self.on_cmd_traffic_run,
        }

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        self.__title = INUITHY_TITLE.format(INUITHY_VERSION, "Shell")
        self.__running = True
        self.__banner = ""
        self.__host = socket.gethostname()#socket.gethostbyname(socket.gethostname())
        self.__setup_banner()
        self.__register_routes()
        self.create_controller()

    def create_controller(self):
        self.__ctrl = ManualController(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)
        self.__ctrl_proc = threading.Thread(
            target=self.__ctrl.start, name="Ctrl@InuithyShell")
        self.__ctrl_proc.daemon = True

    def on_cmd_agent_restart(self, *args, **kwargs):
        if args == None or len(args) == 0 or len(args[0]) == 0:
            console_write(TSH_ERR_INVALID_PARAM, args, 'help agent')
            return
        clientid = args[0].strip('\t ')
        if len(clientid) == 0:
            console_write(TSH_ERR_INVALID_PARAM, args, 'help agent')
            return
            
        pub_restart_agent(self.__ctrl.subscriber, self.__ctrl.tcfg.mqtt_qos, clientid)

    def on_cmd_agent_stop(self, *args, **kwargs):
        if args == None or len(args) == 0 or len(args[0]) == 0:
            console_write(TSH_ERR_INVALID_PARAM, args, 'help agent')
            return
        clientid = args[0].strip('\t ')
        if len(clientid) == 0:
            console_write(TSH_ERR_INVALID_PARAM, args, 'help agent')
            return
        pub_stop_agent(self.__ctrl.subscriber, self.__ctrl.tcfg.mqtt_qos, clientid)

    def on_cmd_agent_list(self, *args, **kwargs):
        [console_write("AGENT[{}]:{}", k, str(v)) for k,v in self.__ctrl.available_agents.items()] 

    def on_cmd_agent(self, *args, **kwargs):
        """FORMAT:
        - agent[SP]restart[SP][host]
        - agent[SP]stop[SP][host]
        
        """
        if args == None or len(args) == 0:
            return
        command = args[0].strip('\t \n')
        if len(command) == 0:
            return
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(TSH_ERR_INVALID_CMD, command, 'help agent')
            return
        try:
            if self.__cmd_agent_routes.get(cmds[0]):
                self.__cmd_agent_routes[cmds[0]](command[len(cmds[0])+1:])
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

    def on_cmd_ctrl_whohas(self, *args, **kwargs):
        pass

    def on_cmd_traffic(self, *args, **kwargs):
        if args == None or len(args) == 0:
            return
        command = args[0].strip('\t \n')
        if len(command) == 0:
            return
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(TSH_ERR_INVALID_CMD, command, 'help traffic')
            return
        try:
            if self.__cmd_traffic_routes.get(cmds[0]):
                self.__cmd_traffic_routes[cmds[0]](command[len(cmds[0])+1:])
            else:
                console_write(self.usages['usage_traffic'])
        except Exception as ex:
            console_write(TSH_ERR_HANDLING_CMD, command, ex)
#TODO
    def on_cmd_traffic_host(self, *args, **kwargs):
        pass
    def on_cmd_traffic_load(self, *args, **kwargs):
        pass
    def on_cmd_traffic_run(self, *args, **kwargs):
        pass

    def on_cmd_config(self, *args, **kwargs):
        pass

    def on_cmd_help(self, *args, **kwargs):
        """FORMAT: help
        """
        if args == None or len(args) == 0 or len(args[0]) == 0:
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

    def on_cmd_sys(self, *args, **kwargs):
        """FORMAT: ![SP][system command]
        """
        if args == None or len(args) == 0:
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
        if command == None or len(command) == 0:
            return
        cmds = valid_cmds(command)
        if len(cmds) == 0 or len(cmds[0]) == 0:
            console_write(TSH_ERR_INVALID_CMD, command, 'help')
        try:
            if self.__cmd_routes.get(cmds[0]):
                self.__cmd_routes[cmds[0]](command[len(cmds[0])+1:])
            else:
                self.on_cmd_help()
        except Exception as ex:
            console_write(TSH_ERR_HANDLING_CMD, command, ex)

def start_console(lg=None):
    lconf.fileConfig(INUITHY_LOGCONFIG)
    term = Console()
    term.start()
    console_write("\nBye~\n")

if __name__ == '__main__':
    start_console()
