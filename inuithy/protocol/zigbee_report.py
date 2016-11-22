""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
MessageType, T_HOST, StorageType, T_NODE, T_MSG, T_TRAFFIC_TYPE,\
T_RECORDS, T_MSG_TYPE, string_write, T_TIME, T_GENID, T_CLIENTID,\
T_SRC, T_DEST, T_PKGSIZE, T_REPORTDIR, T_PATH, T_GATEWAY,\
T_TIME, T_ZBEE_NWK_ADDR, T_MACTXBCAST, T_MACTXUCASTRETRY,\
T_MACTXUCASTFAIL, T_MACTXUCAST, T_MACRXUCAST, T_NEIGHBORADDED, T_NEIGHBORRMED,\
T_NEIGHBORSTALE, T_AVGMACRETRY, T_RTDISCINIT, T_RELAYEDUCAST,\
T_PKGBUFALLOCFAIL, T_APSTXBCAST, T_APSTXUCASTSUCCESS, T_APSTXUCASTFAIL,\
T_APSTXUCASTRETRY, T_APSRXBCAST, T_APSRXUCAST, T_MACRXBCAST,\
console_write, string_write
from inuithy.storage.storage import Storage
from inuithy.util.config_manager import create_inuithy_cfg, create_traffic_cfg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib as mplib
import pandas as pd
import numpy as np
import logging
import logging.config as lconf
from bson.objectid import ObjectId
from datetime import datetime as dt
import json
import time

mplib.style.use('ggplot')
lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class PandasPlugin(object):
    """Zigbee report helper"""

    @staticmethod
    def create_csv(recs, header, genid):
        """Create CSV format from records
        """
        data = []
        index = set()

        try:
            for rec in recs:
                if len([rec.get(k) for k in header if rec.get(k) is not None]) != len(header):
                    continue
                line = [rec.get(k) for k in header if rec.get(k)]
                line_fmt = ('{},' * len(line)).strip(',')
                data.append(string_write(line_fmt, *tuple(line)))
        except Exception as ex:
            console_write("ERROR: {}", ex)
        return data

    @staticmethod
    def item_based(pdata, item, pdf_pg, nodes=None, iloc_range=None, title=None):
        try:
            df = None
            if nodes is None:
                addr_grp = pdata.groupby([T_ZBEE_NWK_ADDR], as_index=False)
                nodes = addr_grp.groups.keys()

            
            for addr in nodes:
                if df is None:
                    df = pd.DataFrame({addr: pd.Timedelta(pdata[item][pdata[T_ZBEE_NWK_ADDR]==addr])})
                else:
                    df = df.join(pd.DataFrame({addr:pdata[item][pdata[T_ZBEE_NWK_ADDR]==addr]}), how='outer')
                
            if df is not None and not df.empty:
                df = df.fillna(value=0)
                if iloc_range is not None:
                    df = df.iloc[iloc_range[0]:iloc_range[1]]
                if title is None or len(title) == 0:
                    title = string_write("{} by {}", item, T_ZBEE_NWK_ADDR)
                df.plot(grid=False, xticks=[], figsize=(28, 7))
                plt.ylabel(item)
                plt.title(title)
                pdf_pg.savefig()
            else:
                console_write("WARN: DataFrame is empty")
        except Exception as ex:
            console_write("ERROR: {}", ex)

    @staticmethod
    def prep_info(inuithy_cfgpath=INUITHY_CONFIG_PATH, genid=None):
        """
        time,"zbee_nwk_addr",macTxBcast,macTxUcastRetry,macTxUcastFail,macTxUcast,macRxBcast,macRxUcast,neighborAdded,neighborRemoved,neighborStale,averageMACRetryPerAPSMessageSent,routeDiscInitiated,relayedUcast,packetBufferAllocateFailure,apsTxBcast,apsTxUcastSuccess,apsTxUcastFail,apsTxUcastRetry,apsRxBcast,apsRxUcast
        """
        cfg = create_inuithy_cfg(inuithy_cfgpath)
        if cfg is None:
            lgr.error(string_write("Failed to load inuithy configure"))
            return False

        csv_path = string_write('{}/{}.csv', cfg.config[T_REPORTDIR][T_PATH], genid)
        pdf_path = string_write('{}/{}.pdf', cfg.config[T_REPORTDIR][T_PATH], genid)

        header = (T_TIME, T_ZBEE_NWK_ADDR,\
            T_MACTXBCAST, T_MACTXUCASTRETRY, T_MACTXUCASTFAIL, T_MACTXUCAST, T_MACRXBCAST,\
            T_MACRXUCAST, T_NEIGHBORADDED, T_NEIGHBORRMED, T_NEIGHBORSTALE, T_AVGMACRETRY,\
            T_RTDISCINIT, T_RELAYEDUCAST, T_PKGBUFALLOCFAIL, T_APSTXBCAST, T_APSTXUCASTSUCCESS,\
            T_APSTXUCASTFAIL, T_APSTXUCASTRETRY, T_APSRXBCAST, T_APSRXUCAST)
        return header, csv_path, pdf_path, cfg

    @staticmethod
    def gen_csv(header, csv_path, pdf_path, cfg, genid=None):
        """
        time,"zbee_nwk_addr",macTxBcast,macTxUcastRetry,macTxUcastFail,macTxUcast,macRxBcast,macRxUcast,neighborAdded,neighborRemoved,neighborStale,averageMACRetryPerAPSMessageSent,routeDiscInitiated,relayedUcast,packetBufferAllocateFailure,apsTxBcast,apsTxUcastSuccess,apsTxUcastFail,apsTxUcastRetry,apsRxBcast,apsRxUcast
        """
        storage = Storage(cfg, lgr)
        for r in storage.trafrec.find({
                "genid": genid,
            }):
            recs = r.get(T_RECORDS)

            csv_data = PandasPlugin.create_csv(recs, header, genid)

        with open(csv_path, 'w') as fd:
            fd.write(','.join(h for h in header) + '\n')
            [fd.write(line + '\n') for line in csv_data]

    @staticmethod
    def gen_report(header, csv_path, pdf_path, cfg):

