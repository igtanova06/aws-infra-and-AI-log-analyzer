<?php
// /lecturer/grading.php  
session_start();
if (!isset($_SESSION['user'])) {
  header("Location: /index.php");
  exit;
}
if (($_SESSION['user']['role'] ?? '') !== 'LECTURER') {
  http_response_code(403);
  echo "403 Forbidden";
  exit;
}

require __DIR__ . "/../api/db.php";

$user = $_SESSION['user'];
$user_id = (int) ($user['user_id'] ?? 0);

$msg = "";
$okmsg = "";

// POST: cập nhật điểm
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'grade') {
  $student_id = (int) ($_POST['student_id'] ?? 0);
  $class_id = (int) ($_POST['class_id'] ?? 0);
  $score_raw = trim((string) ($_POST['score'] ?? ''));
  $notes = trim((string) ($_POST['notes'] ?? ''));

  if ($student_id <= 0 || $class_id <= 0) {
    $msg = "Thiếu thông tin student_id hoặc class_id.";
  } else {
    // Kiểm tra giảng viên có dạy lớp này không
    $sqlCheck = "SELECT class_id FROM classes WHERE class_id = ? AND lecturer_id = ? LIMIT 1";
    $stCheck = $mysqli->prepare($sqlCheck);
    $stCheck->bind_param("ii", $class_id, $user_id);
    $stCheck->execute();
    $resCheck = $stCheck->get_result();

    if (!$resCheck || !$resCheck->fetch_assoc()) {
      $msg = "Bạn không có quyền chấm điểm lớp này.";
    } else {
      // Validate điểm
      $score = null;
      if ($score_raw !== '') {
        if (!is_numeric($score_raw)) {
          $msg = "Điểm phải là số.";
        } else {
          $score = (float) $score_raw;
          if ($score < 0 || $score > 10) {
            $msg = "Điểm phải trong khoảng 0 - 10.";
          }
        }
      }

      if ($msg === "") {
        // UPSERT vào grades
        if ($score === null) {
          $sqlUp = "INSERT INTO grades (student_id, class_id, score, notes, graded_by, graded_at) 
                              VALUES (?, ?, NULL, ?, ?, NOW())
                              ON DUPLICATE KEY UPDATE score = NULL, notes = VALUES(notes), graded_by = VALUES(graded_by), graded_at = NOW()";
          $stUp = $mysqli->prepare($sqlUp);
          $stUp->bind_param("iisi", $student_id, $class_id, $notes, $user_id);
        } else {
          $sqlUp = "INSERT INTO grades (student_id, class_id, score, notes, graded_by, graded_at) 
                              VALUES (?, ?, ?, ?, ?, NOW())
                              ON DUPLICATE KEY UPDATE score = VALUES(score), notes = VALUES(notes), graded_by = VALUES(graded_by), graded_at = NOW()";
          $stUp = $mysqli->prepare($sqlUp);
          $stUp->bind_param("iidsi", $student_id, $class_id, $score, $notes, $user_id);
        }

        if ($stUp->execute()) {
          $okmsg = "Đã lưu điểm!";
        } else {
          $msg = "Lỗi lưu điểm: " . $mysqli->error;
        }
      }
    }
  }
}

// Load danh sách sinh viên trong các lớp giảng viên đang dạy
$sql = "
SELECT 
  s.student_id,
  s.student_code,
  u.full_name AS student_name,
  c.class_id,
  c.class_code,
  c.class_name,
  c.subject,
  g.score,
  g.notes,
  g.graded_at
FROM classes c
JOIN students s ON s.class_id = c.class_id
JOIN users u ON u.user_id = s.user_id
LEFT JOIN grades g ON g.student_id = s.student_id AND g.class_id = c.class_id
WHERE c.lecturer_id = ?
ORDER BY c.class_code ASC, s.student_code ASC
";
$stmt = $mysqli->prepare($sql);
$stmt->bind_param("i", $user_id);
$stmt->execute();
$res = $stmt->get_result();
$rows = $res ? $res->fetch_all(MYSQLI_ASSOC) : [];
?>
<!doctype html>
<html lang="vi">

