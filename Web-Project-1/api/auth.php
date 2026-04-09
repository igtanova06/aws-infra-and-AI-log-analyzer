<?php
if (session_status() === PHP_SESSION_NONE) session_start();

function require_login(){
  if (empty($_SESSION["user"])) {
    header("Location: /index.php");
    exit;
  }
}

function require_role($role){
  require_login();
  $u = $_SESSION["user"];
  if (($u["role"] ?? "") !== $role) {
    header("Location: /index.php");
    exit;
  }
}

function role_code_from_id($id){
  $id = (int)$id;
  if ($id === 1) return "ADMIN";
  if ($id === 2) return "LECTURER";
  if ($id === 3) return "STUDENT";
  return "UNKNOWN";
}
