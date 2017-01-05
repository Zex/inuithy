""" Traffic state transition
 @author: Zex Li <top_zlynch@yahoo.com>
 @refer tools/pysniffer.py
 @brief

    Sniffer ==> Tshark ==> MQ ==> DB
\code
    python tools/pysniffer.py -b 230400 -d /dev/ttyUSB4 -L build/sniffer.log -c 17 --stdout
\endcode
"""
from inuithy.common.predef import _s, _c, _l,\
T_CHANNEL, T_PORT, T_BAUD, T_ENABLED, T_GENID, T_MSG,\
T_SNIFFER, T_PCAP, T_TSHARK
from inuithy.common.runtime import Runtime as rt
from inuithy.common.runtime import load_configs
from inuithy.util.task_manager import ProcTaskManager
from inuithy.util.helper import remove_dotted_key
from inuithy.util.cmd_helper import pub_sniffer
from tools.pysniffer import SerialInputHandler, PcapStdOutHandler, PcapDumpOutHandler, FifoOutHandler, logger, Frame
import paho.mqtt.client as mqtt
from os import path, makedirs, mkfifo
import subprocess as sp
import json
import threading
import time
import sys

logger = _l

class PcapToMq(object):
    """
    tshark -l -n -T json -i/tmp/sniffer.fifo
    """
    clientid = None
    _mqclient = None
    proc = None
    genid = 'na'

    @staticmethod
    def __create_mqtt_client(host, port):
        PcapToMq.clientid = "inuithy/sniffer"
        PcapToMq._mqclient = mqtt.Client(PcapToMq.clientid, True, PcapToMq)
        PcapToMq._mqclient.connect(host, port)

    @staticmethod
    def init(host, port, sniconf, pcap_file=None, genid='na'):
        """
        if @pcap_file is not `None`, read data from @pcap_file
        """
        _l.info("Pcap2MQ initialization")
        try:
            if sniconf.get(T_TSHARK) is None:
                return False
            
            PcapToMq.genid = genid
            _c("GENID: {}", PcapToMq.genid)

            PcapToMq.__create_mqtt_client(host, port)

            cmd = []
            if pcap_file is None:
                cmd = [sniconf.get(T_TSHARK), '-l', '-T', 'json', '-i', Sniffer.fifo_path]
            else:
                cmd = [sniconf.get(T_TSHARK), '-l', '-T', 'json', '-r', pcap_file]
            PcapToMq.proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=False, universal_newlines=True)
        except Exception as ex:
            _l.error(_s("Pcap to MQ init failed: {}", ex))
            return False
        return True

    @staticmethod
    def __try_load(buf):
        """Return `true` if data is valid json block
        """
        try:
            if buf is None or len(buf) == 0:
                return False
            data = json.loads(buf)
            if PcapToMq._mqclient is not None:
                data = remove_dotted_key(data)
                data.update({T_GENID: PcapToMq.genid})
                pub_sniffer(PcapToMq._mqclient, data={T_MSG: data})
#        except json.decoder.JSONDecodeError:
#            return False
        except Exception as ex:
            _l.error(_s("Try load failed: {}", ex))
            return False
        return True
    
    @staticmethod
    def start():
        """Post data by block
        """
        _l.info("Pcap2MQ routine started")
        _c("Starting sniffer ...")
        buf, cnt = '', 0
        
        try:

            while PcapToMq.proc.poll() is None and Sniffer.running:
                line = PcapToMq.proc.stdout.readline()
                if line:
                    line = line.rstrip('\r\n ')
                if not line.endswith('[') and len(buf) == 0:
                    pass
                if line.endswith('['):
                    break
            _c("TSHARK HEAD SKIPPED")
            
            while PcapToMq.proc.poll() is None and Sniffer.running:
                line = PcapToMq.proc.stdout.readline()
                if line:
                    line = line.rstrip('\r\n ')
                    if line.endswith(']'):
                        break
                    if line.endswith('{'):
                        cnt += 1
                    elif line.endswith('},') or line.endswith('}'):
                        cnt -= 1
            
                    if len(line) == 0 or line.endswith(' ,'):
                        continue
            
                    buf += line + '\n'
                    if cnt == 0 and len(buf) > 0:
                        PcapToMq.__try_load(buf)
                        buf = ''
            _c("TSHARK DATA END")
        except KeyboardInterrupt:
            _c("Terminating ...")
            Sniffer.running = False
        except Exception as ex:
            _c("Exception on processing sniffer data: {}", ex)

    @staticmethod
    def stop():
        if PcapToMq._mqclient:
            PcapToMq._mqclient.disconnect()
    
