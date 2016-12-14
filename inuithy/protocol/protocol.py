""" High-level protocol definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import INUITHY_LOGCONFIG
import logging
import logging.config as lconf
lconf.fileConfig(INUITHY_LOGCONFIG)

class Protocol(object):
    """High-level protocol definition
    """
    EOL = "\r\n"
    lgr = logging

    def __init__(self):
        pass


