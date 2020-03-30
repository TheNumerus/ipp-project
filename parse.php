<?php

require 'error.php';

const ROOT = '<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode20"></program>';
const OPCODE_ARGS = [
    'RETURN' =>      [0],
    'PUSHFRAME' =>   [0],
    'POPFRAME' =>    [0],
    'CREATEFRAME' => [0],
    'BREAK' =>       [0],

    'DEFVAR' => [1, "var"],
    'POPS' =>   [1, "var"],
    'WRITE' =>  [1, "symbol"],
    'PUSHS' =>  [1, "symbol"],
    'EXIT' =>   [1, "symbol"],
    'DPRINT' => [1, "symbol"],
    'LABEL' =>  [1, "label"],
    'CALL' =>   [1, "label"],
    'JUMP' =>   [1, "label"],

    'MOVE' =>     [2, "var", "symbol"],
    'INT2CHAR' => [2, "var", "symbol"],
    'STRLEN' =>   [2, "var", "symbol"],
    'TYPE'=>      [2, "var", "symbol"],
    'NOT' =>      [2, "var", "symbol"],
    'READ' =>     [2, "var", "type"],

    'CONCAT' =>    [3, "var", "symbol", "symbol"],
    'GETCHAR' =>   [3, "var", "symbol", "symbol"],
    'SETCHAR' =>   [3, "var", "symbol", "symbol"],
    'ADD' =>       [3, "var", "symbol", "symbol"],
    'SUB' =>       [3, "var", "symbol", "symbol"],
    'MUL' =>       [3, "var", "symbol", "symbol"],
    'IDIV' =>      [3, "var", "symbol", "symbol"],
    'LT' =>        [3, "var", "symbol", "symbol"],
    'GT' =>        [3, "var", "symbol", "symbol"],
    'EQ' =>        [3, "var", "symbol", "symbol"],
    'AND' =>       [3, "var", "symbol", "symbol"],
    'OR' =>        [3, "var", "symbol", "symbol"],
    'STRI2INT' =>  [3, "var", "symbol", "symbol"],
    'JUMPIFNEQ' => [3, "label", "symbol", "symbol"],
    'JUMPIFEQ' =>  [3, "label", "symbol", "symbol"],
];

main();

function main() {
    global $argv;
    global $argc;

    $stats_opt;
    
    // parse arguments
    if ($argc == 2 && $argv[1] == "--help") {
        print_help();
        exit(0);
    } else {
        $stats_opt = StatsOpt::parse();
    }

    $xml = new SimpleXMLElement(ROOT);
    $first_line = true;

    $stats = new Stats();

    while($line = fgets(STDIN)) {
        // if comment is found, cut it, and cut whitespace on both sides
        if (preg_match('/(^[^#]*)(?=#)/', $line, $matches)) {
            $line = trim($matches[0]);
            $stats->comments++;
        } else {
            $line = trim($line);
        }
        
        // skip empty lines
        if (strlen($line) == 0) {
            continue;
        }

        // if line is comment only, then skip it
        if ($line[0] == '#') {
            $stats->comments++;
            continue;
        }

        // seperate line into parts divided by whitespace
        $parts = preg_split('/\s/', $line);
        $parts = array_values(array_filter($parts, 'strlen'));

        if ($first_line) {
            // handle header
            if ( strtolower($parts[0]) != ".ippcode20") {
                return_error(ERR_HEADER);
            }
            
            if (count($parts) != 1) {
                return_error(ERR_HEADER);
            }
            $first_line = false;
        } else {
            // create child node
            $child = $xml->addChild("instruction");
            $child->addAttribute("order", $stats->loc + 1);
            $child->addAttribute("opcode", strtoupper($parts[0]));

            // check if known opcode
            if (!array_key_exists(strtoupper($parts[0]), OPCODE_ARGS)) {
                return_error(ERR_OPCODE);
            }

            // check correct number of arguments
            if ((count($parts) - 1) != OPCODE_ARGS[strtoupper($parts[0])][0]) {
                return_error(ERR_OTHER);
            }

            $stats->loc++;

            // parse opcode and check for correctness
            for($i = 1; $i <= OPCODE_ARGS[strtoupper($parts[0])][0]; $i++) {
                switch (OPCODE_ARGS[strtoupper($parts[0])][$i]) {
                    case "var":
                        check_var($parts[$i], $child, $i);
                    break;
                    case "symbol":
                        check_symb($parts[$i], $child, $i);
                    break;
                    case "label":
                        check_label($parts[$i], $child, $i);
                    break;
                    case "type":
                        check_type($parts[$i], $child, $i);
                    break;
                    default:
                        return_error(ERR_INTERNAL);
                    break;
                }
            }

            // count special features
            switch ($parts[0]) {
                case 'LABEL':
                    $stats->labels++;
                break;
                case 'CALL':
                case 'JUMP':
                case 'RETURN':
                case 'JUMPIFNEQ':
                case 'JUMPIFEQ':
                    $stats->jumps++;
                break;
                default:
                break;
            }
        }
    }

    // write stats to file
    $stats->print($stats_opt);

    // write xml to stdout
    echo $xml->asXML();
}

