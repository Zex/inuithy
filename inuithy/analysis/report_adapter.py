""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import _c, _s, _l
from inuithy.common.runtime import Runtime as rt
from inuithy.common.agent_info import SupportedProto
#from bson.objectid import ObjectId
import sys

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
            _l.error("No nodes sample to guess")
            return
        cnt = {}
        try:
            for proto in SupportedProto.protocols.keys():
                cnt[proto] = len([node for node in nodes if node.ntype.name == proto])
            _l.info(_s("Node summary: {}", cnt))
            proto = max(cnt)
            ReportAdapter.handler = SupportedProto.protocols.get(proto)[3]
        except Exception as ex:
            _l.error(_s("Exception on guessing protocol: {}", ex))
        
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
            _l.error("No report handler avalable")

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
            _c("GENID {}", args.genid)
            _c("Nodes of interest {}", args.nodes)
            _c("Subnet gateway {}", args.gateways)
            _c("CSV Path {}", args.csv_path)
        except Exception as ex:
            _c("Exception on handling report arguments: {}", ex)
            return None
        return args

if __name__ == '__main__':

    args = ReportAdapter.handle_args()
    if args is not None:
        ReportAdapter.handler = SupportedProto.protocols.get(args.proto)[3]
        _c("Using report handler {}", ReportAdapter.handler)
        ReportAdapter.generate(args.genid, gw=args.gateways, nodes=args.nodes, irange=None, csv_path=args.csv_path)

