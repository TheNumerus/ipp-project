<?php

const ROOT = '<?xml version="1.0" encoding="UTF-8"?><program language="IPPcode20"></program>';
const ERR_ARG = 10;
const ERR_OUTPUT = 12;
const ERR_HEADER = 21;
const ERR_OPCODE = 22;
const ERR_OTHER = 23;

main();

function main() {
    global $argv;
    global $argc;

    $stats_opt;
    
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
        $matches = [];
        if (preg_match('/(.*)(?=#)/', $line, $matches)) {
            $line = trim($matches[0]);
            $stats->comments++;
        } else {
            $line = trim($line);
        }
        
        if (strlen($line) == 0) {
            continue;
        }

        if ($line[0] == '#') {
            $stats->comments++;
            continue;
        }

        $parts = preg_split('/\s/', $line);
        $parts = array_values(array_filter($parts, function ($item) {
            return strlen($item) != 0;
        }));

        if (!$first_line) {
            $child = $xml->addChild("instruction");
            $child->addAttribute("order", $stats->loc + 1);
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
                    $stats->jumps++;
                break;
                case 'LABEL':
                    check_label($parts[1], $child, 1);
                    if (count($parts) != 2) {
                        return_error(ERR_OPCODE);
                    }
                    $stats->labels++;
                break;
                case 'CALL':
                case 'JUMP':
                    check_label($parts[1], $child, 1);
                    if (count($parts) != 2) {
                        return_error(ERR_OPCODE);
                    }
                    $stats->jumps++;
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
                case 'BREAK':
                    if (count($parts) != 1) {
                        return_error(ERR_OPCODE);
                    }
                break;
                case 'RETURN':
                    if (count($parts) != 1) {
                        return_error(ERR_OPCODE);
                    }
                    $stats->jumps++;
                break;
                default:
                    return_error(ERR_OPCODE);
            }
            
            $child->addAttribute("opcode", $parts[0]);
            $stats->loc++;
        } else {
            if ($parts[0] != ".IPPcode20") {
                return_error(ERR_HEADER);
            }
            $first_line = false;
        }
    }

    $stats->print($stats_opt);

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
}

function check_var(string $var, $parent, int $num) {
    if (preg_match('/^(GF|TF|LF)@[_\-$&%*!?a-zA-Z][_\-$&%*!?\w]*/', $var)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", "var");
        $arg = "arg" . $num;
        $parent->$arg = $var;
        return;
    }
    return_error(ERR_OTHER);
}

function check_symb(string $symb, $parent, int $num) {
    if (preg_match('/^(GF|TF|LF)@/', $symb)) {
        check_var($symb, $parent, $num);
    } else if (preg_match('/^(int|bool|string|nil)@/', $symb, $matches)) {
        $child = $parent->addChild("arg" . $num);
        $child->addAttribute("type", $matches[1]);
        $arg = "arg" . $num;
        switch ($matches[1]) {
            case "string":
                preg_match('/@([\S]*)/', $symb, $str_match);
                $parent->$arg = $str_match[1];
            break;
            case "bool":
                if (!preg_match('/@(true|false)$/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
                $parent->$arg = $str_match[1];
            break;
            case "int":
                if (!preg_match('/@(\-?[0-9]+)/', $symb, $str_match)) {
                    return_error(ERR_OTHER);
                }
                $parent->$arg = $str_match[1];
            break;
            case "nil":
                if (!preg_match('/@(nil)$/', $symb, $str_match)) {
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

function check_label(string $label, $parent, int $num) {
    if (preg_match('/^[_\-$&%*!?a-zA-Z][_\-$&%*!?\w]*/', $label)) {
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

function return_error(int $err) {
    switch ($err) {
        case ERR_ARG:
            fprintf(STDERR, "Invalid argument or combnination of arguments.");
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
            exit(99);
    }
    exit($err);
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
