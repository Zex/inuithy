""" Traffic generator based on configuration
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_PKGRATE, T_DURATION,\
T_NWCONFIG_PATH, T_NWLAYOUT, T_SRCS, T_DESTS,\
T_TARGET_TRAFFICS, TRAFFIC_CONFIG_PATH, NETWORK_CONFIG_PATH,\
T_PKGSIZE, T_NODES, console_write, string_write, T_EVERYONE,\
T_TRAFFIC_STATUS, TrafficStatus, T_TID
from inuithy.util.helper import getnwlayoutid, is_number
#from inuithy.util.trigger import TrafficTrigger
from inuithy.util.cmd_helper import pub_status
import time
import threading
import logging
import logging.config as lconf

TRAFFIC_ERR_NOSUBNET = "No subnet named [{}] in network [{}]"
TRAFFIC_BROADCAST_ADDRESS = '0xFFFF'

class Traffic(object):
    """Traffic information"""
    @property
    def pkgsize(self):
        """Package size"""
        return self.__pkgsize

    @pkgsize.setter
    def pkgsize(self, val):
        if not isinstance(val, int):
            raise TypeError("Integer expected")
        self.__pkgsize = val

    @property
    def src(self):
        """Source address"""
        return self.__src

    @src.setter
    def src(self, val):
        self.__src = val

    @property
    def dest(self):
        """Destination address"""
        return self.__dest

    @dest.setter
    def dest(self, val):
        self.__dest = val

    def __init__(self, psize=1, src=None, dest=None):
        self.__pkgsize = psize
        self.__src = src
        self.__dest = dest

    def __str__(self):
        return string_write(
            "[{}]============P({}) ===========>[{}]",
            self.src, self.pkgsize, self.dest)

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
    def pkgrate(self):
        """Package rate, package to send per second
        """
        return self.__pkgrate

    @pkgrate.setter
    def pkgrate(self, val):
        if not isinstance(val, float):
            raise TypeError("Float expected")
        self.__pkgrate = val

    @property
    def genid(self):
        """Generator ID"""
        return self.__genid
    @genid.setter
    def genid(self, val):
        self.__genid = val

    def __init__(self, trcfg, nwcfg, trname, genid=None):
        self.traffic_name = trname
        self.cur_trcfg = trcfg.config[trname]
        self.__nwconfig_file = ''
        self.__nwconfig_name = ''
        self.__pkgrate = self.cur_trcfg[T_PKGRATE]
        self.__duration = self.cur_trcfg[T_DURATION]
        # In second
        self.interval = 1/self.pkgrate
        self.traffics = []
        self.nwlayoutid = getnwlayoutid(trcfg.config[T_NWCONFIG_PATH], self.cur_trcfg[T_NWLAYOUT])
        self.create_traffic(trcfg, nwcfg)
        self.__genid = genid is not None and genid or string_write("[{}]{}:{}",\
            time.clock_gettime(time.CLOCK_REALTIME), self.nwlayoutid, trname)

    def __str__(self):
        return string_write("genid:{},layout:{},traffic:{},rate:{}/s,dur:{}s,",\
            self.genid, self.nwlayoutid, self.traffic_name, self.pkgrate, self.duration)

    @staticmethod
    def parse_srcs(tr, nwcfg):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected srcs
        """
        nw = tr[T_NWLAYOUT]
        nodes = []
        for s in tr[T_SRCS]:
            if s == T_EVERYONE:
                for sub_name in nwcfg.config.get(nw):
                    sub = nwcfg.subnet(nw, sub_name)
                    if sub is None:
                        raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub_name, nw))
                    [nodes.append(node) for node in sub[T_NODES]]
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub is None:
                    raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, s, nw))
                [nodes.append(node) for node in sub[T_NODES]]
        return nodes

    @staticmethod
    def parse_dests(tr, nwcfg):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected dests
        """
        nw = tr[T_NWLAYOUT]
        nodes = []
        for s in tr[T_DESTS]:
            if s == T_EVERYONE:
                nodes.append(TRAFFIC_BROADCAST_ADDRESS)
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub is None:
                    raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, s, nw))
                [nodes.append(node) for node in sub[T_NODES]]
        return nodes

    def create_traffic(self, trcfg, nwcfg):
        """Create traffic for traffic definition named @trname
        """
        srcs = TrafficGenerator.parse_srcs(self.cur_trcfg, nwcfg)
        dests = TrafficGenerator.parse_dests(self.cur_trcfg, nwcfg)
        for s in srcs:
            for r in dests:
                tr = Traffic(self.cur_trcfg[T_PKGSIZE], s, r)
                self.traffics.append(tr)
        return self


    def start(self):
        self.__trigger.start()

class Duration(object):
    """Duration indicator
    """
    def __init__(self):
        pass

    def __enter__(self):
        console_write(">> {}", time.ctime(time.clock_gettime(time.CLOCK_REALTIME)))

    def __exit__(self, cls, message, traceback):
        console_write("<< {}", time.ctime(time.clock_gettime(time.CLOCK_REALTIME)))

#class TrafficExecutor(TrafficTrigger):
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

    def __init__(self, node, interval, duration, request=None, lgr=None, mqclient=None, tid=None):
        threading.Thread.__init__(self, name=string_write("TE-{}", tid), target=None, daemon=False)
        self.lgr = lgr
        if self.lgr is None:
            self.lgr = logging
        self.interval = interval
        self.duration = duration
        self.node = node
        self.request = request
        self.stop_timer = threading.Timer(duration, self.stop_trigger)
        self.mqclient = mqclient
        self.tid = tid
        self.done = threading.Event()

    def run(self):
        self.lgr.debug(string_write("Start traffic [{}]", self))
        self.running = True
        self.stop_timer.start()

        while self.running: # TODO debug check
            self.node.traffic(self.request)
            self.done.wait(self.interval)
            self.done.clear()

    def stop_trigger(self):
        console_write("{}: ========Stopping trigger============", self)
        self.running = False
        self.stop_timer.cancel()
        if self.mqclient is not None:
            pub_status(self.mqclient, data={
                T_TRAFFIC_STATUS: TrafficStatus.FINISHED.name,
                T_TID: self.tid,
            })

    def __str__(self):
        return string_write("tid[{}]: intv:{}, dur:{}, node:[{}]",\
            self.tid, self.interval, self.duration, str(self.node))

def create_traffics(trcfg, nwcfg):
    """Create traffic generators for targe traffics
    """
    trgens = []
    for trname in trcfg.config[T_TARGET_TRAFFICS]:
        gentor = TrafficGenerator(trcfg, nwcfg, trname)
        trgens.append(gentor)
    return trgens

if __name__ == '__main__':
    from inuithy.util.config_manager import create_traffic_cfg, create_network_cfg
    from inuithy.common.node import NodeBLE, NodeZigbee
    trcfg = create_traffic_cfg(TRAFFIC_CONFIG_PATH)
    nwcfg = create_network_cfg(trcfg.nw_cfgpath)
    tgs = create_traffics(trcfg, nwcfg)
    for tg in tgs:
        console_write("---------------------------------------------")
        console_write(str(tg))
        console_write('\n'.join([str(traffic) for traffic in tg.traffics]))
#    te = TrafficExecutor("BLE", 'shield on', 1/0.9, 3, {"account":88888})
    node = NodeZigbee('/dev/ttyS33')
    te = TrafficExecutor(node, 'shield on', 1/0.9, 3, request={"dest":'4343'}, tid='12345')
    console_write("==========beg=============")
    te.run()
    console_write("==========end=============")

#    cur_trcfg = trcfg.config['traffic_6']
#    srcs = TrafficGenerator.parse_srcs(cur_trcfg, nwcfg)
#    dests = TrafficGenerator.parse_dests(cur_trcfg, nwcfg)
#    print(srcs)
#    print(dests)

#    trgens = create_traffics(trcfg, nwcfg)
#    print(len(trgens))
#    for tg in trgens:
#        print(len(tg.traffics))

