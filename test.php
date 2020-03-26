<?php

const VAR_BOTH = 0;
const VAR_PARSE_ONLY = 1;
const VAR_INT_ONLY = 2;

main();

function main() {
    global $argc;
    global $argv;
    foreach ($argv as $arg) {
        echo $arg . "\n";
    }

    $opts = TestOpts::parse($argc, $argv);

    var_dump($opts);

    exec("python interpret.py");
}

class TestVariant {
    public static int $ParseOnly = 0;
}

class TestOpts {
    public ?String $test_path = ".";
    public ?String $parser_path = "parse.php";
    public ?String $interpret_path = "interpret.py";
    public ?String $xml_test_path = "/pub/courses/ipp/jexamxml/jexamxml.jar";
    public bool $recursive_search = false;
    public int $variant = VAR_BOTH;

    public static function parse(int $argc, array $argv): ?TestOpts {
        $opts = new TestOpts();
        return $opts;
    }
}