<?php
require_once __DIR__ . "/../api/auth.php";
require_role("STUDENT");
require_once __DIR__ . "/../inc/layout.php";

app_header("STUDENT • Lịch học", "/student/schedule.php");
?>
<div class="card">
  <h2>Lịch học tuần này</h2>

  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th>Thứ</th>
          <th>Môn</th>
          <th>Phòng</th>
          <th>Tiết</th>
          <th>Giảng viên</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Thứ 2</td>
          <td><b>CT101</b> — CSDL</td>
          <td>A101</td>
          <td>1-3</td>
          <td>GV01</td>
        </tr>
        <tr>
          <td>Thứ 4</td>
          <td><b>CT102</b> — Java</td>
          <td>B203</td>
          <td>4-6</td>
          <td>GV02</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
<?php app_footer(); ?>
