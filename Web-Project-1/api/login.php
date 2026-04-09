<?php
header("Content-Type: application/json; charset=utf-8");
require_once __DIR__ . "/db.php";
require_once __DIR__ . "/auth.php";

if (session_status() === PHP_SESSION_NONE) session_start();

$raw = file_get_contents("php://input");
$data = json_decode($raw, true);
if (!is_array($data)) $data = $_POST;

$username = trim((string)($data["username"] ?? ""));
$password = (string)($data["password"] ?? "");
$role     = trim((string)($data["role"] ?? ""));

if ($username === "" || $password === "" || $role === "") {
  http_response_code(400);
  echo json_encode(["ok"=>false,"error"=>"MISSING_FIELDS","message"=>"Thiếu username/password/role"], JSON_UNESCAPED_UNICODE);
  exit;
}

/*
  Mật khẩu trong DB của bạn kiểu:
  SHA2(CONCAT(password, username, '_salt'),256)
*/
$sql = "
SELECT u.user_id, u.username, u.full_name, u.role_id
FROM users u
WHERE u.username = ?
  AND u.password = SHA2(CONCAT(?, ?, '_salt'), 256)
LIMIT 1
";
$stmt = $mysqli->prepare($sql);
$stmt->bind_param("sss", $username, $password, $username);
$stmt->execute();
$res = $stmt->get_result();
$row = $res->fetch_assoc();

if (!$row) {
  http_response_code(401);
  echo json_encode(["ok"=>false,"error"=>"INVALID_LOGIN","message"=>"Sai tài khoản hoặc mật khẩu"], JSON_UNESCAPED_UNICODE);
  exit;
}

$role_code = role_code_from_id($row["role_id"]);
if ($role_code !== $role) {
  http_response_code(403);
  echo json_encode(["ok"=>false,"error"=>"ROLE_MISMATCH","message"=>"Vai trò không đúng với tài khoản"], JSON_UNESCAPED_UNICODE);
  exit;
}

$_SESSION["user"] = [
  "user_id"   => (int)$row["user_id"],
  "username"  => $row["username"],
  "full_name" => $row["full_name"],
  "role_id"   => (int)$row["role_id"],
  "role"      => $role_code,
];

$redirect = "/index.php";
if ($role_code === "ADMIN")    $redirect = "/admin/dashboard.php";
if ($role_code === "LECTURER") $redirect = "/lecturer/dashboard.php";
if ($role_code === "STUDENT")  $redirect = "/student/dashboard.php";

echo json_encode([
  "ok"=>true,
  "message"=>"Đăng nhập thành công",
  "user"=>$_SESSION["user"],
  "redirect"=>$redirect
], JSON_UNESCAPED_UNICODE);
