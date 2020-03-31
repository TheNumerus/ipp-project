<?php

class Err {
    const ARG = 10;
    const INPUT = 11;
    const OUTPUT = 12;
    const HEADER = 21;
    const OPCODE = 22;
    const OTHER = 23;
    const INTERNAL = 99;
}

// prints error message
function return_error(int $err) {
    switch ($err) {
        case Err::ARG:
            fprintf(STDERR, "Invalid argument or combnination of arguments.");
            break;
        case Err::INPUT:
            fprintf(STDERR, "Unable to open input file.");
            break;
        case Err::OUTPUT:
            fprintf(STDERR, "Unable to open output file.");
            break;
        case Err::HEADER:
            fprintf(STDERR, "Corrupted or missing header.");
            break;
        case Err::OPCODE:
            fprintf(STDERR, "Corrupted or unknown opcode.");
            break;
        case Err::OTHER:
            fprintf(STDERR, "Other lexical or syntax error.");
            break;
        default:
            fprintf(STDERR, "Internal error.");
            exit(99);
    }
    exit($err);
}