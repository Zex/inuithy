""" Traffic state transition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TID, T_GENID, T_TRAFFIC_TYPE,\
T_CLIENTID, T_NODE, T_HOST, T_DURATION, T_TIMESLOT, T_SENDER,\
T_RECIPIENT, T_PKGSIZE, T_NODES, T_PATH, T_NWLAYOUT, T_PANID,\
console_write, string_write, TrafficType, T_TRAFFIC_FINISH_DELAY,\
TrafficStorage, StorageType, INUITHY_CONFIG_PATH
from inuithy.util.helper import getnwlayoutname
from inuithy.util.cmd_helper import pub_traffic, start_agents
from inuithy.common.traffic import create_traffics
from inuithy.analysis.pandas_plugin import PandasAnalyzer
from inuithy.util.task_manager import ProcTaskManager
from state_machine import State, Event, acts_as_state_machine,\
after, before, InvalidStateTransition
from datetime import datetime as dt
from copy import deepcopy
import logging
import random
import string
import time

class TrafStatChk(object):
    """Traffic status checker maintains a serial of check items
    for traffic and defines conditions for them
    @nwlayout       Network layout deployment status
    @traffire       Traffic fire status
    @traffic_set    Traffic register status
    @expected_agents:  list of agents
    @available_agents: agentid => AgentInfo
    """
    def __init__(self, lgr=None):
        if lgr is None:
            self.lgr = logging
        else:
            self.lgr = lgr
        self.nwlayout = {}
        self.traffire = {}
        self.traffic_set = {}
        self.expected_agents = []
        self.available_agents = {}
        self.host2aid = {}
        self.node2host = {}

    def create_nwlayout(self, nwid, nodes):
        """Create map of network layout configure"""
        self.lgr.info("Create network layout checker")
        if nodes is None or nwid is None:
            return
        self.nwlayout[nwid] = {node:False for node in nodes}

    def create_traffire(self):
        """Create map of traffic to fire"""
        self.lgr.info("Create traffire fire state checker")
        [self.traffire.__setitem__(agentid, False) for agentid in self.available_agents.keys()]

    def is_network_layout_done(self):
        """Whether network layout configured"""
        self.lgr.info("Is network layout done")
        try:
            if self.available_agents is None or len(self.available_agents) == 0:
                raise ValueError("No agent available")
            for nw in self.nwlayout.values():
                chks = [chk for chk in nw.values() if chk is True]
                if len(chks) != len(nw):
                    return False
            return True
        except Exception as ex:
            self.lgr.error(string_write("Failed to check network layout: {}", ex))
            return False

    def is_traffic_finished(self):
        """Whether traffic finished"""
        self.lgr.info("Is traffic finished")
        try:
            if len([chk for chk in self.traffire.values() if chk is False]) == 0:
                return True
            return False
        except Exception as ex:
            self.lgr.error(string_write("Failed to check traffic status: {}", ex))
            return False

    def is_traffic_all_set(self):
        """Whether traffic all registed"""
        self.lgr.info("Is traffic all set")
        try:
            if len(self.available_agents) == 0:
                raise ValueError("No agent available")
            if len([chk for chk in self.traffic_set.values() if chk is False]) == 0:
                return True
            return False
        except Exception as ex:
            self.lgr.error(string_write("Failed to check traffic register status", ex))
            return False

    def is_agents_all_up(self):
        """Whether expected agents all started"""
        self.lgr.info("Check for agents availability")
        try:
            expected = self.expected_agents
            available = self.available_agents
            if len(self.host2aid) == 0:
                return False
            if len(expected) != len(available):
                return False
            for ai in available.values():
                if ai.host not in expected:
                    return False
            return True
        except Exception as ex:
            self.lgr.error(string_write("Failed to check agent availability", ex))
            return False

def transition(sm, event, event_name):
    """Transite between states"""
    try:
        event()
    except InvalidStateTransition as ex:
        console_write("{}: {} => {} Failed: {}", sm, event, event_name, ex)

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
    """
    stopped = State(initial=True)
    created = State()
    started = State()
    nwconfigured = State()
    registered = State()
    running = State()
    traffic_finished = State()
    finished = State()
    waitfor_agent_all_up = State()
    waitfor_nwlayout_done = State()
    waitfor_traffic_all_set = State()
    reportgened = State()

    create = Event(from_states=(stopped, started), to_state=created)
    start = Event(from_states=(stopped, created), to_state=started)
    wait_agent = Event(from_states=(started, created), to_state=waitfor_agent_all_up)
    deploy = Event(from_states=(created, waitfor_agent_all_up, started, traffic_finished),\
                to_state=waitfor_nwlayout_done)
    wait_nwlayout = Event(from_states=(waitfor_nwlayout_done), to_state=nwconfigured)
    register = Event(from_states=(nwconfigured), to_state=waitfor_traffic_all_set)
    wait_traffic = Event(from_states=(waitfor_traffic_all_set), to_state=registered)
    fire = Event(from_states=(registered), to_state=running)
    traffic_finish = Event(from_states=(running), to_state=traffic_finished)
    finish = Event(from_states=(
        stopped, started, created, nwconfigured, registered, running,
        traffic_finished, waitfor_agent_all_up,
        waitfor_nwlayout_done, waitfor_traffic_all_set, reportgened,
    ), to_state=(finished))
    genreport = Event(from_states=traffic_finished, to_state=reportgened)

    def __init__(self, controller, lgr=None, trdelay=1):
        """
        @controller Controler object
        @trdelay    Seconds to delay before start next traffic
        @logger         Logging object
        """
        self.ctrl = controller
        if lgr is None:
            self.lgr = logging
        else:
            self.lgr = lgr
        self.current_tg = None
        self.current_genid = None
        self.traffic_delay = trdelay
        self.running = True

    def record_genid(self, genid):
        """Record running generator ID"""
        try:
            self.current_genid = genid
            with open(self.ctrl.tcfg.config[T_GENID][T_PATH], 'a') as fd:
                fd.write(string_write("{},{}\n", genid, str(dt.now())))
        except Exception as ex:
            self.lgr.error(string_write("Record genid failed: {}", ex))

    @after('wait_agent')
    def do_waitfor_agent_all_up(self):
        """Wait for expected agents startup"""
        self.lgr.info(string_write("Wait for agents all up", str(self.current_state)))
        while self.running and not self.ctrl.chk.is_agents_all_up():
            time.sleep(2)

    @after('wait_nwlayout')
    def do_waitfor_nwlayout_done(self):
        """Wait for network configure to be done"""
        self.lgr.info(string_write("Wait for network layout done: {}", str(self.current_state)))
        while self.running and not self.ctrl.chk.is_network_layout_done():
            time.sleep(2)

    @after('wait_traffic')
    def do_waitfor_traffic_all_set(self):
        """Wait for traffic all registered on agents"""
        self.lgr.info(string_write("Wait for traffic all set: {}", str(self.current_state)))
        while self.running and not self.ctrl.chk.is_traffic_all_set():
            time.sleep(2)

    @before('create')
    def do_create(self):
        self.lgr.info(string_write("Create traffic from configure: {}", str(self.current_state)))
        if not self.running:
            return
        self.trgens = create_traffics(self.ctrl.trcfg, self.ctrl.nwcfg)
        self.next_tgs = self.yield_traffic()
        self.lgr.info(string_write("Total generator: [{}]", len(self.trgens)))

    @after('start')
    def do_start(self):
        """Start traffic deployment"""
        self.lgr.info(string_write("Start traffic sm: {}", str(self.current_state)))
        try:
            self.create()
            start_agents(self.ctrl.chk.expected_agents)
            self.wait_agent()
            try:
                self.next()
                self.start_one()
            except StopIteration:
                self.lgr.info("All traffic generator done")
