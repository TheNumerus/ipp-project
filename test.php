<?php

require 'error.php';

const VAR_BOTH = 0;
const VAR_PARSE_ONLY = 1;
const VAR_INT_ONLY = 2;

const ARG = [
    "help" => false,
    "directory" => true,
    "recursive" => false,
    "parse-script" => true,
    "int-script" => true,
    "parse-only" => false,
    "int-only" => false,
    "jexamxml" => true
];

main();

function main() {
    global $argc;
    global $argv;
    $commands = new Commands();

    //check if not running on merlin and swap commands
    $env = fopen("env" ,"r") != false;
    if ($env) {
        $commands->php = "php";
        $commands->python = "python";
    }

    $opts = TestOpts::parse($argc, $argv);

    var_dump($opts);

    if ($opts->recursive_search) {
        // TODO
    } else {
        // scan folder, skip this folder and parent folder
        $files = test_scan($opts->test_path);
        var_dump($files);
        foreach ($files as $input) {
            run_test($input, $opts);
        }
    }

    exec("python interpret.py");
}

function test_scan(string $path) {
    return array_values(array_filter(array_diff(scandir($path), ['..', '.']), function ($val) use ($path) {
        echo $path."/".$val;
        return !is_dir($path."/".$val) && preg_match('/.+\.src$/', $val);
    }));
}

function run_test(string $test_path, TestOpts $opts) {

}

// prints help
function print_help() {
    echo "IPPcode20 tester (test.php)\n\n";
    echo "Filter type script, runs tests on parser and interpreter.\n\n";
    echo "Parameters:\n";
    echo "--help                  - Prints script manual, exclusive with other arguments\n";
    echo "--directory=PATH        - Check tests in this directory\n";
    echo "--recursive             - Tests will be searched recursively\n";
    echo "--parse-script=FILEPATH - Path to parser\n";
    echo "--int-script=FILEPATH   - Path to interpret\n";
    echo "--parse-only            - Only test parser, cannot be used with --int-* args\n";
    echo "--int-only              - Only test interpret, cannot be used with --parse-* args\n";
    echo "--jexamxml=FILEPATH     - Path to xml tester\n\n";
    echo "Return codes:\n";
    echo " 0 - Success\n";
    echo "10 - Invalid argument or combnination of arguments\n";
    echo "11 - Unable to open input file\n";
    echo "12 - Unable to open output file\n";
    echo "99 - Internal error in the script";
}

class Commands {
    public string $python = "python3.8";
    public string $php = "php7.4";

    public static function exec_python() :ExecResult{
        // TODO
    }

    public static function exec_php() :ExecResult{
        // TODO
    }
}

class ExecResult {
    public int $ret_val = 0;
    public string $output = "";

    public static function new(int $ret_val, String $output) {
        $e = new ExecResult();
        $e->output = $output;
        $e->ret_val = $ret_val;
        return $e;
    }
}

class TestVariant {
    public static int $ParseOnly = 0;
}

class TestOpts {
    public string $test_path = ".";
    public string $parser_path = "parse.php";
    public string $interpret_path = "interpret.py";
    public string $xml_test_path = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    public bool $recursive_search = false;
    public int $variant = VAR_BOTH;

    public static function parse(int $argc, array $argv): ?TestOpts {
        $opts = new TestOpts();

        $int_only = false;
        $parse_only = false;
        foreach (array_slice($argv, 1) as $arg) {
            // parse arg, split into groups
            $result = preg_match( '/^-{1,2}([a-zA-Z-]*)($|=(["\'\\S.\/]+))$/', $arg, $matches);

            // discard invalid arguments
            if ($result == 0) {
                return_error(ERR_ARG);
            }

            // discard unknown arguments
            if (!array_key_exists($matches[1], ARG)) {
                return_error(ERR_ARG);
            }

            // check if arg should have path attached
            if (ARG[$matches[1]] != (strlen($matches[2]) != 0)) {
                return_error(ERR_ARG);
            }

            // if path is specified, it must be valid
            if (ARG[$matches[1]] && !file_exists($matches[3])) {
                return_error(ERR_INPUT);
            }

            switch ($matches[1]) {
                case "help":
                    // help is exclusive with everything else
                    if ($argc != 2) {
                        return_error(ERR_ARG);
                    }
                    print_help();
                    die();
                break;
                case "directory":
                    // check if provided path is a folder
                    if (!is_dir($matches[3])) {
                        return_error(ERR_ARG);
                    }
                    $opts->test_path = $matches[3];
                    break;
                case "recursive":
                    $opts->recursive_search = true;
                    break;
                case "jexamxml":
                    $opts->xml_test_path = $matches[3];
                    break;
                case "parse-script":
                    // check exclusivity
                    if ($int_only) {
                        return_error(ERR_ARG);
                    }
                    $opts->parser_path = $matches[3];
                    break;
                case "int-script":
                    // check exclusivity
                    if ($parse_only) {
                        return_error(ERR_ARG);
                    }
                    $opts->interpret_path = $matches[3];
                    break;
                case "parse-only":
                    // check exclusivity
                    if ($int_only) {
                        return_error(ERR_ARG);
                    }
                    $parse_only = true;
                    $opts->variant = VAR_PARSE_ONLY;
                    break;
                case "int-only":
                    // check exclusivity
                    if ($parse_only) {
                        return_error(ERR_ARG);
                    }
                    $int_only = true;
                    $opts->variant = VAR_INT_ONLY;
                    break;
                default:
                    // should not happen
                    return_error(ERR_INTERNAL);
                    break;
            }
        }
        return $opts;
    }
}
