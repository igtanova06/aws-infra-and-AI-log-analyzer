<?php
// /admin/students.php
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

require __DIR__ . "/../api/db.php";

$user = $_SESSION['user'];

$err = "";
$ok = "";

// Lấy role_id STUDENT để tạo user mới
$roleStudentId = 3;
$rs = $mysqli->query("SELECT role_id FROM roles WHERE role_code='STUDENT' LIMIT 1");
if ($rs && ($row = $rs->fetch_assoc()))
  $roleStudentId = (int) $row['role_id'];

// CREATE student (tạo user + student)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'create') {
  $student_code = trim((string) ($_POST['student_code'] ?? ''));
  $full_name = trim((string) ($_POST['full_name'] ?? ''));
  $email = trim((string) ($_POST['email'] ?? ''));
  $password = (string) ($_POST['password'] ?? '');
  $phone = trim((string) ($_POST['phone'] ?? ''));
  $class_id = (int) ($_POST['class_id'] ?? 0);

  // Auto-generate username từ student_code (chuyển thành chữ thường)
  $username = strtolower($student_code);

  if ($student_code === "" || $full_name === "" || $email === "" || $password === "") {
    $err = "Thiếu dữ liệu (student_code/full_name/email/password).";
  } else {
    // hash theo scheme bạn đang dùng trong login.php: SHA2(password + username + '_salt', 256)
    $mysqli->begin_transaction();
    try {
      $sqlU = "INSERT INTO users (username, password, full_name, email, role_id, is_active) 
               VALUES (?, SHA2(CONCAT(?, ?, '_salt'), 256), ?, ?, ?, 1)";
      $stU = $mysqli->prepare($sqlU);
      $stU->bind_param("sssssi", $username, $password, $username, $full_name, $email, $roleStudentId);
      if (!$stU->execute())
        throw new Exception($mysqli->error);
      $new_user_id = $mysqli->insert_id;

      $sqlS = "INSERT INTO students (student_code, user_id, class_id, phone) VALUES (?, ?, ?, ?)";
      $stS = $mysqli->prepare($sqlS);
      $cid = ($class_id > 0) ? $class_id : null;
      // class_id có thể NULL
      if ($cid === null) {
        $sqlS2 = "INSERT INTO students (student_code, user_id, class_id, phone) VALUES (?, ?, NULL, ?)";
        $stS2 = $mysqli->prepare($sqlS2);
        $stS2->bind_param("sis", $student_code, $new_user_id, $phone);
        if (!$stS2->execute())
          throw new Exception($mysqli->error);
      } else {
        $stS->bind_param("siis", $student_code, $new_user_id, $cid, $phone);
        if (!$stS->execute())
          throw new Exception($mysqli->error);
      }

      $mysqli->commit();
      $ok = "Đã tạo sinh viên mới!";
    } catch (Exception $e) {
      $mysqli->rollback();
      $err = "Lỗi tạo sinh viên: " . $e->getMessage();
    }
  }
}

// UPDATE student basic info
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'update') {
  $student_id = (int) ($_POST['student_id'] ?? 0);
  $class_id = (int) ($_POST['class_id'] ?? 0);
  $phone = trim((string) ($_POST['phone'] ?? ''));
  $status = trim((string) ($_POST['status'] ?? 'Đang học'));

  if ($student_id <= 0) {
    $err = "Thiếu student_id.";
  } else {
    $sql = "UPDATE students SET class_id = ?, phone = ?, status = ? WHERE student_id = ?";
    $st = $mysqli->prepare($sql);
    $cid = ($class_id > 0) ? $class_id : null;
    if ($cid === null) {
      $sql2 = "UPDATE students SET class_id = NULL, phone = ?, status = ? WHERE student_id = ?";
      $st2 = $mysqli->prepare($sql2);
      $st2->bind_param("ssi", $phone, $status, $student_id);
      if ($st2->execute())
        $ok = "Đã cập nhật!";
      else
        $err = "Lỗi cập nhật: " . $mysqli->error;
    } else {
      $st->bind_param("issi", $cid, $phone, $status, $student_id);
      if ($st->execute())
        $ok = "Đã cập nhật!";
      else
        $err = "Lỗi cập nhật: " . $mysqli->error;
    }
  }
}

