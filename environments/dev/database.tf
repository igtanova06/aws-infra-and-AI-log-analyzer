resource "aws_db_subnet_group" "db" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.db[*].id

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

data "aws_db_instance" "existing_db" {
  db_instance_identifier = var.existing_db_identifier
}

output "db_endpoint" {
  value = data.aws_db_instance.existing_db.endpoint
}