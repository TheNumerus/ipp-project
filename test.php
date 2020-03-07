<?php

main();

function main() {
    global $argc;
    global $argv;
    exec("python interpret.py");
    echo "TEST";
}

class TestOpts {

}