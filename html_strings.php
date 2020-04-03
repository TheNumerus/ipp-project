<?php

$style = "
<style>

:root {
    --fg-color:#2e3440;
    --green:#a3be8c;
    --red:#bf616a;
}

body {
    font-family: sans-serif;
    background-color: #ECEFF4;
    color: var(--fg-color);
    display: flex;
    justify-content:center; 
}

h1 {
    font-weight: 500;
}

tr:nth-child(even) {
    background-color: #d8dee9;
}

thead {
    border-bottom: 2px solid var(--fg-color);
}

table {
    border-collapse: collapse;
    margin-top: 20px;
    width: 100%;
}

td, th {
    padding: 2px 4px;
}

.table_passed {
    width: 20px;
    background-color: var(--green);
}

.table_failed {
    width: 20px;
    background-color: var(--red);
}

.hor {
    display: flex;
    justify-content: space-between;
}

p {
    margin: 6px 0;
}
</style>
";

$script = "
<script>
// reset after page reload
window.onload = () => {
    document.getElementById('filter').checked = false
}

function filter() {
    let checkbox = document.getElementById('filter').checked
    let visibility;
    if (checkbox) {
        visibility = 'collapse'
    } else {
        visibility = 'visible'
    }
    for (const o of document.querySelectorAll('.row_passed')) {
        o.style.visibility = visibility
    }
}
</script>
";

$html_head = "
<!doctype html>
<html lang='en'>
<head>
<title>IPPcode20 test results</title>
<meta name='viewport' content='width=device-width, initial-scale=1.0'>
<meta charset='UTF-8'/>
{$style}
{$script}
</head>
<body>
<div class='container'>
<h1>IPPcode20 test results</h1>
";


$html_end = "
</div>
</body>
</html>
";


$html_table_start = "
<table>
<thead>
<tr>
<th>✔️</th>
<th>Result</th>
<th>Test name</th>
<th>Expected RC</th>
<th>Test RC</th>
</tr>
</thead>
";