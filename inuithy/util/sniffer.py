""" Traffic state transition
 @author: Zex Li <top_zlynch@yahoo.com>
 @refer tools/pysniffer.py
 @brief

    Sniffer ==> Tshark ==> MQ ==> DB
\code
    python tools/pysniffer.py -b 230400 -d /dev/ttyUSB4 -L build/sniffer.log -c 17 --stdout
\endcode
"""
from inuithy.common.predef import to_string, to_console,\
T_CHANNEL, T_PORT, T_BAUD, T_ENABLED, T_PATH
from inuithy.common.runtime import Runtime as rt
from tools.pysniffer import SerialInputHandler, PcapStdOutHandler, PcapDumpOutHandler, FifoOutHandler
import subprocess as sp
from inuithy.util.task_manager import ProcTaskManager
import threading
import paho.mqtt.client as mqtt
from os import path, makedirs
import time
import sys

T_SNIFFER = 'sniffer'
T_LOG = 'log'
T_PCAP = 'pcap'

class PcapToTsharkHandler(object):
    """
    tshark -l -n -T json -i/tmp/sniffer.fifo
    """
    def __init__(self, host, port, sniconf):

        self.clientid = "inuithy/sniffer"
        self._mqclient = mqtt.Client(self.clientid, True, self)
        self._mqclient.connect(host, port)
        cmd = [sniconf.get(T_TSHARK), '-T', 'json', '-i', Sniffer.fifo_path]
        self.tshark_worker = sp.run(cmd)
        p = sp.Popen(cmd, stdout=subprocess.PIPE)
        out, err = p.communicate()

    def handle(self, frame):
        if self._mqclient is None:
            return
#        self._mqclient(frame.get_pcap())
        pub_sniffer(self._mqclient, data=data)

class Sniffer():

    running = False
    fifo_path = '/tmp/inuithy-sniffer.fifo'

    @staticmethod
    def prepare():
        """ python tools/pysniffer.py -b 230400 -d /dev/ttyUSB4 -L build/sniffer.log -c 17 --stdout
        """
        in_hander, out_handlers = None, None

        try:
            sniconf = rt.trcfg.config.get(T_SNIFFER)
            if sniconf is not None:
                if not sniconf.get(T_ENABLED):
                    to_console("Sniffer not enabled")
                    return None, None

            to_console("Sniffer enabled")
            if not path.isdir(sniconf.get(T_PCAP)):
                makedirs(sniconf.get(T_PCAP))

            pcap_path = to_string('{}/{}', sniconf.get(T_PCAP), int(time.time()))

            out_hdr = SerialInputHandler(
            port=sniconf.get(T_PATH), baudrate=sniconf.get(T_BAUD),\
            channel=sniconf.get(T_CHANNEL))
    
            out_handlers = []
#            out_handlers.append(PcapStdOutHandler())
            out_handlers.append(FifoOutHandler(Sniffer.fifo_path))
#            out_handlers.append(PcapToTsharkHandler(*rt.tcfg.mqtt))
            out_handlers.append(PcapDumpOutHandler(pcap_path))
            
            to_mq = PcapToTsharkHandler(*rt.tcfg.mqtt, sniconf)
        except Exception as ex:
            to_console("Start sniffer failed: {}", ex)
            return None, None

        Sniffer.start = True
        return in_hander, out_handlers 

    @staticmethod
    def start(out_hdr, out_handlers):
        """
        python tools/pysniffer.py -f /tmp/sniffer.fifo -b 230400 -d /dev/ttyUSB5 -L build/sniffer.log -c 17
        """
        if out_hdr is None or out_handlers is None:
            return

        while Sniffer.running:
            try:
                raw = out_hdr.read_frame()
                if raw:
                    frame = Frame(raw)
                    for h in out_handlers:
                        h.handle(frame)
            except (KeyboardInterrupt, SystemExit):
                out_hdr.close()
                sys.exit(0)

    @staticmethod
    def stop():
        
        Sniffer.running = False
        

if __name__ == '__main__':

    from inuithy.common.runtime import load_configs
    load_configs()
    in_hdr, out_hdr = Sniffer.prepare()
    pool = ProcTaskManager()
    pool.create_task(Sniffer.start, in_hdr, out_hdr)

    input('Enter to quit ...')
    Sniffer.stop()

