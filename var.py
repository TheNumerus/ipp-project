from enum import Enum
from error import *


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
            pass
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
