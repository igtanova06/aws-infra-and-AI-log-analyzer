<?php
require __DIR__ . "/../api/auth.php";
require_role("ADMIN");
require __DIR__ . "/../api/db.php";
require __DIR__ . "/../inc/layout.php";

$student_id = (int)($_GET["student_id"] ?? 0);

if ($student_id > 0) {
  $stmt = $mysqli->prepare("
    SELECT e.enrollment_id, s.student_code, sub.subject_code, sub.subject_name, e.semester, e.academic_year,
           g.score, g.grade_letter, g.rating, g.graded_at
    FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN subjects sub ON sub.subject_id = e.subject_id
    LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
    WHERE e.student_id=?
    ORDER BY e.enrollment_id DESC
    LIMIT 200
  ");
  $stmt->bind_param("i", $student_id);
  $stmt->execute();
  $rows = $stmt->get_result()->fetch_all(MYSQLI_ASSOC);
} else {
  $rows = $mysqli->query("
    SELECT e.enrollment_id, s.student_code, sub.subject_code, sub.subject_name, e.semester, e.academic_year,
           g.score, g.grade_letter, g.rating, g.graded_at
    FROM enrollments e
    JOIN students s ON s.student_id = e.student_id
    JOIN subjects sub ON sub.subject_id = e.subject_id
    LEFT JOIN grades g ON g.enrollment_id = e.enrollment_id
    ORDER BY e.enrollment_id DESC
    LIMIT 200
  ")->fetch_all(MYSQLI_ASSOC);
}

app_header("ADMIN • Enrollments / Điểm", "/admin/enrollments.php");
?>
<div class="card" style="margin-top:14px;">
  <h2><i class="fa-solid fa-clipboard-list"></i> Danh sách</h2>
  <table class="table">
    <thead>
      <tr>
        <th>EnrollID</th><th>SV</th><th>Môn</th><th>HK</th><th>Năm</th><th>Điểm</th><th>Chữ</th><th>Xếp loại</th><th>Chấm lúc</th>
      </tr>
    </thead>
    <tbody>
    <?php foreach($rows as $r): ?>
      <tr>
        <td><?= (int)$r["enrollment_id"] ?></td>
        <td><?= h2($r["student_code"]) ?></td>
        <td><b><?= h2($r["subject_code"]) ?></b> — <?= h2($r["subject_name"]) ?></td>
        <td><?= h2($r["semester"]) ?></td>
        <td><?= h2($r["academic_year"]) ?></td>
        <td><?= h2($r["score"]) ?></td>
        <td><?= h2($r["grade_letter"]) ?></td>
        <td><?= h2($r["rating"]) ?></td>
        <td><?= h2($r["graded_at"]) ?></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php app_footer(); ?>
