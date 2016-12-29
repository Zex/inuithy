#!/usr/bin/env python

# Copyright (c) 2012, George Oikonomou (oikonomou@users.sf.net)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the owner nor the names of its contributors may be
#     used to endorse or promote products derived from this software without
#     specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Read IEEE802.15.4 frames from a serial line (captured by a sniffer) and pipe
# them to wireshark. At the same time, the frames can be logged to a file for
# subsequent offline processing


# ToDo:
# * Python 3 support
# * Configuration file support (ConfigParser ?)
import serial
import argparse
import os
import sys
import time
import stat
import errno
import logging
import logging.handlers
import struct

#import ieee15dot4 as ieee
#####################################
### Constants
#####################################
__version__ = '0.1 alpha'
SENSSNIFF_START = '\xaa\x55\x03'

#####################################
### Default configuration values
#####################################
defaults = {
    'device': 'COM5',
    'baud_rate': 230400,
    'channel': 13,
    'out_fifo': '/tmp/pysniffer',
    'out_pcap': 'pysniffer.pcap',
    'log_level': 'INFO',
    'log_file': 'pysniffer.log',
}

#####################################
### PCAP and Command constants
#####################################
LINKTYPE_IEEE802_15_4_NOFCS = 230
LINKTYPE_IEEE802_15_4 = 195
MAGIC_NUMBER = 0xA1B2C3D4
VERSION_MAJOR = 2
VERSION_MINOR = 4
THISZONE = 0
SIGFIGS = 0
SNAPLEN = 0xFFFF
NETWORK = LINKTYPE_IEEE802_15_4

PCAP_GLOBAL_HDR_FMT = '<LHHlLLL'
PCAP_FRAME_HDR_FMT = '<LLLL'

def encoded_write(port, data):
    port.write(data.encode())
#####################################
### Globals
#####################################
logger = logging.getLogger(__name__)
stats = {}
#####################################
class Frame(object):
    def __init__(self, raw):
        self.__raw = raw
        self.__t = time.time()
        self.len = len(self.__raw)

        self.__pcap_hdr = self.__generate_frame_hdr()

        self.pcap = self.__pcap_hdr + self.__raw

    def __generate_frame_hdr(self):
        sec = int(self.__t)
        usec = int((self.__t % 1) * 1000000)
        return struct.pack(PCAP_FRAME_HDR_FMT,
                           sec, usec, self.len, self.len)

    def get_pcap(self):
        return self.pcap

    def get_timestamp(self):
        return self.__t

    def get_macPDU(self):
        return self.__raw        

#####################################
#####################################
class SerialInputHandler(object):
    def __init__(self,
                 port = defaults['device'],
                 baudrate = defaults['baud_rate'],
                 channel = defaults['channel']):
        self.__pysniffer_magic = struct.pack('BBB', 0xaa, 0x55, 0x03)
        stats['Captured'] = 0
        stats['Non-Frame'] = 0
        try:
            self.channel = channel
            self.port = serial.Serial(port = port,
                                      baudrate = baudrate,
                                      bytesize = serial.EIGHTBITS,
                                      parity = serial.PARITY_NONE,
                                      stopbits = serial.STOPBITS_ONE,
                                      xonxoff = False,
                                      rtscts = False,
                                      timeout = 0.1)
        except (serial.SerialException, ValueError, IOError, OSError) as e:
            logging.error('Error opening port: %s\r\n' % (port,))
            logging.error('The error was: %s\r\n' % (e,))
            sys.exit(1)
            
        logging.info('Serial port %s opened\r\n' % (self.port.name))

        try:
            encoded_write(self.port, "[QoS,Channel,%d]\r" % (self.channel))
            logging.info('Channel set to %d\r\n' % (self.channel))
            encoded_write(self.port, "[QoS,Sniffer,1]\r")
    
            self.port.flushInput()
            self.port.flushOutput()
        except (serial.SerialException, ValueError, IOError, OSError) as e:
            logging.error('Error opening port: %s\r\n' % (port,))
            logging.error('The error was: %s\r\n' % (e,))
            self.port.close()
            sys.exit(1)


    def close(self):
        encoded_write(self.port, "[QoS,Channel,0]\r")
        encoded_write(self.port, "[QoS,Sniffer,0]\r")
        self.port.flushInput()
        self.port.flushOutput()
        self.port.close()


    def read_frame(self):
        try:
            bytes = self.port.read(13)
     
            if not bytes:
                return None
            
             #logging.debug(','.join(["%02x" % ord(c) for c in bytes]))
             
            if len(bytes) != 13:
                return None
    
            if bytes[0:len(SENSSNIFF_START)] != SENSSNIFF_START:
                # Throw this line messages
                while True:
                    c = self.port.read()
                    if not c:
                        break;
                return None
    
            size = ord(bytes[-1]) + 2
            bytes = self.port.read(size)
        except (IOError, OSError) as e:
            logging.error('Error reading port: %s\r\n' % (self.port.port,))
            logging.error('The error was: %s\r\n' % (e,))
            self.port.close()
            sys.exit(1)
            
        if len(bytes) != size:
            return None

        logging.debug('Length %d Data:%s\r\n' % (size ,','.join(["%02x" % ord(c) for c in bytes])))
        return bytes

