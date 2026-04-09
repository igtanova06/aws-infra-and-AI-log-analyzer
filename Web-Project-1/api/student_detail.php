<?php
header("Content-Type: application/json; charset=utf-8");
require_once __DIR__ . "/db.php";
require_once __DIR__ . "/auth.php";

require_login();

$id = isset($_GET["id"]) ? (int)$_GET["id"] : 0;
if ($id <= 0) {
  http_response_code(400);
  echo json_encode(["ok"=>false,"error"=>"BAD_ID","message"=>"Thiếu id"], JSON_UNESCAPED_UNICODE);
  exit;
}

$sql = "SELECT student_id, student_code, user_id, class_id, date_of_birth, gender, phone, address, enrollment_date, status
        FROM students WHERE student_id = ? LIMIT 1";
$stmt = $mysqli->prepare($sql);
$stmt->bind_param("i", $id);
$stmt->execute();
$res = $stmt->get_result();
$row = $res->fetch_assoc();

if (!$row) {
  http_response_code(404);
  echo json_encode(["ok"=>false,"error"=>"NOT_FOUND","message"=>"Không tìm thấy sinh viên"], JSON_UNESCAPED_UNICODE);
  exit;
}

echo json_encode(["ok"=>true,"data"=>$row], JSON_UNESCAPED_UNICODE);
