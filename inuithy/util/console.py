""" Console for manual mode
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT, INUITHY_VERSION
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_TITLE,\
INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH, console_write, string_write
from inuithy.agent import Agent
from inuithy.mode.manual_mode import ManualController
from inuithy.common.command import TSH_ERR_GENERAL, TSH_ERR_HANDLING_CMD,\
Command, Usage, TSH_ERR_INVALID_CMD
from inuithy.util.helper import valid_cmds, runonremote, delimstr
from inuithy.util.cmd_helper import start_agents, stop_agents
import multiprocessing as mp
import socket, threading, logging, signal, sys, glob, os, os.path
import logging.config as lconf
from random import randint
import copy

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
TSH_CMD_FORCE_STOP = "fstop"
TSH_CMD_LIST = "list"
TSH_CMD_LIST_LESS = "ll"
TSH_CMD_HOST = "host"
TSH_CMD_DEPLOY = "deploy"
TSH_CMD_RUN = "run"
TSH_CMD_REGTRAF = "regtraf"
TSH_CMD_WHOHAS = "whohas"
TSH_CMD_GENREPORT = "report"

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
        # TODO command routes
        self.usages = {
            "usage": Usage(self.__title, [
    Command(TSH_CMD_HELP, desc="Print inuithy shell usage"),
    Command(TSH_CMD_HELP, "<command>", desc="Print usage for <command>"),
    Command(TSH_CMD_QUIT, desc="Leave me"),
#    Command(TSH_CMD_CONFIG, desc="Configure items"),
    Command(TSH_CMD_AGENT, desc="Operations on agents"),
    Command(TSH_CMD_TRAFFIC, desc="Run traffic"),
    Command(TSH_CMD_EXCLAM, "<system command>", desc="Execute shell command"),
    Command(TSH_CMD_AT, "<host> <system command>",\
        desc="Execute shell command on remote host"),
    ]),
            "usage_agent": Usage(self.__title, [
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_LIST), desc="Print available agents"),
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_LIST_LESS),\
        desc="Print available agents with less details"),
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_START),
        desc="Start agent on <host>\n"\
    "'*' for all targetted hosts"),
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_STOP),\
        desc="Stop agent on <host>\n"\
    "'*' for all targetted hosts"),
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_FORCE_STOP),\
        desc="Force stop agent on <host>\n"\
    "'*' for all targetted hosts"),
    ]),
            "usage_traffic": Usage(self.__title, [
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_HOST),\
    "<host>:<node addr> <serial command>",
    "Send serial command to agent on <host>"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_DEPLOY),\
        desc="Deploy predefined network layout"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_REGTRAF),\
        desc="Register predefined traffic to agents"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_RUN),\
        desc="Run registed traffic"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_GENREPORT),\
        desc="Generate report for previous traffic"),]),
#            "usage_config": Usage(self.__title, [
#    Command(delimstr(' ', TSH_CMD_CONFIG, 'nw'),\
#        "<network_config_file>",\
#        "Create network layout based on <network_config_file>"),]),
        "usage_quit": Usage(self.__title, [
    Command(TSH_CMD_QUIT, desc="Leave me")]),
        "usage_help": Usage(self.__title, [
    Command(TSH_CMD_HELP, desc="Print inuithy shell usage")]),
        "usage_!": Usage(self.__title, [
    Command(TSH_CMD_EXCLAM, "<system command>",\
        desc="Execute shell command"),]),
        "usage_@": Usage(self.__title, [
    Command(TSH_CMD_AT, "<host> <system command>",\
        desc="Execute shell command on remote host"),]),
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
            TSH_CMD_START: self.on_cmd_agent_start,
            TSH_CMD_STOP: self.on_cmd_agent_stop,
            TSH_CMD_FORCE_STOP: self.on_cmd_agent_stop_force,
            TSH_CMD_LIST: self.on_cmd_agent_list,
            TSH_CMD_LIST_LESS: self.on_cmd_agent_list_less,
        }
        self.__cmd_traffic_routes = {
            TSH_CMD_HOST:       self.on_cmd_traffic_host,
            TSH_CMD_DEPLOY:     self.on_cmd_traffic_deploy,
            TSH_CMD_RUN:        self.on_cmd_traffic_run,
            TSH_CMD_REGTRAF:    self.on_cmd_traffic_regtraf,
            TSH_CMD_GENREPORT:  self.on_cmd_traffic_genreport,
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
        """Run a Controller in manual mode"""
        self.__ctrl = ManualController(INUITHY_CONFIG_PATH, TRAFFIC_CONFIG_PATH)
        self.__ctrl_proc = threading.Thread(target =self.__ctrl.start, name ="Ctrl@InuithyShell")
        self.__ctrl_proc.daemon = False

    def on_cmd_agent_start(self, *args, **kwargs):
        """Agent start command handler"""
        if args is None or len(args) < 1:
            return
        hosts = args[0]
        if hosts == '*':
            self.__ctrl.expected_agents
            agents = copy.deepcopy(self.__ctrl.expected_agents)
        else:
            agents = [hosts]
        start_agents(agents)

    def on_cmd_agent_stop(self, *args, **kwargs):
        """Agent stop command handler"""
        if args is None or len(args) < 1:
            return
        clientid = args[0]
        stop_agents(self.__ctrl.subscriber, clientid=clientid)

    def on_cmd_agent_stop_force(self, *args, **kwargs):
        """Agent force stop command handler"""
        if args is None or len(args) < 1:
            return
        hosts = args[0]
        if hosts == '*':
            self.__ctrl.expected_agents
            agents = copy.deepcopy(self.__ctrl.expected_agents)
        else:
            agents = [hosts]
        force_stop_agents(agents)


    def on_cmd_agent_list_less(self, *args, **kwargs):
        """List available agnents with less details"""
        [console_write("{}", k) for k in self.__ctrl.available_agents.keys()]

    def on_cmd_agent_list(self, *args, **kwargs):
        """List available agnents"""
        [console_write("AGENT[{}]:{}", k, str(v)) for k,v in self.__ctrl.available_agents.items()]

    def on_cmd_agent(self, *args, **kwargs):
        """Operation on agent"""
        if args is None or len(args) == 0:
            console_write(str(self.usages['usage_agent']))
            return
        params = args[1:]
        if self.__cmd_agent_routes.get(args[0]):
            self.__cmd_agent_routes[args[0]](*(params))
        else:
            console_write(str(self.usages['usage_agent']))

    def on_cmd_traffic(self, *args, **kwargs):
        """Traffic command handler"""
        if args is None or len(args) == 0:
            console_write(str(self.usages['usage_traffic']))
            return
        params = args[1:]
        if self.__cmd_traffic_routes.get(args[0]):
            self.__cmd_traffic_routes[args[0]](*(params))
        else:
            console_write(str(self.usages['usage_traffic']))

    def on_cmd_traffic_host(self, *args, **kwargs):
        """Run serial command on specific host
        traffic host 127.0.0.1:1111 lighton 1112
        ['traffic', 'host', '127.0.0.1', 'lighton', '1112']
        ('127.0.0.1', 'lighton', '1112')
        """
        if len(args) < 3:
            console_write(str(self.usages['usage_traffic']))
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
        """Traffic deploy command handler"""
        console_write("Initialize traffic configure")
        self.__ctrl.traffic_state.create()
        self.__ctrl.traffic_state.next()
        console_write("Waiting for agents to get ready")
        self.__ctrl.traffic_state.wait_agent()
        console_write("Start deploying network layout")
        self.__ctrl.traffic_state.deploy()
        self.__ctrl.traffic_state.wait_nwlayout()
        console_write("Netowrk deployment finished")

    def on_cmd_traffic_genreport(self, *args, **kwargs):
        """Traffic report generation handler"""
        console_write("Generating traffic report")
        self.__ctrl.traffic_state.genreport()

    def on_cmd_traffic_regtraf(self, *args, **kwargs):
        """Register traffic command handler"""
        console_write("Start registering traffic")
        self.__ctrl.traffic_state.register()
        self.__ctrl.traffic_state.wait_traffic()
        console_write("Traffic registerd")

    def on_cmd_traffic_run(self, *args, **kwargs):
        """Run traffic command handler"""
        console_write("Start firing")
        self.__ctrl.traffic_state.fire()
        self.__ctrl.traffic_state.traffic_finish()
        console_write("One traffic fired")

    def on_cmd_help(self, *args, **kwargs):
        """Help command handler"""
        if args is None or len(args) == 0 or len(args[0]) == 0:
            console_write(str(self.usages['usage']))
            return
        command = args[0].strip()
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            console_write(str(self.usages['usage']))
            return
        subhelp = 'usage_{}'.format(cmds[0])
        if self.usages.get(subhelp):
            console_write(str(self.usages[subhelp]))
            return
        console_write(TSH_ERR_INVALID_CMD, command, 'help')

    def on_cmd_quit(self, *args, **kwargs):
        """Quit command handler"""
        try:
            self.running = False
            if self.__ctrl:
                self.__ctrl.teardown()
            if self.__ctrl_proc and self.__ctrl_proc.is_alive():
                self.__ctrl_proc.join()
        except Exception as ex:
            console_write("Exception on quit", ex)

    def on_cmd_rsys(self, *args, **kwargs):
        """Remote system command handler"""
        if args is None or len(args) < 2:
            return
        runonremote('root', args[0], ' '.join(args[1:]))

    def on_cmd_sys(self, *args, **kwargs):
        """System command handler"""
        if args is None or len(args) == 0:
            return
        os.system(args[0])

    def console_loop(self, tshhist=None):
        """Console main loop"""
        while self.running:
            try:
                command = console_reader(DEFAULT_PROMPT.format(self.__host))
                command = command.strip()
                if len(command) == 0:
                    continue
                if tshhist:
                    tshhist.write(str(command)+'\n')
                self.dispatch(command)
            except Exception as ex:
                console_write(TSH_ERR_GENERAL, ex)
            except KeyboardInterrupt:
                self.on_cmd_quit()

    def start(self):
        """Start inuithy shell"""
        console_write(self.__title)
        console_write(self.__banner)
        self.__ctrl_proc.start()
        mod = os.path.exists(self.__ctrl.tcfg.tsh_hist) and 'a+' or 'w+'
        with open(self.__ctrl.tcfg.tsh_hist, mod) as tshhist:
            self.console_loop(tshhist)

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
    """Shortcut to start a inuithy shell"""
    term = Console()
    term.start()
    console_write("\nBye~\n")

if __name__ == '__main__':
    start_console()
