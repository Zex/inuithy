""" Zigbee protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import string_write
from inuithy.protocol.protocol import Protocol

class ZigbeeProtocol(Protocol):
    
    def __init__(self):
        pass

    def joinnw(self, ch):
        return string_write("join {}", ch)

    def writeattribute2(self, destination, packet_size, response=False):
        self.nr_messages_requested += 1
        send_request = {}
        send_request['time'] = time.time()
        send_request['type'] = 'snd_req'
        send_request['zbee_nwk_src'] = self.get_network_address()
        send_request['zbee_nwk_dst'] = destination
        if response == True:
            rsp = "1"
            send_request['ack'] = 'y'
        else:
            rsp = "0"
            send_request['ack'] = 'n'

        msg = 'writeAttribute2  s '+str(destination)+' 20 0 4 0x42 "1" %s '%str(packet_size) + rsp +"\r"

#        self.log_queue.put(send_request)
#        self.sport.write(msg)

        return msg