// DELETE student (xóa grades + enrollments + student + user)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'delete') {
  $student_id = (int) ($_POST['student_id'] ?? 0);
  if ($student_id <= 0) {
    $err = "Thiếu student_id.";
  } else {
    // lấy user_id để xóa user
    $stG = $mysqli->prepare("SELECT user_id FROM students WHERE student_id=? LIMIT 1");
    $stG->bind_param("i", $student_id);
    $stG->execute();
    $rG = $stG->get_result();
    $urow = $rG ? $rG->fetch_assoc() : null;
    if (!$urow) {
      $err = "Không tìm thấy sinh viên.";
    } else {
      $uid = (int) $urow['user_id'];

      $mysqli->begin_transaction();
      try {
        // xóa grades theo enrollment của student
        $sql1 = "DELETE g FROM grades g 
                 JOIN enrollments e ON e.enrollment_id = g.enrollment_id
                 WHERE e.student_id = ?";
        $st1 = $mysqli->prepare($sql1);
        $st1->bind_param("i", $student_id);
        if (!$st1->execute())
          throw new Exception($mysqli->error);

        // xóa enrollments
        $st2 = $mysqli->prepare("DELETE FROM enrollments WHERE student_id=?");
        $st2->bind_param("i", $student_id);
        if (!$st2->execute())
          throw new Exception($mysqli->error);

        // xóa student
        $st3 = $mysqli->prepare("DELETE FROM students WHERE student_id=?");
        $st3->bind_param("i", $student_id);
        if (!$st3->execute())
          throw new Exception($mysqli->error);

        // xóa user
        $st4 = $mysqli->prepare("DELETE FROM users WHERE user_id=?");
        $st4->bind_param("i", $uid);
        if (!$st4->execute())
          throw new Exception($mysqli->error);

        $mysqli->commit();
        $ok = "Đã xóa sinh viên!";
      } catch (Exception $e) {
        $mysqli->rollback();
        $err = "Lỗi xóa: " . $e->getMessage();
      }
    }
  }
}

// Load classes for dropdown
$classes = [];
$rc = $mysqli->query("SELECT class_id, class_code, class_name FROM classes ORDER BY class_name ASC");
if ($rc)
  $classes = $rc->fetch_all(MYSQLI_ASSOC);

// Load student list
$sqlList = "
SELECT 
  s.student_id,
  s.student_code,
  u.full_name,
  u.email,
  c.class_name,
  s.phone,
  s.status
FROM students s
JOIN users u ON u.user_id = s.user_id
LEFT JOIN classes c ON c.class_id = s.class_id
ORDER BY s.student_id DESC
";
$r = $mysqli->query($sqlList);
$rows = $r ? $r->fetch_all(MYSQLI_ASSOC) : [];
?>
<!doctype html>
<html lang="vi">

