import xml.etree.ElementTree as Et
from copy import copy, deepcopy

# my imports
from helper import *
from error import *
from var import *
from parse import *


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
    IDIV = 3,
    DIV = 4


class CompOpType(Enum):
    LESSER = 0,
    GREATER = 1,
    EQUAL = 2,


class LogicOpType(Enum):
    AND = 0
    OR = 1,


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
        self.call_stack = []

        self.handlers = {
            "CREATEFRAME": self.create_frame,
            "PUSHFRAME": self.push_frame,
            "POPFRAME": self.pop_frame,
            "DEFVAR": self.defvar,
            "MOVE": self.move,
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
            "DIV": lambda: self.math(op=OpType.DIV),
            "IDIV": lambda: self.math(op=OpType.IDIV),
            "READ": self.read,
            "CALL": self.call,
            "RETURN": self.return_op,
            "LT": lambda: self.comp(op=CompOpType.LESSER),
            "GT": lambda: self.comp(op=CompOpType.GREATER),
            "EQ": lambda: self.comp(op=CompOpType.EQUAL),
            "AND": lambda: self.logic(op=LogicOpType.AND),
            "OR": lambda: self.logic(op=LogicOpType.OR),
            "NOT": self.not_op,
            "DPRINT": self.dprint,
            "BREAK": self.break_op,
            "LABEL": self.label_op,
            "INT2CHAR": self.int_to_char,
            "STRI2INT": self.stri_to_int,
            "INT2FLOAT": self.int_to_float,
            "FLOAT2INT": self.float_to_int,
            "CONCAT": self.concat,
            "STRLEN": self.strlen,
            "GETCHAR": self.get_char,
            "SETCHAR": self.set_char,
            "CLEARS": self.clears,
            "ADDS": lambda: self.maths(op=OpType.ADD),
            "SUBS": lambda: self.maths(op=OpType.SUB),
            "MULS": lambda: self.maths(op=OpType.MUL),
            "IDIVS": lambda: self.maths(op=OpType.IDIV),
            "DIVS": lambda: self.maths(op=OpType.DIV),
            "LTS": lambda: self.comps(op=CompOpType.LESSER),
            "GTS": lambda: self.comps(op=CompOpType.GREATER),
            "EQS": lambda: self.comps(op=CompOpType.EQUAL),
            "ANDS": lambda: self.logics(op=LogicOpType.AND),
            "ORS": lambda: self.logics(op=LogicOpType.OR),
            "NOTS": self.nots_op,
            "INT2CHARS": self.int_to_chars,
            "STRI2INTS": self.stri_to_ints,
            "JUMPIFEQS": lambda: self.jumpifs(equal=True),
            "JUMPIFNEQS": lambda: self.jumpifs(equal=False),
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
            if self.temp_frame is None:
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

    def arg_to_var(self, symbol_type: str, symbol_value: str) -> Var:
        if symbol_type == "var":
            return self.symbol_to_var(symbol_value)
        else:
            return Var.from_symbol(symbol_type, symbol_value)

    def stack_pop(self) -> Var:
        if len(self.data_stack) == 0:
            Error.ERR_MISSING_VALUE.exit()
        return self.data_stack.pop()

    def create_frame(self):
        self.temp_frame = {}
        self.ip += 1

    def push_frame(self):
        if self.temp_frame is None:
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
        source_var = self.arg_to_var(source_type, source_value)

        target_var.value = copy(source_var.value)
        target_var.var_type = copy(source_var.var_type)
        self.ip += 1

    def write(self):
        symb_type, symb_value = self.fetch_args()[0]

        var = self.arg_to_var(symb_type, symb_value)

        val_to_write = ""
        if var.var_type == VarType.INT:
            val_to_write = str(var.value)
        elif var.var_type == VarType.STRING:
            val_to_write = unescape_string(var.value)
        elif var.var_type == VarType.BOOL:
            val_to_write = "true" if var.value else "false"
        elif var.var_type == VarType.NIL:
            val_to_write = ""
        elif var.var_type == VarType.FLOAT:
            val_to_write = var.value.hex()
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
        var = self.arg_to_var(source_type, source_value)
        self.data_stack.append(deepcopy(var))
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

    def clears(self):
        self.data_stack = []
        self.ip += 1

    def type_op(self):
        (_, dest_loc), (src_type, src_val) = self.fetch_args()
        dest_var = self.symbol_to_var(dest_loc)
        dest_var.var_type = VarType.STRING

        if src_type == "var":
            src_var = self.symbol_to_var(src_val)
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
            elif src_var.var_type == VarType.FLOAT:
                dest_var.value = "float"
            else:
                Error.ERR_XML_STRUCT.exit()   
        else:
            dest_var.value = src_type
        self.ip += 1

    def jump(self):
        _, label = self.fetch_args()[0]
        if label not in self.labels:
            Error.ERR_SEMANTIC.exit()
        self.ip = self.labels[label]

    def jumpif(self, *, equal: bool):
        (_, label), (type_1, value_1), (type_2, value_2) = self.fetch_args()

        var_1 = self.arg_to_var(type_1, value_1)
        var_2 = self.arg_to_var(type_2, value_2)

        self._jumpif_op(var_1, var_2, label, equal)

    def jumpifs(self, *, equal: bool):
        _, label = self.fetch_args()[0]

        var_2 = self.stack_pop()
        var_1 = self.stack_pop()

        self._jumpif_op(var_1, var_2, label, equal)

    def _jumpif_op(self, var_1: Var, var_2: Var, label: str, equal: bool):
        if label not in self.labels:
            Error.ERR_SEMANTIC.exit()

        if var_1.var_type != var_2.var_type and var_1.var_type != VarType.NIL and var_2.var_type != VarType.NIL:
            Error.ERR_OP_TYPE.exit()
        if var_1.var_type == VarType.NIL or var_2.var_type == VarType.NIL:
            self.ip = self.labels[label]

        if (var_1.value == var_2.value) ^ (not equal):
            self.ip = self.labels[label]
        else:
            self.ip += 1

    def math(self, *, op: OpType):
        (_, target), (type_1, value_1), (type_2, value_2) = self.fetch_args()
        target = self.symbol_to_var(target)

        var_1 = self.arg_to_var(type_1, value_1)
        var_2 = self.arg_to_var(type_2, value_2)

        Program._math_op(var_1, var_2, target, op)

        self.ip += 1

    def maths(self, *, op: OpType):
        target = Var(VarType.UNDEF, None)

        var_2 = self.stack_pop()
        var_1 = self.stack_pop()

        Program._math_op(var_1, var_2, target, op)
        self.data_stack.append(target)
        self.ip += 1

    @staticmethod
    def _math_op(var_1: Var, var_2: Var, target: Var, op: OpType):
        if var_1.var_type != var_2.var_type or (var_1.var_type != VarType.INT and var_1.var_type != VarType.FLOAT):
            Error.ERR_OP_TYPE.exit()

        if op == OpType.ADD:
            target.value = var_1.value + var_2.value
        elif op == OpType.SUB:
            target.value = var_1.value - var_2.value
        elif op == OpType.MUL:
            target.value = var_1.value * var_2.value
        elif op == OpType.DIV:
            if var_1.var_type != VarType.FLOAT or var_2.var_type != VarType.FLOAT:
                Error.ERR_OP_TYPE.exit()
            if var_2.value == 0.0:
                Error.ERR_OP_VALUE.exit()
            target.value = var_1.value / var_2.value
        else:
            # must be `IDIV`
            if var_1.var_type != VarType.INT or var_2.var_type != VarType.INT:
                Error.ERR_OP_TYPE.exit()
            if var_2.value == 0:
                Error.ERR_OP_VALUE.exit()
            target.value = var_1.value // var_2.value
        target.var_type = var_1.var_type
        return target

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
            # must be float
            try:
                i = float.fromhex(i)
            except ValueError:
                error = True
                i = None
        var.value = i
        if error:
            var.var_type = VarType.NIL
        else:
            var.var_type = VarType.from_str(src_type)
        self.ip += 1

    def call(self):
        _, label = self.fetch_args()[0]
        if label not in self.labels:
            Error.ERR_SEMANTIC.exit()
        self.call_stack.append(self.ip + 1)
        self.ip = self.labels[label]

    def return_op(self):
        if len(self.call_stack) == 0:
            Error.ERR_MISSING_VALUE.exit()
        self.ip = self.call_stack.pop()

    def comp(self, *, op: CompOpType):
        (_, target), (type_1, value_1), (type_2, value_2) = self.fetch_args()
        target = self.symbol_to_var(target)
        var_1 = self.arg_to_var(type_1, value_1)
        var_2 = self.arg_to_var(type_2, value_2)

        Program._comp_op(var_1, var_2, target, op)

        self.ip += 1

    def comps(self, *, op: CompOpType):
        target = Var(VarType.UNDEF, None)

        var_2 = self.stack_pop()
        var_1 = self.stack_pop()

        Program._comp_op(var_1, var_2, target, op)

        self.data_stack.append(target)
        self.ip += 1

    @staticmethod
    def _comp_op(var_1: Var, var_2: Var, target: Var, op: CompOpType):
        if (var_1.var_type == VarType.NIL or var_2.var_type == VarType.NIL) and op != CompOpType.EQUAL:
            Error.ERR_OP_TYPE.exit()

        target.var_type = VarType.BOOL
        if var_1.var_type == var_2.var_type and var_1 != VarType.NIL:
            if op == CompOpType.LESSER:
                target.value = var_1.value < var_2.value
            elif op == CompOpType.GREATER:
                target.value = var_1.value > var_2.value
            else:
                # must be `EQUAL`
                target.value = var_1.value == var_2.value
        else:
            target.value = False

    def logic(self, *, op: LogicOpType):
        (_, target), (type_1, value_1), (type_2, value_2) = self.fetch_args()
        target = self.symbol_to_var(target)
        var_1 = self.arg_to_var(type_1, value_1)
        var_2 = self.arg_to_var(type_2, value_2)

        Program._logic_op(var_1, var_2, target, op)

        self.ip += 1

    def logics(self, *, op: LogicOpType):
        target = Var(VarType.UNDEF, None)
        var_2 = self.stack_pop()
        var_1 = self.stack_pop()

        Program._logic_op(var_1, var_2, target, op)

        self.data_stack.append(target)
        self.ip += 1

    @staticmethod
    def _logic_op(var_1: Var, var_2: Var, target: Var, op: LogicOpType):
        if var_1.var_type == var_2.var_type and var_1.var_type == VarType.BOOL:
            target.var_type = VarType.BOOL
            if op == LogicOpType.AND:
                target.value = var_1.value and var_2.value
            else:
                # must be `OR`
                target.value = var_1.value or var_2.value
        else:
            Error.ERR_OP_TYPE.exit()

    def not_op(self):
        (_, target), (type_1, value_1) = self.fetch_args()
        target = self.symbol_to_var(target)
        var = self.arg_to_var(type_1, value_1)
        if var.var_type == VarType.BOOL:
            target.var_type = VarType.BOOL
            target.value = not var.value
        else:
            Error.ERR_OP_TYPE.exit()
        self.ip += 1

    def nots_op(self):
        target = self.stack_pop()
        if target.var_type == VarType.BOOL:
            target.var_type = VarType.BOOL
            target.value = not target.value
        else:
            Error.ERR_OP_TYPE.exit()
        self.ip += 1

    def dprint(self):
        type_1, value_1 = self.fetch_args()[0]
        var = self.arg_to_var(type_1, value_1)
        eprint(var)
        self.ip += 1

    def break_op(self):
        eprint("frames: " + str(self.frames))
        eprint("temp_frame: " + str(self.temp_frame))
        eprint("global: " + str(self.global_frame))
        eprint("stack: " + str(self.data_stack))
        eprint("")
        self.ip += 1

    def label_op(self):
        self.ip += 1

    def int_to_char(self):
        (_, target), (src_type, src_value) = self.fetch_args()
        target = self.symbol_to_var(target)
        src = self.arg_to_var(src_type, src_value)

        Program._int_to_char_op(src, target)

        self.ip += 1

    def int_to_chars(self):
        src = self.stack_pop()

        Program._int_to_char_op(src, src)

        self.data_stack.append(src)
        self.ip += 1

    @staticmethod
    def _int_to_char_op(src: Var, target: Var):
        if src.var_type != VarType.INT:
            Error.ERR_OP_TYPE.exit()

        try:
            char = chr(src.value)
        except ValueError:
            Error.ERR_STRING.exit()

        target.value = char
        target.var_type = VarType.STRING

    def stri_to_int(self):
        (_, target), (src_type, src_value), (index_type, index_value) = self.fetch_args()
        target = self.symbol_to_var(target)
        src = self.arg_to_var(src_type, src_value)
        index = self.arg_to_var(index_type, index_value)

        Program._stri_to_int_op(target, src, index)

        self.ip += 1

    def stri_to_ints(self):
        target = Var(VarType.UNDEF, None)
        index = self.stack_pop()
        src = self.stack_pop()

        Program._stri_to_int_op(target, src, index)

        self.data_stack.append(target)
        self.ip += 1

    @staticmethod
    def _stri_to_int_op(target: Var, src: Var, index: Var):
        if src.var_type != VarType.STRING or index.var_type != VarType.INT:
            Error.ERR_OP_TYPE.exit()

        try:
            char = ord(src.value[index.value])
        except IndexError:
            Error.ERR_STRING.exit()

        target.value = char
        target.var_type = VarType.INT

    def concat(self):
        (_, target), (type_1, value_1), (type_2, value_2) = self.fetch_args()
        target = self.symbol_to_var(target)
        var_1 = self.arg_to_var(type_1, value_1)
        var_2 = self.arg_to_var(type_2, value_2)
        if var_1.var_type != VarType.STRING or var_2.var_type != VarType.STRING:
            Error.ERR_OP_TYPE.exit()
        
        target.value = var_1.value + var_2.value
        target.var_type = VarType.STRING
        self.ip += 1

    def strlen(self):
        (_, target), (type_1, value_1) = self.fetch_args()
        target = self.symbol_to_var(target)
        var_1 = self.arg_to_var(type_1, value_1)
        if var_1.var_type != VarType.STRING:
            Error.ERR_OP_TYPE.exit()
        
        target.value = len(var_1.value)
        target.var_type = VarType.INT
        self.ip += 1

    def get_char(self):
        (_, target), (src_type, src_value), (index_type, index_value) = self.fetch_args()
        target = self.symbol_to_var(target)
        src = self.arg_to_var(src_type, src_value)
        index = self.arg_to_var(index_type, index_value)
        if src.var_type != VarType.STRING or index.var_type != VarType.INT:
            Error.ERR_OP_TYPE.exit()

        try:
            char = src.value[index.value]
        except IndexError:
            Error.ERR_STRING.exit()
        
        target.value = char
        target.var_type = VarType.STRING
        self.ip += 1

    def set_char(self):
        (_, target), (index_type, index_value), (src_type, src_value) = self.fetch_args()
        target = self.symbol_to_var(target)
        index = self.arg_to_var(index_type, index_value)
        src = self.arg_to_var(src_type, src_value)
        if target.var_type != VarType.STRING or index.var_type != VarType.INT or src.var_type != VarType.STRING:
            Error.ERR_OP_TYPE.exit()

        try:
            target.value[index.value] = src.value[0]
        except IndexError:
            Error.ERR_STRING.exit()
        
        self.ip += 1

    def int_to_float(self):
        (_, target), (src_type, src_value) = self.fetch_args()
        target = self.symbol_to_var(target)
        src = self.arg_to_var(src_type, src_value)
        if src.var_type != VarType.INT:
            Error.ERR_OP_TYPE.exit()

        try:
            fl = float(src.value)
        except ValueError:
            Error.ERR_STRING.exit()

        target.value = fl
        target.var_type = VarType.FLOAT
        self.ip += 1

    def float_to_int(self):
        (_, target), (src_type, src_value) = self.fetch_args()
        target = self.symbol_to_var(target)
        src = self.arg_to_var(src_type, src_value)
        if src.var_type != VarType.FLOAT:
            Error.ERR_OP_TYPE.exit()

        try:
            i = int(src.value)
        except ValueError:
            Error.ERR_STRING.exit()

        target.value = i
        target.var_type = VarType.INT
        self.ip += 1

    def execute(self):
        for instr in self:
            opcode = instr.get("opcode")
            if opcode not in self.handlers:
                Error.ERR_SEMANTIC.exit()
            else:
                self.handlers[opcode]()


def main():
    src = parse_args()
    code = src.read()
    try:
        xml = Et.fromstring(code)
    except Et.ParseError:
        Error.ERR_XML_PARSE.exit()   
    check_xml(xml)
    program = Program(xml)
    program.execute()


if __name__ == "__main__":
    main()
