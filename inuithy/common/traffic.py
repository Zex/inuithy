## Traffic generator based on configuration
# Author: Zex Li <top_zlynch@yahoo.com>
#

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
        if not isinstance(int, val): raise TypeError("Integer expected")
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
        if not isinstance(int, val): raise TypeError("Integer expected")
        self.__duration = val

    @property
    def nwconfig(self):
        """Network config format <config_file>:<config_name>
        """
        return self.__nwconfig_file, self.__nwconfig_name

    @nwconfig.setter
    def nwconfig(self, val):
        if not isinstance(tuple, val): raise TypeError("Tuple expected")
        self.__nwconfig_file, self.__nwconfig_name = val

    @property
    def pkgrate(self):
        """Package rate, package to send per second
        """
        return self.__pkgrate

    @pkgrate.setter
    def pkgrate(self, val):
        if not isinstance(float, val): raise TypeError("Float expected")
        self.__pkgrate = val

    def __init__(self, trcfg, nwcfg, trname):
        self.pkgrate  = trcfg.config[trname][CFGKW_PKGRATE]
        self.duration = trcfg.config[trname][CFGKW_DURATION]
        # In second
        self.timeslot = 1/self.pkgrate
        self.traffics = []
        self.traffic_name = trname
        self.create_traffic(trcfg, nwcfg, trname)

    def __str__(self):
        return string_write("layout:{},traffic:{},rate:{}/s,dur:{}s,",self.nwlayoutid, self.traffic_name, self.pkgrate, self.duration)

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
            elif s.startswith('0x'):
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
            elif s.startswith('0x'):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub == None: raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub , nw))
                [nodes.append(node) for node in sub[CFGKW_NODES]]
        return nodes

    def create_traffic(self, trcfg, nwcfg, trname):
        """Create traffic for traffic definition named @trname
        """
        cfg = trcfg.config
        tr = cfg[trname]
        self.nwlayoutid = getnwlayoutid(trcfg.config[CFGKW_NWCONFIG_PATH], tr[CFGKW_NWLAYOUT])
        senders = TrafficGenerator.parse_senders(tr, nwcfg)
        recipients = TrafficGenerator.parse_recipients(tr, nwcfg)
        for s in senders:
            for r in recipients:
                tr = Traffic(cfg[trname][CFGKW_PKGSIZE], s, r)
                self.traffics.append(tr)
        return self

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

