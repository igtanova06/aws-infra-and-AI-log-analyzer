<?php
require_once __DIR__ . "/../api/auth.php";
require_role("STUDENT");
require_once __DIR__ . "/../inc/layout.php";

app_header("STUDENT • Điểm", "/student/grades.php");
?>
<div class="card">
  <h2>Bảng điểm</h2>

  <div class="table-wrap">
    <table class="table">
      <thead>
        <tr>
          <th>Môn</th>
          <th>Giữa kỳ</th>
          <th>Cuối kỳ</th>
          <th>Tổng kết</th>
          <th>Xếp loại</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>CT101 — CSDL</td>
          <td>7.5</td>
          <td>8.0</td>
          <td><b>7.8</b></td>
          <td><span class="badge ok">Khá</span></td>
        </tr>
        <tr>
          <td>CT102 — Java</td>
          <td>8.0</td>
          <td>8.5</td>
          <td><b>8.3</b></td>
          <td><span class="badge ok">Giỏi</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
<?php app_footer(); ?>
