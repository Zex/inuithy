""" Data analysis with Pandas
 @uthor: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
MessageType, T_HOST, StorageType, T_NODE, T_MSG, T_TRAFFIC_TYPE,\
T_RECORDS, T_MSG_TYPE, string_write, T_TIME, T_GENID, T_CLIENTID,\
T_SENDER, T_RECIPIENT, T_PKGSIZE, T_REPORTDIR, T_PATH, T_GATEWAY,\
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
            data[n][t] = 1
        else:
            data[n][t] += 1

    @staticmethod
    def build_report_data(index, data):
#        print(int(index[-1])-int(index[0]))
        repo = {}
        for k, v in data.items():
            repo[k] = []
            for i in index:
                repo[k].append(v.get(i))
#                fd.write(str((k, i, v.get(i)))+'\n')
        return repo

    @staticmethod
    def gen_sender_pack(recs, genid, pdf_pg):

        data = {}
        index = set()

        try:
            for rec in recs:
    #            if rec.get(T_MSG_TYPE) != MessageType.SENT.name or rec.get(T_SENDER) is None or rec.get(T_RECIPIENT) is None:
                if rec.get(T_MSG_TYPE) != MessageType.SENT.name:
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
                df.plot.line(grid=False, colormap='rainbow', figsize=(20, 20))
                plt.title("Number of packs sent via address")
                pdf_pg.savefig()
        except Exception as ex:
            console_write("ERROR: {}", ex)

    @staticmethod
    def gen_recipient_pack(recs, genid, pdf_pg):
        """
        """
        data = {}
        index = set()
        try:
            for rec in recs:
#            if rec.get(T_MSG_TYPE) != MessageType.RECV.name or rec.get(T_SENDER) is None or rec.get(T_RECIPIENT) is None:
#                continue
                if rec.get(T_MSG_TYPE) != MessageType.RECV.name:
                    continue
                n, t = rec.get(T_NODE), rec.get(T_TIME)
                if n is None or t is None:
                    continue
                PandasPlugin.insert_data(n, t, index, data)
            cache = list(index)
            cache.sort()
            index = cache
            repo = PandasPlugin.build_report_data(index, data)
#        print(repo)
            if len(repo) > 0:
                df = pd.DataFrame(repo, index=range(len(index)), columns=repo.keys())
                df.plot.line(grid=False, colormap='rainbow', figsize=(30, 30))
                plt.title("Number of packs received via address")
                pdf_pg.savefig()
        except Exception as ex:
            console_write("ERROR: {}", ex)

    @staticmethod
    def gen_total_gwpack(recs, genid, pdf_pg):
        """Generate total packages send/recv via gateway
        """
        index = set()
        data = {}

        try:
            for v in recs:
                n, t, g = v.get(T_NODE), v.get(T_TIME), v.get(T_GATEWAY)
                if n is None or t is None or n != g:
                    continue
                PandasPlugin.insert_data(n, t, index, data)
            cache = list(index)
            cache.sort()
            index = cache
            repo = PandasPlugin.build_report_data(index, data)
    
            if len(repo) > 0:
                df = pd.DataFrame(data, index=range(len(index)), columns=data.keys())
                df.plot.line(grid=False, colormap='rainbow', figsize=(20, 20))
                plt.title("Total of packs via gateway")
                pdf_pg.savefig()
        except Exception as ex:
            console_write("ERROR: {}", ex)

    @staticmethod
    def gen_total_pack(recs, genid, pdf_pg):
       
        try:
            repo = {
                MessageType.SENT.name: 0,
                MessageType.RECV.name: 0,
                }
            for v in recs:
                repo[v.get(T_MSG_TYPE)] += 1
    
            df = pd.DataFrame(list(repo.values()), index=list(repo.keys()))
            df.plot(kind='bar', colormap='plasma', grid=False)
            plt.title("Total of requested and received packets")
            pdf_pg.savefig()
        except Exception as ex:
            console_write("ERROR: {}", ex)

    @staticmethod
    def create_csv(recs, header, genid):
        """Create CSV format from records
        """
        data = []
        index = set()

        try:
            for rec in recs:
                if rec.get(T_SENDER) is None or rec.get(T_RECIPIENT) is None:
                    continue
                line = [rec.get(k) for k in header]
                line_fmt = ('{},' * len(line)).strip(',')
                data.append(string_write(line_fmt, *tuple(line)))
        except Exception as ex:
            console_write("ERROR: {}", ex)
        return data

    @staticmethod
    def groupby(pdata, item, pdf_pg):
        try:
            n = pdata.groupby(item)
            n.plot(kind='line', colormap='plasma', figsize=(20, 20))
            plt.title(string_write("Group by {}", item))
            pdf_pg.savefig()
        except Exception as ex:
            console_write("ERROR: {}", ex)

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

#            jdata = json.dumps(recs)
            pdata = pd.read_csv(string_write('{}/{}.csv', cfg.config[T_REPORTDIR][T_PATH], genid))
            print(pdata)
#            print("=========================================================")
#            continue
            with PdfPages(string_write('{}/{}.pdf', cfg.config[T_REPORTDIR][T_PATH], genid)) as pdf_pg:
                [PandasPlugin.groupby(pdata, item, pdf_pg) for item in header] 
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

