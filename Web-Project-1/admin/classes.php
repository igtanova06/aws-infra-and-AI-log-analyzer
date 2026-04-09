<?php
// /admin/classes.php
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

// CREATE class
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'create') {
    $class_code = trim((string) ($_POST['class_code'] ?? ''));
    $class_name = trim((string) ($_POST['class_name'] ?? ''));
    $subject = trim((string) ($_POST['subject'] ?? ''));
    $lecturer_id = (int) ($_POST['lecturer_id'] ?? 0);
    $schedule = trim((string) ($_POST['schedule'] ?? ''));
    $room = trim((string) ($_POST['room'] ?? ''));
    $semester = trim((string) ($_POST['semester'] ?? ''));

    if ($class_code === "" || $class_name === "") {
        $err = "Thiếu dữ liệu (class_code/class_name).";
    } else {
        $mysqli->begin_transaction();
        try {
            $sql = "INSERT INTO classes (class_code, class_name, subject, lecturer_id, schedule, room, semester, created_at) 
              VALUES (?, ?, ?, ?, ?, ?, ?, NOW())";
            $st = $mysqli->prepare($sql);
            $lid = ($lecturer_id > 0) ? $lecturer_id : null;

            if ($lid === null) {
                $sql2 = "INSERT INTO classes (class_code, class_name, subject, lecturer_id, schedule, room, semester, created_at) 
                 VALUES (?, ?, ?, NULL, ?, ?, ?, NOW())";
                $st2 = $mysqli->prepare($sql2);
                $st2->bind_param("ssssss", $class_code, $class_name, $subject, $schedule, $room, $semester);
                if (!$st2->execute())
                    throw new Exception($mysqli->error);
            } else {
                $st->bind_param("sssssss", $class_code, $class_name, $subject, $lid, $schedule, $room, $semester);
                if (!$st->execute())
                    throw new Exception($mysqli->error);
            }

            $mysqli->commit();
            $ok = "Đã tạo lớp học mới!";
        } catch (Exception $e) {
            $mysqli->rollback();
            $err = "Lỗi tạo lớp học: " . $e->getMessage();
        }
    }
}

// UPDATE class
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'update') {
    $class_id = (int) ($_POST['class_id'] ?? 0);
    $class_name = trim((string) ($_POST['class_name'] ?? ''));
    $subject = trim((string) ($_POST['subject'] ?? ''));
    $lecturer_id = (int) ($_POST['lecturer_id'] ?? 0);
    $schedule = trim((string) ($_POST['schedule'] ?? ''));
    $room = trim((string) ($_POST['room'] ?? ''));
    $semester = trim((string) ($_POST['semester'] ?? ''));

    if ($class_id <= 0) {
        $err = "Thiếu class_id.";
    } else {
        $lid = ($lecturer_id > 0) ? $lecturer_id : null;

        if ($lid === null) {
            $sql = "UPDATE classes SET class_name = ?, subject = ?, lecturer_id = NULL, schedule = ?, room = ?, semester = ? WHERE class_id = ?";
            $st = $mysqli->prepare($sql);
            $st->bind_param("sssssi", $class_name, $subject, $schedule, $room, $semester, $class_id);
        } else {
            $sql = "UPDATE classes SET class_name = ?, subject = ?, lecturer_id = ?, schedule = ?, room = ?, semester = ? WHERE class_id = ?";
            $st = $mysqli->prepare($sql);
            $st->bind_param("ssisssi", $class_name, $subject, $lid, $schedule, $room, $semester, $class_id);
        }

        if ($st->execute())
            $ok = "Đã cập nhật!";
        else
            $err = "Lỗi cập nhật: " . $mysqli->error;
    }
}

// DELETE class
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'delete') {
    $class_id = (int) ($_POST['class_id'] ?? 0);
    if ($class_id <= 0) {
        $err = "Thiếu class_id.";
    } else {
        $mysqli->begin_transaction();
        try {
            // Xóa class
            $st = $mysqli->prepare("DELETE FROM classes WHERE class_id = ?");
            $st->bind_param("i", $class_id);
            if (!$st->execute())
                throw new Exception($mysqli->error);

            $mysqli->commit();
            $ok = "Đã xóa lớp học!";
        } catch (Exception $e) {
            $mysqli->rollback();
            $err = "Lỗi xóa: " . $e->getMessage();
        }
    }
}

// Load lecturers for dropdown
$lecturers = [];
$rl = $mysqli->query("SELECT user_id, username, full_name FROM users WHERE role_id = 2 ORDER BY full_name ASC");
if ($rl)
    $lecturers = $rl->fetch_all(MYSQLI_ASSOC);

// Load class list
$sqlList = "
SELECT 
  c.class_id,
  c.class_code,
  c.class_name,
  c.subject,
  c.lecturer_id,
  c.schedule,
  c.room,
  c.semester,
  u.full_name as lecturer_name
FROM classes c
LEFT JOIN users u ON u.user_id = c.lecturer_id
ORDER BY c.class_id DESC
";
$r = $mysqli->query($sqlList);
$rows = $r ? $r->fetch_all(MYSQLI_ASSOC) : [];
?>
<!doctype html>
<html lang="vi">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ADMIN • Quản lý lớp học</title>
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

        .grid3 {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
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
            min-width: 1200px;
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
            min-width: 140px
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

            .grid,
            .grid3 {
                grid-template-columns: 1fr
            }

            table {
                min-width: 1180px
            }
        }
    </style>
