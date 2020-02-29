from enum import Enum, IntEnum
import xml.etree.ElementTree as ET
import sys
import re
from helper import *

def eprint(str: str):
    print(str, file=sys.stderr)

class Error(IntEnum):
    ERR_ARGS = 10
    ERR_INPUT = 11
    ERR_OUTPUT = 12
    ERR_XML_PARSE = 31
    ERR_XML_STRUCT = 32
    ERR_SEMANTIC = 52
    ERR_OP_TYPE = 53
    ERR_VAR_NOT_FOUND = 54
    ERR_FRAME_NOT_FOUND = 55
    ERR_MISSING_VALUE = 56
    ERR_OP_VALUE = 57
    ERR_STRING = 58
    ERR_INTERNAL = 99
    def exit(self):
        eprint("Error: " + self.name)
        exit(self)

def print_help():
    for string in help_strings:
        print(string)

def parse_args():
    args = sys.argv[1:]
    inp = sys.stdin
    src = sys.stdin
    if len(args) == 1:
        if args[0] == "--help":
            print_help()
            exit(0)
        else:
            parts = re.split(r'[=]', args[0])
            if len(parts) != 2:
                Error.ERR_ARGS.exit()
            if parts[0] == "--source":
                try:
                    src = open(parts[1])
                except:
                    Error.ERR_INPUT.exit()
            elif parts[0] == "--input":
                try:
                    inp = open(parts[1])
                except:
                    Error.ERR_INPUT.exit()
            else:
                Error.ERR_ARGS.exit()
    elif len(args) == 2:
        parts_first = re.split(r'[=]', args[0])
        parts_second = re.split(r'[=]', args[1])
        if len(parts_first) != 2 or len(parts_second) != 2:
            Error.ERR_ARGS.exit()
        if parts_first[0] == "--source" and parts_second[0] == "--input":
            try:
                src = open(parts_first[1])
                inp = open(parts_second[1])
            except:
                Error.ERR_INPUT.exit()
        elif parts_first[0] == "--input" and parts_second[0] == "--source":
            try:
                inp = open(parts_first[1])
                src = open(parts_second[1])
            except:
                Error.ERR_INPUT.exit()
        else:
            Error.ERR_ARGS.exit()
    else:
        Error.ERR_ARGS.exit()
    return (inp, src)

def check_xml(program):
    # check root node
    if program.get("language") != "IPPcode20" or program.tag != "program":
        Error.ERR_XML_STRUCT.exit()
    if program.get("name") != None:
        eprint("Name:   " + program.get("name"))
    if program.get("description") != None:
        eprint("Desc:   " + program.get("description"))
    
    orders = set()
    
    for instr in program:
        opcode = instr.get("opcode")
        order = instr.get("order")
        # check for invalid structure
        if instr.tag != "instruction" or order is None or opcode is None:
            Error.ERR_XML_STRUCT.exit()

        # check duplicate orders
        if order in orders:
            Error.ERR_XML_STRUCT.exit()
        orders.add(order)

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
                if arg_type == "var" or arg_type == "string" or arg_type == "nil" or arg_type == "bool" or arg_type == "int":
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
                pattern = re.compile(r"^[-]?[0-9]+$")
            elif arg_type == "label":
                pattern = re.compile(r"^[_\-$&%*!?a-zA-Z][\-$&%*!?\w]*$")
            elif arg_type == "type":
                pattern = re.compile(r"^(bool|string|int)$")
            else:
                Error.ERR_XML_STRUCT.exit()

            match = pattern.search(arg.text)
            if match is None:
                Error.ERR_XML_STRUCT.exit()

class Program:
    def __init__(self, program):
        self.program = sorted(program, key=lambda instr: int(instr.get("order")))
        self.labels = list(map(lambda x: (x[0] + 1, x[1].find("arg1").text), filter(lambda i: i[1].get("opcode") == "LABEL", enumerate(self.program))))
        self.ip = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.ip >= len(self.program):
            raise StopIteration
        self.ip += 1
        return self.program[self.ip - 1]

def execute(program, inp):
    global_frame = {}
    frames = []
    prog = Program(program)
    print(prog.labels)
    for instr in prog:
        print("opcode: " + instr.get("opcode") + ", order:  " + instr.get("order"))
        #prog.ip += 1
        pass

def main():
    inp, src = parse_args()
    code = src.read()
    try:
        program = ET.fromstring(code)
    except ET.ParseError:
        Error.ERR_XML_PARSE.exit()   
    check_xml(program)
    execute(program, inp)

if __name__ == "__main__":
    main()