#####################################
class FifoOutHandler(object):
    def __init__(self, out_fifo):
        self.out_fifo = out_fifo
        self.of = None
        self.needs_pcap_hdr = True
        stats['Piped'] = 0
        stats['Not Piped'] = 0
        self.__pcap_global_hdr = struct.pack(
            PCAP_GLOBAL_HDR_FMT, MAGIC_NUMBER, VERSION_MAJOR, VERSION_MINOR,
            THISZONE, SIGFIGS, SNAPLEN, NETWORK)

        self.__create_fifo()

    def __create_fifo(self):
        try:
            os.mkfifo(self.out_fifo)
            logging.info('Opened FIFO %s' % (self.out_fifo,))
        except OSError as e:
            if e.errno == errno.EEXIST:
                if stat.S_ISFIFO(os.stat(self.out_fifo).st_mode) is False:
                    logging.error('File %s exists and is not a FIFO'
                                 % (self.out_fifo,))
                    sys.exit(1)
                else:
                    logging.warn('FIFO %s exists. Using it' % (self.out_fifo,))
            else:
                raise

    def __open_fifo(self):
        try:
            fd = os.open(self.out_fifo, os.O_NONBLOCK | os.O_WRONLY)
            self.of = os.fdopen(fd, 'w')
        except OSError as e:
            if e.errno == errno.ENXIO:
                logging.warn('Remote end not reading')
                stats['Not Piped'] += 1
                self.of = None
                self.needs_pcap_hdr = True
            elif e.errno == errno.ENOENT:
                logging.error('%s vanished under our feet' % (self.out_fifo,))
                logging.error('Trying to re-create it')
                self.__create_fifo_file()
                self.of = None
                self.needs_pcap_hdr = True
            else:
                raise

    def handle(self, data):
        if self.of is None:
            self.__open_fifo()

        if self.of is not None:
            try:
                if self.needs_pcap_hdr is True:
                    self.of.write(self.__pcap_global_hdr)
                    self.needs_pcap_hdr = False
                self.of.write(data.pcap)
                self.of.flush()
                logging.debug('Wrote a frame of size %d bytes' % (data.len))
                stats['Piped'] += 1
            except IOError as e:
                if e.errno == errno.EPIPE:
                    logging.info('Remote end stopped reading')
                    stats['Not Piped'] += 1
                    self.of = None
                    self.needs_pcap_hdr = True
                else:
                    raise
