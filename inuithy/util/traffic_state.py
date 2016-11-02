""" Traffic state transition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_TID, T_GENID, T_TRAFFIC_TYPE,\
T_CLIENTID, T_NODE, T_HOST, T_DURATION, T_TIMESLOT, T_SENDER,\
T_RECIPIENT, T_PKGSIZE, string_write, T_PATH, T_NWLAYOUT, T_PANID,\
T_NODES
from inuithy.util.cmd_helper import pub_traffic
from state_machine import State, Event, acts_as_state_machine,\
after, before, InvalidStateTransition
from datetime import datetime as dt
from copy import deepcopy
import logging, random, string


class TrafStatChk(object):
    """Traffic status checker maintains a serial of check items for traffic and defines conditions for them
    @nwlayout       Network layout deployment status
    @traffire       Traffic fire status 
    @traffic_set    Traffic register status
    @expected_agents:  list of agents
    @available_agents: agentid => AgentInfo
    """
    def __init__(self, logger=None):
        if logger == None:
            self.logger = logging
        else:
            self.logger = logger
        self.nwlayout = {}
        self.traffire = {}
        self.traffic_set = {}
        self.expected_agents = []
        self.available_agents = {}
        self.host2aid = {}
        self.node2host = {}

    def create_nwlayout(self, nwid, nodes):
        self.logger.info("Create network layout checker")
        if None == nodes or nwid == None: return
        self.nwlayout[nwid] = {node:False for node in nodes}

    def create_traffire(self):
        self.logger.info("Create traffire fire state checker")
        [self.traffire.__setitem__(agentid, False) for agentid in self.available_agents.keys()]

    def is_network_layout_done(self, avaliable):
        self.logger.info("Is network layout done")
        if available == None or len(available) == 0:
            raise ValueError("No agent available")
        for nw in self.nwlayout.values():
            chks = [chk for chk in nw.values() if chk == True]
            if len(chks) != len(nw): return False
        return True

    def is_traffic_finished(self):
        self.logger.info("Is traffic finished")
        if len([chk for chk in self.traffire.values() if chk == False]) == 0:
            return True
        return False

    def is_traffic_all_set(self):
        self.logger.info("Is traffic all set")
        if len(self.__available_agents) == 0:
            raise ValueError("No agent available")
        if len([chk for chk in self.traffic_set.values() if chk == False]) == 0:
            return True
        return False

    def is_agents_all_up(self, expected, available):
        self.logger.info("Check for agents availablity")
        if len(expected) != len(available): return False

        for ai in available.values():
            if ai.host not in expected: return False

        if len(self.host2aid) == 0:
            return False
        return True

@acts_as_state_machine
class TrafficState:
    """
    @controller Controller object
    @logger         For log handling

    STOP,             # Initial status, traffic not yet launched
    STARTED,          # Traffic routine started
    NWCONFIGED,       # Network layout configured
    REGISTERED,       # Traffics already been registered to agents
    RUNNING,          # Traffics are fired
    FINISHED,         # Traffics finished
    """
    stopped = State(initial =True)
    started = State()
    nwconfigured = State()
    registered = State()
    running = State()
    traffic_finished = State()
    finished = State()
    waitfor_agent_all_up = State()
    waitfor_nwlayout_done = State()
    waitfor_traffic_all_set = State()

    start = Event(from_states =(stopped), to_state =started)
    wait_agent = Event(from_states =(started), to_state =waitfor_agent_all_up)
    deploy = Event(from_states =(waitfor_agent_all_up, started, traffic_finished), to_state =waitfor_nwlayout_done)
    wait_nwlayout = Event(from_states =(waitfor_nwlayout_done), to_state =nwconfigured)
    register = Event(from_states =(nwconfigured), to_state =waitfor_traffic_all_set)
    wait_traffic = Event(from_states =(waitfor_traffic_all_set), to_state =registered)
    fire = Event(from_states =(registered), to_state =running)
    traffic_finish = Event(from_states =(running), to_state =traffic_finished)
    finish = Event(from_states =(
        stopped, started, nwconfigured, registered, running,
        traffic_finished, waitfor_agent_all_up,
        waitfor_nwlayout_done, waitfor_traffic_all_set,
    ), to_state =(finished))

    def __init__(self, controller, logger=None, trdelay=1):
        """
        @controller Controler object
        @trdelay    Seconds to delay before start next traffic
        @logger         Logging object
        """
        self.ctrl = controller
        if logger == None: self.logger = logging
        else: self.logger = logger
        self.__current_tg = None
        self.traffic_delay = trdelay
        self.running = True

    def record_genid(self, genid):
        try:
            with open(self.ctrl.tcfg.config[T_GENID][T_PATH], 'a') as fd:
                fd.write(string_write("{},{}\n", genid, str(dt.now())))
        except Exception as ex:
            self.logger.error(string_write("Record genid failed: {}", ex))

    @after('wait_agent')
    def do_waitfor_agent_all_up(self):
        self.logger.info(string_write("Wait for agents all up", str(self.current_state)))
        while self.running and not self.ctrl.is_agents_all_up(): time.sleep(2)

    @after('wait_nwlayout')
    def do_waitfor_nwlayout_done(self):
        self.logger.info(string_write("Wait for network layout done: {}", str(self.current_state)))
        while self.running and not self.ctrl.is_network_layout_done(): time.sleep(2)

    @after('wait_traffic')
    def do_waitfor_traffic_all_set(self):
        self.logger.info(string_write("Wait for traffic all set: {}", str(self.current_state)))
        while self.running and not self.ctrl.is_traffic_all_set(): time.sleep(2)

    @after('start')
    def do_start(self):
        self.logger.info(string_write("Start traffic sm: {}", str(self.current_state)))
        try:
            self.trgens = create_traffics(self.ctrl.trcfg, self.ctrl.nwcfg)
            self.logger.info(string_write("Total generator: [{}]", len(self.trgens)))
            start_agents(self.ctrl.expected_agents)
            self.wait_agent()
            [self.start_one(tg) for tg in self.trgens]
        except Exception as rex:
            self.logger.error(string_write("Traffic runtime error: {}", rex))
        finally:
            self.finish()

    def start_one(self, tg):
        try:
            self.logger.info(string_write("Deploy network begin"))
            self.__current_tg = tg
            nwlayoutname = getnwlayoutname(tg.nwlayoutid)
            cfg = {
                T_NWLAYOUT: deepcopy(self.ctrl.nwcfg.config.get(nwlayoutname))
            }
            tg.genid = self.ctrl.storage.insert_config(cfg)
            self.record_genid(tg.genid)
            self.deploy()
            self.wait_nwlayout()
            self.register()
            self.wait_traffic()
            self.fire()
            self.traffic_finish()
        except Exception as ex:
            self.logger.error(string_write("Traffic state transition failed: {}", str(ex)))

    def config_network(self, nwlayoutname):
        """Configure network by given network layout
        """
        self.logger.info(string_write("Config network: [{}]", nwlayoutname))
        for name, subnet in self.ctrl.nwcfg.config.get(nwlayoutname).items():
            data = subnet
            self.ctrl.create_nwlayout_chk(subnet.get(T_PANID), subnet.get(T_NODES))
            for node in subnet.get(T_NODES):
                target_host = self.ctrl.node2host.get(node)
                if None == target_host:
                    raise ValueError(string_write("Node [{}] not found on any agent", node))
                data[T_HOST] = target_host
                data[T_CLIENTID] = self.ctrl.host2aid.get(target_host)
                data[T_GENID] = self.__current_tg.genid
                data[T_NODE] = node
                data[T_TRAFFIC_TYPE] = TrafficType.JOIN.name
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)

    @before('deploy')
    def do_deploy(self, tg=None):
        self.logger.info(string_write("Deploy network layout: {}", str(self.current_state)))
        if tg == None: tg = self.__current_tg
        self.logger.info(string_write("Deploy network: {}", tg.nwlayoutid))
        self.logger.info(string_write("Current traffic [{}]", str(tg)))
        if self.ctrl.current_nwlayout != tg.nwlayoutid:
            self.config_network(getnwlayoutname(tg.nwlayoutid))

    @after('register')
    def do_register(self, tg=None):
        self.logger.info(string_write("Register traffic task: {}", str(self.current_state)))
        if tg == None: tg = self.__current_tg
        self.logger.info(string_write("Register traffic: [{}]", str(tg)))
        for tr in tg.traffics:
            try:
                self.logger.debug(string_write("TRAFFIC: {}", tr))
                target_host = self.ctrl.node2host.get(tr.sender)
                tid = ''.join([random.choice(string.hexdigits) for i in range(7)])
                data = {
                T_TID:          tid,
                T_GENID:        self.__current_tg.genid,
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
                self.ctrl.traffic_set_chk[tid] = False
            except Exception as ex:
                self.logger.error(string_write("Exception on registering traffic, network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, str(ex)))

    @after('fire')
    def do_fire(self):
        self.logger.info(string_write("Fire traffic: {}", str(self.current_state)))
        self.ctrl.create_traffire_chk()
        data = {
            T_TRAFFIC_TYPE: TrafficType.START.name,
        }
        pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)      

    @before('traffic_finish')
    def do_traffic_finish(self):
        self.logger.info(string_write("Traffic finished: {}", str(self.current_state)))
        while self.running and not self.ctrl.is_traffic_finished(): time.sleep(2)
        self.ctrl.traffire_chk = {}

    @after('finish')
    def do_finish(self):
        self.logger.info(string_write("All finished: {}", str(self.current_state)))
#        self.ctrl.teardown()

def transition(sm, event, event_name):
    try:
        event()
    except InvalidStateTransition as ex:
        console_write("{}: {} => {} Failed", sm, event, event_name)

if __name__ == '__main__':
    pass
#    ts = TrafficState("AutoTraffic")
#    ts.start()
#    ts.deploy()
#    ts.register()
#    ts.finish()
