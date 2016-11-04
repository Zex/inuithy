""" General command definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import console_write, string_write
from inuithy.util.helper import delimstr

TSH_ERR_GENERAL = "ERROR: {}"
TSH_ERR_INVALID_CMD = "Invalid command [{}], type `{}` for the usages."
TSH_ERR_INVALID_PARAM = "Invalid parameters [{}], type `{}` for the usages."
TSH_ERR_HANDLING_CMD = "Exception on handling command [{}]: {}"

class Command(object):
    """
    @name: name of the command
    @args: optional arguments
    @desc: command description
    @handler: handler to the command
    """
    def __init__(self, name, args='', desc='', handler=None):
        self.name = name
        self.args = args
        self.desc = desc
        self.handler = handler

    def run(self, *args, **kwargs):
        """Execute handler"""
        if self.handler is not None:
            try:
                self.handler(args, kwargs)
            except Exception as ex:
                console_write(TSH_ERR_HANDLING_CMD, self.name, ex)
                
    def __str__(self):

        ret = string_write('{:>5} ', self.name)
        desc_fmt = '{:>65}'

        if len(self.args) > 0:
            ret += string_write('{:<20}', self.args)
        if len(self.args) > 20:
            desc_fmt = '{:>100}'
            ret += '\n'
        else:
            desc_fmt = '{:>65}'

        descs = self.desc.split('\n')

        ret += string_write('{}', descs[0])
        if len(descs) > 1:
            for line in descs[1:]:
                ret += string_write(desc_fmt, line)
                ret += '\n'
        ret = ret.strip('\n')
        return ret

class Usage(object):
    """A group of commands"""
    def __init__(self, title='', cmds=None):
        self.title = title
        self.cmds = cmds

    def __str__(self):
        return delimstr('\n', self.title, *(str(cmd) for cmd in self.cmds if cmd is not None))

if __name__ == "__main__":
    
    cmd_0 = Command('agent list', '', 'Print available agents')
    cmd_1 = Command('agent ll', '', 'Print available agents with less details')
    cmd_2 = Command('agent start', '<host>', "Start agent on <host>\n"\
                    "           '*' for all targetted hosts")
    cmd_3 = Command('agent stop', '<host>', "Stop agent on <host>\n"\
                    "           '*' for all targetted hosts")
    for cmd in [cmd_0, cmd_1, cmd_2, cmd_3]:
        print(str(cmd))

