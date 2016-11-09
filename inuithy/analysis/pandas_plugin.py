""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
MessageType, T_HOST, StorageType, T_NODE, T_MSG,\
T_RECORDS, T_MSG_TYPE, string_write, T_TIME, T_GENID, T_CLIENTID,\
T_SENDER, T_RECIPIENT, T_PKGSIZE, T_REPORTDIR, T_PATH, T_GATEWAY
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
    def gen_sender_pack(recs, genid, pdf_pg):
   
        index = []
        count = {}
        for v in recs:
            t = v.get(T_TIME)
            n = v.get(T_SENDER)
            if n is None or t is None:
                continue
            if count.get(n) is None:
                count[n] = {t:1}
            elif count.get(n).get(t) is None:
                count[n][t] = 1
            else:
                count[n][t] += 1
            index = count.get(n).keys()
        index = list(index)
        index.sort()
        data = {}
        for i in index:
            for n, c in count.items():
                if data.get(n) is not None:
                    data[n].append(c.get(i))
                else:
                    data[n] = [c.get(i)]

        df = pd.DataFrame(data, index=range(len(index)), columns=data.keys())
        df.plot.line(grid=False, colormap='rainbow')
        plt.title("Number of packs sent via address")
        pdf_pg.savefig()

    @staticmethod
    def gen_recipient_pack(recs, genid, pdf_pg):
   
        index = []
        count = {}
        for v in recs:
            t = v.get(T_TIME)
            n = v.get(T_RECIPIENT)
            if n is None or t is None:
                continue
            if count.get(n) is None:
                count[n] = {t:1}
            elif count.get(n).get(t) is None:
                count[n][t] = 1
            else:
                count[n][t] += 1
            index = count.get(n).keys()
        index = list(index)
        index.sort()
        data = {}
        for i in index:
            for n, c in count.items():
                if data.get(n) is not None:
                    data[n].append(c.get(i))
                else:
                    data[n] = [c.get(i)]

        df = pd.DataFrame(data, index=range(len(index)), columns=data.keys())
        df.plot.line(grid=False, colormap='rainbow')
        plt.title("Number of packs received via address")
        pdf_pg.savefig()

    @staticmethod
    def gen_total_gwpack(recs, genid, pdf_pg):

        index = []
        count = {}
        for v in recs:
            t = v.get(T_TIME)
            n = v.get(T_GATEWAY)
#            print(t, n, v.get(T_RECIPIENT), v.get(T_SENDER), v.get(T_NODE))
            if n is None or t is None:
                continue
#            if n != v.get(T_RECIPIENT) and n != v.get(T_SENDER):
            if n != v.get(T_NODE):
                continue
            if count.get(n) is None:
                count[n] = {t:1}
            elif count.get(n).get(t) is None:
                count[n][t] = 1
            else:
                count[n][t] += 1
            index = count.get(n).keys()
        index = list(index)
        index.sort()
        data = {}
        for i in index:
            for n, c in count.items():
                if data.get(n) is not None:
                    data[n].append(c.get(i))
                else:
                    data[n] = [c.get(i)]

        df = pd.DataFrame(data, index=range(len(index)), columns=data.keys())
        df.plot.line(grid=False, colormap='rainbow')
        plt.title("Total of packs via gateway")
        pdf_pg.savefig()

    @staticmethod
    def gen_total_pack(recs, genid, pdf_pg):
        
        count = {
            MessageType.SENT.name: 0,
            MessageType.RECV.name: 0,
            }
        for v in recs:
            count[v[T_MSG_TYPE]] += 1

        df = pd.DataFrame(count, index=count.keys())
        df.plot.hist(bins=len(count)*2, colormap='Blues')
        plt.title("Total of requested and received packets")
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
            #DEBUG
            with open('records-{}'.format(genid), 'w') as fd:
                for r in recs:
                    fd.write(str(r))
            with PdfPages(string_write('{}/{}.pdf', cfg.config[T_REPORTDIR][T_PATH], genid)) as pdf_pg:
                PandasAnalyzer.gen_total_pack(recs, genid, pdf_pg) 
                PandasAnalyzer.gen_sender_pack(recs, genid, pdf_pg) 
                PandasAnalyzer.gen_recipient_pack(recs, genid, pdf_pg) 
                PandasAnalyzer.gen_total_gwpack(recs, genid, pdf_pg)

if __name__ == '__main__':

#    PandasAnalyzer.gen_report(genid='581fdfe3362ac719d1c96eb3')
#    PandasAnalyzer.gen_report(genid='1478508817')
    PandasAnalyzer.gen_report(genid='1478585096')

#import matplotlib.pyplot as plt
#import pandas as pd
