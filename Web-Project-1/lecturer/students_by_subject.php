<?php
require __DIR__ . "/../api/auth.php";
require_role("LECTURER");
require __DIR__ . "/../api/db.php";
require __DIR__ . "/../inc/layout.php";
require __DIR__ . "/../inc/ids.php";

$lecturer_id = get_lecturer_id_by_user((int)$_SESSION["user"]["user_id"]);

$subs = $mysqli->prepare("
  SELECT DISTINCT sub.subject_id, sub.subject_code, sub.subject_name
  FROM lecturer_subjects ls
  JOIN subjects sub ON sub.subject_id = ls.subject_id
  WHERE ls.lecturer_id=?
  ORDER BY sub.subject_code
");
$subs->bind_param("i", $lecturer_id);
$subs->execute();
$subjects = $subs->get_result()->fetch_all(MYSQLI_ASSOC);

$subject_id = (int)($_GET["subject_id"] ?? 0);
$rows = [];

if ($subject_id > 0) {
  $stmt = $mysqli->prepare("
    SELECT e.enrollment_id, s.student_id, s.student_code, s.class_id, e.semester, e.academic_year,
           g.score, g.grade_letter, g.rating
    FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
    WHERE e.subject_id=?
    ORDER BY s.student_code
    LIMIT 500
  ");
  $stmt->bind_param("i", $subject_id);
  $stmt->execute();
  $rows = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
}

app_header("LECTURER • SV theo môn", "/lecturer/students_by_subject.php");
?>
<div class="card" style="margin-top:14px;">
  <h2><i class="fa-solid fa-filter"></i> Chọn môn</h2>
  <form method="get" style="display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
    <select class="input" name="subject_id">
      <option value="0">-- Chọn môn --</option>
      <?php foreach($subjects as $s): ?>
        <option value="<?= (int)$s["subject_id"] ?>" <?= $subject_id==(int)$s["subject_id"] ? "selected" : "" ?>>
          <?= h2($s["subject_code"]) ?> - <?= h2($s["subject_name"]) ?>
        </option>
      <?php endforeach; ?>
    </select>
    <button class="btnx primary" type="submit"><i class="fa-solid fa-eye"></i> Xem</button>
    <a class="btnx" href="/lecturer/grade.php"><i class="fa-solid fa-pen-to-square"></i> Chấm điểm</a>
  </form>
</div>

<div class="card" style="margin-top:14px;">
  <h2><i class="fa-solid fa-user-group"></i> Danh sách</h2>
  <?php if ($subject_id<=0): ?>
    <div class="alert">Hãy chọn môn để xem danh sách sinh viên.</div>
  <?php else: ?>
    <table class="table">
      <thead><tr><th>EnrollID</th><th>SV</th><th>Lớp</th><th>HK</th><th>Năm</th><th>Điểm</th><th>Chữ</th><th>Xếp loại</th><th></th></tr></thead>
      <tbody>
      <?php foreach($rows as $r): ?>
        <tr>
          <td><?= (int)$r["enrollment_id"] ?></td>
          <td><b><?= h2($r["student_code"]) ?></b></td>
          <td><?= h2($r["class_id"]) ?></td>
          <td><?= h2($r["semester"]) ?></td>
          <td><?= h2($r["academic_year"]) ?></td>
          <td><?= h2($r["score"]) ?></td>
          <td><?= h2($r["grade_letter"]) ?></td>
          <td><?= h2($r["rating"]) ?></td>
          <td><a class="btnx" href="/lecturer/grade.php?enrollment_id=<?= (int)$r["enrollment_id"] ?>"><i class="fa-solid fa-pen"></i> Chấm</a></td>
        </tr>
      <?php endforeach; ?>
      </tbody>
    </table>
  <?php endif; ?>
</div>

<?php app_footer(); ?>
