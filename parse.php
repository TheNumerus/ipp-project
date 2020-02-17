<?php

const ROOT = '<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode20"></program>';
const ERR_ARG = 10;
const ERR_HEADER = 21;
const ERR_OPCODE = 22;
const ERR_OTHER = 23;

if ($argc == 2 && $argv[1] == "--help") {
    print_help();
    exit(0);
} else if ($argc != 1) {
    return_error(ERR_HEADER);
}

$xml = new SimpleXMLElement(ROOT);
$line_number = 0;

while($line = fgets(STDIN)) {
    $matches = [];
    if (preg_match('/(.*)(?=#)/', $line, $matches)) {
        $line = trim($matches[0]);
    } else {
        $line = trim($line);
    }
    
    if (strlen($line) == 0) {
        continue;
    }

    if ($line[0] == '#') {
        continue;
    }

    //var_dump($line);

    $parts = preg_split('/\s/', $line);

    if ($line_number != 0) {
        $child = $xml->addChild("instruction");
        $child->addAttribute("order", $line_number);
        switch ($parts[0]) {
            case 'DEFVAR':
            case 'POPS':
                check_var($parts[1], $child, 1);
                if (count($parts) != 2) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'MOVE':
            case 'INT2CHAR':
            case 'STRLEN':
            case 'TYPE':
                check_var($parts[1], $child, 1);
                check_symb($parts[2], $child, 2);
                if (count($parts) != 3) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'WRITE':
            case 'PUSHS':
            case 'EXIT':
            case 'DPRINT':
                check_symb($parts[1], $child, 1);
                if (count($parts) != 2) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'CONCAT':
            case 'GETCHAR':
            case 'SETCHAR':
            case 'ADD':
            case 'SUB':
            case 'MUL':
            case 'IDIV':
            case 'LT':
            case 'GT':
            case 'EQ':
            case 'AND':
            case 'OR':
            case 'NOT':
            case 'STR2INT':
                check_var($parts[1], $child, 1);
                check_symb($parts[2], $child, 2);
                check_symb($parts[3], $child, 3);
                if (count($parts) != 4) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'JUMPIFNEQ':
            case 'JUMPIFEQ':
                check_label($parts[1], $child, 1);
                check_symb($parts[2], $child, 2);
                check_symb($parts[3], $child, 3);
                if (count($parts) != 4) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'CALL':
            case 'LABEL':
            case 'JUMP':
                check_label($parts[1], $child, 1);
                if (count($parts) != 2) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'READ':
                check_var($parts[1], $child, 1);
                check_type($parts[2], $child, 2);
                if (count($parts) != 3) {
                    return_error(ERR_OPCODE);
                }
            break;
            case 'PUSHFRAME':
            case 'POPFRAME':
            case 'CREATEFRAME':
            case 'RETURN':
            case 'BRAKE':
                if (count($parts) != 1) {
                    return_error(ERR_OPCODE);
                }
            break;
            default:
                return_error(ERR_OPCODE);
        }
        
        $child->addAttribute("opcode", $parts[0]);
    } else {
        if ($parts[0] != ".IPPcode20") {
            return_error(ERR_HEADER);
        }
    }
    //var_dump($parts);
    $line_number++;
}

echo $xml->asXML();

// prints help
function print_help() {
    echo "IPPcode20 code analyzer (parse.php)\n\n";
    echo "Filter type script, loads IPPcode20 source file from standard input, checks lexical and syntax code correctness and writes XML program representation to standard output.\n\n";
    echo "Parameters:\n";
    echo "--help - Prints script manual\n\n";
    echo "Return codes:\n";
    echo "0 - Success\n";
    echo "10 - Invalid combnination of arguments\n";
    echo "21 - Corrupted or missing header in IPPcode20 source file\n";
    echo "22 - Corrupted or unknown opcode in IPPcode20 source file\n";
    echo "23 - Other lexical or syntax error in IPPcode20 source file\n";
}

function check_var($var, $parent, $num) {
    if (preg_match('/^(GF|TF|LF)@[_\-$&%*!?a-zA-Z][_\-$&%*!?\w]*/', $var)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "var");
        $arg = "arg" . $num;
        $parent->$arg = $var;
        return;
    }
    return_error(ERR_OTHER);
}

function check_symb($symb, $parent, $num) {
    if (preg_match('/^(GF|TF|LF)@/', $symb)) {
        check_var($symb, $parent, $num);
    } else if (preg_match('/^(int|bool|string|nil)/', $symb, $matches)) {
        switch ($matches[0]) {
            case "string":
                $child = $parent->addChild("arg" . $num);
                $child->addAttribute("type", "string");
                $arg = "arg" . $num;
                preg_match('/@([\S]*)/', $symb, $str_match);
                $parent->$arg = $str_match[1];
            break;
            case "bool":
                $child = $parent->addChild("arg" . $num);
                $child->addAttribute("type", "bool");
                $arg = "arg" . $num;
                if (!preg_match('/@(true|false)/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
                $parent->$arg = $str_match[1];
            break;
            case "int":
                $child = $parent->addChild("arg" . $num);
                $child->addAttribute("type", "int");
                $arg = "arg" . $num;
                if (!preg_match('/@(\-?[0-9]+)/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
                $parent->$arg = $str_match[1];
            break;
            case "nil":
                $child = $parent->addChild("arg" . $num);
                $child->addAttribute("type", "nil");
                $arg = "arg" . $num;
                if (!preg_match('/@(nil)/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
                $parent->$arg = "nil";
            break;
            default:
            return_error(ERR_OTHER);
        }
    } else {
        return_error(ERR_OTHER);
    }
}

function check_label($label, $parent, $num) {
    if (preg_match('/^[_\-$&%*!?a-zA-Z][_\-$&%*!?\w]*/', $label)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "label");
        $arg = "arg" . $num;
        $parent->$arg = $label;
        return;
    }
    return_error(ERR_OTHER);
}

function check_type($type, $parent, $num) {
    if (preg_match('/^(string|int|bool)$/', $type)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "type");
        $arg = "arg" . $num;
        $parent->$arg = $type;
        return;
    }
    return_error(ERR_OTHER);
}

function return_error($err) {
    switch ($err) {
        case ERR_ARG:
            fprintf(STDERR, "Invalid combnination of arguments.");
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
            exit(99);
    }
    exit($err);
}