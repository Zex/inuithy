""" General command definition
 @author: Zex Li <top_zlynch@yahoo.com>
"""
from inuithy.common.predef import _c, _s
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
                self.handler(*args, **kwargs)
            except Exception as ex:
                _c(TSH_ERR_HANDLING_CMD, self.name, ex)
                
    def __str__(self):

        ret = _s('{:<15} ', self.name)
        desc_fmt = ' {}'

        if len(self.args) >= 30:
            ret += _s('{:<30}\n', self.args)
            ret += _s(' ' * 46)
        elif len(self.args) > 0 and len(self.args) < 30:
            ret += _s('{:<30}', self.args)
        elif len(self.args) == 0:
            ret += _s(' ' * 30)

        descs = self.desc.split('\n')

        ret += _s(desc_fmt, descs[0])

        if len(descs) > 1:
            ret += _s('\n' + ' ' * 46)
            for line in descs[1:]:
                ret += _s(desc_fmt, line)
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
        _c(str(cmd))

