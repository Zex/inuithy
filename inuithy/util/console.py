""" Console for manual mode
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.version import INUITHY_ROOT, __version__, DEPLOY_SH
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_TITLE,\
to_console, to_string, T_EVERYONE
from inuithy.common.command import TSH_ERR_GENERAL, TSH_ERR_HANDLING_CMD,\
Command, Usage, TSH_ERR_INVALID_CMD
from inuithy.util.helper import valid_cmds, runonremote, delimstr
from inuithy.util.task_manager import ProcTaskManager
from inuithy.util.cmd_helper import start_agents, stop_agents
from inuithy.common.runtime import Runtime as rt
from inuithy.common.traffic import Phase
import multiprocessing as mp
import socket
import threading
import signal
import sys
import glob
import os
import os.path
import logging
import logging.config as lconf
from random import randint
import copy

lconf.fileConfig(INUITHY_LOGCONFIG)

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
TSH_CMD_SHARP = "#"
TSH_CMD_UPDATE = "update"

TSH_CMD_RESTART = "restart"
TSH_CMD_START = "start"
TSH_CMD_STOP = "stop"
TSH_CMD_FORCE_STOP = "fstop"
TSH_CMD_LIST = "list"
TSH_CMD_LIST_LESS = "ll"
TSH_CMD_HOST = "host"
TSH_CMD_USEPHASE = "usephase"
TSH_CMD_LSPHASE = "lsphase"
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

class Console(object):#threading.Thread):
    """
    """
    __mutex = threading.Lock()

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, val):
        with Console.__mutex:
            self._running = val

    def _setup_banner(self):
        try:
            self._banner_path = os.path.abspath(INUITHY_ROOT+'/banner/*')
            banners = glob.glob(self._banner_path)
            if banners is None or len(banners) == 0:
                return
            self._banner_path = banners[randint(0, len(banners)-1)]
            with open(self._banner_path, 'r') as fd:
                self._banner = fd.read()
        except Exception as ex:
            to_console("Setup banner failed: {}", ex)

    def _register_routes(self):
        self.usages = {
        "usage": Usage(self._title, [\
    Command(TSH_CMD_HELP, desc="Print inuithy shell usage"),\
    Command(TSH_CMD_HELP, "<command>", desc="Print usage for <command>"),\
    Command(TSH_CMD_QUIT, desc="Leave me"),\
#    Command(TSH_CMD_CONFIG, desc="Configure items"),
    Command(TSH_CMD_AGENT, desc="Operations on agents"),\
    Command(TSH_CMD_TRAFFIC, desc="Run traffic"),\
    Command(TSH_CMD_UPDATE, desc="Update Inuithy components on hosts"),\
    Command(TSH_CMD_EXCLAM, "<system command>", desc="Execute shell command"),\
    Command(TSH_CMD_AT, "<host> <system command>",\
        desc="Execute shell command on remote host"),\
    Command(TSH_CMD_SHARP, "<path|command>", desc="Execute Python command or script")
        ]),
        "usage_agent": Usage(self._title, [\
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_LIST), desc="Print available agents"),\
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_LIST_LESS),\
        desc="Print available agents with less details"),\
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_START),\
        desc="Start agent on <host>\n'*' for all targetted hosts"),
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_STOP),\
        desc="Stop agent on <host>\n'*' for all targetted hosts"),\
    Command(delimstr(' ', TSH_CMD_AGENT, TSH_CMD_FORCE_STOP),\
        desc="Force stop agent on <host>\n'*' for all targetted hosts"),\
        ]),
        "usage_traffic": Usage(self._title, [\
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_HOST),\
    "<host>:<node addr> <serial command>",\
    "Send serial command to agent on <host>"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_LSPHASE),\
        desc="Print configured phases"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_USEPHASE),\
        "<phase index>", desc="Use specific phase"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_DEPLOY),\
        desc="Deploy predefined network layout"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_REGTRAF),\
        desc="Register predefined traffic to agents"),
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_RUN),\
        desc="Run registed traffic"),\
    Command(delimstr(' ', TSH_CMD_TRAFFIC, TSH_CMD_GENREPORT),\
        desc="Generate report for previous traffic"),
        ]),
        "usage_update": Usage(self._title, [\
    Command(delimstr(' ', TSH_CMD_UPDATE, TSH_CMD_HOST),\
        "<directory contains inuithy package> <host>...",\
        desc="Deploy <inuithy package> on <host> \n'*' for all targetted hosts"),\
        ]),
        "usage_quit": Usage(self._title, [\
    Command(TSH_CMD_QUIT, desc="Leave me")]),\
        "usage_help": Usage(self._title, [\
    Command(TSH_CMD_HELP, desc="Print inuithy shell usage")]),\
        "usage_!": Usage(self._title, [\
    Command(TSH_CMD_EXCLAM, "<system command>",\
        desc="Execute shell command"),]),\
        "usage_@": Usage(self._title, [\
    Command(TSH_CMD_AT, "<host> <system command>",\
        desc="Execute shell command on remote host"),]),
        "usage_#": Usage(self._title, [\
    Command(TSH_CMD_SHARP, "<path|command>",\
        desc="Execute Python command or script")])
        }
        self._cmd_routes = {
            TSH_CMD_AGENT:      self.on_cmd_agent,
            TSH_CMD_TRAFFIC:    self.on_cmd_traffic,
#            TSH_CMD_CONFIG:     self.on_cmd_config,
            TSH_CMD_HELP:       self.on_cmd_help,
            TSH_CMD_QUIT:       self.on_cmd_quit,
            TSH_CMD_EXCLAM:     self.on_cmd_sys,
            TSH_CMD_AT:         self.on_cmd_rsys,
            TSH_CMD_SHARP:      self.on_cmd_py,
            TSH_CMD_UPDATE:     self.on_cmd_update,
        }
        self._cmd_agent_routes = {
            TSH_CMD_START: self.on_cmd_agent_start,
            TSH_CMD_STOP: self.on_cmd_agent_stop,
            TSH_CMD_FORCE_STOP: self.on_cmd_agent_stop_force,
            TSH_CMD_LIST: self.on_cmd_agent_list,
            TSH_CMD_LIST_LESS: self.on_cmd_agent_list_less,
        }
        self._cmd_traffic_routes = {
            TSH_CMD_HOST: self.on_cmd_traffic_host,
            TSH_CMD_LSPHASE: self.on_cmd_traffic_list_phase,
            TSH_CMD_USEPHASE: self.on_cmd_traffic_load_phase,
            TSH_CMD_DEPLOY: self.on_cmd_traffic_deploy,
            TSH_CMD_RUN: self.on_cmd_traffic_run,
            TSH_CMD_REGTRAF: self.on_cmd_traffic_register,
            TSH_CMD_GENREPORT: self.on_cmd_traffic_genreport,
        }

    def __init__(self, ctrl=None, lgr=None):
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging #logging.getLogger("InuithyShell")
        self._title = INUITHY_TITLE.format(__version__, "Shell")
        self._running = True
        self._banner = ""
        self._host = socket.gethostname()#socket.gethostbyname(socket.gethostname())
        self._setup_banner()
        self._register_routes()
        self.ctrl = ctrl

    def on_cmd_agent_start(self, *args, **kwargs):
        """Agent start command handler"""
        self.lgr.info("On command agent start")
        if args is None or len(args) < 1:
            return
        hosts = args[0]
        if hosts == T_EVERYONE:
            agents = copy.deepcopy(self.ctrl.expected_agents)
        else:
            agents = list(hosts)
#        to_console("Initialize traffic configure")
#        self.ctrl.traffic_state.create()
        start_agents(agents)
        to_console("Waiting for agents to get ready")
        self.ctrl.traffic_state.wait_agent()

    def on_cmd_agent_stop(self, *args, **kwargs):
        """Agent stop command handler"""
        self.lgr.info("On command agent stop")
        if args is None or len(args) < 1:
            return
        clientid = args[0]
        stop_agents(self.ctrl.mqclient, clientid=clientid)

    def on_cmd_agent_stop_force(self, *args, **kwargs):
        """Agent force stop command handler"""
        self.lgr.info("On command agent force stop")
        if args is None or len(args) < 1:
            return
        hosts = args[0]
        if hosts == T_EVERYONE:
            agents = copy.deepcopy(self.ctrl.expected_agents)
        else:
            agents = list(hosts)
        force_stop_agents(agents)

    def on_cmd_agent_list_less(self, *args, **kwargs):
        """List available agnents with less details"""
        self.lgr.info("On command agent list less")
        [to_console("{}", k) for k in self.ctrl.available_agents.keys()]

    def on_cmd_agent_list(self, *args, **kwargs):
        """List available agnents"""
        self.lgr.info("On command agent list")
        [to_console("AGENT[{}]:{}", k, str(v)) for k, v in self.ctrl.available_agents.items()]

    def on_cmd_agent(self, *args, **kwargs):
        """Operation on agent"""
        self.lgr.info("On command agent")
        if args is None or len(args) == 0:
            to_console(str(self.usages['usage_agent']))
            return
        params = args[1:]
        if self._cmd_agent_routes.get(args[0]):
            self._cmd_agent_routes[args[0]](*(params))
        else:
            to_console(str(self.usages['usage_agent']))

    def on_cmd_traffic(self, *args, **kwargs):
        """Traffic command handler"""
        self.lgr.info("On command traffic")
        if args is None or len(args) == 0:
            to_console(str(self.usages['usage_traffic']))
            return
        params = args[1:]
        if self._cmd_traffic_routes.get(args[0]):
            self._cmd_traffic_routes[args[0]](*(params))
        else:
            to_console(str(self.usages['usage_traffic']))

    def on_cmd_traffic_host(self, *args, **kwargs):
        """Run serial command on specific host
        traffic host 127.0.0.1:1111 lighton 1112
        ['traffic', 'host', '127.0.0.1', 'lighton', '1112']
        ('127.0.0.1', 'lighton', '1112')
        """
        self.lgr.info("On command traffic host")
        if len(args) < 2:
            to_console(str(self.usages['usage_traffic']))
            return
        if len(self.ctrl.node2aid) == 0:
            to_console("No available agent")
            return
        host, node = args[0].split(':')
        data = {
            T_TRAFFIC_TYPE: TrafficType.TSH.name,
            T_HOST:         host,
            T_NODE:         node,
            T_CLIENTID:     self.ctrl.node2aid.get(node),
            T_MSG:          ' '.join(list(args[1:])),
        }
        to_console("Sending {}", ' '.join(list(args[1:])))
        pub_tsh(self.ctrl.mqclient, rt.tcfg.mqtt_qos, data)

    def on_cmd_traffic_list_phase(self, *args, **kwargs):
        """Traffic load phase command handler"""
        self.lgr.info("On command load phase")
        for ph in rt.trcfg.target_phases:
            to_console("[{}] {}", rt.trcfg.target_phases.index(ph), ph)

    def on_cmd_traffic_load_phase(self, *args, **kwargs):
        """Traffic load phase command handler"""
        self.lgr.info("On command load phase")
        if len(args) < 1:
            to_console(str(self.usages['usage_traffic']))
            return
        to_console("loading phase {}", args[0])
        self.ctrl.traffic_state.current_phase = Phase(
            rt.trcfg, rt.nwcfg, rt.trcfg.target_phases[int(args[0])])
        to_console("current phase\n{}", self.ctrl.traffic_state.current_phase)

    def on_cmd_traffic_deploy(self, *args, **kwargs):
        """Traffic deploy command handler
            self.deploy, self.wait_nwlayout, self.register, self.wait_traffic,
            self.fire, self.phase_finish, self.genreport,
        """
        self.lgr.info("On command traffic deploy")
        self.ctrl.traffic_state.next()
        to_console("Start deploying network layout")
        self.ctrl.traffic_state.deploy()
        self.ctrl.traffic_state.wait_nwlayout()
        to_console("Netowrk deployment finished")

    def on_cmd_traffic_genreport(self, *args, **kwargs):
        """Traffic report generation handler"""
        self.lgr.info("On command traffic genreport")
        to_console("Generating traffic report")
        self.ctrl.traffic_state.genreport()
        to_console("Report [{}]", self.ctrl.traffic_state.current_genid)

    def on_cmd_traffic_register(self, *args, **kwargs):
        """Register traffic command handler"""
        self.lgr.info("On command traffic register")
        to_console("Registering traffic")
        self.ctrl.traffic_state.register()
        self.ctrl.traffic_state.wait_traffic()
        to_console("Traffic registerd")

    def on_cmd_traffic_run(self, *args, **kwargs):
        """Run traffic command handler"""
        self.lgr.info("On command traffic run")
        to_console("Start firing")
        self.ctrl.traffic_state.fire()
        self.ctrl.traffic_state.phase_finish()
        to_console("One traffic fired")

    def on_cmd_help(self, *args, **kwargs):
        """Help command handler"""
        self.lgr.info("On command help")
        if args is None or len(args) == 0 or len(args[0]) == 0:
            to_console(str(self.usages['usage']))
            return
        command = args[0].strip()
        cmds = valid_cmds(command)
        if len(cmds) == 0:
            to_console(str(self.usages['usage']))
            return
        subhelp = 'usage_{}'.format(cmds[0])
        if self.usages.get(subhelp):
            to_console(str(self.usages[subhelp]))
            return
        to_console(TSH_ERR_INVALID_CMD, command, 'help')

    def on_cmd_quit(self, *args, **kwargs):
        """Quit command handler"""
        self.lgr.info("On command quit")
        try:
            self.running = False
            if self.ctrl and self.ctrl.traffic_state:
                self.ctrl.traffic_state.finish()
        except Exception as ex:
            to_console("Exception on quit: {}", ex)

    def on_cmd_update(self, *args, **kwargs):
        """Update inuithy handler
            update build/* 192.168.1.190 192.168.1.185
        """
        self.lgr.info("On command update")
        if args is None or len(args) < 2:
            return
        dest_base = '/media/card'
        targets = to_string('{}/{}', args[0], T_EVERYONE)
        packs = []
#        [packs.extend(glob.glob(target)) for target in targets]
        packs.extend(glob.glob(targets))
        hosts = args[1:]
        user = 'root'
        if T_EVERYONE in hosts:
            agents = copy.deepcopy(self.ctrl.expected_agents)
        else:
            agents = list(hosts)
        if len(packs) == 0:
            to_console("Package not found")
        cmd = ' '.join(['scp', ' '.join(packs)])
        failed = False
        for agent in agents:
            try:
                to_console("loading {}@{}", packs, agent)
                buf = ' '.join([cmd, to_string("{}@{}:{}", user, agent, dest_base)])
                to_console(buf)
                os.system(buf)
                runonremote(user, agent, to_string('{}/{}', dest_base, DEPLOY_SH))
            except Exception as ex:
                to_console("Unable to deploy {} on {}: {}", packs, agent, ex)
                failed = True
                break

        to_console("Update {}!", failed and 'failed' or 'finished!')

    def on_cmd_rsys(self, *args, **kwargs):
        """Remote system command handler"""
        self.lgr.info("On command rsys")
        if args is None or len(args) < 2:
            return
        runonremote('root', args[0], ' '.join(args[1:]))

    def on_cmd_sys(self, *args, **kwargs):
        """System command handler"""
        self.lgr.info("On command sys")
        if args is None or len(args) == 0:
            return
        os.system(' '.join(list(args)))

    def on_cmd_py(self, *args, **kwargs):
        """Execute python script"""
        self.lgr.info("On command sys")
        if args is None or len(args) == 0:
            return
        path = args[0]
        try:
            if os.path.isfile(path):
                with open(path) as fd:
                    exec(fd.read())
            elif len(path) == 1:
                exec(path, globals(), locals())
            elif len(path) > 1:
                exec(' '.join(list(args)), globals(), locals())
            else:
                to_console("Unable to execute {}, no such file or command", path)
        except Exception as ex:
            to_console("Exception on executing {}: {}", args, ex)

    def console_loop(self, tshhist=None):
        """Console main loop"""
        self.lgr.info("Console loop started")
        while self.running:
            try:
                command = console_reader(to_string(DEFAULT_PROMPT, self._host))
                command = command.strip()
                if len(command) == 0:
                    continue
                if tshhist:
                    tshhist.write(str(command)+'\n')
                self.dispatch(command)
            except Exception as ex:
                to_console(TSH_ERR_GENERAL, ex)
            except KeyboardInterrupt:
                to_console("Terminating ...")
                self.on_cmd_quit()

    def start(self):
        """Start inuithy shell"""
        self.lgr.info("Start console")
        to_console(self._title)
        to_console(self._banner)
        mod = os.path.exists(rt.tcfg.tsh_hist) and 'a+' or 'w+'
        with open(rt.tcfg.tsh_hist, mod) as tshhist:
            self.console_loop(tshhist)

    def dispatch(self, command):
        self.lgr.info("Dispatch command")
        if command is None or len(command) == 0:
            return
        cmds = valid_cmds(command)
        if len(cmds) == 0 or len(cmds[0]) == 0:
            to_console(TSH_ERR_INVALID_CMD, command, 'help')
        params = cmds[1:]
        try:
            if self._cmd_routes.get(cmds[0]):
                self._cmd_routes[cmds[0]](*(params))
            else:
                self.on_cmd_help()
        except Exception as ex:
            to_console(TSH_ERR_HANDLING_CMD, command, ex)

#def start_console(ctrl):
#    """Shortcut to start a inuithy shell"""
#    term = Console(ctrl)
#    term.start()
#    to_console("\nBye~\n")
#
#if __name__ == '__main__':
#    start_console()
