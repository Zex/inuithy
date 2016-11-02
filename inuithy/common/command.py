""" General command definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import console_write
TSH_ERR_GENERAL = "ERROR: {}"
TSH_ERR_INVALID_CMD = "Invalid command [{}], type `{}` for the usages."
TSH_ERR_INVALID_PARAM = "Invalid parameters [{}], type `{}` for the usages."
TSH_ERR_HANDLING_CMD = "Exception on handling command [{}]: {}"

class Command(object):
    """
    - name: name of the command
    - desc: command description
    - handler: handler to the command
    """
    def __init__(self, name, usage='', desc='', handler=None):
        self.name = name
        self.desc = desc
        self.usage = usage
        self.handler = handler

    def run(self, *args, **kwargs):
        if self.handler != None:
            try:
                self.handler(args, kwargs)
            except Exception as ex:
                console_write(TSH_ERR_HANDLING_CMD, self.name, ex)
    def __str__(self):
        return "{} {} {}".format(self.name, self.usage, self.desc)

