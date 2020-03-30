<?php
const ERR_ARG = 10;
const ERR_INPUT = 11;
const ERR_OUTPUT = 12;
const ERR_HEADER = 21;
const ERR_OPCODE = 22;
const ERR_OTHER = 23;
const ERR_INTERNAL = 99;

// prints error message
function return_error(int $err) {
    switch ($err) {
        case ERR_ARG:
            fprintf(STDERR, "Invalid argument or combnination of arguments.");
            break;
        case ERR_INPUT:
            fprintf(STDERR, "Unable to open input file.");
            break;
        case ERR_OUTPUT:
            fprintf(STDERR, "Unable to open output file.");
            break;
        case ERR_HEADER:
            fprintf(STDERR, "Corrupted or missing header.");
            break;
        case ERR_OPCODE:
            fprintf(STDERR, "Corrupted or unknown opcode.");
            break;
        case ERR_OTHER:
            fprintf(STDERR, "Other lexical or syntax error.");
            break;
        default:
            fprintf(STDERR, "Internal error.");
            exit(99);
    }
    exit($err);
}