class Sniffer():

    running = False
    fifo_path = '/tmp/inuithy-sniffer.fifo'
    sniffer_worker = None
    tshark_worker = None

    @staticmethod
    def init(genid='na'):
        """ python tools/pysniffer.py -b 230400 -d /dev/ttyUSB4 -L build/sniffer.log -c 17 --stdout
        """
        _l.info("Sniffer initialization")
        in_hdr, out_hdr = None, None

        try:
            sniconf = rt.trcfg.config.get(T_SNIFFER)
            if sniconf is not None:
                if not sniconf.get(T_ENABLED) or sniconf.get(T_ENABLED) is False:
                    _c("Sniffer not enabled")
                    return None, None

            _c("Sniffer enabled")
            if not path.isdir(sniconf.get(T_PCAP)):
                makedirs(sniconf.get(T_PCAP))

            pcap_path = _s('{}/{}.pcap', sniconf.get(T_PCAP), genid)
            _c("PCAP path: {}", pcap_path)

            if not path.exists(Sniffer.fifo_path):
                mkfifo(Sniffer.fifo_path)
            _c("{}, {}, {}", sniconf.get(T_PORT), sniconf.get(T_BAUD),\
                sniconf.get(T_CHANNEL))

            in_hdr = SerialInputHandler(
            port=sniconf.get(T_PORT), baudrate=sniconf.get(T_BAUD),\
            channel=sniconf.get(T_CHANNEL))
    
            out_hdr = []
#            out_hdr.append(PcapStdOutHandler())
            fifo_hdr = FifoOutHandler(Sniffer.fifo_path)
            out_hdr.append(fifo_hdr)

            pcap_hdr = PcapDumpOutHandler(pcap_path)
            out_hdr.append(pcap_hdr)

            if not PcapToMq.init(rt.tcfg.mqtt[0], rt.tcfg.mqtt[1], sniconf, genid=genid):
                return None, None
#                Sniffer.sniffer_worker = threading.Thread(target=PcapToMq.start)

            _l.info(_s("Sniffer initialized"))
        except Exception as ex:
            _l.error(_s("Failed to initialize sniffer: {}", ex))
            return None, None

        Sniffer.running = True
        return in_hdr, out_hdr 

    @staticmethod
    def start(in_hdr, out_hdr):
        """
        python tools/pysniffer.py -f /tmp/sniffer.fifo -b 230400 -d /dev/ttyUSB5 -L build/sniffer.log -c 17
        """
        _l.info("Sniffer start")
        if in_hdr is None or out_hdr is None:
            return

        Sniffer.sniffer_worker = threading.Thread(target=Sniffer._start, args=(in_hdr, out_hdr))
        Sniffer.sniffer_worker.start()
        Sniffer.tshark_worker = threading.Thread(target=PcapToMq.start)
        Sniffer.tshark_worker.start()
#        PcapToMq.start()

    @staticmethod
    def _start(in_hdr, out_hdr):
        _l.info("Sniffer routine started")
        while Sniffer.running:
            try:
                raw = in_hdr.read_frame()
                if raw:
                    frame = Frame(raw)
                    for h in out_hdr:
                        h.handle(frame)
                PcapToMq._mqclient.loop()
            except (KeyboardInterrupt, SystemExit):
                in_hdr.close()
                sys.exit(0)
            except Exception as ex:
                _l.error(_s("Runtime error in sniffer routine: {}", ex))

    @staticmethod
    def stop():
        
        if not Sniffer.running:
            return
        _c("Stopping sniffer ...")
        Sniffer.running = False

        if Sniffer.sniffer_worker:
            Sniffer.sniffer_worker.join()

        PcapToMq.stop()
        if Sniffer.tshark_worker:
            Sniffer.tshark_worker.join()

def start_sniffer(genid=None):

    if genid is None:
        genid = str(int(time.time()))
    in_hdr, out_hdr = Sniffer.init(genid)
    Sniffer.start(in_hdr, out_hdr)

def stop_sniffer():

    Sniffer.stop()

def handle_args(in_args=None):
    """Arguments handler"""    
    args = None
    try:
        rt.parser.description = 'Inuithy Sniffer'
        rt.parser.add_argument('-gid', '--genid', required=True, help='Traffic generation identifier')
        args = rt.handle_args()
        load_configs()
    except Exception as ex:
        _c("Exception on handling sniffer arguments: {}", ex)
        return None
    return args

if __name__ == '__main__':

    args = handle_args()
    start_sniffer(args.genid)
    try:
        input('Enter to quit ...')
    except SyntaxError:
        _c("Using Py2")
    stop_sniffer()


