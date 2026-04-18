<?php
mysqli_report(MYSQLI_REPORT_ERROR | MYSQLI_REPORT_STRICT);

$db_host = "p1-dev-apse1-db.cvmygmiqa7t4.ap-southeast-1.rds.amazonaws.com";
$db_port = 3306;

$mysqli = new mysqli($db_host, $db_user, $db_pass, $db_name, $db_port);
$mysqli->set_charset("utf8mb4");

function db_connect()
{
    global $db_host, $db_user, $db_pass, $db_name, $db_port;
    $conn = new mysqli($db_host, $db_user, $db_pass, $db_name, $db_port);
    $conn->set_charset("utf8mb4");
    return $conn;
}
