""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
MessageType, T_HOST, StorageType, T_NODE, T_MSG,\
T_RECORDS, T_MSG_TYPE, string_write, T_TIME, T_GENID, T_CLIENTID,\
T_SENDER, T_RECIPIENT, T_PKGSIZE, T_REPORTDIR, T_PATH
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

mplib.style.use('ggplot')
lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class PandasAnalyzer(object):
    """Analysis helper"""
    @staticmethod
    def gen_linechart_by_gid(recs, genid, pdf_pg):
   
        count = {}

        for v in recs:
            if count.get(v[T_NODE]) is None:
                count[v[T_NODE]] = 1
            else:
                count[v[T_NODE]] += 1

#        recv_times = [v[T_TIME].split(' ')[1] for v in r[T_RECORDS] if v[T_MSG_TYPE] == MessageType.SENT.name]

#       df = pd.DataFrame(np.random.randn(10, 5), columns=['a', 'b', 'c', 'd', 'e'])
        df = pd.DataFrame(count, index=range(len(recs)), columns=count.keys())
        df.plot()
        pdf_pg.savefig()

    @staticmethod
    def gen_barchart_by_gid(recs, genid, pdf_pg):
        counter = {
            MessageType.SENT.name: 0,
            MessageType.RECV.name: 0,
            }
        for v in recs:
            counter[v[T_MSG_TYPE]] += 1

        df = pd.DataFrame(counter, index=counter.keys(), columns=counter.keys())
        df.plot.bar(colormap='Blues')
        pdf_pg.savefig()

    @staticmethod
    def gen_report(inuithy_cfgpath=INUITHY_CONFIG_PATH, genid=None):
    
        cfg = create_inuithy_cfg(inuithy_cfgpath)
        if cfg is None:
            lgr.error(string_write("Failed to load inuithy configure"))
            return False

        storage = Storage(cfg, lgr)
        for r in storage.trafrec.find({
#                "_id": ObjectId(genid),
                "genid": genid,
            }):
            recs = r.get(T_RECORDS)
            with PdfPages(string_write('{}/{}.pdf', cfg.config[T_REPORTDIR][T_PATH], genid)) as pdf_pg:
                PandasAnalyzer.gen_linechart_by_gid(recs, genid, pdf_pg) 
                PandasAnalyzer.gen_barchart_by_gid(recs, genid, pdf_pg) 


if __name__ == '__main__':

#    PandasAnalyzer.gen_report(genid='581fdfe3362ac719d1c96eb3')
    PandasAnalyzer.gen_report(genid='1478508817')

