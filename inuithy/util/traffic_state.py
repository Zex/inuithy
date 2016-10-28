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
    nwconfigured    = State()
    registered      = State()
    running         = State()
    finished        = State()

    start           = Event(from_states=(stopped), to_state=started)
    deploy          = Event(from_states=(started), to_state=nwconfigured)
    register        = Event(from_states=(nwconfigured), to_state=registered)
    fire            = Event(from_states=(registered), to_state=running)
    finish          = Event(from_states=(running), to_state=(finished))

    def __init__(self, controller, lg=None):
        self.ctrl = controller
        if lg == None: self.lg = logging
        else: self.lg = lg

    @before('start')
    def do_start(self):
        self.lg.info(string_write("Run traffics, mode:[{}]", self.ctrl.tcfg.workmode))
        print(self.current_state)
        self.trgens = create_traffics(self.ctrl.trcfg, self.ctrl.nwcfg)
        self.lg.info(string_write("Total generator: [{}]", len(self.trgens)))
        for tg in self.trgens:
#TODO
#            while not self.is_agents_all_up(): pass
            self.lg.info(string_write("Deploy network begin"))
            self.do_deploy(tg)
#            while not self.is_network_layout_done(): pass
            self.lg.info(string_write("Register traffic begin"))
            self.do_register(tg)
#            while not self.is_traffic_all_set(): pass
            self.lg.info(string_write("Fire traffic begin"))
            self.do_fire()
            self.do_finish()

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

    @before('deploy')
    def do_deploy(self, tg):
        self.lg.info(string_write("Deploy network: {}", tg.nwlayoutid))
        print(self.current_state)
        try:
            self.lg.info(string_write("Current traffic [{}]", str(tg)))
            if self.ctrl.current_nwlayout != tg.nwlayoutid:
                self.config_network(getnwlayoutname(tg.nwlayoutid))
        except Exception as ex:
            self.lg.error(string_write("Exception on configuring network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, ex))

    @before('register')
    def do_register(self, tg):
        lg.info(string_write("Register traffic: [{}]", str(tg)))
        print(self.current_state)
        for tr in tg.traffics:
            try:
                lg.debug(string_write("TRAFFIC: {}", tr))
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
                lg.error(string_write("Exception on publishing traffic, network [{}], traffic [{}]: {}", tg.nwlayoutid, tg.traffic_name, ex))

    @before('fire')
    def do_fire(self):
        self.lg.info(string_write("Fire traffic"))
        print(self.current_state)
        data = {
            CFGKW_TRAFFIC_TYPE: TrafficType.START.name,
        }
        pub_traffic(self.ctrl.subscriber, self.ctrl.tcfg.mqtt_qos, data)      

    @before('finish')
    def do_finish(self):
        self.lg.info(string_write("Trafic finished"))
        print(self.current_state)

def transition(sm, event, event_name):
    try:
        event()
    except InvalidStateTransition as ex:
        print("{}: {} => {} Failed".format(sm, event, event_name))

if __name__ == '__main__':
    pass
#    ts = TrafficState("AutoTraffic")
#    ts.do_start()
#    ts.do_deploy()
#    ts.do_register()
#    ts.do_finish()
