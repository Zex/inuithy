## Traffic generator based on configuration
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.util.trigger import *
from queue import Queue

TRAFFIC_ERR_NOSUBNET = "No subnet named [{}] in network [{}]"
TRAFFIC_BROADCAST_ADDRESS = '0xFFFF'

class Traffic:

    @property
    def pkgsize(self):
        """Package size
        """
        return self.__pkgsize

    @pkgsize.setter
    def pkgsize(self, val):
        if not isinstance(val, int): raise TypeError("Integer expected")
        self.__pkgsize = val

    def __init__(self, psize=1, sender=None, recv=None):
        self.pkgsize    = psize
        self.sender     = sender
        self.recipient  = recv

    def __str__(self):
        return string_write(
        "[{}]============P({})===========>[{}]",\
         self.sender, self.pkgsize, self.recipient)

class TrafficGenerator:
    """Parse senders/recipients, define network traffics
    """
    @property
    def duration(self):
        """Duration in second
        """
        return self.__duration

    @duration.setter
    def duration(self, val):
        if not isinstance(val, int): raise TypeError("Integer expected")
        self.__duration = val

    @property
    def nwconfig(self):
        """Network config format <config_file>:<config_name>
        """
        return self.__nwconfig_file, self.__nwconfig_name

    @nwconfig.setter
    def nwconfig(self, val):
        if not isinstance(val, tuple): raise TypeError("Tuple expected")
        self.__nwconfig_file, self.__nwconfig_name = val

    @property
    def pkgrate(self):
        """Package rate, package to send per second
        """
        return self.__pkgrate

    @pkgrate.setter
    def pkgrate(self, val):
        if not isinstance(val, float): raise TypeError("Float expected")
        self.__pkgrate = val

    @property
    def genid(self):
        """Generator ID
        """
        return self.__genid
    @genid.setter
    def genid(self, val):
        self.__genid = val

    def __init__(self, trcfg, nwcfg, trname, genid=None):
        self.traffic_name = trname
        self.cur_trcfg = trcfg.config[trname]
        self.pkgrate  = self.cur_trcfg[CFGKW_PKGRATE]
        self.duration = self.cur_trcfg[CFGKW_DURATION]
        # In second
        self.timeslot = 1/self.pkgrate
        self.traffics = []
        self.nwlayoutid = getnwlayoutid(trcfg.config[CFGKW_NWCONFIG_PATH], self.cur_trcfg[CFGKW_NWLAYOUT])
        self.create_traffic(trcfg, nwcfg)
        self.__genid = genid != None and genid or string_write("[{}]{}:{}", time.clock_gettime(time.CLOCK_REALTIME), self.nwlayoutid, trname)

    def __str__(self):
        return string_write("layout:{},traffic:{},rate:{}/s,dur:{}s,", self.nwlayoutid, self.traffic_name, self.pkgrate, self.duration)

    @staticmethod
    def parse_senders(tr, nwcfg):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected senders
        """
        nw = tr[CFGKW_NWLAYOUT]
        nodes = []
        for s in tr[CFGKW_SENDERS]:
            if s == '*': 
                for sname in nw.keys():
                    sub = nwcfg.subnet(nw, sub)
                    if sub == None: raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub , nw))
                    [nodes.append(node) for node in sub[CFGKW_NODES]]
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub == None: raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub , nw))
                [nodes.append(node) for node in sub[CFGKW_NODES]]
        return nodes

    @staticmethod
    def parse_recipients(tr, nwcfg):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected recipients
        """
        nw = tr[CFGKW_NWLAYOUT]
        nodes = []
        for s in tr[CFGKW_RECIPIENTS]:
            if s == '*':
                nodes.append(TRAFFIC_BROADCAST_ADDRESS)
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub == None: raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub , nw))
                [nodes.append(node) for node in sub[CFGKW_NODES]]
        return nodes

    def create_traffic(self, trcfg, nwcfg):
        """Create traffic for traffic definition named @trname
        """
        senders = TrafficGenerator.parse_senders(self.cur_trcfg, nwcfg)
        recipients = TrafficGenerator.parse_recipients(self.cur_trcfg, nwcfg)
        for s in senders:
            for r in recipients:
                tr = Traffic(self.cur_trcfg[CFGKW_PKGSIZE], s, r)
                self.traffics.append(tr)
        return self


    def start(self):
        self.__trigger.start()

class TrafficExecutor(TrafficTrigger):
    """
    @node       Sender node
    @command    Command to send
    @timeslot   Traffic trigger interval, in second
    @duration   Stop traffic after given duration, in second
    """
    def __init__(self, node, command, timeslot, duration, data=None):
        TrafficTrigger.__init__(self, timeslot, duration)
        self.timeslot = timeslot
        self.duration = duration
        self.node = node
        self.command = command
        self.data = data

    def run(self):

        self.__running = True
        self.__stop_timer.start()

        while self.__running:
            if TrafficTrigger.__mutex.acquire():
                self.node.write(self.command, self.data)
                TrafficTrigger.__mutex.release()
            time.sleep(self.__interval)

    def __str__(self):
        return string_write("TE: ts:{}, dur:{}, node:[{}], cmd:{} ", self.timeslot, self.duration, str(self.node), self.command)

def create_traffics(trcfg, nwcfg):
    """Create traffic generators for targe traffics
    """
    cfg = trcfg.config
    trs = [] 
    for trname in trcfg.config[CFGKW_TARGET_TRAFFICS]:
        gentor = TrafficGenerator(trcfg, nwcfg, trname)
        trs.append(gentor)
    return trs

if __name__ == '__main__':
    from inuithy.util.config_manager import *
    trcfg = TrafficConfig(TRAFFIC_CONFIG_PATH)
    trcfg.load()
    nwcfg = TrafficConfig(NETWORK_CONFIG_PATH)
    nwcfg.load()
    tgs = create_traffics(trcfg, nwcfg)
    for tg in tgs:
        console_write("---------------------------------------------")
        console_write(str(tg))
        console_write('\n'.join([str(traffic) for traffic in tg.traffics]))