#        pdata = pd.read_csv(csv_path, index_col=False, names=list(header), header=None)
#        pdata = pd.read_csv('docs/UID1478067701.csv', index_col=False, names=list(header), header=None)
        pdata = pd.read_csv('docs/UID1470021754.csv', index_col=False, names=list(header), header=None)
        console_write(pdata.info())
        pdata[T_TIME] = pdata[T_TIME].astype(str)
        pdata.index = [pdata[T_TIME]]

#        nodes=['0x0000', '0x0001', '0x0102', '0x0103', '0x0205', '0x0206', '0x0303', '0x0304', '0x0400', '0x0401']
#        gw = '0x0207'
#        irange = (70, 150)
        nodes = None
        gw = '0x0303' 
        irange = None

        help(pd.DataFrame)
        with PdfPages(pdf_path) as pdf_pg:
#            for item in header[2:]:
#                PandasPlugin.item_based(pdata, item, pdf_pg, [gw],
#                    title = string_write("{} by gateway", item))
            for item in header[2:]:
                PandasPlugin.item_based(pdata, item, pdf_pg, nodes, (40, 90))
                break

if __name__ == '__main__':

#    PandasPlugin.gen_report(genid='581fdfe3362ac719d1c96eb3')
#    PandasPlugin.gen_report(genid='1478508817')
#    PandasPlugin.gen_report(genid='1478585096')
    
    import sys
    ts = [1470023287.241, 1470023287.370, 1470023289.550]
    [print(pd.Timedelta(t).delta) for t in ts]
    sys.exit(1)
    if len(sys.argv) > 1:
        header, csv_path, pdf_path, cfg = PandasPlugin.prep_info(genid=sys.argv[1])
#       PandasPlugin.gen_csv(genid=sys.argv[1])
        PandasPlugin.gen_report(header, csv_path, pdf_path, cfg)
    else:
        console_write("Genid not given")

