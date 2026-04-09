<?php
header("Content-Type: application/json; charset=utf-8");
require_once __DIR__ . "/db.php";
require_once __DIR__ . "/auth.php";

require_login(); // ai đăng nhập cũng xem được list demo

$limit = isset($_GET["limit"]) ? max(1, min(200, (int)$_GET["limit"])) : 50;

$sql = "SELECT student_id, student_code, user_id, class_id, date_of_birth, gender, phone, address, enrollment_date, status
        FROM students
        ORDER BY student_id DESC
        LIMIT ?";
$stmt = $mysqli->prepare($sql);
$stmt->bind_param("i", $limit);
$stmt->execute();
$res = $stmt->get_result();

$rows = [];
while($r = $res->fetch_assoc()) $rows[] = $r;

echo json_encode(["ok"=>true,"count"=>count($rows),"data"=>$rows], JSON_UNESCAPED_UNICODE);
