<?php
require_once __DIR__ . "/../api/auth.php";
require_role("STUDENT");
require_once __DIR__ . "/../inc/layout.php";

app_header("STUDENT • Dashboard", "/student/dashboard.php");
$u = $_SESSION["user"];
?>
<div class="grid">
  <div class="card">
    <h2>Xin chào</h2>
    <p><b><?= htmlspecialchars($u["full_name"] ?: $u["username"]) ?></b></p>
    <p>Quyền: <span class="badge ok">STUDENT</span></p>

    <div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">
      <a class="btnx primary" href="/student/schedule.php"><i class="fa-solid fa-calendar-check"></i> Lịch học</a>
      <a class="btnx" href="/student/grades.php"><i class="fa-solid fa-chart-column"></i> Xem điểm</a>
    </div>
  </div>

  <div class="card">
    <h2>Thông tin</h2>
    <p>• Lịch học và điểm hiển thị gọn, dễ đọc</p>
    <p>• Nối DB thật mình làm tiếp theo schema bạn</p>
  </div>
</div>
<?php app_footer(); ?>
