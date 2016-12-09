""" Traffic generator based on configuration
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_DURATION, T_INTERVAL,\
T_NWCONFIG_PATH, T_NWLAYOUT, T_SRCS, T_DESTS, T_GATEWAY,\
T_TARGET_PHASES, TRAFFIC_CONFIG_PATH, NETWORK_CONFIG_PATH,\
T_PKGSIZE, T_NODES, to_console, to_string, T_EVERYONE,\
T_TRAFFIC_STATUS, TrafficStatus, T_TID, T_NOI, T_TRAFFICS
from inuithy.util.helper import getnwlayoutid, is_number
from inuithy.util.cmd_helper import pub_status
from inuithy.common.node import SerialNode
from inuithy.common.runtime import Runtime as rt
import time
import threading
import random
import string
import logging
import logging.config as lconf

TRAFFIC_ERR_NOSUBNET = "No subnet named [{}] in network [{}]"
TRAFFIC_BROADCAST_ADDRESS = 'FFFF'

class Traffic(object):
    """Traffic information block"""

    def __init__(self, psize=1, src=None, dest=None):
        self.tid = ''.join([random.choice(string.hexdigits) for _ in range(7)])
        self.pkgsize = psize
        self.src = src
        self.dest = dest

    def __str__(self):
        return to_string("[{}] <{}>---P({})---><{}>",
            self.tid, self.src, self.pkgsize, self.dest)

class TrafficGenerator(object):
    """Parse srcs/dests, define network traffics
    """
    @property
    def duration(self):
        """Duration in second"""
        return self.__duration

    @duration.setter
    def duration(self, val):
        if not isinstance(val, int):
            raise TypeError("Integer expected")
        self.__duration = val

    @property
    def nwconfig(self):
        """Network config format <config_file>:<config_name>
        """
        return self.__nwconfig_file, self.__nwconfig_name

    @nwconfig.setter
    def nwconfig(self, val):
        if not isinstance(val, tuple):
            raise TypeError("Tuple expected")
        self.__nwconfig_file, self.__nwconfig_name = val

    @property
    def interval(self):
        """Package rate, package to send per second
        """
        return self.__interval

    @interval.setter
    def interval(self, val):
        if not isinstance(val, float):
            raise TypeError("Float expected")
        self.__interval = val

    def __init__(self, trcfg, nwcfg, trname, phase=None):
        self.traffic_name = trname
        self.cur_trcfg = trcfg.config[trname]
        self.__nwconfig_file = ''
        self.__nwconfig_name = ''
        self.__interval = self.cur_trcfg.get(T_INTERVAL) # seconds
        self.__duration = self.cur_trcfg.get(T_DURATION)
        self.traffics = []
        self.noi = set()
        self.create_traffic(nwcfg, phase.info)

    def __str__(self):
        return to_string("[{}] interval:{}s dur:{}s traffics: \n{}",\
            self.traffic_name, self.interval, self.duration, '\n'.join([str(tr) for tr in self.traffics]))

    @staticmethod
    def parse_srcs(tr, nwcfg, nw):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected srcs
        """
