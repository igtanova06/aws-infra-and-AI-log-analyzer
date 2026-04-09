<?php
// /admin/lecturers.php
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

// Lấy role_id LECTURER để tạo user mới
$roleLecturerId = 2;
$rs = $mysqli->query("SELECT role_id FROM roles WHERE role_code='LECTURER' LIMIT 1");
if ($rs && ($row = $rs->fetch_assoc()))
    $roleLecturerId = (int) $row['role_id'];

// CREATE lecturer (tạo user với role LECTURER)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'create') {
    $username = trim((string) ($_POST['username'] ?? ''));
    $full_name = trim((string) ($_POST['full_name'] ?? ''));
    $email = trim((string) ($_POST['email'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');
    $phone = trim((string) ($_POST['phone'] ?? ''));

    if ($username === "" || $full_name === "" || $email === "" || $password === "") {
        $err = "Thiếu dữ liệu (username/full_name/email/password).";
    } else {
        // hash theo scheme bạn đang dùng trong login.php: SHA2(password + username + '_salt', 256)
        $mysqli->begin_transaction();
        try {
            $sqlU = "INSERT INTO users (username, password, full_name, email, phone, role_id, is_active) 
               VALUES (?, SHA2(CONCAT(?, ?, '_salt'), 256), ?, ?, ?, ?, 1)";
            $stU = $mysqli->prepare($sqlU);
            $stU->bind_param("ssssssi", $username, $password, $username, $full_name, $email, $phone, $roleLecturerId);
            if (!$stU->execute())
                throw new Exception($mysqli->error);

            $mysqli->commit();
            $ok = "Đã tạo giảng viên mới!";
        } catch (Exception $e) {
            $mysqli->rollback();
            $err = "Lỗi tạo giảng viên: " . $e->getMessage();
        }
    }
}

// UPDATE lecturer info
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'update') {
    $user_id = (int) ($_POST['user_id'] ?? 0);
    $full_name = trim((string) ($_POST['full_name'] ?? ''));
    $email = trim((string) ($_POST['email'] ?? ''));
    $phone = trim((string) ($_POST['phone'] ?? ''));
    $is_active = (int) ($_POST['is_active'] ?? 1);

    if ($user_id <= 0) {
        $err = "Thiếu user_id.";
    } else {
        $sql = "UPDATE users SET full_name = ?, email = ?, is_active = ? WHERE user_id = ? AND role_id = ?";
        $st = $mysqli->prepare($sql);
        $st->bind_param("ssiii", $full_name, $email, $is_active, $user_id, $roleLecturerId);
        if ($st->execute())
            $ok = "Đã cập nhật!";
        else
            $err = "Lỗi cập nhật: " . $mysqli->error;
    }
}

// DELETE lecturer
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'delete') {
    $user_id = (int) ($_POST['user_id'] ?? 0);
    if ($user_id <= 0) {
        $err = "Thiếu user_id.";
    } else {
        $mysqli->begin_transaction();
        try {
            // Xóa user (giảng viên)
            $st = $mysqli->prepare("DELETE FROM users WHERE user_id = ? AND role_id = ?");
            $st->bind_param("ii", $user_id, $roleLecturerId);
            if (!$st->execute())
                throw new Exception($mysqli->error);

            $mysqli->commit();
            $ok = "Đã xóa giảng viên!";
        } catch (Exception $e) {
            $mysqli->rollback();
            $err = "Lỗi xóa: " . $e->getMessage();
        }
    }
}

// Load lecturer list
$sqlList = "
SELECT 
  u.user_id,
  u.username,
  u.full_name,
  u.email,
  u.is_active,
  u.created_at
FROM users u
WHERE u.role_id = ?
ORDER BY u.user_id DESC
";
$stList = $mysqli->prepare($sqlList);
$stList->bind_param("i", $roleLecturerId);
$stList->execute();
$r = $stList->get_result();
$rows = $r ? $r->fetch_all(MYSQLI_ASSOC) : [];
?>
<!doctype html>
<html lang="vi">

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>ADMIN • Quản lý giảng viên</title>
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
                <h1 class="h1">Quản lý giảng viên</h1>
                <span class="pill">Quyền: ADMIN</span>
            </div>

            <?php if ($ok): ?>
                <div class="alert ok"><?= htmlspecialchars($ok) ?></div><?php endif; ?>
            <?php if ($err): ?>
                <div class="alert err"><?= htmlspecialchars($err) ?></div><?php endif; ?>

            <div class="card">
                <h3 style="margin:0 0 10px 0">Tạo giảng viên mới</h3>
                <form method="post" class="grid">
                    <input type="hidden" name="action" value="create" />
                    <div><input name="username" placeholder="Mã GV (VD: GV01)" required></div>
                    <div><input name="full_name" placeholder="Họ tên" required></div>
                    <div><input name="email" placeholder="Email" required></div>
                    <div><input name="password" placeholder="Mật khẩu" required></div>
                    <div><input name="phone" placeholder="Số điện thoại (tùy chọn)"></div>
                    <div style="grid-column:1/-1">
                        <button class="save" type="submit">Tạo</button>
                    </div>
                </form>
            </div>

            <div class="card">
                <h3 style="margin:0 0 10px 0">Danh sách giảng viên</h3>
                <div class="tablewrap">
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Mã GV</th>
                                <th>Họ tên</th>
                                <th>Email</th>
                                <th>Trạng thái</th>
                                <th>Ngày tạo</th>
                                <th>Cập nhật</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php if (!$rows): ?>
                                <tr>
                                    <td colspan="7" style="opacity:.85;padding:14px">Chưa có dữ liệu giảng viên.</td>
                                </tr>
                            <?php else: ?>
                                <?php foreach ($rows as $r): ?>
                                    <tr>
                                        <td><b>#<?= (int) $r['user_id'] ?></b></td>
                                        <td><?= htmlspecialchars($r['username']) ?></td>
                                        <td><?= htmlspecialchars($r['full_name']) ?></td>
                                        <td style="opacity:.9"><?= htmlspecialchars($r['email']) ?></td>
                                        <td><?= ($r['is_active'] == 1) ? 'Hoạt động' : 'Khóa' ?></td>
                                        <td><?= $r['created_at'] ? date('d/m/Y', strtotime($r['created_at'])) : '-' ?></td>
                                        <td>
                                            <div class="act">
                                                <form method="post" class="row" style="margin:0">
                                                    <input type="hidden" name="action" value="update" />
                                                    <input type="hidden" name="user_id" value="<?= (int) $r['user_id'] ?>" />

                                                    <div style="min-width:200px">
                                                        <input name="full_name" placeholder="Họ tên"
                                                            value="<?= htmlspecialchars($r['full_name']) ?>" />
                                                    </div>

                                                    <div style="min-width:200px">
                                                        <input name="email" placeholder="Email"
                                                            value="<?= htmlspecialchars($r['email']) ?>" />
                                                    </div>

                                                    <div style="min-width:140px">
                                                        <select name="is_active">
                                                            <option value="1" <?= ($r['is_active'] == 1) ? 'selected' : '' ?>>Hoạt
                                                                động</option>
                                                            <option value="0" <?= ($r['is_active'] == 0) ? 'selected' : '' ?>>Khóa
                                                            </option>
                                                        </select>
                                                    </div>

                                                    <button class="save" type="submit">Lưu</button>
                                                </form>

                                                <form method="post" onsubmit="return confirm('Xóa giảng viên này?');"
                                                    style="margin:0">
                                                    <input type="hidden" name="action" value="delete" />
                                                    <input type="hidden" name="user_id" value="<?= (int) $r['user_id'] ?>" />
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