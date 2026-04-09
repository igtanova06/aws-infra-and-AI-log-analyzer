<?php
require_once __DIR__ . "/../api/auth.php";
require_role("LECTURER");
require_once __DIR__ . "/../inc/layout.php";

app_header("LECTURER • Dashboard", "/lecturer/dashboard.php");
$u = $_SESSION["user"];
?>
<div class="grid">
  <div class="card">
    <h2>Chào mừng</h2>
    <p>Xin chào <b><?= htmlspecialchars($u["full_name"] ?: $u["username"]) ?></b></p>
    <p>Quyền: <span class="badge ok">LECTURER</span></p>

    <div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">
      <a class="btnx primary" href="/lecturer/teaching.php"><i class="fa-solid fa-calendar-days"></i> Lịch dạy</a>
      <a class="btnx" href="/lecturer/grading.php"><i class="fa-solid fa-pen-to-square"></i> Chấm điểm</a>
    </div>
  </div>

  <div class="card">
    <h2>Gợi ý</h2>
    <p>• Lịch dạy hiển thị gọn, có bảng scroll ngang</p>
    <p>• Chấm điểm: demo UI, muốn nối DB mình làm tiếp</p>
  </div>
</div>
<?php app_footer(); ?>