#            [self.start_one() for tg in self.next_tgs]
        except Exception as rex:
            self.lgr.error(string_write("Traffic runtime error: {}", rex))
        self.finish()

    def yield_traffic(self):
        """Yield traffic generator"""
        if not self.running:
            return
        for tg in self.trgens:
            yield tg

    def next(self):
        """Next traffic generator"""
        if not self.running:
            return
        self.current_tg = next(self.next_tgs)
        nwlayoutname = getnwlayoutname(self.current_tg.nwlayoutid)
        cfg = {
            T_NWLAYOUT: deepcopy(self.ctrl.nwcfg.config.get(nwlayoutname))
        }
        self.current_tg.genid = self.ctrl.storage.insert_config(cfg)
        self.record_genid(self.current_tg.genid)
        return self.current_tg

    def start_one(self):
        """Start one traffic"""
        try:
            self.lgr.info(string_write("Deploy network begin"))
            stat_transition = [
                self.deploy, self.wait_nwlayout, self.register, self.wait_traffic,
                self.fire, self.traffic_finish, self.genreport,
            ]
            [stat() for stat in stat_transition if self.running]
        except Exception as ex:
            self.lgr.error(string_write("Traffic state transition failed: {}", str(ex)))

    def config_network(self, nwlayoutname):
        """Configure network by given network layout"""
        self.lgr.info(string_write("Config network: [{}]", nwlayoutname))
        if not self.running:
            return
        for subnet in self.ctrl.nwcfg.config.get(nwlayoutname).values():
            data = deepcopy(subnet)
            del data[T_NODES]
            self.ctrl.chk.create_nwlayout(subnet.get(T_PANID), subnet.get(T_NODES))
            for node in subnet.get(T_NODES):
                target_host = self.ctrl.node2host.get(node)
                if target_host is None:
                    raise ValueError(string_write("Node [{}] not found on any agent", node))
                data[T_HOST] = target_host
                data[T_CLIENTID] = self.ctrl.host2aid.get(target_host)
                data[T_GENID] = self.current_tg.genid
                data[T_NODE] = node
                data[T_TRAFFIC_TYPE] = TrafficType.JOIN.name
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)

    @after('deploy')
    def do_deploy(self, tg=None):
        """Deploy network layout based on configure"""
        self.lgr.info(string_write("Deploy network layout: {}", str(self.current_state)))
        if tg is None:
            tg = self.current_tg
        self.lgr.info(string_write("Deploy network: {}", tg.nwlayoutid))
        self.lgr.info(string_write("Current traffic [{}]", str(tg)))
        if self.ctrl.current_nwlayout != tg.nwlayoutid:
            self.config_network(getnwlayoutname(tg.nwlayoutid))

    @after('register')
    def do_register(self, tg=None):
        """Register traffic to agents"""
        self.lgr.info(string_write("Register traffic task: {}", str(self.current_state)))
        if tg is None:
            tg = self.current_tg
        self.lgr.info(string_write("Register traffic: [{}]", str(tg)))
        for tr in tg.traffics:
            try:
                self.lgr.debug(string_write("TRAFFIC: {}", tr))
                target_host = self.ctrl.node2host.get(tr.sender)
                tid = ''.join([random.choice(string.hexdigits) for _ in range(7)])
                data = {
                    T_TID:          tid,
                    T_GENID:        self.current_tg.genid,
                    T_TRAFFIC_TYPE: TrafficType.SCMD.name,
                    T_CLIENTID:     self.ctrl.host2aid.get(target_host),
                    T_NODE:         tr.sender,
                    T_HOST:         target_host,
                    T_DURATION:     tg.duration,
                    T_TIMESLOT:     tg.timeslot,
                    T_SENDER:       tr.sender,
                    T_RECIPIENT:    tr.recipient,
                    T_PKGSIZE:      tr.pkgsize,
                }
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)
                self.ctrl.chk.traffic_set[tid] = False
            except Exception as ex:
                self.lgr.error(string_write(
                    "Exception on registering traffic, network [{}], traffic [{}]: {}",
                    tg.nwlayoutid, tg.traffic_name, str(ex)))

    @after('fire')
    def do_fire(self):
        """Tell agents to fire registerd traffic"""
        self.lgr.info(string_write("Fire traffic: {}", str(self.current_state)))
        self.ctrl.chk.create_traffire()
        for agent in self.ctrl.chk.available_agents.keys():
            console_write(string_write("Fire on {}", agent))
            data = {
                T_CLIENTID: agent,
                T_TRAFFIC_TYPE: TrafficType.START.name,
            }
            pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)

    @before('traffic_finish')
    def do_traffic_finish(self):
        """Waif for one traffic finished"""
        self.lgr.info(string_write("Traffic finished: {}", str(self.current_state)))
        while self.running and not self.ctrl.chk.is_traffic_finished():
            time.sleep(2)
        self.ctrl.chk.traffire = {}

    @after('genreport')
    def do_genreport(self):
        """Analyze collected data and generate report"""
        self.lgr.info(string_write("Try analysing: {}", str(self.current_state)))
        if self.ctrl.tcfg.storagetype in [\
            (TrafficStorage.DB.name, StorageType.MongoDB.name),]:
            if self.current_genid is not None:
                tmg = ProcTaskManager()
                tmg.create_task(PandasAnalyzer.gen_report, (INUITHY_CONFIG_PATH, self.current_genid,))
                tmg.waitall()
#                PandasAnalyzer.gen_report(genid=self.current_genid)
        else:
            self.lgr.info(string_write("Unsupported storage type: {}", str(self.ctrl.tcfg.storagetype)))

    @after('finish')
    def do_finish(self):
        """All traffic finished"""
        self.lgr.info(string_write("All finished: {}", str(self.current_state)))
        console_write("Wait for last notifications")
        if not self.ctrl.tcfg.enable_localdebug:
            time.sleep(self.ctrl.tcfg.config.get(T_TRAFFIC_FINISH_DELAY))
        self.ctrl.teardown()


if __name__ == '__main__':
    pass
#    ts = TrafficState("AutoTraffic")
#    ts.start()
#    ts.deploy()
#    ts.register()
#    ts.finish()