// prints help
function print_help() {
    echo "IPPcode20 code analyzer (parse.php)\n\n";
    echo "Filter type script, loads IPPcode20 source file from standard input, checks lexical and syntax code correctness and writes XML program representation to standard output.\n\n";
    echo "Parameters:\n";
    echo "--help           - Prints script manual, exclusive with other arguments\n\n";
    echo "--stats=FILEPATH - Writes code stats to specified file, is used with:\n";
    echo "    --comments   - Number of comments in code\n";
    echo "    --jumps      - Number of jump instructions in code\n";
    echo "    --labels     - Number of labels in code\n";
    echo "    --loc        - Number of lines of code / instuctions\n\n";
    echo "Return codes:\n";
    echo " 0 - Success\n";
    echo "10 - Invalid argument or combnination of arguments\n";
    echo "12 - Unable to open output file\n";
    echo "21 - Corrupted or missing header in IPPcode20 source file\n";
    echo "22 - Corrupted or unknown opcode in IPPcode20 source file\n";
    echo "23 - Other lexical or syntax error in IPPcode20 source file\n";
    echo "99 - Internal error in the script";
}

function check_var(string $var, $parent, int $num) {
    //check correct variable format
    if (preg_match('/^(GF|TF|LF)@[_\-$&%*!?a-zA-Z][\-$&%*!?\w]*$/', $var)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "var");
        $arg = "arg" . $num;
        $parent->$arg = $var;
        return;
    }
    return_error(ERR_OTHER);
}

function check_symb(string $symb, $parent, int $num) {
    //symbol can be variable or constant
    if (preg_match('/^(GF|TF|LF)@/', $symb)) {
        check_var($symb, $parent, $num);
    } else if (preg_match('/^(int|bool|string|nil)@/', $symb, $matches)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", $matches[1]);
        $arg = "arg" . $num;
        switch ($matches[1]) {
            case "string":
                if (!preg_match('/@(([^\\s#@\\\\]|\\\\[0-9]{3})*)$/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
            break;
            case "bool":
                if (!preg_match('/@(true|false)$/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
            break;
            case "int":
                if (!preg_match('/@([\-\+]?[0-9]+)$/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
            break;
            case "nil":
                if (!preg_match('/@(nil)$/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
            break;
            default:
            return_error(ERR_OTHER);
        }
        $parent->$arg = $str_match[1];
    } else {
        return_error(ERR_OTHER);
    }
}

function check_label(string $label, $parent, int $num) {
    // label is same as var
    if (preg_match('/^[_\-$&%*!?a-zA-Z][\-$&%*!?\w]*$/', $label)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "label");
        $arg = "arg" . $num;
        $parent->$arg = $label;
        return;
    }
    return_error(ERR_OTHER);
}

function check_type(string $type, $parent, int $num) {
    if (preg_match('/^(string|int|bool)$/', $type)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "type");
        $arg = "arg" . $num;
        $parent->$arg = $type;
        return;
    }
    return_error(ERR_OTHER);
}

class Stats {
    public int $comments = 0;
    public int $loc = 0;
    public int $jumps = 0;
    public int $labels = 0;

    public function print(?StatsOpt $opt) {
        if ($opt == null) {
            return;
        }
        $file = fopen($opt->filepath, "w");
        if ($file) {
            foreach ($opt->options as $index => $value) {
                fprintf($file, "%d\n", $this->$value);
            }
        } else {
            return_error(ERR_OUTPUT);
        }
    }
}

class StatsOpt {
    public string $filepath;
    public array $options;

    public static function parse(): ?StatsOpt {
        global $argv;
        global $argc;
        if ($argc == 1) {
            return null;
        }
        if (preg_match("/^\-\-stats=(\S*)$/", $argv[1], $matches)) {
            if (strlen($matches[1]) == 0) {
                return_error(ERR_ARG);
            }
            $opt = new StatsOpt();
            $opt->filepath = $matches[1];
            $opt->options = [];
            for ($i = 2; $i < $argc; $i++) {
                if (preg_match("/^\-\-(loc|comments|jumps|labels)$/", $argv[$i], $arg_matches)) {
                    $opt->options[] = $arg_matches[1];
                } else {
                    return_error(ERR_ARG);
                }
            }
            return $opt;
        } else if ($argc == 1) {
            return null;
        } else {
            return_error(ERR_ARG);
        }
    }
}
