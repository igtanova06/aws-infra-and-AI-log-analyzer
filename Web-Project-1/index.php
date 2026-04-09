<?php
if (session_status() === PHP_SESSION_NONE) session_start();
$u = $_SESSION["user"] ?? null;
if ($u) {
  if ($u["role"] === "ADMIN") header("Location: /admin/dashboard.php");
  if ($u["role"] === "LECTURER") header("Location: /lecturer/dashboard.php");
  if ($u["role"] === "STUDENT") header("Location: /student/dashboard.php");
  exit;
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Hệ thống Quản lý Sinh viên - Đăng nhập">
  <title>Đăng Nhập - QLSV System</title>

  <link rel="stylesheet" href="/assets/css/style.css">
  <link rel="stylesheet" href="/assets/css/custom.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
  <div class="login-page">
    <div class="login-container animate-fade-in">
      <div class="login-card">
        <div class="login-header">
          <div class="login-logo">
            <i class="fas fa-graduation-cap"></i>
          </div>
          <h1>QLSV System</h1>
          <p>Hệ thống Quản lý Sinh viên</p>
        </div>

        <form class="login-form" id="loginForm">
          <div class="form-group animate-fade-in animate-delay-1">
            <label class="form-label" for="username">
              <i class="fas fa-user"></i> Tên đăng nhập
            </label>
            <input type="text" class="form-input" id="username" name="username" placeholder="Nhập tên đăng nhập..." required>
          </div>

          <div class="form-group animate-fade-in animate-delay-2">
            <label class="form-label" for="password">
              <i class="fas fa-lock"></i> Mật khẩu
            </label>
            <input type="password" class="form-input" id="password" name="password" placeholder="Nhập mật khẩu..." required>
          </div>

          <div class="form-group animate-fade-in animate-delay-3">
            <label class="form-label" for="role">
              <i class="fas fa-user-tag"></i> Vai trò
            </label>
            <select class="form-input form-select" id="role" name="role" required>
              <option value="">-- Chọn vai trò --</option>
              <option value="ADMIN">Quản trị viên</option>
              <option value="LECTURER">Giảng viên</option>
              <option value="STUDENT">Sinh viên</option>
            </select>
          </div>

          <div class="animate-fade-in animate-delay-4">
            <button type="submit" class="btn btn-primary">
              <i class="fas fa-sign-in-alt"></i> Đăng Nhập
            </button>
          </div>

          <div id="loginMsg" style="margin-top:12px;font-size:14px;"></div>
        </form>

        <div class="login-footer animate-fade-in animate-delay-4">
          <p class="text-muted mb-0">
            Quên mật khẩu? <a href="#">Liên hệ quản trị viên</a>
          </p>
        </div>
      </div>
    </div>
  </div>

<script>
  const form = document.getElementById("loginForm");
  const msgBox = document.getElementById("loginMsg");

  function showMsg(text, ok=false){
    msgBox.textContent = text;
    msgBox.style.color = ok ? "lime" : "salmon";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;

    if(!username || !password || !role){
      showMsg("Vui lòng nhập đủ tài khoản, mật khẩu và chọn vai trò!");
      return;
    }

    showMsg("Đang đăng nhập...");

    try{
      const res = await fetch("/api/login.php", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ username, password, role })
      });

      const data = await res.json();
      if(!data.ok){
        showMsg(data.message || "Đăng nhập thất bại!");
        return;
      }

      showMsg("Đăng nhập thành công!", true);
      setTimeout(() => {
        window.location.href = data.redirect || "/index.php";
      }, 250);

    }catch(err){
      showMsg("Lỗi kết nối API: " + err);
    }
  });
</script>
</body>
</html>