</head>

<body>
    <div class="layout">
        <aside class="sidebar">
            <div class="brand">ADMIN • Dashboard</div>
            <div class="muted">Xin chào: <b><?= htmlspecialchars($user['full_name'] ?? $user['username'] ?? '') ?></b>
            </div>

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
                <h1 class="h1">Quản lý lớp học</h1>
                <span class="pill">Quyền: ADMIN</span>
            </div>

            <?php if ($ok): ?>
                <div class="alert ok"><?= htmlspecialchars($ok) ?></div><?php endif; ?>
            <?php if ($err): ?>
                <div class="alert err"><?= htmlspecialchars($err) ?></div><?php endif; ?>

            <div class="card">
                <h3 style="margin:0 0 10px 0">Tạo lớp học mới</h3>
                <form method="post" class="grid3">
                    <input type="hidden" name="action" value="create" />
                    <div><input name="class_code" placeholder="Mã lớp (VD: IT001)" required></div>
                    <div><input name="class_name" placeholder="Tên lớp" required></div>
                    <div><input name="subject" placeholder="Môn học"></div>
                    <div>
                        <select name="lecturer_id">
                            <option value="0">-- Chọn giảng viên (có thể để trống) --</option>
                            <?php foreach ($lecturers as $lec): ?>
                                <option value="<?= (int) $lec['user_id'] ?>">
                                    <?= htmlspecialchars(($lec['full_name'] ?: $lec['username'])) ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    <div><input name="schedule" placeholder="Lịch học (VD: Thứ 2, 7-9h)"></div>
                    <div><input name="room" placeholder="Phòng (VD: A101)"></div>
                    <div><input name="semester" placeholder="Học kỳ (VD: HK1 2025)"></div>
                    <div style="grid-column:1/-1">
                        <button class="save" type="submit">Tạo</button>
                    </div>
                </form>
            </div>

            <div class="card">
                <h3 style="margin:0 0 10px 0">Danh sách lớp học</h3>
                <div class="tablewrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Mã lớp</th>
                                <th>Tên lớp</th>
                                <th>Môn học</th>
                                <th>Giảng viên</th>
                                <th>Lịch học</th>
                                <th>Phòng</th>
                                <th>Học kỳ</th>
                                <th>Cập nhật</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php if (!$rows): ?>
                                <tr>
                                    <td colspan="9" style="opacity:.85;padding:14px">Chưa có dữ liệu lớp học.</td>
                                </tr>
                            <?php else: ?>
                                <?php foreach ($rows as $r): ?>
                                    <tr>
                                        <td><b>#<?= (int) $r['class_id'] ?></b></td>
                                        <td><?= htmlspecialchars($r['class_code']) ?></td>
                                        <td><?= htmlspecialchars($r['class_name']) ?></td>
                                        <td><?= htmlspecialchars($r['subject'] ?? '-') ?></td>
                                        <td><?= htmlspecialchars($r['lecturer_name'] ?? '-') ?></td>
                                        <td><?= htmlspecialchars($r['schedule'] ?? '-') ?></td>
                                        <td><?= htmlspecialchars($r['room'] ?? '-') ?></td>
                                        <td><?= htmlspecialchars($r['semester'] ?? '-') ?></td>
                                        <td>
                                            <div class="act">
                                                <form method="post" class="row" style="margin:0">
                                                    <input type="hidden" name="action" value="update" />
                                                    <input type="hidden" name="class_id" value="<?= (int) $r['class_id'] ?>" />

                                                    <div style="min-width:160px">
                                                        <input name="class_name" placeholder="Tên lớp"
                                                            value="<?= htmlspecialchars($r['class_name']) ?>" />
                                                    </div>

                                                    <div style="min-width:140px">
                                                        <input name="subject" placeholder="Môn học"
                                                            value="<?= htmlspecialchars($r['subject'] ?? '') ?>" />
                                                    </div>

                                                    <div style="min-width:180px">
                                                        <select name="lecturer_id">
                                                            <option value="0">-- Không GV --</option>
                                                            <?php foreach ($lecturers as $lec):
                                                                $selected = ($r['lecturer_id'] == $lec['user_id']) ? 'selected' : '';
                                                                ?>
                                                                <option value="<?= (int) $lec['user_id'] ?>" <?= $selected ?>>
                                                                    <?= htmlspecialchars($lec['full_name'] ?: $lec['username']) ?>
                                                                </option>
                                                            <?php endforeach; ?>
                                                        </select>
                                                    </div>

                                                    <div style="min-width:140px">
                                                        <input name="schedule" placeholder="Lịch"
                                                            value="<?= htmlspecialchars($r['schedule'] ?? '') ?>" />
                                                    </div>

                                                    <div style="min-width:100px">
                                                        <input name="room" placeholder="Phòng"
                                                            value="<?= htmlspecialchars($r['room'] ?? '') ?>" />
                                                    </div>

                                                    <div style="min-width:120px">
                                                        <input name="semester" placeholder="Học kỳ"
                                                            value="<?= htmlspecialchars($r['semester'] ?? '') ?>" />
                                                    </div>

                                                    <button class="save" type="submit">Lưu</button>
                                                </form>

                                                <form method="post" onsubmit="return confirm('Xóa lớp học này?');"
                                                    style="margin:0">
                                                    <input type="hidden" name="action" value="delete" />
                                                    <input type="hidden" name="class_id" value="<?= (int) $r['class_id'] ?>" />
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