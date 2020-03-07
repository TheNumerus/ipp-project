from enum import Enum, IntEnum
import xml.etree.ElementTree as ET
import sys
import re
from helper import *
from copy import copy

def eprint(*args):
    for arg in args:
        print(arg, file=sys.stderr, end=" ")
    print("", file=sys.stderr)

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
    sys.stdin = inp
    return src

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

def unescape_string(string):
    if string is None:
        return ""
    i = 0
    escaped = ""
    esc = re.compile(r"\\[0-9]{3}")
    # somewhere, this will horribly fail
    while i < len(string):
        match = esc.search(string[i:i+4])
        if match is not None:
            escaped += chr(int(string[i+1:i+4]))
            i += 4
        else:
            escaped += string[i]
            i += 1
    return escaped

class OpType(Enum):
    ADD = 0,
    SUB = 1
    MUL = 2,
    IDIV = 3

class VarType(Enum):
    BOOL = 0,
    INT = 1,
    STRING = 2,
    NIL = 3,
    UNDEF = 4
    
    @staticmethod
    def from_str(string):
        if string == "bool":
            return VarType.BOOL
        elif string == "int":
            return VarType.INT
        elif string == "nil":
            return VarType.NIL
        elif string == "string":
            return VarType.STRING
        else:
            Error.ERR_INTERNAL.exit()

class Var:
    def __init__(self, var_type: VarType, value):
        self.var_type = var_type
        self.value = value

    def __repr__(self):
        return "VarType={type: " + self.var_type.name + ", value: " + str(self.value) + "}"
    
    @staticmethod
    def from_symbol(var_type, value):
        var_type = VarType.from_str(var_type)
        if var_type == VarType.STRING:
            pass
        elif var_type == VarType.INT:
            value = int(value)
        elif var_type == VarType.NIL:
            value = None
        elif var_type == VarType.BOOL:
            value = value == "true"
        else:
            Error.ERR_INTERNAL.exit()
        return Var(var_type, value)

