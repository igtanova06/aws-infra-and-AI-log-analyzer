<?php
require __DIR__ . "/../api/auth.php";
require_role("LECTURER");
require __DIR__ . "/../api/db.php";
require __DIR__ . "/../inc/layout.php";
require __DIR__ . "/../inc/ids.php";

$lecturer_id = get_lecturer_id_by_user((int)$_SESSION["user"]["user_id"]);
$enrollment_id = (int)($_GET["enrollment_id"] ?? $_POST["enrollment_id"] ?? 0);

$msg = "";
$ok = false;

if ($_SERVER["REQUEST_METHOD"] === "POST") {
  $score = trim($_POST["score"] ?? "");
  $grade_letter = trim($_POST["grade_letter"] ?? "");
  $rating = trim($_POST["rating"] ?? "");
  $notes = trim($_POST["notes"] ?? "");

  if ($enrollment_id <= 0 || $score === "") {
    $msg = "Thiếu enrollment_id hoặc score.";
  } else {
    // nếu đã có grade -> update, chưa có -> insert
    $chk = $mysqli->prepare("SELECT grade_id FROM grades WHERE enrollment_id=? LIMIT 1");
    $chk->bind_param("i", $enrollment_id);
    $chk->execute();
    $exists = $chk->get_result()->fetch_assoc();

    if ($exists) {
      $stmt = $mysqli->prepare("UPDATE grades SET score=?, grade_letter=?, rating=?, graded_by=?, graded_at=NOW(), notes=? WHERE enrollment_id=?");
      $stmt->bind_param("dssisi", $score, $grade_letter, $rating, $lecturer_id, $notes, $enrollment_id);
      $stmt->execute();
    } else {
      $stmt = $mysqli->prepare("INSERT INTO grades(enrollment_id, score, grade_letter, rating, graded_by, graded_at, notes)
                                VALUES(?,?,?,?,?,NOW(),?)");
      $stmt->bind_param("idssis", $enrollment_id, $score, $grade_letter, $rating, $lecturer_id, $notes);
      $stmt->execute();
    }
    $ok = true;
    $msg = "Lưu điểm thành công!";
  }
}

// load info enrollment để hiển thị
$info = null;
if ($enrollment_id > 0) {
  $stmt = $mysqli->prepare("
    SELECT e.enrollment_id, s.student_code, sub.subject_code, sub.subject_name, e.semester, e.academic_year,
           g.score, g.grade_letter, g.rating, g.notes
    FROM enrollments e
    JOIN students s ON s.student_id=e.student_id
    JOIN subjects sub ON sub.subject_id=e.subject_id
    LEFT JOIN grades g ON g.enrollment_id=e.enrollment_id
    WHERE e.enrollment_id=? LIMIT 1
  ");
  $stmt->bind_param("i", $enrollment_id);
  $stmt->execute();
  $info = $stmt->get_result()->fetch_assoc();
}

app_header("LECTURER • Chấm điểm", "/lecturer/grade.php");
?>
<div class="card" style="margin-top:14px;">
  <h2><i class="fa-solid fa-pen-to-square"></i> Nhập điểm</h2>

  <?php if($msg): ?>
    <div class="alert <?= $ok ? "ok" : "" ?>"><?= h2($msg) ?></div>
  <?php endif; ?>

  <form method="get" style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">
    <input class="input" name="enrollment_id" placeholder="Nhập enrollment_id..." value="<?= $enrollment_id>0 ? (int)$enrollment_id : "" ?>">
    <button class="btnx primary" type="submit"><i class="fa-solid fa-magnifying-glass"></i> Load</button>
  </form>

  <?php if(!$info && $enrollment_id>0): ?>
    <div class="alert" style="margin-top:12px;">Không tìm thấy enrollment_id này.</div>
  <?php endif; ?>

  <?php if($info): ?>
    <div style="margin-top:12px;">
      <div class="kv"><b>SV</b><span><?= h2($info["student_code"]) ?></span></div>
      <div class="kv"><b>Môn</b><span><b><?= h2($info["subject_code"]) ?></b> — <?= h2($info["subject_name"]) ?></span></div>
      <div class="kv"><b>HK/Năm</b><span><?= h2($info["semester"]) ?> / <?= h2($info["academic_year"]) ?></span></div>
    </div>

    <form method="post" style="margin-top:14px;display:grid;gap:10px;max-width:520px;">
      <input type="hidden" name="enrollment_id" value="<?= (int)$info["enrollment_id"] ?>">

      <input class="input" name="score" placeholder="Score (vd 8.5)" value="<?= h2($info["score"]) ?>">
      <input class="input" name="grade_letter" placeholder="Grade letter (A/B/C...)" value="<?= h2($info["grade_letter"]) ?>">
      <input class="input" name="rating" placeholder="Xếp loại (Giỏi/Khá/TB...)" value="<?= h2($info["rating"]) ?>">
      <input class="input" name="notes" placeholder="Ghi chú" value="<?= h2($info["notes"]) ?>">

      <button class="btnx primary" type="submit"><i class="fa-solid fa-floppy-disk"></i> Lưu điểm</button>
    </form>
  <?php endif; ?>
</div>
<?php app_footer(); ?>
