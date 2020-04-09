from enum import Enum

class ArgType(Enum):
    VAR = 0
    SYMBOL = 1
    LABEL = 2
    TYPE = 3
    def __str__(self):
        if self == ArgType.VAR:
            return "var"
        elif self == ArgType.TYPE:
            return "type"
        elif self == ArgType.LABEL:
            return "label"
        return "symbol"
        

help_strings = [
    "IPPcode20 interpreter (interpret.py)\n",
    "Parameters:",
    "--help            - Prints script manual, exclusive with other arguments\n",
    "--input=FILEPATH  - Program input",
    "--source=FILEPATH - Program source file\n",
    "Either --source or --input must be set. Both can be passed at the same time\n",
    "Return codes:",
    " 0 - Success",
    "10 - Invalid argument or combnination of arguments",
    "11 - Unable to open input file",
    "12 - Unable to open output file",
    "31 - XML Parse error",
    "32 - Invalid XML structure",
    "52 - Program semantic error",
    "53 - Runtime operand type error",
    "54 - Runtime variable not found error",
    "55 - Runtime frame not found error",
    "56 - Runtime missing value error",
    "57 - Runtime operand value error",
    "58 - Runtime string manipulation error",
    "99 - Internal error in the script"
]


def print_help():
    for string in help_strings:
        print(string)


opcodes = {
    'RETURN':      [],
    'PUSHFRAME':   [],
    'POPFRAME':    [],
    'CREATEFRAME': [],
    'BREAK':       [],
    'CLEARS':      [],
    'ADDS':        [],
    'SUBS':        [],
    'MULS':        [],
    'IDIVS':       [],
    'DIVS':        [],
    'LTS':         [],
    'GTS':         [],
    'EQS':         [],
    'ANDS':        [],
    'ORS':         [],
    'NOTS':        [],
    'INT2CHARS':   [],
    'STRI2INTS':   [],

    'DEFVAR':     [ArgType.VAR],
    'POPS':       [ArgType.VAR],
    'WRITE':      [ArgType.SYMBOL],
    'PUSHS':      [ArgType.SYMBOL],
    'EXIT':       [ArgType.SYMBOL],
    'DPRINT':     [ArgType.SYMBOL],
    'LABEL':      [ArgType.LABEL],
    'CALL':       [ArgType.LABEL],
    'JUMP':       [ArgType.LABEL],
    'JUMPIFEQS':  [ArgType.LABEL],
    'JUMPIFNEQS': [ArgType.LABEL],

    'MOVE':      [ArgType.VAR, ArgType.SYMBOL],
    'INT2CHAR':  [ArgType.VAR, ArgType.SYMBOL],
    'STRLEN':    [ArgType.VAR, ArgType.SYMBOL],
    'TYPE':      [ArgType.VAR, ArgType.SYMBOL],
    'NOT':       [ArgType.VAR, ArgType.SYMBOL],
    'INT2FLOAT': [ArgType.VAR, ArgType.SYMBOL],
    'FLOAT2INT': [ArgType.VAR, ArgType.SYMBOL],
    'READ':      [ArgType.VAR, ArgType.TYPE],

    'CONCAT':    [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'GETCHAR':   [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'SETCHAR':   [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'ADD':       [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'SUB':       [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'MUL':       [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'IDIV':      [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'DIV':       [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'LT':        [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'GT':        [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'EQ':        [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'AND':       [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'OR':        [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'STRI2INT':  [ArgType.VAR,   ArgType.SYMBOL, ArgType.SYMBOL],
    'JUMPIFNEQ': [ArgType.LABEL, ArgType.SYMBOL, ArgType.SYMBOL],
    'JUMPIFEQ':  [ArgType.LABEL, ArgType.SYMBOL, ArgType.SYMBOL]
}
