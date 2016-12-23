""" Traffic state transition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TID, T_GENID, T_TRAFFIC_TYPE,\
T_CLIENTID, T_NODE, T_HOST, T_DURATION, T_INTERVAL, T_GATEWAY, T_SRC,\
T_DEST, T_PKGSIZE, T_NODES, T_PATH, T_NWLAYOUT, T_PANID, T_SPANID,\
to_console, to_string, TrafficType, T_TRAFFIC_FINISH_DELAY,\
TrafficStorage, StorageType, TrafficStatus, T_JITTER, T_DESTS
from inuithy.common.runtime import Runtime as rt
from inuithy.util.helper import getnwlayoutname
from inuithy.util.cmd_helper import pub_nwlayout, pub_traffic, start_agents,\
stop_agents, force_stop_agents
from inuithy.common.traffic import create_phases#, TRAFFIC_BROADCAST_ADDRESS
from inuithy.analysis.report_adapter import ReportAdapter
from inuithy.util.task_manager import ProcTaskManager
from state_machine import State, Event, acts_as_state_machine,\
after, before, InvalidStateTransition
from datetime import datetime as dt
from copy import deepcopy
import logging
import time
import threading

class TrafStatChk(object):
    """Traffic status checker maintains a serial of check items
    for traffic and defines conditions for them
    @nwlayout       Network layout deployment status
    @traffic_stat    Each traffic status
    @expected_agents:  list of agents
    @available_agents: agentid => AgentInfo
    """
    def __init__(self, lgr=None):
        TrafStatChk.lgr = lgr is None and logging or lgr
        self.nwlayout = {}
        self.traffic_stat = {}
        self.expected_agents = []
        self.available_agents = {}
        self.node2aid = {}
        self.node2host = {}
#        self.cond = threading.Condition()
        self.done = threading.Event()
        self._is_agents_up = threading.Event()
        self._is_nwlayout_done = threading.Event()
        self._is_traffic_registered = threading.Event()
        self._is_traffic_all_fired = threading.Event()
        self._is_phase_finished = threading.Event()
        self._is_agents_unregistered = threading.Event()

    def set_all(self):
        TrafStatChk.lgr.info("Notify all waiting processes")
        try:
            [e.set() for e in [
            self._is_agents_up,
            self._is_nwlayout_done,
            self._is_traffic_registered,
            self._is_traffic_all_fired,
            self._is_phase_finished,
#           self._is_agents_unregistered,
            ]]
        except Exception as ex:
            TrafStatChk.lgr.error("Failed to set all waiting")

    def clear_all(self):
        TrafStatChk.lgr.info("Clear all waiting processes")
        try:
            [e.clear() for e in [
            self._is_agents_up,
            self._is_nwlayout_done,
            self._is_traffic_registered,
            self._is_traffic_all_fired,
            self._is_phase_finished,
    #           self._is_agents_unregistered,
            ]]
        except Exception as ex:
            TrafStatChk.lgr.error("Failed to set all waiting")

    def create_nwlayout(self, nwinfo):#nwid, nodes):
        """Create map of network layout configure"""
        TrafStatChk.lgr.info("Create network layout checker")
        if nwinfo is None:
            return
#        self.nwlayout[nwid] = {node:False for node in nodes}
        self.nwlayout = {node:False for node in nwinfo.get(T_NODES)}

    def is_nwlayout_done(self):
        """Whether network layout configured"""
#        TrafStatChk.lgr.info("Is network layout done")
        try:
            if self.available_agents is None or len(self.available_agents) == 0:
                raise RuntimeError("No agent available")
            nw = self.nwlayout
            if all(nw.values()):
                return True
            chks = [k for k, v in nw.items() if v is False]
            to_console("Node join state: [{}/{}], waiting for [{}]", len(nw)-len(chks), len(nw), chks)
            return False
        except Exception as ex:
            TrafStatChk.lgr.error(to_string("Failed to check network layout: {}", ex))
            return False

    def is_traffic_all_fired(self):
        """Whether traffic are fired"""
#        TrafStatChk.lgr.info("Is traffic all fired")
        try:
            if len(self.available_agents) == 0:
                raise ValueError("No agent available")
            if len(self.traffic_stat) == 0:
                return True
            TrafficState.lgr.debug(self.traffic_stat)
            if len([chk for chk in self.traffic_stat.values() if chk == TrafficStatus.RUNNING]) == len(self.traffic_stat):
                return True
            return False
        except Exception as ex:
            TrafStatChk.lgr.error(to_string("Failed to check whether traffic fired: {}", ex))
            return False

    def is_traffic_registered(self):
        """Whether traffics are registed"""
#        TrafStatChk.lgr.info("Is traffic registered")
        try:
            if len(self.available_agents) == 0:
                raise ValueError("No agent available")
            if len(self.traffic_stat) == 0:
                return True
#            TrafficState.lgr.debug(self.traffic_stat)
            if len([chk for chk in self.traffic_stat.values() if chk == TrafficStatus.REGISTERED]) == len(self.traffic_stat):
                return True
            return False
        except Exception as ex:
            TrafStatChk.lgr.error(to_string("Failed to check whether traffic registered: {}", ex))
            return False

    def is_phase_finished(self):
        """Whether traffics are finished"""
#        TrafStatChk.lgr.info("Is traffic all finished")
        try:
            if len(self.available_agents) == 0:
                raise ValueError("No agent available")
            if len(self.traffic_stat) == 0:
                return True
            TrafficState.lgr.debug(self.traffic_stat)
            if len([chk for chk in self.traffic_stat.values() if chk == TrafficStatus.FINISHED]) == len(self.traffic_stat):
                return True
            return False
        except Exception as ex:
            TrafStatChk.lgr.error(to_string("Failed to check whether traffic finished: {}", ex))
            return False

    def is_agents_up(self):
        """Whether expected agents all started"""
#        TrafStatChk.lgr.info("Check for agents availability")
        try:
            expected = self.expected_agents
            available = self.available_agents
            if len(self.node2aid) == 0:
                return False
            if len(expected) != len(available):
                return False
            for ai in available.values():
                if ai.host not in expected:
                    return False
            return True
        except Exception as ex:
            TrafStatChk.lgr.error(to_string("Failed to check agent availability", ex))
            return False

def transition(sm, event):
    """Transite between states"""
    try:
        event()
    except InvalidStateTransition as ex:
        TrafficState.lgr.error(to_string("Failed to transite status {}: {}", event, ex))
        sm.traf_running = True

def publish_nwlayout(nwlayoutname, nwcfg, tcfg, chk, genid, pub):
    """Configure network by given network layout"""
    for subnet in nwcfg.config.get(nwlayoutname).values():
        data = deepcopy(subnet)
        del data[T_NODES] # Remove additional info
        chk.create_nwlayout(subnet)
        for node in subnet.get(T_NODES):
            target_host = chk.node2host.get(node)
            if target_host is None:
                raise ValueError(to_string("Node [{}] not found on any agent", node))
            data[T_HOST] = target_host
            data[T_GENID] = genid #self.current_phase.genid
            data[T_NODE] = node
            data[T_TRAFFIC_TYPE] = TrafficType.JOIN.name

            if not tcfg.enable_localdebug:
                data[T_CLIENTID] = chk.node2aid.get(node)
                pub_nwlayout(pub, data=data)
            else: # DEBUG
                for aid in chk.node2aid.values():
                    data[T_CLIENTID] = aid
                    pub_nwlayout(pub, data=data)
                    break

def publish_traffic(genid, tg, tr, chk, pub, enable_localdebug=False):
    try:
        target_host = chk.node2host.get(tr.src)
        data = {
            T_TID: tr.tid,
            T_GENID: genid,
            T_TRAFFIC_TYPE: TrafficType.SCMD.name,
            T_NODE: tr.src,
            T_HOST: target_host,
            T_DURATION: tg.duration,
            T_JITTER: tg.jitter,
            T_INTERVAL: tg.interval,
            T_SRC: tr.src,
            T_DESTS: tr.dests,
            T_PKGSIZE: tr.pkgsize,
        }
        chk.traffic_stat[tr.tid] = TrafficStatus.REGISTERING
        if not enable_localdebug:
            data[T_CLIENTID] = chk.node2aid.get(tr.src)
            pub_traffic(pub, data=data)
        else: # DEBUG
            for aid in chk.node2aid.values():
                data[T_CLIENTID] = aid
                pub_traffic(pub, data=data)
                break
        TrafficState.lgr.debug(to_string("TRAFFIC: {}:{}:{}", data.get(T_TID), data.get(T_CLIENTID), tr))
        return True
    except Exception as ex:
        TrafficState.lgr.error(to_string(
            "Exception on registering traffic, traffic [{}]: {}",
            tg.traffic_name, str(ex)))
        return False

def publish_phase(phase, chk, pub, enable_localdebug=False):
    """Register one phase to agent"""
    chk.traffic_stat.clear()
    TrafficState.lgr.info(to_string("network [{}]", phase.nwlayoutid))
    for tg in phase.tgs:
        for tr in tg.traffics:
            if not publish_traffic(phase.genid, tg, tr, chk, pub, enable_localdebug):
                return False
    TrafficState.lgr.debug(to_string("Total traffic: [{}]", len(chk.traffic_stat)))
    return True

@acts_as_state_machine
class TrafficState:
    """
    @controller Controller object
    @lgr         For log handling

    STOP,             # Initial status, traffic not yet launched
    CREATED,          # Initialize traffic based on configure
    STARTED,          # Traffic routine started
    NWCONFIGED,       # Network layout configured
    REGISTERED,       # Traffics already been registered to agents
    RUNNING,          # Traffics are fired
    FINISHED,         # Traffics finished
    _________________
    =================
    State transition:

    ================================================================
    Single traffic state(Traced by TID, Traffic ID)

        REGISTERING -> REGISTERED -> RUNNING -> FINISHED

    ================================================================

    Global traffic state(Traced by GENID, Generator ID)

        STOPPED -> CREATED -> STARTED -> AGENTS_STARTED(ALL) ---------+
                                                                      |
             +-------NWCONFIGURED <---------------------- DEPLOYING <-+
             |                                                  A
             +----------------------------------------+         |
                                                      |         |
             +--------------- REGISTERED(ALL) <-------+         |
             |                                                  |
             +- RUNNING(ALL) -> TRAFFIC_FINISHED(ALL)-+         |
                                                      |         |
                                                      V         |
                                              GENREPORT(GID) ---+
                                                      |      hasnext
                          +---------------------------+
                          V                   alldone
                    ALL_FINISHED

    Definition of phase:

           Phase 0: 
            TrafficGenerator_0
            TrafficGenerator_1
            TrafficGenerator_2
            TrafficGenerator_3
                                 Phase 1:
                                  TrafficGenerator_13
                                  TrafficGenerator_1
                                  TrafficGenerator_2
                                                       Phase 2:
                                                        TrafficGenerator_10

      ------------------------------------------------------------------------->
        time

      NOTE: Network layout within the same phase should be the same
    """
    stopped = State(initial=True)
    created = State()
    started = State()
    nwconfigured = State()
    registered = State()
    running = State()
    phase_finished = State()
    finished = State()
    waitfor_agent_all_up = State()
    waitfor_nwlayout_done = State()
    waitfor_traffic_set = State()
    reportgened = State()

    start = Event(from_states=(stopped, phase_finished), to_state=started)
    create = Event(from_states=(stopped, started, phase_finished), to_state=created)
    wait_agent = Event(from_states=(stopped, started, created), to_state=waitfor_agent_all_up)
    deploy = Event(from_states=(created, waitfor_agent_all_up, started,
                phase_finished, reportgened), to_state=waitfor_nwlayout_done)
    wait_nwlayout = Event(from_states=(waitfor_nwlayout_done), to_state=nwconfigured)
    register = Event(from_states=(nwconfigured), to_state=waitfor_traffic_set)
    wait_traffic = Event(from_states=(waitfor_traffic_set), to_state=registered)
    fire = Event(from_states=(registered), to_state=running)
    phase_finish = Event(from_states=(running), to_state=phase_finished)
    finish = Event(from_states=(
        stopped, started, created, nwconfigured, registered, running,
        phase_finished, waitfor_agent_all_up,
        waitfor_nwlayout_done, waitfor_traffic_set, reportgened,
    ), to_state=(finished))
    genreport = Event(from_states=phase_finished, to_state=reportgened)

    def __init__(self, controller, lgr=None, trdelay=1):
        """
        @controller Controler object
        @trdelay    Seconds to delay before start next traffic
        @logger         Logging object
        """
        self.ctrl = controller
        TrafficState.lgr = lgr is None and logging or lgr
        self.current_phase = None
        self.current_genid = None
        self.traffic_delay = trdelay
        self.traf_running = True
        self.chk_delay = 10
        self.phases = []
        self.chk = TrafStatChk()

    def record_genid(self, genid):
        """Record running generator ID"""
        if not self.traf_running:
            return
        try:
            self.current_genid = genid
            with open(rt.tcfg.config[T_GENID][T_PATH], 'a') as fd:
                fd.write(to_string("{},{}\n", genid, str(dt.now())))
        except Exception as ex:
            TrafficState.lgr.error(to_string("Record genid failed: {}", ex))

    def update_stat(self, item, stat, cond=None):
        self.chk.traffic_stat[item] = stat
        if cond is not None:
            self.check(cond)

    def check(self, cond):
        """Check for condition"""
        TrafficState.lgr.info(to_string("Current state: {}, check for: {}", str(self.current_state), cond))
        if hasattr(self.chk, cond) and getattr(self.chk, cond)():
            getattr(self.chk, "_"+cond).set()

    @after('wait_agent')
    def do_waitfor_agent_all_up(self):
        """Wait for expected agents startup"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Wait for agents get ready", str(self.current_state)))
        to_console("Wait for agents get ready")
        try:
            self.chk._is_agents_up.wait()
        except KeyboardInterrupt:
            TrafficState.lgr.info("Terminating ...")
        except Exception as rex:
            TrafficState.lgr.error(to_string("Wait for agent up: {}", ex))

    @after('wait_nwlayout')
    def do_waitfor_nwlayout_done(self):
        """Wait for network configure to be done"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Wait for network layout done: {}", str(self.current_state)))
        to_console("Wait for network layout done")
        try:
            self.chk._is_nwlayout_done.wait()
        except KeyboardInterrupt:
            TrafficState.lgr.info("Terminating ...")
        except Exception as ex:
            TrafficState.lgr.error(to_string("Wait for network layout done: {}", ex))

    @after('wait_traffic')
    def do_waitfor_traffic_set(self):
        """Wait for traffic all registered on agents"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Wait for traffic registered: {}", str(self.current_state)))
        to_console("Wait for traffic registered")
        try:
            self.chk._is_traffic_registered.wait()
        except KeyboardInterrupt:
            TrafficState.lgr.info("Terminating ...")
        except Exception as rex:
            TrafficState.lgr.error(to_string("Wait for get traffic registered: {}", ex))

    @before('create')
    def do_create(self):
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Create traffic from configure: {}", str(self.current_state)))
        to_console("Loading traffics")
        self.phases = create_phases(rt.trcfg, rt.nwcfg)
        TrafficState.lgr.info(to_string("Total phase: [{}]", len(self.phases)))
        self.next_phase = self.yield_traffic()

    @after('start')
    def do_start(self):
        """Start traffic deployment"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Start traffic sm: {}", str(self.current_state)))
        try:
            self.create()
            TrafficState.lgr.info("Starting agents ...")
            to_console("Starting agents ...")
            start_agents(self.chk.expected_agents)
            self.wait_agent()
            try:
                while self.traf_running:
#                    gid = self.next()
                    self.current_phase = next(self.next_phase)
                    gid = self.record_phase()
                    if gid is not None:
                        self.start_phase()
            except StopIteration:
                TrafficState.lgr.info("All traffic generator done")
#            [self.start_phase() for tg in self.next_phase]
        except KeyboardInterrupt:
            TrafficState.lgr.info("Terminating ...")
        except Exception as ex:
            TrafficState.lgr.error(to_string("Traffic runtime error: {}", ex))
        self.finish()

    def yield_traffic(self):
        """Yield traffic generator"""
        if not self.traf_running:
            return
        yield from self.phases

    def record_phase(self):
        """Record running phase"""
        if not self.traf_running:
            return
        nwlayoutname = getnwlayoutname(self.current_phase.nwlayoutid)
        cfg = {
            T_NWLAYOUT: deepcopy(rt.nwcfg.config.get(nwlayoutname))
        }
        self.current_phase.genid = self.ctrl.storage.insert_config(cfg)
        to_console("Current phase: {}", self.current_phase)
        self.record_genid(self.current_phase.genid)
        return self.current_phase

    def start_phase(self):
        """Start one traffic"""
        try:
            if not self.traf_running:
                return
            TrafficState.lgr.info(to_string("Start one traffic"))
            self.chk.clear_all()
            phase_stat = [
                self.deploy, self.wait_nwlayout,\
                self.register, self.wait_traffic, self.fire,\
                self.phase_finish,\
                self.genreport,
            ]
            [transition(self, stat) for stat in phase_stat if self.traf_running]
        except Exception as ex:
            TrafficState.lgr.error(to_string("Traffic state transition failed: {}", str(ex)))

    @after('deploy')
    def do_deploy(self):
        """Deploy network layout based on configure"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Deploy network layout: {}", str(self.current_state)))
        to_console("Deploying network layout")
        phase = self.current_phase
        if self.ctrl.current_nwlayout != phase.nwlayoutid:
            nwlayoutname = getnwlayoutname(phase.nwlayoutid)
            publish_nwlayout(nwlayoutname,
                rt.nwcfg, rt.tcfg,
                self.chk, self.current_phase.genid,
                self.ctrl.mqclient)
            self.ctrl.current_nwlayout = tuple(phase.nwlayoutid.split(':'))
        else:
            self.chk._is_nwlayout_done.set()
        TrafficState.lgr.info(to_string("Current network layout: {}", self.ctrl.current_nwlayout))

    @after('register')
    def do_register(self):
        """Register traffic to agents
        Ex:
            phase0 [tg0, tg1, tg2]
            phase1 [tg5, tg3]
        """
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Register traffic task: {}", str(self.current_state)))
        to_console("Registering traffic")
        phase = self.current_phase
        TrafficState.lgr.info(to_string("Register traffic: [{}]", str(phase)))
        if not publish_phase(phase, self.chk, self.ctrl.mqclient, rt.tcfg.enable_localdebug):
            self.traf_running = False

    @after('fire')
    def do_fire(self):
        """Tell agents to fire registerd traffic"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Fire traffic: {}", str(self.current_state)))
        to_console("Firing traffics ...")
        for agent in self.chk.available_agents.keys():
            if not self.traf_running:
                break
            to_console(to_string("Fire on {}", agent))
            data = {
                T_CLIENTID: agent,
                T_TRAFFIC_TYPE: TrafficType.START.name,
            }
            pub_traffic(self.ctrl.mqclient, rt.tcfg.mqtt_qos, data)

    @before('phase_finish')
    def do_phase_finish(self):
        """Waif for one traffic finished"""
        if not self.traf_running:
            return
        TrafficState.lgr.info(to_string("Traffic finished: {}", str(self.current_state)))
        try:
            self.chk._is_phase_finished.wait()
        except KeyboardInterrupt:
            TrafficState.lgr.info("Terminating ...")
        except Exception as rex:
            TrafficState.lgr.error(to_string("Traffic runtime error: {}", rex))

    @after('genreport')
    def do_genreport(self):
        """Analyze collected data and generate report"""
        TrafficState.lgr.info(to_string("Try analysing: {}", str(self.current_state)))
        if not self.traf_running:
            return
        if rt.tcfg.storagetype in [\
            (TrafficStorage.DB.name, StorageType.MongoDB.name),]:
            if self.current_genid is not None:
                tmg = ProcTaskManager(with_child=True)
                nodes = []
                for agent in self.chk.available_agents.values():
                    nodes = [n for n in agent.nodes]
                ReportAdapter.guess_proto(nodes)
                tmg.create_task(ReportAdapter.generate,\
                    self.current_genid,\
                    list(self.current_phase.noi.get(T_GATEWAY)),\
                    list(self.current_phase.noi.get(T_NODES)))
                tmg.waitall()
        else:
            TrafficState.lgr.info(to_string("Unsupported storage type: {}", str(rt.tcfg.storagetype)))

    @after('finish')
    def do_finish(self):
        """All traffic finished"""
        TrafficState.lgr.info(to_string("All finished: {}", str(self.current_state)))
#        if not self.traf_running:
#            return

        try:
            self.phases.clear()
            TrafficState.lgr.info("Stopping agents ...")
            stop_agents(self.ctrl.mqclient, rt.tcfg.mqtt_qos)

            if len(self.chk.available_agents) > 0:
                TrafficState.lgr.info("Wait for last notifications")
                self.chk._is_agents_unregistered.wait(int(rt.trcfg.config.get(T_TRAFFIC_FINISH_DELAY)))
        except KeyboardInterrupt:
            TrafficState.lgr.info("Terminating ...")
            to_console("Terminating ...")
#            self.chk.set_all()
        except Exception as ex:
            TrafficState.lgr.error(to_string("Exception on stopping agents: {}", ex))

        TrafficState.lgr.info("Stopping controller ...")
        self.ctrl.teardown()
#        self.chk.done.wait(rt.trcfg.config.get(T_TRAFFIC_FINISH_DELAY))
#        self.chk.done.clear()

        try:
            if len(self.chk.available_agents) > 0:
                TrafficState.lgr.info("Force stopping agents ...")
                force_stop_agents(self.chk.expected_agents)
        except Exception as ex:
            TrafficState.lgr.error(to_string("Exception on force stopping agents: {}", ex))

        TrafficState.lgr.info("Agents stopped")

if __name__ == '__main__':
    pass
#    ts = TrafficState("AutoTraffic")
#    ts.start()
#    ts.deploy()
#    ts.register()
#    ts.finish()
