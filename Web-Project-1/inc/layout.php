<?php
require_once __DIR__ . "/../api/auth.php";

function h($s)
{
  return htmlspecialchars((string) ($s ?? ""), ENT_QUOTES, "UTF-8");
}

function menu_items($role)
{
  if ($role === "ADMIN") {
    return [
      ["label" => "Dashboard", "icon" => "fa-gauge", "href" => "/admin/dashboard.php"],
      ["label" => "Sinh viên", "icon" => "fa-users", "href" => "/admin/students.php"],
      ["label" => "Giảng viên", "icon" => "fa-chalkboard-user", "href" => "/admin/lecturers.php"],
      ["label" => "Lớp học", "icon" => "fa-door-open", "href" => "/admin/classes.php"],
    ];
  }
  if ($role === "LECTURER") {
    return [
      ["label" => "Dashboard", "icon" => "fa-chalkboard-user", "href" => "/lecturer/dashboard.php"],
      ["label" => "Lịch dạy", "icon" => "fa-calendar-days", "href" => "/lecturer/teaching.php"],
      ["label" => "Chấm điểm", "icon" => "fa-pen-to-square", "href" => "/lecturer/grading.php"],
    ];
  }
  if ($role === "STUDENT") {
    return [
      ["label" => "Dashboard", "icon" => "fa-user-graduate", "href" => "/student/dashboard.php"],
      ["label" => "Lịch học", "icon" => "fa-calendar-check", "href" => "/student/schedule.php"],
      ["label" => "Điểm", "icon" => "fa-chart-column", "href" => "/student/grades.php"],
    ];
  }
  return [];
}

function app_header($title, $activeHref = "")
{
  $u = $_SESSION["user"] ?? null;
  $name = $u ? ($u["full_name"] ?: $u["username"]) : "Guest";
  $role = $u ? ($u["role"] ?? "") : "";
  ?>
  <!doctype html>
  <html lang="vi">

  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title><?= h($title) ?></title>
    <link rel="stylesheet" href="/assets/css/style.css">
    <link rel="stylesheet" href="/assets/css/custom.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  </head>

  <body>
    <div class="app">
      <header class="horizontal-header">
        <div class="header-container">
          <div class="brand">
            <div class="logo"><i class="fa-solid fa-graduation-cap"></i></div>
            <div>
              <p class="t1">QLSV System</p>
              <p class="t2">Hệ thống quản lý sinh viên</p>
            </div>
          </div>

          <?php if ($u): ?>
            <nav class="horizontal-nav">
              <?php foreach (menu_items($role) as $it):
                $isActive = ($activeHref === $it["href"]) ? "active" : "";
                ?>
                <a class="<?= $isActive ?>" href="<?= h($it["href"]) ?>">
                  <i class="fa-solid <?= h($it["icon"]) ?>"></i> <?= h($it["label"]) ?>
                </a>
              <?php endforeach; ?>
            </nav>

            <div class="user-section">
              <span class="user-info">
                <i class="fa-solid fa-user"></i>
                <b><?= h($name) ?></b> • <span class="badge"><?= h($role) ?></span>
              </span>
              <a class="btnx danger" href="/api/logout.php">
                <i class="fa-solid fa-right-from-bracket"></i> Logout
              </a>
            </div>
          <?php else: ?>
            <nav class="horizontal-nav">
              <a class="active" href="/index.php"><i class="fa-solid fa-right-to-bracket"></i> Login</a>
            </nav>
          <?php endif; ?>
        </div>
      </header>

      <main class="main">
        <div class="container">
          <div class="page-title">
            <h1><?= h($title) ?></h1>
          </div>
          <?php
}

function app_footer()
{
  ?>
          <div class="footer-note">© QLSV System</div>
        </div>
      </main>
    </div>
  </body>

  </html>
  <?php
}

