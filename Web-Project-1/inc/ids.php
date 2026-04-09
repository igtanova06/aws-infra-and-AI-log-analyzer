<?php
require_once __DIR__ . "/../api/db.php";

function get_lecturer_id_by_user($user_id){
  global $mysqli;
  $stmt = $mysqli->prepare("SELECT lecturer_id FROM lecturers WHERE user_id=? LIMIT 1");
  $stmt->bind_param("i", $user_id);
  $stmt->execute();
  $row = $stmt->get_result()->fetch_assoc();
  return $row ? (int)$row["lecturer_id"] : 0;
}

function get_student_id_by_user($user_id){
  global $mysqli;
  $stmt = $mysqli->prepare("SELECT student_id FROM students WHERE user_id=? LIMIT 1");
  $stmt->bind_param("i", $user_id);
  $stmt->execute();
  $row = $stmt->get_result()->fetch_assoc();
  return $row ? (int)$row["student_id"] : 0;
}
