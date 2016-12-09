""" Runtime data block
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_CONFIG_PATH, NETWORK_CONFIG_PATH, TRAFFIC_CONFIG_PATH
from inuithy.util.config_manager import InuithyConfig, NetworkConfig, TrafficConfig
import argparse as ap

class Runtime:
    """Maintain runtime context"""
    parser = ap.ArgumentParser(description='Inuithy Runtime')
    # Configure paths 
    tcfg_path = INUITHY_CONFIG_PATH
    nwcfg_path = NETWORK_CONFIG_PATH
    trcfg_path = TRAFFIC_CONFIG_PATH
    # Configure contents
    tcfg = None
    nwcfg = None
    trcfg = None

    def handle_args(in_args=None):
        """Arguments handler"""    
    #   Runtime.parser.add_mutually_exclusive_group()
        args = Runtime.parser.parse_args(in_args)
    
        if 'tcfg' in dir(args) and args.tcfg is not None:
            Runtime.tcfg_path = args.tcfg
        if 'trcfg' in dir(args) and args.trcfg is not None:
            Runtime.trcfg_path = args.trcfg
        return args

def load_tcfg(cfgpath):
    """Create inuithy config object and load configure from given path
    """
    Runtime.tcfg = InuithyConfig(cfgpath)
    if Runtime.tcfg.load() is False:
        raise RuntimeError("Failed to load inuithy configure")

def load_trcfg(cfgpath):
    Runtime.trcfg = TrafficConfig(cfgpath)
    if Runtime.trcfg.load() is False:
        raise RuntimeError("Failed to load traffic configure")

def load_nwcfg(cfgpath):
    Runtime.nwcfg = NetworkConfig(cfgpath)
    if Runtime.nwcfg.load() is False:
        raise RuntimeError("Failed to load network configure")

def load_configs():
    """Load runtime configure from inuithy configure file,
    load traffic definitions from traffic file
    """
    load_tcfg(Runtime.tcfg_path)
    load_trcfg(Runtime.trcfg_path)
    load_nwcfg(Runtime.trcfg.nw_cfgpath)

Runtime.parser.add_argument('-tcfg', nargs=1, help='Inuithy configure path')
Runtime.parser.add_argument('-trcfg', nargs=1, help='Traffic configure path')

