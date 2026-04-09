<?php
// /admin/dashboard.php
session_start();
if (!isset($_SESSION['user'])) {
  header("Location: /index.php");
  exit;
}
if (($_SESSION['user']['role'] ?? '') !== 'ADMIN') {
  http_response_code(403);
  echo "403 Forbidden";
  exit;
}

require __DIR__ . "/../inc/layout.php";

app_header("ADMIN • Dashboard", "/admin/dashboard.php");
$u = $_SESSION["user"];
?>
<div class="grid">
  <div class="card">
    <h2><i class="fa-solid fa-gauge"></i> Tổng quan</h2>
    <p>Xin chào <b><?= h($u["full_name"]) ?></b> — quyền <b>ADMIN</b>.</p>
    <p>ADMIN có quyền đầy đủ: quản lý sinh viên, xem enrollments/điểm, (mở rộng: quản lý môn/lớp/giảng viên).</p>
    <div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">
      <a class="btnx primary" href="/admin/students.php"><i class="fa-solid fa-users"></i> Sinh viên (CRUD)</a>
      <a class="btnx" href="/admin/enrollments.php"><i class="fa-solid fa-clipboard-list"></i> Enrollments/Điểm</a>
    </div>
  </div>

  <div class="card">
    <h2><i class="fa-solid fa-shield-halved"></i> RBAC</h2>
    <div class="kv"><b>/admin/*</b><span>ADMIN only</span></div>
    <div class="kv"><b>/lecturer/*</b><span>LECTURER only</span></div>
    <div class="kv"><b>/student/*</b><span>STUDENT only</span></div>
    <div class="kv"><b>Session</b><span>Chưa login → redirect về login</span></div>
  </div>


</div>
<?php app_footer(); ?>