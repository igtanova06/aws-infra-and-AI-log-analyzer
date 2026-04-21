resource "aws_db_subnet_group" "db" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.db[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%"
}

resource "aws_db_instance" "main" {
  identifier           = "${local.name_prefix}-db"
  instance_class       = "db.t3.micro"
  engine               = "mysql"
  engine_version       = "8.0"
  username             = var.db_username 
  password             = random_password.db_password.result # Dùng pass ngẫu nhiên
  db_name              = "qlsv_system"
  
  allocated_storage     = 20
  storage_type          = "gp2"
  db_subnet_group_name  = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot   = true
  multi_az             = false
  
  # Enable CloudWatch Logs export
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  
  # Enable Performance Insights (optional but recommended)
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  
  # Backup configuration
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  
  tags = {
    Name        = "${local.name_prefix}-db"
    Environment = var.env
  }
}

output "db_endpoint" {
  value = aws_db_instance.main.address
}

# Output này giúp bạn lấy mật khẩu mà không cần mò vào Console
output "db_password" {
  value     = random_password.db_password.result
  sensitive = true
}