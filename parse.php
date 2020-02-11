<?php

const ROOT = '<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode20"></program>';

if ($argc == 2 && $argv[1] == "--help") {
    print_help();
    exit(0);
} else if ($argc != 1) {
    // error
    fprintf(STDERR, "Invalid combnination of arguments.");
    exit(10);
}

$xml = new SimpleXMLElement(ROOT);
$line_number = 0;

while(($line = fgets(STDIN))) {
    $matches = [];
    if (preg_match('/(.*)(?=#)/', $line, $matches)) {
        $line = htmlspecialchars(trim($matches[0]));
    } else {
        $line = htmlspecialchars(trim($line));
    };
    
    if (strlen($line) == 0) {
        continue;
    }

    if ($line[0] == '#') {
        continue;
    }

    //var_dump($line);

    $parts = explode(' ', $line);

    if ($line_number != 0) {
        $child = $xml->addChild("instruction");
        $child->addAttribute("order", $line_number);
        switch ($parts[0]) {
            case 'DEFVAR':
                check_var($parts[1], $child, 1);
            break;
            case 'MOVE':
                check_var($parts[1], $child, 1);
                check_symb($parts[2], $child, 2);
            break;
            case 'WRITE':
                check_symb($parts[1], $child, 1);
            break;
            case 'CONCAT':
            case 'GETCHAR':
            case 'SETCHAR':
                check_var($parts[1], $child, 1);
                check_symb($parts[2], $child, 2);
                check_symb($parts[3], $child, 3);
            break;
            case 'JUMPIFNEQ':
            case 'JUMPIFEQ':
                check_label($parts[1], $child, 1);
                check_symb($parts[2], $child, 2);
                check_symb($parts[3], $child, 3);
            break;
            case 'CALL':
            case 'LABEL':
            case 'JUMP':
                check_label($parts[1], $child, 1);
            break;
            default:
                fprintf(STDERR, "Corrupted or unknown opcode.");
                exit(21);
        }
        
        $child->addAttribute("opcode", $parts[0]);
    } else {
        if ($parts[0] != ".IPPcode20") {
            fprintf(STDERR, "Corrupted or missing header.");
            exit(21);
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
    fprintf(STDERR, "Other lexical or syntax error.");
    exit(23);
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
                    fprintf(STDERR, "Other lexical or syntax error.");
                    exit(23);
                }
                $parent->$arg = $str_match[1];
            break;
            case "int":
                $child = $parent->addChild("arg" . $num);
                $child->addAttribute("type", "int");
                $arg = "arg" . $num;
                if (!preg_match('/@(\-?[0-9]+)/', $symb, $str_match)) {
                    fprintf(STDERR, "Other lexical or syntax error.");
                    exit(23);
                }
                $parent->$arg = $str_match[1];
            break;
            case "nil":
                $child = $parent->addChild("arg" . $num);
                $child->addAttribute("type", "nil");
                $arg = "arg" . $num;
                if (!preg_match('/@(nil)/', $symb, $str_match)) {
                    fprintf(STDERR, "Other lexical or syntax error.");
                    exit(23);
                }
                $parent->$arg = "nil";
            break;
            default:
                fprintf(STDERR, "Other lexical or syntax error.");
                exit(23);
        }
    } else {
        fprintf(STDERR, "Other lexical or syntax error.");
        exit(23);
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
    fprintf(STDERR, "Other lexical or syntax error.");
    exit(23);
}