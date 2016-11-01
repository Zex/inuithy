## Traffic state transition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging, random, string
from datetime import datetime as dt
from state_machine import State, Event, acts_as_state_machine, after, before, InvalidStateTransition
from inuithy.util.cmd_helper import *
from inuithy.common.traffic import *
from copy import deepcopy

@acts_as_state_machine
class TrafficState:
    """
    @controller Controller object
    @lg         For log handling

    STOP,             # Initial status, traffic not yet launched
    STARTED,          # Traffic routine started
    NWCONFIGED,       # Network layout configured
    REGISTERED,       # Traffics already been registered to agents
    RUNNING,          # Traffics are fired
    FINISHED,         # Traffics finished
    """
    stopped                 = State(initial =True)
    started                 = State()
    nwconfigured            = State()
    registered              = State()
    running                 = State()
    traffic_finished        = State()
    finished                = State()
    waitfor_agent_all_up    = State()
    waitfor_nwlayout_done   = State()
    waitfor_traffic_all_set = State()

    start           = Event(from_states=(stopped), to_state=started)
    wait_agent      = Event(from_states=(started), to_state=waitfor_agent_all_up)
    deploy          = Event(from_states=(waitfor_agent_all_up, started, traffic_finished), to_state=waitfor_nwlayout_done)
    wait_nwlayout   = Event(from_states=(waitfor_nwlayout_done), to_state=nwconfigured)
    register        = Event(from_states=(nwconfigured), to_state=waitfor_traffic_all_set)
    wait_traffic    = Event(from_states=(waitfor_traffic_all_set), to_state=registered)
    fire            = Event(from_states=(registered), to_state=running)
    traffic_finish  = Event(from_states=(running), to_state=traffic_finished)
    finish          = Event(from_states=(
        stopped, started, nwconfigured, registered, running,
        traffic_finished, waitfor_agent_all_up,
        waitfor_nwlayout_done, waitfor_traffic_all_set,
    ), to_state=(finished))

    def __init__(self, controller, lg=None, trdelay=1):
        """
        @controller Controler object
        @trdelay    Seconds to delay before start next traffic
        @lg         Logging object
        """
        self.ctrl = controller
        if lg == None: self.lg = logging
        else: self.lg = lg
        self.__current_tg = None
        self.traffic_delay = trdelay
        self.running = True

    def record_genid(self, genid):
        try:
            with open(self.ctrl.tcfg.config[CFGKW_GENID][CFGKW_PATH], 'a') as fd:
                fd.write(string_write("{},{}\n", genid, str(dt.now())))
        except Exception as ex:
            self.lg.error(string_write("Record genid failed: {}", ex))

    @after('wait_agent')
    def do_waitfor_agent_all_up(self):
        self.lg.info(string_write("Wait for agents all up", str(self.current_state)))
        while self.running and not self.ctrl.is_agents_all_up(): time.sleep(2)

    @after('wait_nwlayout')
    def do_waitfor_nwlayout_done(self):
        self.lg.info(string_write("Wait for network layout done: {}", str(self.current_state)))
        while self.running and not self.ctrl.is_network_layout_done(): time.sleep(2)

    @after('wait_traffic')
    def do_waitfor_traffic_all_set(self):
        self.lg.info(string_write("Wait for traffic all set: {}", str(self.current_state)))
        while self.running and not self.ctrl.is_traffic_all_set(): time.sleep(2)

    @after('start')
    def do_start(self):
        self.lg.info(string_write("Start traffic sm: {}", str(self.current_state)))
        try:
            self.trgens = create_traffics(self.ctrl.trcfg, self.ctrl.nwcfg)
            self.lg.info(string_write("Total generator: [{}]", len(self.trgens)))
            start_agents(self.ctrl.expected_agents)
            self.wait_agent()
            [self.start_one(tg) for tg in self.trgens]
        except Exception as rex:
            self.lg.error(string_write("Traffic runtime error: {}", rex))
        finally:
            self.finish()

    def start_one(self, tg):
        try:
            self.lg.info(string_write("Deploy network begin"))
            self.__current_tg = tg
            nwlayoutname = getnwlayoutname(tg.nwlayoutid)
            cfg = {
                CFGKW_NWLAYOUT: deepcopy(self.ctrl.nwcfg.config.get(nwlayoutname))
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
            self.lg.error(string_write("Traffic state transition failed: {}", str(ex)))

    def config_network(self, nwlayoutname):
        """Configure network by given network layout
        """
        self.lg.info(string_write("Config network: [{}]", nwlayoutname))
        for name, subnet in self.ctrl.nwcfg.config.get(nwlayoutname).items():
            data = subnet
            self.ctrl.create_nwlayout_chk(subnet.get(CFGKW_PANID), subnet.get(CFGKW_NODES))
            for node in subnet.get(CFGKW_NODES):
                target_host = self.ctrl.node2host.get(node)
                if None == target_host:
                    raise ValueError(string_write("Node [{}] not found on any agent", node))
                data[CFGKW_HOST]         = target_host
                data[CFGKW_CLIENTID]     = self.ctrl.host2aid.get(target_host)
                data[CFGKW_GENID]        = self.__current_tg.genid
                data[CFGKW_NODE]         = node
                data[CFGKW_TRAFFIC_TYPE] = TrafficType.JOIN.name
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)

    @before('deploy')
    def do_deploy(self, tg=None):
        self.lg.info(string_write("Deploy network layout: {}", str(self.current_state)))
        if tg == None: tg = self.__current_tg
        self.lg.info(string_write("Deploy network: {}", tg.nwlayoutid))
        self.lg.info(string_write("Current traffic [{}]", str(tg)))
        if self.ctrl.current_nwlayout != tg.nwlayoutid:
            self.config_network(getnwlayoutname(tg.nwlayoutid))

    @after('register')
    def do_register(self, tg=None):
        self.lg.info(string_write("Register traffic task: {}", str(self.current_state)))
        if tg == None: tg = self.__current_tg
        self.lg.info(string_write("Register traffic: [{}]", str(tg)))
        for tr in tg.traffics:
            try:
                self.lg.debug(string_write("TRAFFIC: {}", tr))
                target_host = self.ctrl.node2host.get(tr.sender)
                tid = ''.join([random.choice(string.hexdigits) for i in range(7)])
                data = {
                CFGKW_TID:          tid,
                CFGKW_GENID:        self.__current_tg.genid,
                CFGKW_TRAFFIC_TYPE: TrafficType.SCMD.name,
                CFGKW_CLIENTID:     self.ctrl.host2aid.get(target_host),
                CFGKW_NODE:         tr.sender,
                CFGKW_HOST:         target_host,
                CFGKW_DURATION:     tg.duration,
                CFGKW_TIMESLOT:     tg.timeslot,
                CFGKW_SENDER:       tr.sender,
                CFGKW_RECIPIENT:    tr.recipient,
                CFGKW_PKGSIZE:      tr.pkgsize,
                }
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)
                self.ctrl.traffic_set_chk[tid] = False
            except Exception as ex:
                self.lg.error(string_write("Exception on registering traffic, network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, str(ex)))

    @after('fire')
    def do_fire(self):
        self.lg.info(string_write("Fire traffic: {}", str(self.current_state)))
        self.ctrl.create_traffire_chk()
        data = {
            CFGKW_TRAFFIC_TYPE: TrafficType.START.name,
        }
        pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)      

    @before('traffic_finish')
    def do_traffic_finish(self):
        self.lg.info(string_write("Traffic finished: {}", str(self.current_state)))
        while self.running and not self.ctrl.is_traffic_finished(): time.sleep(2)
        self.ctrl.traffire_chk = {}

    @after('finish')
    def do_finish(self):
        self.lg.info(string_write("All finished: {}", str(self.current_state)))
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
