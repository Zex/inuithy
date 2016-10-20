## Console for manual mode
# Author: Zex Li <top_zlynch@yahoo.com>
#
from inuithy.common.predef import *
import socket, argparse, threading
import signal, sys
import os, multiprocessing, logging

DEFAULT_PROMPT = "inuithy@{}>"
# Inuithy shell commands
TSH_CMD_AGENT       = "agent"
TSH_CMD_HELP        = "help"
TSH_CMD_QUIT        = "quit"
TSH_CMD_EXCLAM      = "!"

TSH_CMD_START       = "start"
TSH_CMD_STOP        = "stop"

console_reader = hasattr(__builtins__, 'raw_input') and raw_input or input

class Command:
    """
    - name: name of the command
    - desc: command description
    - handler: handler to the command
    """
    def __init__(self, name, desc, handler):
        self.name = name
        self.desc = desc
        self.handler = handler

    def run(self, *args, **kwargs):
        if self.handler != None:
            try:
                self.handler(args, kwargs)
            except Exception as ex:
                print("Exception on executing command [{}]".format(self.name))
    def __str__(self):
        return "{}  {}".format(self.name, self.desc)

class Console(threading.Thread):
    """
    """
    __mutex = threading.Lock() 

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, val):
        if Console.__mutex.acquire():
            self.__running = val
            Console.__mutex.release()

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, verbose=None):
        super(Console, self).__init__(group, target, name, args, kwargs, verbose)
        self.__title = INUITHY_TITLE.format(INUITHY_VERSION, "Shell")
        self.__running = True
        self.__host = socket.gethostbyname(socket.gethostname())
        self.__greeting_path = INUITHY_ROOT+'/greetings/aaa'
        with open(self.__greeting_path, 'r') as fd:
            self.__greeting = fd.read()
        self.usage = self.__title + "\n" \
         + "\thelp  Print inuithy shell usage\n"\
         + "\tquit  Leave me\n"\
         + "\tagent Operations on agents\n"\
         + "\t!<system command>  Excute shell command\n"
        self.__command_handlers = {
            TSH_CMD_AGENT:      self.on_cmd_agent,
            TSH_CMD_HELP:       self.on_cmd_help,
            TSH_CMD_QUIT:       self.on_cmd_quit,
            TSH_CMD_EXCLAM:     self.on_cmd_sys,
        }

    def on_cmd_agent(self, *args, **kwargs):
        pass

    def on_cmd_help(self, *args, **kwargs):
        print(self.usage)

    def on_cmd_quit(self, *args, **kwargs):
        self.running = False

    def on_cmd_sys(self, *args, **kwargs):
        print(">>>>>>>>>>>",args)
        os.system(args[0])

    def start(self): 
        print(self.__title)
        print(self.__greeting)
        while self.running:
            try:
                command = console_reader(DEFAULT_PROMPT.format(self.__host))
                self.dispatch(command)
            except Exception as ex:
                print("ERROR: {}".format(ex))
            except KeyboardInterrupt:
                self.on_cmd_quit()
                print("Bye~")

    def dispatch(self, command):
        if command == None or len(command) == 0:
            return
        command = command.strip()
        cmds = command.split(' ')
        if len(cmds) == 0:
            print("Invalid command [{}], type `help` for the usage.".format(command))

        try:
            if self.__command_handlers.has_key(cmds[0]):
                print(command[len(command)+1:])
                self.__command_handlers[cmds[0]](command[len(command)+1:])
            else:
                self.on_cmd_help()
        except Exception as ex:
            print("Exception on handling command [{}]: {}".format(command, ex))

if __name__ == '__main__':
    term = Console()
    term.start()

