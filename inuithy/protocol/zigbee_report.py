""" Report generator for Zigbee protocol
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
T_NODE, T_RECORDS, T_MSG_TYPE, T_TIME, T_GENID, T_REPORTDIR, T_PATH,\
T_GATEWAY, to_console, to_string, MessageType, T_HOST, StorageType,\
GenInfo, T_TYPE, TrafficStorage
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as PROTO
from inuithy.protocol.zigbee_proto import T_ZBEE_NWK_ADDR
from inuithy.common.runtime import Runtime as rt, load_configs
from inuithy.storage.storage import Storage
from inuithy.protocol.zigbee_proto import ZigbeeProtocol as ZbeeProto
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib as mplib
import pandas as pd
import numpy as np
import logging
import logging.config as lconf
#from bson.objectid import ObjectId
import json
import sys
from os import path, makedirs
from copy import deepcopy

mplib.style.use('ggplot')
lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class ZbeeReport(object):
    """Zigbee report helper
    Ex:
            nodes = ['0x0000', '0x0001', '0x0102', '0x0103',\
                     '0x0205', '0x0206', '0x0303', '0x0304',\
                     '0x0400', '0x0401']
            gw = '0x0207'
            irange = None #(70, 150)
            -------------------------------
            nodes = None
            gw = '0x0303'
            irange = None
            gw = ['1122']
            nodes = ['11a1', '11a3', '11f2', '1131', '1174', '1132', '1181', '1172', '1182', '1134', '11e3', '11d4', '11f3', '11f4', '11e1', '1133', '11b3', '11b4', '1124', '1152', '11b1', '1142', '1193', '1113', '1164', '1153', '11c2', '1162', '1144', '1154', '1112', '11c4', '11f1', '1141', '1183', '1163', '1111', '1103', '1102', '11b2', '11d3', '11c1', '11a2', '11e2', '1173', '11d2', '1194', '1191', '1101', '1114', '11c3', '11e4', '11d1', '1123', '1104', '11a4', '1151', '1143', '1122', '1161', '1192', '1121']
            nodes = [
                '0x0000', '0x0001', '0x0102', '0x0103',
                '0x0206', '0x0303', '0x0304',
                '0x0401', '0x0400'
            ]
