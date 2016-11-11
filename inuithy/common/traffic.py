""" Traffic generator based on configuration
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import T_PKGRATE, T_DURATION,\
T_NWCONFIG_PATH, T_NWLAYOUT, T_SENDERS, T_RECIPIENTS,\
T_TARGET_TRAFFICS, TRAFFIC_CONFIG_PATH, NETWORK_CONFIG_PATH,\
T_PKGSIZE, T_NODES, console_write, string_write
from inuithy.util.helper import getnwlayoutid, is_number
from inuithy.util.trigger import TrafficTrigger
import time

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
    def sender(self):
        """Sender address"""
        return self.__sender

    @sender.setter
    def sender(self, val):
        self.__sender = val

    @property
    def recipient(self):
        """Recipient address"""
        return self.__recipient

    @recipient.setter
    def recipient(self, val):
        self.__recipient = val

    def __init__(self, psize=1, sender=None, recv=None):
        self.__pkgsize = psize
        self.__sender = sender
        self.__recipient = recv

    def __str__(self):
        return string_write(
            "[{}]============P({}) ===========>[{}]",
            self.sender, self.pkgsize, self.recipient)

class TrafficGenerator(object):
    """Parse senders/recipients, define network traffics
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
        self.timeslot = 1/self.pkgrate
        self.traffics = []
        self.nwlayoutid = getnwlayoutid(trcfg.config[T_NWCONFIG_PATH], self.cur_trcfg[T_NWLAYOUT])
        self.create_traffic(trcfg, nwcfg)
        self.__genid = genid is not None and genid or string_write("[{}]{}:{}",\
            time.clock_gettime(time.CLOCK_REALTIME), self.nwlayoutid, trname)

    def __str__(self):
        return string_write("layout:{},traffic:{},rate:{}/s,dur:{}s,",\
            self.nwlayoutid, self.traffic_name, self.pkgrate, self.duration)

    @staticmethod
    def parse_senders(tr, nwcfg):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected senders
        """
        nw = tr[T_NWLAYOUT]
        nodes = []
        for s in tr[T_SENDERS]:
            if s == T_EVERYONE:
                for sub_name in nwcfg.config.get(nw):
                    sub = nwcfg.subnet(nw, sub_name)
                    if sub is None: raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub, nw))
                    [nodes.append(node) for node in sub[T_NODES]]
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub is None: raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub, nw))
                [nodes.append(node) for node in sub[T_NODES]]
        return nodes

    @staticmethod
    def parse_recipients(tr, nwcfg):
        """
        @param[in] tr    A traffic block
        @param[in] nwcfg Network layout definition
        @return Expected recipients
        """
        nw = tr[T_NWLAYOUT]
        nodes = []
        for s in tr[T_RECIPIENTS]:
            if s == T_EVERYONE:
                nodes.append(TRAFFIC_BROADCAST_ADDRESS)
            elif is_number(s):
                nodes.append(s)
            else:
                sub = nwcfg.subnet(nw, s)
                if sub is None:
                    raise ValueError(string_write(TRAFFIC_ERR_NOSUBNET, sub, nw))
                [nodes.append(node) for node in sub[T_NODES]]
        return nodes

    def create_traffic(self, trcfg, nwcfg):
        """Create traffic for traffic definition named @trname
        """
        senders = TrafficGenerator.parse_senders(self.cur_trcfg, nwcfg)
        recipients = TrafficGenerator.parse_recipients(self.cur_trcfg, nwcfg)
        for s in senders:
            for r in recipients:
                tr = Traffic(self.cur_trcfg[T_PKGSIZE], s, r)
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

    def run(self): #TODO remove print
        self.running = True
        self.stop_timer.start()

        while self.running: # TODO debug check
#            console_write(self.command, self.data)
            self.node.write(self.command, self.data)
            time.sleep(self.timeslot)

    def __str__(self):
        return string_write("TE: ts:{}, dur:{}, node:[{}], cmd:{} ",\
            self.timeslot, self.duration, str(self.node), self.command)

def create_traffics(trcfg, nwcfg):
    """Create traffic generators for targe traffics
    """
    trs = []
    for trname in trcfg.config[T_TARGET_TRAFFICS]:
        gentor = TrafficGenerator(trcfg, nwcfg, trname)
        trs.append(gentor)
    return trs

if __name__ == '__main__':
    from inuithy.util.config_manager import TrafficConfig
    trcfg = TrafficConfig(TRAFFIC_CONFIG_PATH)
    trcfg.load()
    nwcfg = TrafficConfig(NETWORK_CONFIG_PATH)
    nwcfg.load()
    tgs = create_traffics(trcfg, nwcfg)
    for tg in tgs:
        console_write("---------------------------------------------")
        console_write(str(tg))
        console_write('\n'.join([str(traffic) for traffic in tg.traffics]))
    te = TrafficExecutor("BLE", 'shield on', 1/0.9, 3, {"account":88888})
    te.run()
    print("===========end==============")