#####################################
#####################################
class PcapStdOutHandler(object):
    def __init__(self):
        if sys.platform == "win32":
            import os, msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            """
        else:
            import codecs
            if sys.stdout.encoding != 'UTF-8':
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')
            if sys.stderr.encoding != 'UTF-8':
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr, 'strict')
                """

        self.__pcap_global_hdr = struct.pack(
            PCAP_GLOBAL_HDR_FMT, MAGIC_NUMBER, VERSION_MAJOR, VERSION_MINOR,
            THISZONE, SIGFIGS, SNAPLEN, NETWORK)
        try:
            sys.stdout.write(self.__pcap_global_hdr)
            sys.stdout.flush()
            
            logging.debug('Wrote __pcap_global_hdr\r\n')
        except IOError as e:
            logging.info('Remote end stopped reading\r\n')

    def handle(self, data):
        try:
            sys.stdout.write(data.pcap)
            sys.stdout.flush()
        
            logging.debug('Wrote a frame of size %d bytes\r\n' % (data.len))
        except IOError as e:
            if e.errno == errno.EPIPE:
                logging.info('Remote end stopped reading\r\n')
            else:
                sys.exit(1)
            #    raise
#####################################
class PcapDumpOutHandler(object):
    def __init__(self, out_pcap):
        self.out_pcap = out_pcap
        stats['Dumped to PCAP'] = 0
        self.__pcap_global_hdr = struct.pack(
            PCAP_GLOBAL_HDR_FMT, MAGIC_NUMBER, VERSION_MAJOR, VERSION_MINOR,
            THISZONE, SIGFIGS, SNAPLEN, NETWORK)

        try:
            self.of = open(self.out_pcap, 'wb')
            self.of.write(self.__pcap_global_hdr)
            logging.info("Dumping PCAP to %s\r\n" % (self.out_pcap,))
        except IOError as e:
            self.of = None
            logging.warn("Error opening %s to save pcap. Skipping\r\n"
                         % (out_pcap))
            logging.warn("The error was: %d - %s\r\n"
                         % (e))

    def handle(self, frame):
        if self.of is None:
            return
        self.of.write(frame.get_pcap())
        self.of.flush()
        logging.info('PcapDumpOutHandler: Dumped a frame of size %d bytes\r\n'
                     % (frame.len))
        stats['Dumped to PCAP'] += 1
        
#####################################
class ZigBeeParser(object):
    def __init__(self):
        stats['Dissection errors'] = 0
        return

    def handle(self, frame):
        try:
            frame = ieee.IEEE15dot4FrameFactory.parse(frame)
            sys.stderr.write("%s\r\n" %(frame.__repr__()))
            sys.stderr.flush()
            
        except Exception as e:
            logging.warn("Error dissecting frame.\r\n")
            logging.warn("The error was: %s\r\n" % (e))
            stats["Dissection errors"] += 1     
        
