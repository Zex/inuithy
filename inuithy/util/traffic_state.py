## Traffic state transition
# Author: Zex Li <top_zlynch@yahoo.com>
#
import logging
from state_machine import State, Event, acts_as_state_machine, after, before, InvalidStateTransition
from inuithy.util.cmd_helper import *
from inuithy.common.traffic import *

@acts_as_state_machine
class TrafficState:
    """
    @controller Controller object
    @lg         For log handling

    STOP,             # Initial status, traffic not yet launched
    STARTED,          # Traffic routine started
    NWCONFIGURING,    # Configuring network layout
    NWCONFIGED,       # Network layout configured
    REGISTERING,      # Registering traffics
    REGISTERED,       # Traffics already been registered to agents
    RUNNING,          # Traffics are fired
    FINISHED,         # Traffics finished
    """
    stopped = State(initial=True)
    started = State()
    nwconfigured        = State()
    registered          = State()
    running             = State()
    traffic_finished    = State()
    finished            = State()

    start           = Event(from_states=(stopped), to_state=started)
    deploy          = Event(from_states=(started, traffic_finished), to_state=nwconfigured)
    register        = Event(from_states=(nwconfigured), to_state=registered)
    fire            = Event(from_states=(registered), to_state=running)
    traffic_finish  = Event(from_states=(running), to_state=traffic_finished)
    finish          = Event(from_states=(stopped, started, traffic_finished), to_state=(finished))

    def __init__(self, controller, trdelay=1, lg=None):
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

    @after('start')
    def do_start(self):
        print("Start", self.current_state)
        self.lg.info(string_write("Run traffics, mode:[{}]", self.ctrl.tcfg.workmode))
        self.trgens = create_traffics(self.ctrl.trcfg, self.ctrl.nwcfg)
        self.lg.info(string_write("Total generator: [{}]", len(self.trgens)))
        for tg in self.trgens:
            try:
#TODO
#            while not self.is_agents_all_up(): pass
                self.lg.info(string_write("Deploy network begin"))
                self.__current_tg = tg
                self.deploy()
#            while not self.is_network_layout_done(): pass
                self.lg.info(string_write("Register traffic begin"))
                self.register()
#            while not self.is_traffic_all_set(): pass
                self.lg.info(string_write("Fire traffic begin"))
                self.fire()
                self.traffic_finish()
            except Exception as ex:
                self.lg.error(string_write("Traffic state transition failed: {}", ex))
        self.finish()

    def config_network(self, nwlayoutname):
        """Configure network by given network layout
        """
        self.lg.info(string_write("Config network: [{}]", nwlayoutname))

        for subnet in self.ctrl.nwcfg.config[nwlayoutname].values():
            data = subnet
            for node in subnet[CFGKW_NODES]:
                if None == self.ctrl.node2host.get(node):
                    raise ValueError(string_write("Node [{}] not found on any agent", node))
                target_agent = self.ctrl.node2host[node]
                data[CFGKW_CLIENTID]     = target_agent,
                data[CFGKW_NODE]         = node
                data[CFGKW_TRAFFIC_TYPE] = TrafficType.JOIN.name
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)

    @after('deploy')
    def do_deploy(self, tg=None):
        print("Deploy", self.current_state)
        if tg == None: tg = self.__current_tg
        self.lg.info(string_write("Deploy network: {}", tg.nwlayoutid))
        try:
            self.lg.info(string_write("Current traffic [{}]", str(tg)))
            if self.ctrl.current_nwlayout != tg.nwlayoutid:
                self.config_network(getnwlayoutname(tg.nwlayoutid))
        except Exception as ex:
            self.lg.error(string_write("Exception on configuring network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, ex))

    @after('register')
    def do_register(self, tg=None):
        print("Register", self.current_state)
        if tg == None: tg = self.__current_tg
        self.lg.info(string_write("Register traffic: [{}]", str(tg)))
        for tr in tg.traffics:
            try:
                self.lg.debug(string_write("TRAFFIC: {}", tr))
                data = {
                CFGKW_GENID:        tg.genid,
                CFGKW_DURATION:     tg.duration,
                CFGKW_TIMESLOT:     tg.timeslot,
                CFGKW_SENDER:       tr.sender,
                CFGKW_RECIPIENT:    tr.recipient,
                CFGKW_PKGSIZE:      tr.pkgsize,
                }
                pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)
            except Exception as ex:
                self.lg.error(string_write("Exception on publishing traffic, network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, ex))

    @after('fire')
    def do_fire(self):
        self.lg.info(string_write("Fire traffic"))
        print("Fire", self.current_state)
        data = {
            CFGKW_TRAFFIC_TYPE: TrafficType.START.name,
        }
        pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)      

    @after('traffic_finish')
    def do_traffic_finish(self):
        print("Traffic finish", self.current_state)
        self.lg.info(string_write("Traffic finished"))
        time.sleep(self.traffic_delay)

    @after('finish')
    def do_finish(self):
        print("Finish", self.current_state)
        self.lg.info(string_write("All finished"))
        self.ctrl.teardown()

def transition(sm, event, event_name):
    try:
        event()
    except InvalidStateTransition as ex:
        print("{}: {} => {} Failed".format(sm, event, event_name))

if __name__ == '__main__':
    pass
#    ts = TrafficState("AutoTraffic")
#    ts.start()
#    ts.deploy()
#    ts.register()
#    ts.finish()