<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ADMIN • Quản lý sinh viên</title>
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

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px
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
      min-width: 1000px;
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

    input,
    select {
      padding: 8px 10px;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, .16);
      background: rgba(0, 0, 0, .18);
      color: #e9eef5;
      outline: none;
      width: 100%;
    }

    .row {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap
    }

    .row>div {
      flex: 1;
      min-width: 160px
    }

    .act {
      display: flex;
      gap: 8px;
      align-items: center
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

    .danger {
      padding: 8px 12px;
      border-radius: 10px;
      cursor: pointer;
      background: rgba(255, 80, 80, .14);
      border: 1px solid rgba(255, 80, 80, .26);
      color: #e9eef5;
    }

    .danger:hover {
      background: rgba(255, 80, 80, .20)
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

      .grid {
        grid-template-columns: 1fr
      }

      table {
        min-width: 980px
      }
    }
  </style>
</head>

<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">ADMIN • Dashboard</div>
      <div class="muted">Xin chào: <b><?= htmlspecialchars($user['full_name'] ?? $user['username'] ?? '') ?></b></div>

      <div class="nav">
        <a class="btn" href="/admin/dashboard.php">Trang chủ</a>
        <a class="btn" href="/admin/students.php">Quản lý sinh viên</a>
        <a class="btn" href="/admin/lecturers.php">Quản lý giảng viên</a>
        <a class="btn" href="/admin/classes.php">Quản lý lớp học</a>
        <a class="btn red" href="/api/logout.php">Logout</a>
      </div>
    </aside>

    <main class="content">
      <div class="topbar">
        <h1 class="h1">Quản lý sinh viên</h1>
        <span class="pill">Quyền: ADMIN</span>
      </div>

      <?php if ($ok): ?>
        <div class="alert ok"><?= htmlspecialchars($ok) ?></div><?php endif; ?>
      <?php if ($err): ?>
        <div class="alert err"><?= htmlspecialchars($err) ?></div><?php endif; ?>

      <div class="card">
        <h3 style="margin:0 0 10px 0">Tạo sinh viên mới</h3>
        <form method="post" class="grid">
          <input type="hidden" name="action" value="create" />
          <div><input name="student_code" placeholder="Mã SV (VD: SV011)" required></div>
          <div><input name="full_name" placeholder="Họ tên" required></div>
          <div><input name="email" placeholder="Email" required></div>
          <div><input name="phone" placeholder="Số điện thoại"></div>
          <div><input name="password" placeholder="Mật khẩu" required></div>
          <div>
            <select name="class_id">
              <option value="0">-- Chọn lớp (có thể bỏ trống) --</option>
              <?php foreach ($classes as $c): ?>
                <option value="<?= (int) $c['class_id'] ?>">
                  <?= htmlspecialchars($c['class_name'] . " (" . $c['class_code'] . ")") ?>
                </option>
              <?php endforeach; ?>
            </select>
          </div>
          <div style="grid-column:1/-1">
            <button class="save" type="submit">Tạo</button>
          </div>
        </form>
      </div>

      <div class="card">
        <h3 style="margin:0 0 10px 0">Danh sách sinh viên</h3>
        <div class="tablewrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Mã SV</th>
                <th>Họ tên</th>
                <th>Email</th>
                <th>Lớp</th>
                <th>Phone</th>
                <th>Trạng thái</th>
                <th>Cập nhật</th>
              </tr>
            </thead>
            <tbody>
              <?php if (!$rows): ?>
                <tr>
                  <td colspan="8" style="opacity:.85;padding:14px">Chưa có dữ liệu students.</td>
                </tr>
              <?php else: ?>
                <?php foreach ($rows as $r): ?>
                  <tr>
                    <td><b>#<?= (int) $r['student_id'] ?></b></td>
                    <td><?= htmlspecialchars($r['student_code']) ?></td>
                    <td><?= htmlspecialchars($r['full_name']) ?></td>
                    <td style="opacity:.9"><?= htmlspecialchars($r['email']) ?></td>
                    <td><?= htmlspecialchars($r['class_name'] ?? '-') ?></td>
                    <td><?= htmlspecialchars($r['phone'] ?? '-') ?></td>
                    <td><?= htmlspecialchars($r['status'] ?? '-') ?></td>
                    <td>
                      <div class="act">
                        <form method="post" class="row" style="margin:0">
                          <input type="hidden" name="action" value="update" />
                          <input type="hidden" name="student_id" value="<?= (int) $r['student_id'] ?>" />

                          <div style="min-width:200px">
                            <select name="class_id">
                              <option value="0">-- Lớp (NULL) --</option>
                              <?php foreach ($classes as $c): ?>
                                <option value="<?= (int) $c['class_id'] ?>">
                                  <?= htmlspecialchars($c['class_code']) ?>
                                </option>
                              <?php endforeach; ?>
                            </select>
                          </div>

                          <div style="min-width:160px">
                            <input name="phone" placeholder="Phone" value="<?= htmlspecialchars($r['phone'] ?? '') ?>" />
                          </div>

                          <div style="min-width:160px">
                            <select name="status">
                              <?php
                              $opts = ["Đang học", "Nghỉ học", "Tốt nghiệp", "Bảo lưu"];
                              foreach ($opts as $op) {
                                $sel = (($r['status'] ?? '') === $op) ? 'selected' : '';
                                echo "<option $sel>" . htmlspecialchars($op) . "</option>";
                              }
                              ?>
                            </select>
                          </div>

                          <button class="save" type="submit">Lưu</button>
                        </form>

                        <form method="post"
                          onsubmit="return confirm('Xóa sinh viên này? (sẽ xóa enrollments/grades liên quan)');"
                          style="margin:0">
                          <input type="hidden" name="action" value="delete" />
                          <input type="hidden" name="student_id" value="<?= (int) $r['student_id'] ?>" />
                          <button class="danger" type="submit">Xóa</button>
                        </form>
                      </div>
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