<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>LECTURER • Chấm điểm</title>
  <style>
    * {
      box-sizing: border-box
    }

    body {
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
      color: #e9eef5;
      background: radial-gradient(900px 600px at 30% 20%, rgba(120, 110, 255, .35), transparent 60%),
        radial-gradient(900px 600px at 70% 80%, rgba(0, 200, 255, .18), transparent 60%),
        linear-gradient(135deg, #0b1020, #0a2a33);
      min-height: 100vh;
    }

    a {
      color: inherit;
      text-decoration: none
    }

    .layout {
      display: flex;
      min-height: 100vh
    }

    .sidebar {
      width: 260px;
      padding: 18px;
      position: sticky;
      top: 0;
      height: 100vh;
      background: rgba(255, 255, 255, .06);
      border-right: 1px solid rgba(255, 255, 255, .10);
      backdrop-filter: blur(10px);
    }

    .brand {
      font-weight: 800;
      letter-spacing: .5px;
      font-size: 18px;
      margin-bottom: 6px
    }

    .muted {
      opacity: .75;
      font-size: 13px;
      margin-bottom: 14px
    }

    .nav {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 14px
    }

    .btn {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 12px;
      border-radius: 12px;
      background: rgba(255, 255, 255, .08);
      border: 1px solid rgba(255, 255, 255, .12);
    }

    .btn:hover {
      background: rgba(255, 255, 255, .12)
    }

    .btn.red {
      background: rgba(255, 80, 80, .12);
      border-color: rgba(255, 80, 80, .25)
    }

    .content {
      flex: 1;
      padding: 22px
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 12px
    }

    .h1 {
      font-size: 22px;
      font-weight: 800;
      margin: 0
    }

    .pill {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(255, 255, 255, .10);
      border: 1px solid rgba(255, 255, 255, .14);
      font-size: 12px;
      opacity: .95;
    }

    .card {
      background: rgba(255, 255, 255, .07);
      border: 1px solid rgba(255, 255, 255, .12);
      border-radius: 16px;
      padding: 16px;
      backdrop-filter: blur(10px);
      margin-bottom: 12px;
    }

    .alert {
      padding: 10px 12px;
      border-radius: 12px;
      margin-bottom: 12px;
      border: 1px solid rgba(255, 255, 255, .12)
    }

    .alert.ok {
      background: rgba(80, 255, 160, .10);
      border-color: rgba(80, 255, 160, .20)
    }

    .alert.err {
      background: rgba(255, 80, 80, .10);
      border-color: rgba(255, 80, 80, .20)
    }

    .tablewrap {
      overflow: auto;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, .12)
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
      background: rgba(0, 0, 0, .10)
    }

    th,
    td {
      padding: 12px 10px;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, .10);
      vertical-align: top
    }

    th {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .08em;
      opacity: .8
    }

    tr:hover td {
      background: rgba(255, 255, 255, .05)
    }

    .mini {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap
    }

    input,
    textarea {
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, .16);
      background: rgba(0, 0, 0, .18);
      color: #e9eef5;
      outline: none;
    }

    input {
      width: 90px
    }

    textarea {
      width: 160px;
      height: 60px;
      resize: vertical
    }

    .save {
      padding: 8px 12px;
      border-radius: 10px;
      cursor: pointer;
      background: rgba(120, 110, 255, .18);
      border: 1px solid rgba(120, 110, 255, .28);
      color: #e9eef5;
    }

    .save:hover {
      background: rgba(120, 110, 255, .25)
    }

    @media (max-width: 900px) {
      .layout {
        flex-direction: column
      }

      .sidebar {
        width: 100%;
        height: auto;
        position: relative
      }

      table {
        min-width: 900px
      }
    }
  </style>
</head>

<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">LECTURER • Dashboard</div>
      <div class="muted">Xin chào: <b><?= htmlspecialchars($user['full_name'] ?? $user['username'] ?? '') ?></b></div>
      <div class="nav">
        <a class="btn" href="/lecturer/dashboard.php">Trang chủ</a>
        <a class="btn" href="/lecturer/teaching.php">Lịch dạy</a>
        <a class="btn" href="/lecturer/grading.php">Chấm điểm</a>
        <a class="btn red" href="/api/logout.php">Logout</a>
      </div>
    </aside>

    <main class="content">
      <div class="topbar">
        <h1 class="h1">Chấm điểm</h1>
        <span class="pill">Quyền: LECTURER</span>
      </div>

      <?php if ($okmsg): ?>
        <div class="alert ok"><?= htmlspecialchars($okmsg) ?></div><?php endif; ?>
      <?php if ($msg): ?>
        <div class="alert err"><?= htmlspecialchars($msg) ?></div><?php endif; ?>

      <div class="card">
        <p style="opacity:.85; margin:0 0 12px 0">Danh sách sinh viên trong các lớp bạn đang dạy</p>
        <div class="tablewrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Mã SV</th>
                <th>Họ tên</th>
                <th>Lớp</th>
                <th>Điểm</th>
                <th>Ngày chấm</th>
                <th>Chấm điểm</th>
              </tr>
            </thead>
            <tbody>
              <?php if (!$rows): ?>
                <tr>
                  <td colspan="7" style="opacity:.85;padding:14px">Chưa có sinh viên trong các lớp của bạn.</td>
                </tr>
              <?php else: ?>
                <?php $i = 1;
                foreach ($rows as $r): ?>
                  <tr>
                    <td><?= $i++ ?></td>
                    <td><b><?= htmlspecialchars($r['student_code']) ?></b></td>
                    <td><?= htmlspecialchars($r['student_name']) ?></td>
                    <td>
                      <div><b><?= htmlspecialchars($r['class_code']) ?></b></div>
                      <div style="opacity:.85; font-size:13px"><?= htmlspecialchars($r['class_name']) ?></div>
                      <div style="opacity:.7; font-size:12px"><?= htmlspecialchars($r['subject'] ?? '') ?></div>
                    </td>
                    <td>
                      <?php if ($r['score'] === null): ?>
                        <span style="opacity:.6">Chưa chấm</span>
                      <?php else: ?>
                        <b style="color:#50ffa0"><?= htmlspecialchars($r['score']) ?></b>
                      <?php endif; ?>
                    </td>
                    <td style="opacity:.8; font-size:13px">
                      <?= $r['graded_at'] ? date('d/m/Y H:i', strtotime($r['graded_at'])) : '-' ?>
                    </td>
                    <td>
                      <form method="post" class="mini">
                        <input type="hidden" name="action" value="grade" />
                        <input type="hidden" name="student_id" value="<?= (int) $r['student_id'] ?>" />
                        <input type="hidden" name="class_id" value="<?= (int) $r['class_id'] ?>" />
                        <input name="score" placeholder="0-10" value="<?= htmlspecialchars($r['score'] ?? '') ?>" />
                        <textarea name="notes"
                          placeholder="Ghi chú (tùy chọn)"><?= htmlspecialchars($r['notes'] ?? '') ?></textarea>
                        <button class="save" type="submit">Lưu</button>
                      </form>
                    </td>
                  </tr>
                <?php endforeach; ?>
              <?php endif; ?>
            </tbody>
          </table>
        </div>
      </div>

    </main>
  </div>
</body>

</html>