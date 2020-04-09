from enum import IntEnum
import sys


def eprint(*args):
    """Shortcut print function"""
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
