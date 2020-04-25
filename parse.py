from enum import Enum
from typing import Iterable
import re

from error import *
from helper import *

arg_types = {
    "help": False,
    "source": True,
    "input": True,
    "stats": True,
    "insts": False,
    "vars": False
}


class Stat(Enum):
    INSTS = 0,
    VARS = 1,


class Stats:
    def __init__(self, path: str, opts: Iterable[Stat]):
        self.path = path
        self.opts = opts
        self.insts = 0
        self.vars = 0

    def __repr__(self):
        return 'Stats = {{path: "{self.path}", opts: "{self.opts}", insts: {self.insts}, vars: {self.vars}}}'.format(self=self)


def parse_args():
    args = sys.argv[1:]
    inp = sys.stdin
    src = sys.stdin

    found_stats = False
    stat_opts = []
    stat_file = None

    found_input = False

    # splits argument into name and optional path
    arg_format = re.compile(r'^--?([a-zA-Z]+)(?:$|=([\S]+))$')

    for arg in args:
        try:
            name, path = arg_format.findall(arg)[0]
        except IndexError:
            # invalid argument format
            Error.ERR_ARGS.exit()
            # added so pycharm wont show warning
            return

        # check for unknown arg
        if name not in arg_types:
            Error.ERR_ARGS.exit()

        # check if path missing
        if arg_types[name] != (len(path) != 0):
            Error.ERR_ARGS.exit()

        try:
            if name == "help":
                if len(args) != 1:
                    Error.ERR_ARGS.exit()
                print_help()
                exit(0)
            elif name == "source":
                src = open(path)
                found_input = True
            elif name == "input":
                inp = open(path)
                found_input = True
            elif name == "insts":
                stat_opts.append(Stat.INSTS)
            elif name == "vars":
                stat_opts.append(Stat.VARS)
            elif name == "stats":
                found_stats = True
                stat_file = path
        except OSError:
            Error.ERR_INPUT.exit()

    # source or input was not found
    if not found_input:
        Error.ERR_ARGS.exit()

    # stats args without --stats
    if not found_stats and len(stat_opts) != 0:
        Error.ERR_ARGS.exit()

    if found_stats:
        stats = Stats(stat_file, stat_opts)
    else:
        stats = None

    sys.stdin = inp
    return src, stats


def check_xml(program):
    # check root node
    if program.get("language") != "IPPcode20" or program.tag != "program":
        Error.ERR_XML_STRUCT.exit()
    if program.get("name") is not None:
        eprint("Name:   " + program.get("name"))
    if program.get("description") is not None:
        eprint("Desc:   " + program.get("description"))

    orders = set()

    for instr in program:
        opcode = instr.get("opcode")
        order = instr.get("order")
        # check for invalid structure
        if instr.tag != "instruction" or order is None or opcode is None:
            Error.ERR_XML_STRUCT.exit()

        # opcode dict has opcodes in uppercase
        opcode = opcode.upper()

        # check duplicate orders
        if order in orders:
            Error.ERR_XML_STRUCT.exit()
        orders.add(order)

        try:
            # check if positive number
            if int(order) < 1:
                Error.ERR_XML_STRUCT.exit()
        except ValueError:
            # check if number
            Error.ERR_XML_STRUCT.exit()

        # check unknown opcode
        if opcode not in opcodes:
            Error.ERR_XML_STRUCT.exit()

        # check corrupted opcode
        if len(instr) != len(opcodes[opcode]):
            Error.ERR_XML_STRUCT.exit()

        # check opcode arg nodes
        for i in range(len(opcodes[opcode])):
            arg = instr.find("arg" + str(i + 1))
            if arg is None:
                Error.ERR_XML_STRUCT.exit()

            arg_type = arg.get("type")

            if arg_type is None:
                Error.ERR_XML_STRUCT.exit()

            if opcodes[opcode][i] == ArgType.SYMBOL:
                # check symbols
                if arg_type == "var" or arg_type == "string" or arg_type == "nil" or arg_type == "bool" or arg_type == "int" or arg_type == "float":
                    pass
                else:
                    Error.ERR_XML_STRUCT.exit()
            elif str(opcodes[opcode][i]) != arg_type:
                # wrong type in `type` tag
                Error.ERR_XML_STRUCT.exit()

            # only string can have empty text element
            if arg_type != "string" and arg.text is None:
                Error.ERR_XML_STRUCT.exit()
            elif arg_type == "string" and arg.text is None:
                continue

            # check valid format of text element
            if arg_type == "var":
                pattern = re.compile(r"^(GF|TF|LF)@[_\-$&%*!?a-zA-Z][\-$&%*!?\w]*$")
            elif arg_type == "string":
                pattern = re.compile(r"^(([^\s#@\\]|(\\[0-9]{3}))*)$")
            elif arg_type == "nil":
                pattern = re.compile(r"^nil$")
            elif arg_type == "bool":
                pattern = re.compile(r"^(true|false)$")
            elif arg_type == "int":
                pattern = re.compile(r"^[-+]?[0-9]+$")
            elif arg_type == "float":
                pattern = re.compile(r"^[-+]?(?:0x)?[0-9a-f]?\.?[0-9a-f]*(?:p(?:0|[+-][0-9]+))?$")
            elif arg_type == "label":
                pattern = re.compile(r"^[_\-$&%*!?a-zA-Z][\-$&%*!?\w]*$")
            elif arg_type == "type":
                pattern = re.compile(r"^(bool|string|int|float)$")
            else:
                Error.ERR_XML_STRUCT.exit()

            match = pattern.search(arg.text)
            if match is None:
                Error.ERR_XML_STRUCT.exit()