#            nodes = ['0x0401', '0x0102',]
    """
    @staticmethod
    def create_csv(recs, ginfo):
        """Create CSV format from records
        """
        lgr.info(to_string("Create csv data for genid {}", ginfo.genid))
        df = pd.DataFrame.from_records(recs)
        df = df.fillna(value=0)
        data = df.to_csv(columns=ginfo.header, index=False)
        return data

    @staticmethod
    def diag_item_based(ginfo, pdata, item, pdf_pg, nodes=None, iloc_range=None, title=None):
        lgr.info(to_string("Creating figure for item {}", item))
        df = None
        index_l = 0
        data = {}
        try:
            addr_grp = pdata.groupby([T_ZBEE_NWK_ADDR], as_index=False)
            if nodes is None or len(nodes) == 0:
                nodes = addr_grp.groups.keys()

            for addr in nodes:
                try:
                    grp = addr_grp.get_group(addr)
                    index_l = max(index_l, len(grp[item].values))
                    buf = np.array(grp[item].values)
                    buf = np.diff(buf)
                    data[addr] = buf
                except KeyError as ex:
                    lgr.warning(to_string("No record for node [{}]: {}", addr, ex))
        except Exception as ex:
            lgr.error(to_string("Exception on processing diag data {}: {}", item, ex))
            return

        for k in data:
            buf = [np.nan] * index_l
            buf[:len(data[k])] = data[k]
            data[k] = buf
        index = np.arange(0, index_l)
        df = pd.DataFrame(data, index=index)

        try:
            if df is not None and not df.empty:
                if iloc_range is not None:
                    df = df.iloc[iloc_range[0]:iloc_range[1]]
#                else:
#                    df = df.iloc[1:]
                if title is None or len(title) == 0:
                    title = to_string("{} by {}", item, T_ZBEE_NWK_ADDR)
                df.plot(xticks=[], lw=1.5, colormap=ginfo.colormap, figsize=ginfo.figsize)
            else:
                lgr.warning("DataFrame is empty")
        except Exception as ex:
            lgr.error(to_string("Exception on creating diag data figure {}: {}", item, ex))
            return

        try:
#            plt.ylim(0, df.max()[1])
#            plt.ylim(df.min()[1], df.max()[1])
            plt.autoscale(enable=False, axis='y', tight=True)
            plt.xlabel(T_TIME)
            plt.ylabel(item)
            plt.title(title)
            legend_ncol = len(nodes) > 24 and (len(nodes) // 24 + 1) or 1
            plt.legend(loc=2, bbox_to_anchor=(1, 1), borderpad=0.5,\
                framealpha=0.0, ncol=legend_ncol, fontsize='medium')
            plt.grid(axis='x')
            plt.yscale('linear')

            if ginfo.fig_base is not None:
                plt.savefig(to_string("{}/{}.png", ginfo.fig_base, title), transparent=False, facecolor='w', edgecolor='b', bbox_inches='tight')
            if pdf_pg is not None:
                pdf_pg.savefig(transparent=False, facecolor='w', edgecolor='b', bbox_inches='tight')
            plt.close()
        except Exception as ex:
            lgr.error(to_string("Exception on saving diag data figure {}: {}", item, ex))

    @staticmethod
    def total_pack(ginfo, pdata, pdf_pg, title=None):
        """Create package sent/recv summary"""
        lgr.info("Create package summary")

        try:
            total_send = len(pdata[T_TYPE][pdata.type == ZbeeProto.MsgType.snd.name])
            total_recv = len(pdata[T_TYPE][pdata.type == ZbeeProto.MsgType.rcv.name])
            total_dgn = len(pdata[T_TYPE][pdata.type == ZbeeProto.MsgType.dgn.name])
            total_snd_req = len(pdata[T_TYPE][pdata.type == ZbeeProto.MsgType.snd_req.name])
    
            data = {
                ZbeeProto.MsgType.snd.name: total_send,
                ZbeeProto.MsgType.rcv.name: total_recv,
                ZbeeProto.MsgType.dgn.name: total_dgn,
                ZbeeProto.MsgType.snd_req.name: total_snd_req,
            }
            df = pd.DataFrame(list(data.values()), index=data.keys(), columns=[T_TYPE])

            if df is not None and not df.empty:
                df = df.fillna(value=0)
                if title is None or len(title) == 0:
                    title = to_string("Package summary")
                df.plot(kind='bar', colormap='plasma', grid=False, figsize=ginfo.figsize)
            else:
                lgr.warning("WARN: DataFrame is empty")

#           plt.ylabel(item)
            plt.title(title)
            plt.legend(loc=2, bbox_to_anchor=(1, 1), borderpad=1.)
            plt.grid(axis='y')

            if ginfo.fig_base is not None:
                plt.savefig(to_string("{}/{}.png", ginfo.fig_base, title), bbox_inches='tight')
            if pdf_pg is not None:
                pdf_pg.savefig(bbox_inches='tight')
            plt.close()
        except Exception as ex:
            lgr.error(to_string("Exception on creating package summary figure: {}", ex))

    @staticmethod
    def prep_info(genid):
        """
        time,"zbee_nwk_addr",
        macTxBcast,macTxUcastRetry,macTxUcastFail,macTxUcast,macRxBcast,macRxUcast,
        neighborAdded,neighborRemoved,neighborStale,averageMACRetryPerAPSMessageSent,
        routeDiscInitiated,relayedUcast,packetBufferAllocateFailure,
        apsTxBcast,apsTxUcastSuccess,apsTxUcastFail,apsTxUcastRetry,apsRxBcast,apsRxUcast
        """
        lgr.info(to_string("Prepare generation info with {}", genid))
        ginfo = GenInfo()

        ginfo.genid = genid
        ginfo.fig_base = to_string('{}/{}',\
            rt.tcfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.csv_path = to_string('{}/{}.csv',\
            rt.tcfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.raw_csv_path = to_string('{}/raw-{}.csv',\
            rt.tcfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.pdf_path = to_string('{}/{}.pdf',\
            rt.tcfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.src_type = rt.tcfg.storagetype[0]
        ginfo.figsize = (15, 6)

        ginfo.header = [T_TIME, T_ZBEE_NWK_ADDR]
        ginfo.header.extend(PROTO.DIAG_ITEM)
        if not path.isdir(ginfo.fig_base):
            makedirs(ginfo.fig_base)
        return ginfo

    @staticmethod
    def gen_csv(ginfo):
        """
        time,"zbee_nwk_addr",
        macTxBcast,macTxUcastRetry,macTxUcastFail,macTxUcast,macRxBcast,macRxUcast,
        neighborAdded,neighborRemoved,neighborStale,averageMACRetryPerAPSMessageSent,
        routeDiscInitiated,relayedUcast,packetBufferAllocateFailure,
        apsTxBcast,apsTxUcastSuccess,apsTxUcastFail,apsTxUcastRetry,apsRxBcast,apsRxUcast
        """
        lgr.info(to_string("Generate csv with ginfo[{}]", ginfo))
        try:
            storage = Storage(rt.tcfg, lgr)

            if ginfo.src_type == TrafficStorage.DB.name:
                return ZbeeReport.import_from_db(ginfo, storage)
            elif ginfo.src_type == TrafficStorage.FILE.name:
                return ZbeeReport.import_from_file(ginfo, storage)
            else:
                lgr.error(to_string("Unsupported storage type: {}", ginfo.src_type))
        except Exception as ex:
            lgr.error(to_string("Import data failed: {}", ex))

    @staticmethod
    def import_from_db(ginfo, storage):
        """Import traffic data from database"""
        raw, pdata = None, None
        hasdiag = False
        req = {T_GENID: ginfo.genid,}

        with storage.trafrec.find(req) as cursor:

            if cursor is None or cursor.count() == 0:
                raise ValueError(to_string("Recored with {} not found", ginfo.genid))
    
            for r in cursor:
                recs = r.get(T_RECORDS)
                raw = pd.DataFrame.from_records(recs)
                raw.to_csv(ginfo.raw_csv_path, columns=raw.keys(), index=False)
    
                ret = raw.get(ginfo.header[2])
                if ret is not None:
                    pdata = pd.DataFrame(raw[pd.notnull(raw[ginfo.header[2]])])
    #               pdata = pdata.fillna(value=0)
                    [pdata.__setitem__(item, pdata[item].astype(int)) for item in ginfo.header[2:]]
                    pdata.to_csv(ginfo.csv_path, columns=ginfo.header, index=False)
                    hasdiag = True
                return raw, pdata, hasdiag
            
    @staticmethod
    def import_from_file(ginfo, storage):
        """Import traffic data from file"""
        raw, pdata = None, None
        raw = pd.DataFrame.from_csv(ginfo.csv_path, index_col=None)
        hasdiag = False

        if raw.get(ginfo.header[2]):
            pdata = pd.DataFrame(raw[pd.notnull(raw[ginfo.header[2]])])
            [pdata.__setitem__(item, pdata[item].astype(int)) for item in ginfo.header[2:]]
            hasdiag = True
#       pdata.to_csv(ginfo.csv_path, columns=ginfo.header, index=False)
        return raw, pdata, hasdiag

    @staticmethod
    def gen_report(raw, pdata, ginfo, gw=None, interest_nodes=None, irange=None):
        """Report generation helper"""
        lgr.info(to_string("Generate report with gw={}, nodes={} irange={}", gw, interest_nodes, irange))
        if raw is None or raw.get(T_TIME) is None or len(raw[T_TIME]) == 0:
            lgr.warning(to_string("No time-based records found"))
            return
#        pdata = pd.read_csv(ginfo.csv_path, index_col=False, names=ginfo.header, header=None)
        pdata.info(verbose=True)
        failed = False
        pdata.sort_values(by=T_TIME, inplace=True)
        with PdfPages(ginfo.pdf_path) as pdf_pg:
            ZbeeReport.total_pack(ginfo, raw, pdf_pg)
            if hasattr(ginfo, 'hasdiag') and ginfo.hasdiag:
                try:
                    if gw is not None and len(gw) > 0:
                        for item in ginfo.header[2:]:
                            for gwnode in gw: # Each subnet
                                ZbeeReport.diag_item_based(ginfo, pdata, item, pdf_pg, [gwnode],\
                            title = to_string("{} by gateway {}", item, gwnode))#fig_base=ginfo.fig_base)
                except Exception as ex:
                    lgr.error(to_string("Exception on saving gateway report: {}", ex))
                    failed = True
    
                try:
                    for item in ginfo.header[2:]:
                        ZbeeReport.diag_item_based(ginfo, pdata, item, pdf_pg, interest_nodes, irange)
                except Exception as ex:
                    lgr.error(to_string("Exception on saving diag data report: {}", ex))
                    failed = True
        if not failed:
            to_console("..............................................")
            to_console("gid: {}\ncsv: {}\npdf: {}\nfigures: {}", ginfo.genid, ginfo.csv_path, ginfo.pdf_path, ginfo.fig_base)
        else:
            to_console("Generation failed, check out logs for more details")

    @staticmethod
    def generate(genid, gw=None, nodes=None, irange=None, csv_path=None):
        """Generate CSV data and traffic analysis figures
               ginfo.csv_path = 'docs/UID1478067701.csv'
               ginfo.csv_path = 'docs/UID1470021754.csv'
        """
#        try:
        if True:
            ginfo = ZbeeReport.prep_info(genid)
#TODO: uncomment
            if csv_path is not None:
                ginfo.csv_path = csv_path
            raw, pdata, hasdiag = ZbeeReport.gen_csv(ginfo)
            ginfo.hasdiag = hasdiag
            ZbeeReport.gen_report(raw, pdata, ginfo, gw, nodes, irange)
#        finally: pass
#        except Exception as ex:
#            lgr.error(to_string("Exception on generate reports: {}", ex))

    @staticmethod
    def handle_args(in_args=None):
        """Arguments handler"""    
        args = None
        try:
            rt.parser.description = 'Zigbee Traffic Report Generator'
            rt.parser.add_argument('-gid', '--genid', required=True, help='Traffic generation identifier')
            rt.parser.add_argument('-n', '--nodes', help='Nodes of interest', nargs="+")
            rt.parser.add_argument('-gw', '--gateways', help='Gateway node', nargs="+")
            rt.parser.add_argument('-csv', '--csv_path', help='Path to CSV data source')
            args = rt.handle_args()
            load_configs()
            to_console("GENID {}", args.genid)
            to_console("Nodes of interest {}", args.nodes)
            to_console("Subnet gateway {}", args.gateways)
            to_console("CSV Path {}", args.csv_path)
        except Exception as ex:
            to_console("Exception on handling report arguments: {}", ex)
            return None
        return args


if __name__ == '__main__':

    args = ZbeeReport.handle_args()
    if args is not None:
        ZbeeReport.generate(args.genid, gw=args.gateways, nodes=args.nodes, irange=None, csv_path=args.csv_path)

