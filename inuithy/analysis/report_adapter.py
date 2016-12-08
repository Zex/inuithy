""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
to_console, to_string
from inuithy.common.supported_proto import SupportedProto
import logging
import logging.config as lconf
#from bson.objectid import ObjectId
import sys

lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class ReportAdapter(object):
    """Analysis helper"""
    handler = None
    
    @staticmethod
    def guess_proto(nodes):
        """Guess protocol to use for analysing
            [ntype.name] => (ntype, proto, node, report_hdr)
        @nodes List of Node, sample nodes for guessing
        """
        if nodes is None or len(nodes) == 0:
            lgr.error("No nodes sample to guess")
            return
        cnt = {}
        try:
            for proto in SupportedProto.protocols.keys():
                cnt[proto] = len([node for node in nodes if node.ntype.name == proto])
            lgr.info(to_string("Node summary: {}", cnt))
            proto = max(cnt)
            ReportAdapter.handler = SupportedProto.protocols.get(proto)[3]
        except Exception as ex:
            lgr.error(to_string("Exception on guessing protocol: {}", ex))
        
    #TODO
    @staticmethod
    def create_csv(recs, ginfo):
        """Create CSV format from records"""
        pass

    @staticmethod
    def gen_report(inuithy_cfgpath=INUITHY_CONFIG_PATH, genid=None):
        """Report generation helper"""
        pass

    @staticmethod
    def gen_csv(ginfo):
        """Generate CSV file"""
        pass

    @staticmethod
    def generate(genid, gw=None, nodes=None, irange=None, cfgpath=INUITHY_CONFIG_PATH):
        """Generate CSV data and traffic analysis figures"""
        if ReportAdapter.handler is not None:
            ReportAdapter.handler.generate(genid, gw, nodes, irange, cfgpath)
        else:
            lgr.error("No report handler avalable")

if __name__ == '__main__':

#    ReportAdapter.gen_report(genid='581fdfe3362ac719d1c96eb3')
#    ReportAdapter.gen_report(genid='1478508817')
#    ReportAdapter.gen_report(genid='1478585096')
    if len(sys.argv) > 1:
        ReportAdapter.handler = SupportedProto.protocols.get(sys.argv[1])[2]
        to_console("Using report handler {}", ReportAdapter.handler)
    if len(sys.argv) > 2:
        ReportAdapter.generate(sys.argv[2], gw=None, nodes=None, irange=None)
    else:
        to_console("Genid not given")

