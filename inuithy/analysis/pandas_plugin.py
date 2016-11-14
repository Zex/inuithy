""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
MessageType, T_HOST, StorageType, T_NODE, T_MSG, T_TRAFFIC_TYPE,\
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
import json

mplib.style.use('ggplot')
lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class PandasPlugin(object):
    """Analysis helper"""
    @staticmethod
    def insert_data(n, t, index, data):
        """
        for k, v in rec.items():
            line.append(v)
        ('panid', 'channel', 'msg', 'msgtype', 'gateway', 'genid', 'time', 'traffic_type', 'node', 'clientid', 'host')
        header = (T_NODE, T_SENDER, T_RECIPIENT, T_TRAFFIC_TYPE, T_CLIENTID, T_HOST, T_GENID, T_TIME)
                00 01 02 03 04
        node0: [2, 5, 1, 5, 6]
        node1: [2, 5, 1, 5, 6]
        node2: [2, 5, 1, 5, 6]
        """
        index.add(t)
        if data.get(n) is None:
            data[n] = {t:1}
        elif data.get(n).get(t) is None:
            data.get(n)[t] = 1
        else:
            data.get(n)[t] += 1

    @staticmethod
    def build_report_data(index, data):
#        print(int(index[-1])-int(index[0]))
        repo = {}
        for k, v in data.items():
            repo[k] = []
            for i in index:
                repo.get(k).append(v.get(i))
#                fd.write(str((k, i, v.get(i)))+'\n')
        return repo

    @staticmethod
    def gen_sender_pack(recs, genid, pdf_pg):

        data = {}
        index = set()
        for rec in recs:
            if rec.get(T_MSG_TYPE) != MessageType.SENT.name or rec.get(T_SENDER) is None or rec.get(T_RECIPIENT) is None:
                continue
            n, t = rec.get(T_NODE), rec.get(T_TIME)
            if n is None or t is None:
                continue
            PandasPlugin.insert_data(n, t, index, data)
        cache = list(index)
        cache.sort()
        index = cache
        repo = PandasPlugin.build_report_data(index, data)

        if len(repo) > 0:
            df = pd.DataFrame(repo, index=range(len(index)), columns=repo.keys())
            df.plot.line(grid=False, colormap='rainbow')
            plt.title("Number of packs sent via address")
            pdf_pg.savefig()

    @staticmethod
    def gen_recipient_pack(recs, genid, pdf_pg):
        """
        """
        data = {}
        index = set()
        for rec in recs:
            if rec.get(T_MSG_TYPE) != MessageType.RECV.name or rec.get(T_SENDER) is None or rec.get(T_RECIPIENT) is None:
                continue
            n, t = rec.get(T_NODE), rec.get(T_TIME)
            if n is None or t is None:
                continue
            PandasPlugin.insert_data(n, t, index, data)

        cache = list(index)
        cache.sort()
        index = cache
        repo = PandasPlugin.build_report_data(index, data)

        if len(repo) > 0:
            df = pd.DataFrame(repo, index=range(len(index)), columns=repo.keys())
            df.plot.line(grid=False, colormap='rainbow')
            plt.title("Number of packs received via address")
            pdf_pg.savefig()

    @staticmethod
    def gen_total_gwpack(recs, genid, pdf_pg):

        index = []
        count = {}
        for v in recs:
            n, t = v.get(T_GATEWAY), v.get(T_TIME)
#            print(t, n, v.get(T_RECIPIENT), v.get(T_SENDER), v.get(T_NODE))
            if n is None or t is None:
                continue
#            if n != v.get(T_RECIPIENT) and n != v.get(T_SENDER):
            if n != v.get(T_NODE):
                continue
            PandasPlugin.insert_data(n, t, index, data)
        cache = list(index)
        cache.sort()
        index = cache
        repo = PandasPlugin.build_report_data(index, data)

        df = pd.DataFrame(data, index=range(len(index)), columns=data.keys())
        df.plot.line(grid=False, colormap='rainbow')
        plt.title("Total of packs via gateway")
        pdf_pg.savefig()

    @staticmethod
    def gen_total_pack(recs, genid, pdf_pg):
        
        repo = {
            MessageType.SENT.name: 0,
            MessageType.RECV.name: 0,
            }
        for v in recs:
            repo[v[T_MSG_TYPE]] += 1

        df = pd.DataFrame(list(repo.values()), index=list(repo.keys()))
        df.plot(kind='bar', colormap='plasma')
        plt.title("Total of requested and received packets")
        pdf_pg.savefig()

    @staticmethod
    def create_csv(recs, header, genid):
        """Create CSV format from records
        """
        data = []
        index = set()
        for rec in recs:
            if rec.get(T_SENDER) is None or rec.get(T_RECIPIENT) is None:
                continue
            line = [rec.get(k) for k in header]
            line_fmt = ('{},' * len(line)).strip(',')
            data.append(line_fmt.format(*tuple(line)))
        return data

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
#            with open('records-{}'.format(genid), 'w') as fd:
#                for r in recs:
#                    fd.write(str(r)+'\n')

            header = (T_NODE, T_SENDER, T_RECIPIENT, T_TIME, T_MSG_TYPE, T_TRAFFIC_TYPE, T_CLIENTID, T_HOST, T_GENID)
            csv_data = PandasPlugin.create_csv(recs, header, genid)
            with open(string_write('{}/{}.csv', cfg.config[T_REPORTDIR][T_PATH], genid), 'w') as fd:
                fd.write(','.join(h for h in header) + '\n')
                [fd.write(line + '\n') for line in csv_data]

            jdata = json.dumps(recs)
            pdata = pd.read_json(jdata)
            print(pdata)
            n = pdata.groupby(T_MSG_TYPE)
            print(dir(n))
            print(n.sent.sum())
            continue
            with PdfPages(string_write('{}/{}.pdf', cfg.config[T_REPORTDIR][T_PATH], genid)) as pdf_pg:
                PandasPlugin.gen_total_pack(recs, genid, pdf_pg) 
                PandasPlugin.gen_sender_pack(recs, genid, pdf_pg) 
                PandasPlugin.gen_recipient_pack(recs, genid, pdf_pg) 
                PandasPlugin.gen_total_gwpack(recs, genid, pdf_pg)


if __name__ == '__main__':

#    PandasPlugin.gen_report(genid='581fdfe3362ac719d1c96eb3')
#    PandasPlugin.gen_report(genid='1478508817')
#    PandasPlugin.gen_report(genid='1478585096')
    import sys
    if len(sys.argv) > 1:
        PandasPlugin.gen_report(genid=sys.argv[1])
    else:
        print("Genid not given")
        sys.exit(1)

