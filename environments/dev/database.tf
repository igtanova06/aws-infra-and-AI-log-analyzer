resource "aws_db_subnet_group" "db" {
  name = "${local.name_prefix}-db-subnet-group"
  subnet_ids = [for subnet in aws_subnet.db : subnet.id]

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}


resource "aws_db_instance" "main" {
  identifier = "${local.name_prefix}-db"
  instance_class = "db.t3.micro"
  engine         = "postgres"
  engine_version = "15"
  username = "dbadmin"

  allocated_storage = 20
  storage_type = "gp2"
  password = random_password.db_password.result
  db_subnet_group_name = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot = true
  multi_az = false
  backup_retention_period = 0 # Free tier không hỗ trợ backup retention > 0

}

resource "random_password" "db_password" {
  length = 8
  special = true
  override_special = "!#$"
}