class Program:
    def __init__(self, program):
        self.program = sorted(program, key=lambda instr: int(instr.get("order")))

        # check duplicate labels
        labels = list(map(lambda x: (x[1].find("arg1").text, x[0]), filter(lambda i: i[1].get("opcode") == "LABEL", enumerate(self.program))))
        self.labels = {}
        for k, v in labels:
            if k not in self.labels:
                self.labels[k] = v
            else:
                Error.ERR_SEMANTIC.exit()
        
        self.global_frame = {}
        self.frames = []
        self.temp_frame = None
        self.data_stack = []

        self.handlers = {
            "CREATEFRAME": self.create_frame,
            "PUSHFRAME": self.push_frame,
            "POPFRAME": self.pop_frame,
            "DEFVAR": self.defvar,
            "MOVE" : self.move,
            "WRITE": self.write,
            "EXIT": self.exit,
            "PUSHS": self.push,
            "POPS": self.pop,
            "TYPE": self.type_op,
            "JUMP": self.jump,
            "JUMPIFEQ": lambda: self.jumpif(equal=True),
            "JUMPIFNEQ": lambda: self.jumpif(equal=False),
            "ADD": lambda: self.math(op=OpType.ADD),
            "SUB": lambda: self.math(op=OpType.SUB),
            "MUL": lambda: self.math(op=OpType.MUL),
            "IDIV": lambda: self.math(op=OpType.IDIV),
            "READ": self.read
        }

        self.ip = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.ip >= len(self.program):
            raise StopIteration
        return self.program[self.ip]

    def fetch_args(self):
        instr = self.program[self.ip]
        args = []
        for arg in instr:
            args.append((arg.get("type"), arg.text))
        return args

    @staticmethod
    def parse_var(var):
        scope = var[0:2]
        name = var[3:]
        return scope, name

    def is_var_defined(self, scope, name) -> bool:
        if scope == "GF":
            return name in self.global_frame
        elif scope == "LF":
            if len(self.frames) == 0:
                Error.ERR_FRAME_NOT_FOUND.exit()
            return name in self.frames[-1]
        else:
            # must be "TF"
            if self.temp_frame == None:
                Error.ERR_FRAME_NOT_FOUND.exit()
            return name in self.temp_frame

    def symbol_to_var(self, symbol_value) -> Var:
        scope, name = Program.parse_var(symbol_value)
        if not self.is_var_defined(scope, name):
            Error.ERR_VAR_NOT_FOUND.exit()
        
        if scope == "GF":
            return self.global_frame[name]
        elif scope == "LF":
            return self.frames[-1][name]
        else:
            # must be "TF"
            return self.temp_frame[name]

    def create_frame(self):
        self.temp_frame = {}
        self.ip += 1

    def push_frame(self):
        if self.temp_frame == None:
            Error.ERR_FRAME_NOT_FOUND.exit()
        self.frames.append(self.temp_frame)
        self.temp_frame = None
        self.ip += 1

    def pop_frame(self):
        if len(self.frames) > 0:
            self.temp_frame = self.frames.pop()
        else:
            Error.ERR_FRAME_NOT_FOUND.exit()
        self.ip += 1

    def defvar(self):
        _, name = self.fetch_args()[0]
        scope, name = Program.parse_var(name)
        
        # check redefinition
        if self.is_var_defined(scope, name):
            Error.ERR_SEMANTIC.exit()
        
        if scope == "GF":
            self.global_frame[name] = Var(VarType.UNDEF, None)
        elif scope == "LF":
            self.frames[-1][name] = Var(VarType.UNDEF, None)
        else:
            # must be "TF"
            self.temp_frame[name] = Var(VarType.UNDEF, None)
        self.ip += 1

    def move(self):
        (_, target), (source_type, source_value) = self.fetch_args()
        target_var = self.symbol_to_var(target)

        if source_type == "var":
            source_var = self.symbol_to_var(source_value)
            target_var.value = copy(source_var.value)
            target_var.var_type = copy(source_var.var_type)
        else:
            source_var = Var.from_symbol(source_type, source_value)
            target_var.value = copy(source_var.value)
            target_var.var_type = copy(source_var.var_type)
        self.ip += 1

    def write(self):
        symb_type, symb_value = self.fetch_args()[0]

        val_to_write = ""

        if symb_type == "var":
            var = self.symbol_to_var(symb_value)
        else:
            var = Var.from_symbol(symb_type, symb_value)
        if var.var_type == VarType.INT:
            val_to_write = str(var.value)
        elif var.var_type == VarType.STRING:
            val_to_write = unescape_string(var.value)
        elif var.var_type == VarType.BOOL:
            val_to_write = "true" if var.value else "false"
        elif var.var_type == VarType.NIL:
            val_to_write = ""
        else:
            # must be `VarType.UNDEF`
            Error.ERR_MISSING_VALUE.exit()
        print(val_to_write, end="", flush=True)
        self.ip += 1

    def exit(self):
        symb_type, symb_value = self.fetch_args()[0]

        if symb_type == "int":
            val = int(symb_value)
        elif symb_type == "var":
            var = self.symbol_to_var(symb_value)
            if var.var_type != VarType.INT:
                Error.ERR_OP_TYPE.exit()
            val = var.value
        else:
            Error.ERR_OP_TYPE.exit()
        
        if val > 49 or val < 0:
            Error.ERR_OP_VALUE.exit()
        exit(val)

    def push(self):
        source_type, source_value = self.fetch_args()[0]

        if source_type == "var":
            source_var = self.symbol_to_var(source_value)
            new = Var(copy(source_var.var_type), copy(source_var.value))
        elif source_type == "string":
            new = Var(VarType.STRING, source_value)
        elif source_type == "int":
            new = Var(VarType.INT, source_value)
        elif source_type == "nil":
            new = Var(VarType.NIL, None)
        elif source_type == "bool":
            new = Var(VarType.BOOL, source_value == "true")
        else:
            Error.ERR_XML_STRUCT.exit()

        self.data_stack.append(new)
        self.ip += 1

    def pop(self):
        if len(self.data_stack) == 0:
            Error.ERR_MISSING_VALUE.exit()
        _, dst = self.fetch_args()[0]
        var = self.symbol_to_var(dst)
        pop = self.data_stack.pop()
        var.var_type = pop.var_type
        var.value = pop.value
        self.ip += 1

    def type_op(self):
        (_, dest_loc), (src_type, src_val) = self.fetch_args()
        dest_var = self.symbol_to_var(dest_loc)

        if src_type == "var":
            src_var = self.symbol_to_var(src_val)
            dest_var.var_type = VarType.STRING
            if src_var.var_type == VarType.STRING:
                dest_var.value = "string"
            elif src_var.var_type == VarType.UNDEF:
                dest_var.value = ""
            elif src_var.var_type == VarType.NIL:
                dest_var.value = "nil"
            elif src_var.var_type == VarType.INT:
                dest_var.value = "int"
            elif src_var.var_type == VarType.BOOL:
                dest_var.value = "bool"
            else:
                Error.ERR_XML_STRUCT.exit()   
        else:
            dest_var.var_type = VarType.STRING
            dest_var.value = src_type
        self.ip += 1

    def jump(self):
        _, label = self.fetch_args()[0]
        if label not in self.labels:
            Error.ERR_SEMANTIC.exit()
        self.ip = self.labels[label]

    def jumpif(self,*, equal:bool):
        (_, label), (type_1, value_1), (type_2, value_2) = self.fetch_args()

        if label not in self.labels:
            Error.ERR_SEMANTIC.exit()

        if type_1 == "var":
            var_1 = self.symbol_to_var(value_1)
        else:
            var_1 = Var.from_symbol(type_1, value_1)
        
        if type_2 == "var":
            var_2 = self.symbol_to_var(value_2)
        else:
            var_2 = Var.from_symbol(type_2, value_2)

        if var_1.var_type != var_2.var_type and var_1.var_type != VarType.NIL and var_2.var_type != VarType.NIL:
            Error.ERR_OP_TYPE.exit()
        if var_1.var_type == VarType.NIL or var_2.var_type == VarType.NIL:
            self.ip = self.labels[label]

        if (var_1.value == var_2.value) ^ (not equal):
            self.ip = self.labels[label]
        else:
            self.ip += 1

    def math(self,*, op: OpType):
        (_, target), (type_1, value_1), (type_2, value_2) = self.fetch_args()
        target = self.symbol_to_var(target)

        if type_1 == "var":
            var_1 = self.symbol_to_var(value_1)
        else:
            var_1 = Var.from_symbol(type_1, value_1)
        
        if type_2 == "var":
            var_2 = self.symbol_to_var(value_2)
        else:
            var_2 = Var.from_symbol(type_2, value_2)

        if var_1.var_type != VarType.INT or var_2.var_type != VarType.INT:
            Error.ERR_OP_TYPE.exit()
        
        if op == OpType.ADD:
            target.value = var_1.value + var_2.value
        elif op == OpType.SUB:
            target.value = var_1.value - var_2.value
        elif op == OpType.MUL:
            target.value = var_1.value * var_2.value
        else:
            # must be `IDIV`
            target.value = var_1.value // var_2.value
        target.var_type = VarType.INT
        self.ip += 1

    def read(self):
        (_, target), (_, src_type) = self.fetch_args()
        var = self.symbol_to_var(target)
        error = False
        try:
            i = input()
        except EOFError:
            error = True
            i = None
        if src_type == "string":
            pass
        elif src_type == "bool":
            i = i.lower() == "true"
        elif src_type == "int":
            try:
                i = int(i)
            except ValueError:
                error = True
                i = None
        else:
            pass
        var.value = i
        if error:
            var.var_type = VarType.NIL
        else:
            var.var_type = VarType.from_str(src_type)
        self.ip += 1

    def execute(self):
        for instr in self:
            opcode = instr.get("opcode")
            eprint(opcode)
            if opcode not in self.handlers:
                eprint(opcode + " missing")
                self.ip += 1
            else:
                self.handlers[opcode]()
            eprint("frames: " + str(self.frames))
            eprint("temp_frame: " + str(self.temp_frame))
            eprint("global: " + str(self.global_frame))
            eprint("stack: " + str(self.data_stack))
            eprint("")

def main():
    src = parse_args()
    code = src.read()
    try:
        xml = ET.fromstring(code)
    except ET.ParseError:
        Error.ERR_XML_PARSE.exit()   
    check_xml(xml)
    program = Program(xml)
    program.execute()

if __name__ == "__main__":
    main()