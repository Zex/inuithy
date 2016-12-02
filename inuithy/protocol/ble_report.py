""" Report generator for BLE mesh protocol
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG, INUITHY_CONFIG_PATH,\
T_NODE, T_RECORDS, T_MSG_TYPE, T_TIME, T_GENID, T_REPORTDIR, T_PATH,\
T_GATEWAY, to_console, to_string, MessageType, T_HOST, StorageType,\
GenInfo, T_TYPE, TrafficStorage, T_SRC, T_DEST
from inuithy.storage.storage import Storage
from inuithy.util.config_manager import create_inuithy_cfg, create_traffic_cfg
from inuithy.protocol.ble_proto import BleProtocol as BleProto
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
import argparse as ap

mplib.style.use('ggplot')
lconf.fileConfig(INUITHY_LOGCONFIG)
lgr = logging

class BleReport(object):
    """Ble report helper"""
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
    def item_based(ginfo, pdata, item, pdf_pg, nodes=None, iloc_range=None, title=None):
# TODO
        lgr.info(to_string("Creating figure for item {}", item))
        try:
            df = None
            addr_grp = pdata.groupby([T_NODE], as_index=False)

            if nodes is None or len(nodes) == 0:
                nodes = addr_grp.groups.keys()

            for addr in nodes:
                try:
                    grp = addr_grp.get_group(addr)
                    index = np.arange(len(grp[item].values))
                    data = pd.DataFrame({addr: grp[item].values}, index=index)
                    if df is None:
                        df = data
                    else:
                        df = df.join(data, how='outer')
                except KeyError as ex:
                    lgr.error(to_string("No record for node [{}]: {}", addr, ex))

            if df is not None and not df.empty:
                df = df.fillna(value=0)
#                df = df.diff()
                if iloc_range is not None:
                    df = df.iloc[iloc_range[0]:iloc_range[1]]
                if title is None or len(title) == 0:
                    title = to_string("{} by {}", item, T_NODE)
                df.plot(xticks=[], lw=1.5, colormap='jet_r', figsize=ginfo.figsize)
            else:
                lgr.warning("WARN: DataFrame is empty")
#            plt.ylim(0, df.max()[1])
#            plt.ylim(df.min()[1], df.max()[1])
            plt.autoscale(enable=False, axis='y', tight=False)
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
            lgr.error(to_string("Exception on creating item based figure {}: {}", item, ex))
            raise

    @staticmethod
    def total_pack(ginfo, pdata, pdf_pg, title=None):
        """Create package sent/recv summary"""
        lgr.info("Create package summary")

        try:
            total_send = len(pdata[T_MSG_TYPE][pdata.msgtype == MessageType.SEND.name])
            total_recv = len(pdata[T_MSG_TYPE][pdata.msgtype == MessageType.RECV.name])
    
            data = {
                MessageType.SEND.name: total_send,
                MessageType.RECV.name: total_recv,
            }
            df = pd.DataFrame(list(data.values()), index=data.keys(), columns=[T_MSG_TYPE])

            if df is not None and not df.empty:
                df = df.fillna(value=0)
                if title is None or len(title) == 0:
                    title = to_string("Package summary")
#                df.plot(kind='bar', colormap='Accent', grid=False, figsize=ginfo.figsize)
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
    def prep_info(genid, inuithy_cfgpath=INUITHY_CONFIG_PATH):
        """
        """
        lgr.info(to_string("Prepare generation info with {}", genid))
        ginfo = GenInfo()

        ginfo.cfg = create_inuithy_cfg(inuithy_cfgpath)
        if ginfo.cfg is None:
            lgr.error(to_string("Failed to load inuithy configure"))
            return None

        ginfo.genid = genid
        ginfo.fig_base = to_string('{}/{}',\
            ginfo.cfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.csv_path = to_string('{}/{}.csv',\
            ginfo.cfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.pdf_path = to_string('{}/{}.pdf',\
            ginfo.cfg.config[T_REPORTDIR][T_PATH], ginfo.genid)
        ginfo.src_type = ginfo.cfg.storagetype[0]
        ginfo.figsize = (15, 6)

        ginfo.header = [T_TIME, T_NODE, T_SRC, T_DEST, T_MSG_TYPE]
        if not path.isdir(ginfo.fig_base):
            mkdir(ginfo.fig_base)
        return ginfo

    @staticmethod
    def gen_csv(ginfo):
        """
        """
        lgr.info(to_string("Generate csv with ginfo[{}]", ginfo))
        storage = Storage(ginfo.cfg, lgr)

        if ginfo.src_type == TrafficStorage.DB.name:
            return BleReport.import_from_db(ginfo, storage)
        elif ginfo.src_type == TrafficStorage.FILE.name:
            return BleReport.import_from_file(ginfo, storage)
        else:
            lgr.error(to_string("Unsupported storage type: {}", ginfo.src_type))

    @staticmethod
    def import_from_db(ginfo, storage):
        """Import traffic data from database"""
        raw, pdata = None, None
        for r in storage.trafrec.find({
                T_GENID: ginfo.genid,
            }):
            recs = r.get(T_RECORDS)
            #csv_data = BleReport.create_csv(recs, ginfo)
            raw = pd.DataFrame.from_records(recs)
            pdata = pd.DataFrame(raw[pd.notnull(raw[ginfo.header[2]])])
#            pdata = pdata.fillna(value=0)
#            [pdata.__setitem__(item, pdata[item].astype(int)) for item in ginfo.header[2:]]
            pdata.to_csv(ginfo.csv_path, columns=ginfo.header, index=False)
            return raw, pdata
            
#            with open(ginfo.csv_path, 'w') as fd:
#                fd.write(','.join(h for h in ginfo.header) + '\n')
#                [fd.write(line + '\n') for line in csv_data]
    @staticmethod
    def import_from_file(ginfo, storage):
        """Import traffic data from file"""
        raw, pdata = None, None
        raw = pd.DataFrame.from_csv(ginfo.csv_path, index_col=None)
        pdata = pd.DataFrame(raw[pd.notnull(raw[ginfo.header[2]])])
        [pdata.__setitem__(item, pdata[item].astype(int)) for item in ginfo.header[2:]]
#       pdata.to_csv(ginfo.csv_path, columns=ginfo.header, index=False)
        return raw, pdata

    @staticmethod
    def gen_report(raw, pdata, ginfo, gw=None, interest_nodes=None, irange=None):
        """Report generation helper"""
        lgr.info(to_string("Generate report with gw={}, nodes={} irange={}", gw, interest_nodes, irange))
        if raw is None or len(raw[T_TIME]) == 0:
            lgr.warning(to_string("No time-based records found"))
            return
#        pdata = pd.read_csv(ginfo.csv_path, index_col=False, names=ginfo.header, header=None)
        pdata.info(verbose=True)
        with PdfPages(ginfo.pdf_path) as pdf_pg:
            try:
                BleReport.total_pack(ginfo, raw, pdf_pg)
                if gw is not None and len(gw) > 0:
                    for gwnode in gw: # Each subnet
                        for item in ginfo.header[2:]:
                            BleReport.item_based(ginfo, pdata, item, pdf_pg, [gwnode],\
                            title = to_string("{} by gateway", item))
#                for item in ginfo.header[2:]:
#                    BleReport.item_based(ginfo, pdata, item, pdf_pg, interest_nodes, irange)
            except Exception as ex:
                lgr.error(to_string("Exception on saving report: {}", ex))
                raise

    @staticmethod
    def generate(genid, gw=None, nodes=None, irange=None, cfgpath=INUITHY_CONFIG_PATH, csv_path=None):
        """Generate CSV data and traffic analysis figures"""
        try:
            ginfo = BleReport.prep_info(genid, cfgpath)
            if csv_path is not None:
                ginfo.csv_path = csv_path
            raw, pdata = BleReport.gen_csv(ginfo)
            BleReport.gen_report(raw, pdata, ginfo, gw, nodes, irange)
        except Exception as ex:
            lgr.error(to_string("Exception on generate reports: {}", ex))
            raise

    @staticmethod
    def handle_args():
        """Arguments handler"""    
        args = None
        try:
            parser = ap.ArgumentParser(description='Report generation tool')
#           parser.add_mutually_exclusive_group()
            parser.add_argument('-gid', '--genid', required=True, help='Traffic generation identifier')
            parser.add_argument('-n', '--nodes', help='Nodes of interest', nargs="+")
            parser.add_argument('-gw', '--gateways', help='Gateway node', nargs="+")
            parser.add_argument('-csv', '--csv_path', help='Path to CSV data source')
            args = parser.parse_args()
    
            to_console("GENID {}", args.genid)
            to_console("Nodes of interest {}", args.nodes)
#            [to_console(node) for node in args.nodes is not None and args.nodes or []]
            to_console("Subnet gateway {}", args.gateways)
#            [to_console(node) for node in args.gateways is not None and args.gateways or []]
            to_console("CSV Path {}", args.csv_path)
        except Exception as ex:
            to_console("Exception on handlin report arguments: {}", ex)
            return None
        return args

if __name__ == '__main__':

    args = BleReport.handle_args()
    if args is not None:
        BleReport.generate(args.genid, gw=args.gateways, nodes=args.nodes, irange=None, csv_path=args.csv_path)

