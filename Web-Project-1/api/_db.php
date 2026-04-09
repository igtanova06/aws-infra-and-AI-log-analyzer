<?php
// DB server (máy database)
$DB_HOST = "192.168.2.20";
$DB_NAME = "qlsv_system";
$DB_USER = "webuser";
$DB_PASS = "haonn"; // mật khẩu user webuser
$DB_PORT = 3306;

$mysqli = new mysqli($DB_HOST, $DB_USER, $DB_PASS, $DB_NAME, $DB_PORT);
if ($mysqli->connect_errno) {
  http_response_code(500);
  header("Content-Type: application/json; charset=utf-8");
  echo json_encode(["ok"=>false, "error"=>"DB_CONNECT_FAILED", "detail"=>$mysqli->connect_error], JSON_UNESCAPED_UNICODE);
  exit;
}
$mysqli->set_charset("utf8mb4");
