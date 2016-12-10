""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, to_console, to_string
from inuithy.common.runtime import Runtime as rt
from inuithy.common.agent_info import SupportedProto
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
    def gen_report(genid=None):
        """Report generation helper"""
        pass

    @staticmethod
    def gen_csv(ginfo):
        """Generate CSV file"""
        pass

    @staticmethod
    def generate(genid, gw=None, nodes=None, irange=None, csv_path=None):
        """Generate CSV data and traffic analysis figures"""
        if ReportAdapter.handler is not None:
            ReportAdapter.handler.generate(genid, gw, nodes, irange, csv_path)
        else:
            lgr.error("No report handler avalable")

    @staticmethod
    def handle_args():
        """Arguments handler"""    
        args = None
        try:
            rt.parser.description = 'Report Adapter'
            rt.parser.add_argument('-proto', required=True, help=\
            'Generate report based on protocol', choices=SupportedProto.protocols.keys())
            rt.parser.add_argument('-gid', '--genid', required=True, help='Traffic generation identifier')
            rt.parser.add_argument('-n', '--nodes', help='Nodes of interest', nargs="+")
            rt.parser.add_argument('-gw', '--gateways', help='Gateway node', nargs="+")
            rt.parser.add_argument('-csv', '--csv_path', help='Path to CSV data source')
            args = rt.handle_args()
            to_console("GENID {}", args.genid)
            to_console("Nodes of interest {}", args.nodes)
            to_console("Subnet gateway {}", args.gateways)
            to_console("CSV Path {}", args.csv_path)
        except Exception as ex:
            to_console("Exception on handlin report arguments: {}", ex)
            return None
        return args

if __name__ == '__main__':

    args = ReportAdapter.handle_args()
    if args is not None:
        ReportAdapter.handler = SupportedProto.protocols.get(args.proto)[3]
        to_console("Using report handler {}", ReportAdapter.handler)
        ReportAdapter.generate(args.genid, gw=args.gateways, nodes=args.nodes, irange=None, csv_path=args.csv_path)