#####################################
def arg_parser():
    speed_choices = (9600, 19200, 38400, 57600, 115200, 230400, 460800)
    debug_choices = ('DEBUG', 'INFO', 'WARN', 'ERROR')

    parser = argparse.ArgumentParser(add_help = False,
                                     description = 'Read IEEE802.15.4 frames \
    from a pysniffer enabled device, convert them to pcap and pipe them \
    into wireshark over a FIFO pipe for online analysis. Frames \
    can also be saved in a file in pcap format for offline \
    analysis.')

    in_group = parser.add_argument_group('Input Options')
    in_group.add_argument('-b', '--baud', type = int, action = 'store',
                          choices = speed_choices,
                          default = defaults['baud_rate'],
                          help = 'Set the line\'s BAUD rate to BAUD. \
                                  Only makes sense with -d. \
                                  (Default: %s)' % (defaults['baud_rate'],))
                                  
    in_group.add_argument('-c', '--channel', type = int, action = 'store',
                          default = defaults['channel'],
                          help = 'Read the TI ZigBee Dongle\'s Channel\
                                  (Default: %s)' % (defaults['channel'],))
                                                       
    in_group.add_argument('-d', '--device', action = 'store',
                          default = defaults['device'],
                          help = 'Read from device DEVICE \
                                  (Default: %s)' % (defaults['device'],))

    out_group = parser.add_argument_group('Output Options')
    out_group.add_argument('-p', '--pcap', action = 'store', nargs = '?',
                           const = defaults['out_pcap'], default = False,
                           help = 'Save the capture (pcap format) in PCAP. \
                                   If -p is specified but PCAP is omitted, \
                                   %s will be used. If the argument is \
                                   omitted altogether, the capture will not \
                                   be saved.' % (defaults['out_pcap'],))
                                   
    out_group.add_argument('-f', '--fifo', action = 'store', nargs = '?',
                           const = defaults['out_fifo'], default = False,
                           help = 'Output the capture (pcap format) into pipe. \
                                   If -f is specified but pipe is omitted, \
                                   %s will be used. If the argument is \
                                   omitted altogether, the pipe will not \
                                   be used.' % (defaults['out_fifo'],))
                                                  
    out_group.add_argument('-O', '--stdout', action = 'store_true',
                           default = False,
                           help = 'Enable stdout (Mainly used for debugging and piping) \
                                   (Default: stdout disabled)')

    out_group.add_argument('-P', '--parser', action = 'store_true',
                           default = False,
                           help = 'Enable ZigBee parser (Mainly used for uploading data to Splunk) \
                                   (Default: parser disabled)')
                                   
    log_group = parser.add_argument_group('Verbosity and Logging')
    log_group.add_argument('-L', '--log-file', action = 'store', nargs = '?',
                           const = defaults['log_file'], default = False,
                           help = 'Log output in LOG_FILE. If -L is specified \
                                   but LOG_FILE is omitted, %s will be used. \
                                   If the argument is omitted altogether, \
                                   logging will not take place at all.'
                                   % (defaults['log_file'],))
    log_group.add_argument('-l', '--log-level', action = 'store',
                           choices = debug_choices,
                           default = defaults['log_level'],
                           help = 'Log messages of severity LOG_LEVEL or \
                                   higher. Only makes sense if -L is also \
                                   specified (Default %s)'
                                   % (defaults['log_level'],))

    gen_group = parser.add_argument_group('General Options')
    gen_group.add_argument('-v', '--version', action = 'version',
                           version = 'pysniffer v%s' % (__version__))
    gen_group.add_argument('-h', '--help', action = 'help',
                           help = 'Shows this message and exits')

    return parser.parse_args()
#####################################
def dump_stats():
    logging.info('Frame Stats:\r\n')
    for k, v in stats.items():
        logging.info('%20s: %d\r\n' % (k, v))

#####################################
def log_init():
    logging.setLevel(logging.DEBUG)
     
    if args.log_file is not False:
        #fh = logging.handlers.RotatingFileHandler(filename = args.log_file, mode='w+', maxBytes = 5000000)
        fh = logging.FileHandler(filename = args.log_file, mode='w+')
        fh.setLevel(getattr(logging, args.log_level))
        ff = logging.Formatter('%(asctime)s - %(levelname)8s - %(message)s')
        #ff = logging.Formatter('%(message)s')
        fh.setFormatter(ff)
        logging.addHandler(fh)
#####################################
if __name__ == '__main__':
    args = arg_parser()
    log_init()

    logging.info('Started logging\r\n')

    in_handler = SerialInputHandler(port = args.device, baudrate = args.baud, channel = args.channel)

    out_handlers = []
    if args.fifo is not False:
        out_handlers.append(FifoOutHandler(args.fifo))
            
    if args.stdout is True:
        f = PcapStdOutHandler()
        out_handlers.append(f)
        
    if args.pcap is not False:
        out_handlers.append(PcapDumpOutHandler(args.pcap))
        
    if args.parser is True:
        out_handlers.append(ZigBeeParser())
    
    while 1:
        try:
            raw = in_handler.read_frame()
            if raw:
                frame = Frame(raw)
                for h in out_handlers:
                    h.handle(frame)
        except (KeyboardInterrupt, SystemExit):
            logging.info('Shutting down\r\n')
            dump_stats()
            in_handler.close()
            sys.exit(0)
