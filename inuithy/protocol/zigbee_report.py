""" Report generator for Zigbee protocol
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
T_NODE, T_RECORDS, T_MSG_TYPE, T_TIME, T_GENID, T_REPORTDIR, T_PATH,\
T_GATEWAY, console_write, string_write, MessageType, T_HOST, StorageType,\
GenInfo
from inuithy.protocol.zigbee_proto import T_ZBEE_NWK_ADDR, T_MACTXBCAST,\
T_MACTXUCASTRETRY, T_MACTXUCASTFAIL, T_MACTXUCAST, T_MACRXUCAST,\
T_NEIGHBORADDED, T_NEIGHBORRMED, T_NEIGHBORSTALE, T_AVGMACRETRY,\
T_RTDISCINIT, T_RELAYEDUCAST, T_PKGBUFALLOCFAIL, T_APSTXBCAST,\
T_APSTXUCASTSUCCESS, T_APSTXUCASTFAIL, T_APSTXUCASTRETRY, T_APSRXBCAST,\
T_APSRXUCAST, T_MACRXBCAST
from inuithy.storage.storage import Storage
from inuithy.util.config_manager import create_inuithy_cfg, create_traffic_cfg
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
from os import path, mkdir
from copy import deepcopy

mplib.style.use('ggplot')
lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class ZbeeReport(object):
    """Zigbee report helper"""
    @staticmethod
    def create_csv(recs, ginfo):
        """Create CSV format from records
        """
        lgr.info(string_write("Create csv data for genid {}", ginfo.genid))
        df = pd.DataFrame.from_records(recs)
        df = df.fillna(value=0)
        data = df.to_csv(columns=ginfo.header, index=False)
        return data

#        data = []
#        index = set()
#
#        try:
#            for rec in recs:
#                if len([rec.get(k) for k in ginfo.header if rec.get(k) is not None]) != len(ginfo.header):
#                    continue
#                line = [rec.get(k) for k in ginfo.header if rec.get(k)]
#                print(line)
#                line_fmt = ('{},' * len(line)).strip(',')
#                data.append(string_write(line_fmt, *tuple(line)))
#        except Exception as ex:
#            lgr.error("Exception on CSV creation: {}", ex)
#            raise
#        return data

    @staticmethod
    def item_based(pdata, item, pdf_pg, nodes=None, iloc_range=None, title=None, fig_base=None):
        lgr.info(string_write("Creating figure for item {}", item))
        try:
            df = None
            if nodes is None or len(nodes) == 0:
                addr_grp = pdata.groupby([T_ZBEE_NWK_ADDR], as_index=False)
                nodes = addr_grp.groups.keys()

            xindex = pdata[T_TIME]#.diff()

            for addr in nodes:
                ser = pdata[item][pdata[T_ZBEE_NWK_ADDR] == addr].diff()
                if df is None:
                    df = pd.DataFrame({addr: ser})
                else:
                    df = df.join(pd.DataFrame({addr: ser}), how='outer')
            if df is not None and not df.empty:
                df = df.fillna(value=0)
                if iloc_range is not None:
                    df = df.iloc[iloc_range[0]:iloc_range[1]]
                if title is None or len(title) == 0:
                    title = string_write("{} by {}", item, T_ZBEE_NWK_ADDR)
                df.plot(grid=False, xticks=[], figsize=(28, 7), lw=2.0)
                plt.ylabel(item)
                plt.title(title)
                if fig_base is not None:
                    plt.savefig(string_write("{}/{}.png", fig_base, title))
                if pdf_pg is not None:
                    pdf_pg.savefig()
            else:
                lgr.warning("WARN: DataFrame is empty")
        except Exception as ex:
            lgr.error(string_write("Exception on creating item based figure: {}", ex))
            raise

    @staticmethod
    def prep_info(genid, inuithy_cfgpath=INUITHY_CONFIG_PATH):
        """
        time,"zbee_nwk_addr",
        macTxBcast,macTxUcastRetry,macTxUcastFail,macTxUcast,macRxBcast,macRxUcast,
        neighborAdded,neighborRemoved,neighborStale,averageMACRetryPerAPSMessageSent,
        routeDiscInitiated,relayedUcast,packetBufferAllocateFailure,
        apsTxBcast,apsTxUcastSuccess,apsTxUcastFail,apsTxUcastRetry,apsRxBcast,apsRxUcast
        """
        lgr.info(string_write("Prepare generation info with {}", genid))
        ginfo = GenInfo()

        ginfo.cfg = create_inuithy_cfg(inuithy_cfgpath)
        if ginfo.cfg is None:
            lgr.error(string_write("Failed to load inuithy configure"))
            return None

        ginfo.genid = genid
        ginfo.fig_base = string_write('{}/{}',\
            ginfo.cfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.csv_path = string_write('{}/{}.csv',\
            ginfo.cfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.pdf_path = string_write('{}/{}.pdf',\
            ginfo.cfg.config[T_REPORTDIR][T_PATH], ginfo.genid)

        ginfo.header = [T_TIME, T_ZBEE_NWK_ADDR,\
            T_MACTXBCAST, T_MACTXUCASTRETRY, T_MACTXUCASTFAIL, T_MACTXUCAST, T_MACRXBCAST,\
            T_MACRXUCAST, T_NEIGHBORADDED, T_NEIGHBORRMED, T_NEIGHBORSTALE, T_AVGMACRETRY,\
            T_RTDISCINIT, T_RELAYEDUCAST, T_PKGBUFALLOCFAIL, T_APSTXBCAST, T_APSTXUCASTSUCCESS,\
            T_APSTXUCASTFAIL, T_APSTXUCASTRETRY, T_APSRXBCAST, T_APSRXUCAST]
        if not path.isdir(ginfo.fig_base):
            mkdir(ginfo.fig_base)
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
        lgr.info(string_write("Generate csv with ginfo[{}]", ginfo))
        storage = Storage(ginfo.cfg, lgr)

        for r in storage.trafrec.find({
                T_GENID: ginfo.genid,
            }):
            recs = r.get(T_RECORDS)
            #csv_data = ZbeeReport.create_csv(recs, ginfo)
            pdata = pd.DataFrame.from_records(recs)
            pdata = pdata[pd.notnull(pdata[ginfo.header[2]])]
#            print(pdata)
#            pdata = pdata.fillna(value=0)
            [pdata.__setitem__(item, pdata[item].astype(int)) for item in ginfo.header[2:]]
            pdata.to_csv(ginfo.csv_path, columns=ginfo.header, index=False)
            return pdata
            
#            with open(ginfo.csv_path, 'w') as fd:
#                fd.write(','.join(h for h in ginfo.header) + '\n')
#                [fd.write(line + '\n') for line in csv_data]

    @staticmethod
    def gen_report(pdata, ginfo, gw=None, interest_nodes=None, irange=None):
        """Report generation helper"""
        lgr.info(string_write("Generate report with gw=[{}], nodes=[{}] irange={}", gw, interest_nodes, irange))
#        pdata = pd.read_csv(ginfo.csv_path, index_col=False, names=ginfo.header, header=None)
        pdata.info(verbose=True)
#        pdata[T_TIME] = pdata[T_TIME].astype()
        pdata.index = pdata[T_TIME]#.diff()
        with PdfPages(ginfo.pdf_path) as pdf_pg:
            if gw is not None and len(gw) > 0:
                for gwnode in gw: # Each subnet
                    for item in ginfo.header[2:]:
                        ZbeeReport.item_based(pdata, item, pdf_pg, gwnode,\
                        title = string_write("{} by gateway", item), fig_base=ginfo.fig_base)
            for item in ginfo.header[2:]:
                ZbeeReport.item_based(pdata, item, pdf_pg, interest_nodes, irange, fig_base=ginfo.fig_base)

    @staticmethod
    def generate(genid, gw=None, nodes=None, irange=None, cfgpath=INUITHY_CONFIG_PATH):
        """Generate CSV data and traffic analysis figures"""
        try:
            ginfo = ZbeeReport.prep_info(genid, cfgpath)
            """
            nodes = ['0x0000', '0x0001', '0x0102', '0x0103',\
                     '0x0205', '0x0206', '0x0303', '0x0304',\
                     '0x0400', '0x0401']
            gw = '0x0207'
            irange = None #(70, 150)
            """
            """
            nodes = None
            gw = '0x0303'
            irange = None
            """
#TODO: uncomment
            pdata = ZbeeReport.gen_csv(ginfo)
#           ginfo.csv_path = 'docs/UID1478067701.csv'
#           ginfo.csv_path = 'docs/UID1470021754.csv'
            ZbeeReport.gen_report(pdata, ginfo, gw, nodes, irange)
        except Exception as ex:
            lgr.error(string_write("Exception on generate reports: {}", ex))

if __name__ == '__main__':

#    ZbeeReport.gen_report(genid='581fdfe3362ac719d1c96eb3')
#    ZbeeReport.gen_report(genid='1478508817')
#    ZbeeReport.gen_report(genid='1478585096')
    if len(sys.argv) > 1:
        ZbeeReport.generate(sys.argv[1], gw=None, nodes=None, irange=None)
    else:
        console_write("Genid not given")