#        nw = tr[T_NWLAYOUT]
        nodes = []
        for s in tr[T_SRCS]:
            if s == T_EVERYONE:
                for sub_name in nwcfg.config.get(nw):
                    sub = nwcfg.subnet(nw, sub_name)
                    if sub is None:
                        raise ValueError(to_string(TRAFFIC_ERR_NOSUBNET, sub_name, nw))
                    [nodes.append(node) for node in sub[T_NODES]]
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub is None:
                    raise ValueError(to_string(TRAFFIC_ERR_NOSUBNET, s, nw))
                [nodes.append(node) for node in sub[T_NODES]]
        return nodes

    @staticmethod
    def parse_dests(tr, nwcfg, nw):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected dests
        """
#        nw = tr[T_NWLAYOUT]
        nodes = []
        for s in tr[T_DESTS]:
            if s == T_EVERYONE:
                nodes.append(TRAFFIC_BROADCAST_ADDRESS)
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub is None:
                    raise ValueError(to_string(TRAFFIC_ERR_NOSUBNET, s, nw))
                [nodes.append(node) for node in sub[T_NODES]]
        return nodes

    def create_traffic(self, nwcfg, phase):
        """Create traffic for traffic definition named @trname
        """
        srcs = TrafficGenerator.parse_srcs(self.cur_trcfg, nwcfg, phase[T_NWLAYOUT])
        dests = TrafficGenerator.parse_dests(self.cur_trcfg, nwcfg, phase[T_NWLAYOUT])

        [self.noi.add(n) for n in srcs]
        [self.noi.add(n) for n in dests]

        for s in srcs:
            for r in dests:
                tr = Traffic(self.cur_trcfg[T_PKGSIZE], s, r)
                self.traffics.append(tr)
        return self

class Phase(object):

    def __init__(self, trcfg, nwcfg, cur_phase):
        self.nwlayoutid = getnwlayoutid(trcfg.config[T_NWCONFIG_PATH], cur_phase[T_NWLAYOUT])
        self.noi = {}
        self.info = cur_phase
        self.tgs = []
        self.genid = to_string("{}", int(time.time()))
        self.create_traffics(trcfg, nwcfg)
        self.add_noi(nwcfg)

    def create_traffics(self, trcfg, nwcfg):
        """Create traffic generators for targe traffics
        """
        self.tgs = [TrafficGenerator(trcfg, nwcfg, trname, phase=self) for trname in self.info.get(T_TRAFFICS)]

    def add_noi(self, nwcfg):

        noi = self.info.get(T_NOI)

        self.noi[T_GATEWAY] = set()
        self.noi[T_NODES] = set()

        for subnet in nwcfg.config.get(self.info.get(T_NWLAYOUT)).values():
            self.noi[T_GATEWAY].add(subnet.get(T_GATEWAY))
            if T_EVERYONE in noi:
                [self.noi[T_NODES].add(n) for n in subnet.get(T_NODES)]
            elif noi is not None and len(noi) > 0:
                self.noi[T_NODES] = set(noi)
            else:
                for tg in self.tgs:
                    if TRAFFIC_BROADCAST_ADDRESS not in tg.noi:
                        [self.noi[T_NODES].add(n) for n in tg.noi]
                    else:
                        [self.noi[T_NODES].add(n) for n in subnet.get(T_NODES)]

    def __str__(self):
        return to_string("genid: {} nw: {} noi: {} tgs:{}",
        self.genid, self.nwlayoutid, self.noi, '\n'.join([str(tg) for tg in self.tgs]))

class Duration(object):
    """Duration indicator
    """
    def __init__(self):
        pass

    def __enter__(self):
        to_console(">> {}", time.ctime(time.clock_gettime(time.CLOCK_REALTIME)))

    def __exit__(self, cls, message, traceback):
        to_console("<< {}", time.ctime(time.clock_gettime(time.CLOCK_REALTIME)))

class TrafficExecutor(threading.Thread):
    """ Traffic trigger
    @node       Source node
    @interval   Traffic trigger interval, in second
    @duration   Stop traffic after given duration, in second
    """
    @property
    def finished(self):
        return self.stop_timer.finished
    @finished.setter
    def finished(self, val):
        pass

    def __init__(self, node, interval, duration, request=None, lgr=None, mqclient=None, tid=None, data=None):
        threading.Thread.__init__(self, name=to_string("TE-{}", tid), target=None)
        self.daemon=False
        self.lgr = lgr is None and logging or lgr
        self.interval = interval
        self.duration = duration
        self.node = node
        self.request = request
        self.stop_timer = threading.Timer(duration, self.stop_trigger)
        self.mqclient = mqclient
        self.tid = tid
        self.nextshot = threading.Event()
        self.data = data

    def run(self):
        self.lgr.debug(to_string("Start traffic [{}]", self))
        self.running = True
        self.stop_timer.start()

        while self.running: # TODO debug check
            self.node.traffic(self.request)
            self.nextshot.wait(self.interval)
            self.nextshot.clear()
            if self.data is not None and isinstance(self.data, set):
                [n.read_event.set() for n in self.data if isinstance(n, SerialNode)]

    def stop_trigger(self):
        to_console("{}: ========Stopping trigger============", self)
        self.running = False
        self.stop_timer.cancel()
        if self.mqclient is not None:
            pub_status(self.mqclient, data={
                T_TRAFFIC_STATUS: TrafficStatus.FINISHED.name,
                T_TID: self.tid,
            })

    def __str__(self):
        return to_string("tid[{}]: intv:{}, dur:{}, node:[{}]",\
            self.tid, self.interval, self.duration, str(self.node))

def create_phases(trcfg, nwcfg):
    """Create traffic generators for targe traffics
    """
    phases = []
    for phase in trcfg.target_phases:
        phases.append(Phase(trcfg, nwcfg, phase))
    return phases

if __name__ == '__main__':

    load_configs()
    phases = create_phases(trcfg, nwcfg)
    to_console("---------------------------------------------")
    [to_console(str(phase)) for phase in phases]
#    te = TrafficExecutor("BLE", 'shield on', 1/0.9, 3, {"account":88888})
#    node = NodeZigbee('/dev/ttyS33')
#    te = TrafficExecutor(node, 'shield on', 1/0.9, 3, request={"dest":'4343'}, tid='12345')
#    to_console("==========beg=============")
#    te.run()
#    to_console("==========end=============")

#    cur_trcfg = trcfg.config['traffic_6']
#    srcs = TrafficGenerator.parse_srcs(cur_trcfg, nwcfg)
#    dests = TrafficGenerator.parse_dests(cur_trcfg, nwcfg)

#    trgens = create_traffics(trcfg, nwcfg)

