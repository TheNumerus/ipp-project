import re
from enum import Enum
from error import *


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


class VarType(Enum):
    BOOL = 0,
    INT = 1,
    STRING = 2,
    NIL = 3,
    UNDEF = 4,
    FLOAT = 5,

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
        elif string == "float":
            return VarType.FLOAT
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
            value = unescape_string(value)
        elif var_type == VarType.INT:
            value = int(value)
        elif var_type == VarType.NIL:
            value = None
        elif var_type == VarType.BOOL:
            value = value == "true"
        elif var_type == VarType.FLOAT:
            value = float.fromhex(value)
        else:
            Error.ERR_INTERNAL.exit()
        return Var(var_type, value)
