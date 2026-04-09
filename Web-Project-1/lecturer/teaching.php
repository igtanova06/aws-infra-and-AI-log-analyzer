<?php
// /lecturer/teaching.php
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

// Load các lớp mà giảng viên đang dạy
$sql = "
SELECT 
  c.class_id,
  c.class_code,
  c.class_name,
  c.subject,
  c.schedule,
  c.room,
  c.semester
FROM classes c
WHERE c.lecturer_id = ?
ORDER BY c.semester DESC, c.class_code ASC
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
  <title>LECTURER • Lịch dạy</title>
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
      margin-bottom: 16px;
    }

    .card {
      background: rgba(255, 255, 255, .07);
      border: 1px solid rgba(255, 255, 255, .12);
      border-radius: 16px;
      padding: 16px;
      backdrop-filter: blur(10px);
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

    .tablewrap {
      overflow: auto;
      border-radius: 14px;
      border: 1px solid rgba(255, 255, 255, .12)
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
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

    .empty {
      opacity: .8;
      padding: 14px
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
        min-width: 700px
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
        <h1 class="h1">Lịch dạy</h1>
        <span class="pill">Quyền: LECTURER</span>
      </div>

      <div class="card">
        <div class="tablewrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Mã lớp</th>
                <th>Tên lớp</th>
                <th>Môn học</th>
                <th>Lịch</th>
                <th>Phòng</th>
                <th>Học kỳ</th>
              </tr>
            </thead>
            <tbody>
              <?php if (!$rows): ?>
                <tr>
                  <td colspan="7" class="empty">Chưa có lớp học được phân công.</td>
                </tr>
              <?php else: ?>
                <?php $i = 1;
                foreach ($rows as $r): ?>
                  <tr>
                    <td><?= $i++ ?></td>
                    <td><b><?= htmlspecialchars($r['class_code']) ?></b></td>
                    <td><?= htmlspecialchars($r['class_name']) ?></td>
                    <td><?= htmlspecialchars($r['subject'] ?? '-') ?></td>
                    <td><?= htmlspecialchars($r['schedule'] ?? '-') ?></td>
                    <td><?= htmlspecialchars($r['room'] ?? '-') ?></td>
                    <td><?= htmlspecialchars($r['semester'] ?? '-') ?></td>
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