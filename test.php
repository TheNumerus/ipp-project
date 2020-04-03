<?php

require 'error.php';
require 'html_strings.php';

class Variant {
    const BOTH = 0;
    const PARSE_ONLY = 1;
    const INT_ONLY = 2;
}

class Result {
    const PASSED = 0;
    const WRONG_RC = 1;
    const WRONG_OUT = 2;
}

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

    //check if not running on merlin and swap commands
    $env = fopen("env" ,"r") != false;
    if ($env) {
        Commands::$php = "php";
        Commands::$python = "python";
    }

    $opts = TestOpts::parse($argc, $argv);

    // search for tests
    if ($opts->recursive_search) {
        $files = [];
        test_scan_recursive($opts->test_path, $files);
    } else {
        $files = test_scan($opts->test_path);
    }
    
    $tests = [];
    
    foreach ($files as $input) {
        fprintf(STDERR, "running %s", $input);
        $test_ressult = run_test($input, $opts);
        $tests[] = $test_ressult;
        if ($test_ressult->result != Result::PASSED) {
            fprintf(STDERR, "...\e[0;31mFAILED\e[0;0;1m\n");
        } else {
            fprintf(STDERR, "...\e[0;32mPASSED\e[0;0;1m\n");
        }
    }
    
    print_html($opts, $tests);
}

function test_scan(string $path) {
    // this could be nice functional three-liner, but php is php...

    // remove root and parent folder
    $dir_entries = array_diff(scandir($path), ['..', '.']);

    // filter subdirectories and non-source files
    $dir_entries = array_filter($dir_entries, function ($val) use ($path) {
        return !is_dir($path."/".$val) && preg_match('/.+\.src$/', $val);
    });

    // why does array_map have arguments in different order than array_filter?
    // add path to filename
    $dir_entries = array_map(function ($val) use ($path) {
        return $path."/".$val;
    }, $dir_entries);

    // fix indices
    return array_values($dir_entries);
}

function test_scan_recursive(string $path, &$tests) {
    // remove root and parent folder
    $dir_entries = array_diff(scandir($path), ['..', '.']);

    // filter subdirectories and non-source files
    $dir_entries = array_filter($dir_entries, function ($val) use ($path) {
        return is_dir($path."/".$val);
    });

    // add path to filename
    $dir_entries = array_map(function ($val) use ($path) {
        return $path."/".$val;
    }, $dir_entries);

    foreach ($dir_entries as $dir_entry) {
        test_scan_recursive($dir_entry, $tests);
    }

    $tests = array_merge($tests, test_scan($path));
}

