<?php
require __DIR__ . "/../api/auth.php";
require_role("ADMIN");
require __DIR__ . "/../api/db.php";
require __DIR__ . "/../inc/layout.php";

$id = (int)($_GET["id"] ?? 0);
if ($id <= 0) { app_header("ADMIN • Student Detail",""); echo '<div class="card" style="margin-top:14px;"><div class="alert">Thiếu id</div></div>'; app_footer(); exit; }

$stmt = $mysqli->prepare("SELECT * FROM students WHERE student_id=? LIMIT 1");
$stmt->bind_param("i", $id);
$stmt->execute();
$row = $stmt->get_result()->fetch_assoc();

if (!$row) { app_header("ADMIN • Student Detail",""); echo '<div class="card" style="margin-top:14px;"><div class="alert">Không tìm thấy</div></div>'; app_footer(); exit; }

app_header("ADMIN • Chi tiết sinh viên", "/admin/students.php");
?>
<div class="card" style="margin-top:14px;">
  <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;">
    <div>
      <h2><i class="fa-solid fa-id-card"></i> <?= h2($row["student_code"] ?? ("SV#".$id)) ?></h2>
      <p>ID: <?= (int)$row["student_id"] ?></p>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <a class="btnx" href="/admin/students.php"><i class="fa-solid fa-arrow-left"></i> Back</a>
      <a class="btnx" href="/admin/enrollments.php?student_id=<?= (int)$row["student_id"] ?>"><i class="fa-solid fa-clipboard-list"></i> Enrollments/Điểm</a>
    </div>
  </div>

  <?php foreach($row as $k=>$v): ?>
    <div class="kv">
      <b><?= h2($k) ?></b>
      <span><?= h2(is_null($v) ? "" : (string)$v) ?></span>
    </div>
  <?php endforeach; ?>
</div>
<?php app_footer(); ?>
