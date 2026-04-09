<?php
header('Content-Type: application/json; charset=utf-8');

$host = "192.168.2.20";
$db   = "qlsv_system";
$user = "webuser";
$pass = "haonn";

$conn = new mysqli($host, $user, $pass, $db);
if ($conn->connect_error) {
  http_response_code(500);
  echo json_encode(["ok"=>false, "error"=>$conn->connect_error]);
  exit;
}
$conn->set_charset("utf8mb4");

$res = $conn->query("SHOW TABLES");
$tables = [];
while ($row = $res->fetch_array()) { $tables[] = $row[0]; }

echo json_encode(["ok"=>true, "tables"=>$tables]);
