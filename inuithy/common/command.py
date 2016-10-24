## General command definition
# Author: Zex Li <top_zlynch@yahoo.com>
#

class Command:
    """
    - name: name of the command
    - desc: command description
    - handler: handler to the command
    """
    def __init__(self, name, long_name='', desc='', handler=None):
        self.name = name
        self.long_name = long_name
        self.desc = desc
        self.handler = handler

    def run(self, *args, **kwargs):
        if self.handler != None:
            try:
                self.handler(args, kwargs)
            except Exception as ex:
                console_write(TSH_ERR_HANDLING_CMD, self.name, ex)
    def __str__(self):
        return "{} {} {}".format(self.name, self.lone_name, self.desc)