function run_test(string $test_path, TestOpts $opts) :TestResult {
    $input_path = preg_replace('/src$/', 'in', $test_path);
    $output_path = preg_replace('/src$/', 'out', $test_path);
    $rc_path = preg_replace('/src$/', 'rc', $test_path);

    // create files if missing
    if (!file_exists($input_path)) {
        $file = fopen($input_path, 'w');
        if ($file == null) {
            return_error(Err::INPUT);
        }
    }
    if (!file_exists($output_path)) {
        $file = fopen($output_path, 'w');
        if ($file == null) {
            return_error(Err::INPUT);
        }
    }
    if (!file_exists($rc_path)) {
        $file = fopen($rc_path, 'w');
        if ($file == null) {
            return_error(Err::INPUT);
        }
        fprintf($file, "0");
    }

    $rc_file = fopen($rc_path, 'r');
    $rc = fgets($rc_file);
    if ($rc === false) {
        return_error(Err::INPUT);
    }
    $rc = intval($rc);

    $test_result = new TestResult();
    $test_result->name = $test_path;
    $test_result->expected_rc = $rc;

    if ($opts->variant == Variant::BOTH) {
        $parse_result = Commands::exec_parse($opts, $test_path);
        $test_result->got_rc = $parse_result->ret_val;
        if ($parse_result->ret_val != $rc) {
            $test_result->result = Result::WRONG_RC;
            return $test_result;
        }

        // check if test was supposed to fail
        if ($parse_result->ret_val != 0) {
            return $test_result;
        }

        // create temp file with generated xml
        $temp_result_path = preg_replace('/src$/', 'temp', $test_path);
        $temp_file = fopen($temp_result_path, 'w');
        fwrite($temp_file, $parse_result->output);

        $interpret_result = Commands::exec_interpret($opts, $temp_result_path, $input_path);
        $test_result->got_rc = $interpret_result->ret_val;
        if ($interpret_result->ret_val != $rc) {
            $test_result->result = Result::WRONG_RC;
            return $test_result;
        }

        // check if test was supposed to fail
        if ($interpret_result->ret_val != 0) {
            return $test_result;
        }

        // rewrite xml with data to diff
        ftruncate($temp_file, 0);
        rewind($temp_file);
        fwrite($temp_file, $interpret_result->output);

        $diff_result = Commands::exec_diff($output_path, $temp_result_path);

        //clean up
        unlink($temp_result_path);

        if ($diff_result->ret_val != 0) {
            $test_result->result = Result::WRONG_OUT;
            return $test_result;
        }
    } else if ($opts->variant == Variant::INT_ONLY) {
        $interpret_result = Commands::exec_interpret($opts, $test_path, $input_path);
        $test_result->got_rc = $interpret_result->ret_val;
        if ($interpret_result->ret_val != $rc) {
            $test_result->result = Result::WRONG_RC;
            return $test_result;
        }

        // check if test was supposed to fail
        if ($interpret_result->ret_val != 0) {
            return $test_result;
        }

        // create temp file with output
        $temp_result_path = preg_replace('/src$/', 'temp', $test_path);
        $temp_file = fopen($temp_result_path, 'w');
        fwrite($temp_file, $interpret_result->output);

        $diff_result = Commands::exec_diff($output_path, $temp_result_path);

        //clean up
        unlink($temp_result_path);

        if ($diff_result->ret_val != 0) {
            $test_result->result = Result::WRONG_OUT;
            return $test_result;
        }
    } else {
        $result = Commands::exec_parse($opts, $test_path);
        $test_result->got_rc = $result->ret_val;
        if ($result->ret_val != $rc) {
            $test_result->result = Result::WRONG_RC;
            return $test_result;
        }

        // check if test was supposed to fail
        if ($result->ret_val != 0) {
            return $test_result;
        }

        // create temp file with generated xml
        $temp_result_path = preg_replace('/src$/', 'temp', $test_path);
        $temp_file = fopen($temp_result_path, 'w');
        fwrite($temp_file, $result->output);

        $diff_result = Commands::exec_xmldiff($opts, $output_path, $temp_result_path);

        // clean after jexamxml if needed
        if (file_exists($output_path.".log")) {
            unlink($output_path.".log");
        }
        unlink($temp_result_path);

        if ($diff_result->ret_val != 0) {
            $test_result->result = Result::WRONG_OUT;
            return $test_result;
        }
    }
    return $test_result;
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

function print_html(TestOpts $opts, array $tests) {
    global $html_head;
    global $html_end;
    global $html_table_start;
    
    // head
    echo $html_head;
    echo "<p>Testing variant:  ";
    switch ($opts->variant) {
        case Variant::BOTH:
            echo "Both";
            break;
        case Variant::PARSE_ONLY:
            echo "Parser";
            break;
        default:
            echo "Interpret";
            // must be int only
            break;
    }
    echo "</p>";
    
    echo "<div class='hor'>";
    
    echo "<p> Tests passed:   ";
    $count = count(array_filter($tests, function (TestResult $test) {
        return $test->result == Result::PASSED;
    }));
    $count_total = count($tests);
    $percent = $count / $count_total * 100;
    
    echo "{$count}/{$count_total}  ({$percent}%)</p>";
    
    // filter button
    echo "
        <p><input type='checkbox' id='filter' onclick='filter()'> Filter passed tests</p>
    ";
    
    echo "</div>";
    
    //now print table with tests
    echo $html_table_start;
    foreach ($tests as $test) {
        // color
        switch ($test->result) {
            case Result::PASSED:
                echo "<tr class='row_passed'><td class='table_passed'/>";
                break;
            default:
                echo "<tr><td class='table_failed'/>";
                break;
        }
        
        // result
        echo "<td>";
        switch ($test->result) {
            case Result::PASSED:
                echo "Passed";
                break;
            case Result::WRONG_RC:
                echo "Wrong return code";
                break;
            case Result::WRONG_OUT:
                echo "Wrong output";
                break;
        }
        echo "</td>";
        
        // name
        echo "<td>{$test->name}</td>";
        
        // expected RC
        echo "<td align='center'>{$test->expected_rc}</td>";
        
        // real RC
        echo "<td align='center'>{$test->got_rc}</td>";
        echo "</tr>";
    }
    echo "</table>";
    echo $html_end;
}

class Commands {
    public static string $python = "python3.8";
    public static string $php = "php7.4";
    private static array $spec = [
        0 => array("pipe", "r"),
        1 => array("pipe", "w"),
        2 => array("pipe", "w")
    ];

    public static function exec_interpret(TestOpts $opts, String $source, String $input) :ExecResult {
        $command = Commands::$python." ".$opts->interpret_path." --source=".$source." --input=".$input;
        Commands::exec($command, $rc, $output);
        return ExecResult::new($rc, $output);
    }

    public static function exec_parse(TestOpts $opts, String $source) :ExecResult {
        $command = Commands::$php." ".$opts->parser_path." <".$source;
        Commands::exec($command, $rc, $output);
        return ExecResult::new($rc, $output);
    }

    public static function exec_diff(String $expected, String $got): ExecResult {
        $command = "diff ".$expected." ".$got;
        Commands::exec($command, $rc, $output);
        return ExecResult::new($rc, $output);
    }

    public static function exec_xmldiff(TestOpts $opts, String $expected, String $got): ExecResult {
        $command = "java -jar ".$opts->xml_test_path." ".$expected." ".$got;
        Commands::exec($command, $rc, $output);
        return ExecResult::new($rc, $output);
    }
    
    private static function exec(String $command, &$rc, &$output) {
        $process = proc_open($command, Commands::$spec, $pipes);
        $output = stream_get_contents($pipes[1]);
        fclose($pipes[0]);
        fclose($pipes[1]);
        fclose($pipes[2]);
        $rc = proc_close($process);
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

class TestResult {
    public string $name = "";
    public int $result = Result::PASSED;
    public int $expected_rc;
    public int $got_rc;
}

class TestOpts {
    public string $test_path = ".";
    public string $parser_path = "parse.php";
    public string $interpret_path = "interpret.py";
    public string $xml_test_path = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    public bool $recursive_search = false;
    public int $variant = Variant::BOTH;

    public static function parse(int $argc, array $argv): ?TestOpts {
        $opts = new TestOpts();

        $int_only = false;
        $parse_only = false;
        foreach (array_slice($argv, 1) as $arg) {
            // parse arg, split into groups
            $result = preg_match( '/^-{1,2}([a-zA-Z-]*)($|=(["\'\\S.\/]+))$/', $arg, $matches);

            // discard invalid arguments
            if ($result == 0) {
                return_error(Err::ARG);
            }

            // discard unknown arguments
            if (!array_key_exists($matches[1], ARG)) {
                return_error(Err::ARG);
            }

            // check if arg should have path attached
            if (ARG[$matches[1]] != (strlen($matches[2]) != 0)) {
                return_error(Err::ARG);
            }

            // if path is specified, it must be valid
            if (ARG[$matches[1]] && !file_exists($matches[3])) {
                return_error(Err::INPUT);
            }

            switch ($matches[1]) {
                case "help":
                    // help is exclusive with everything else
                    if ($argc != 2) {
                        return_error(Err::ARG);
                    }
                    print_help();
                    die();
                break;
                case "directory":
                    // check if provided path is a folder
                    if (!is_dir($matches[3])) {
                        return_error(Err::ARG);
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
                        return_error(Err::ARG);
                    }
                    $opts->parser_path = $matches[3];
                    break;
                case "int-script":
                    // check exclusivity
                    if ($parse_only) {
                        return_error(Err::ARG);
                    }
                    $opts->interpret_path = $matches[3];
                    break;
                case "parse-only":
                    // check exclusivity
                    if ($int_only) {
                        return_error(Err::ARG);
                    }
                    $parse_only = true;
                    $opts->variant = Variant::PARSE_ONLY;
                    break;
                case "int-only":
                    // check exclusivity
                    if ($parse_only) {
                        return_error(Err::ARG);
                    }
                    $int_only = true;
                    $opts->variant = Variant::INT_ONLY;
                    break;
                default:
                    // should not happen
                    return_error(Err::INTERNAL);
                    break;
            }
        }
        return $opts;
    }
}
