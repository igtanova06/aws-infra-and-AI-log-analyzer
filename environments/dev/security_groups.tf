# ── ALB SG — nhận HTTP/HTTPS từ internet ────────────────────────────
resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-sg-alb"
  description = "Allow HTTP/HTTPS inbound from internet"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-sg-alb"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = local.ports.http
  to_port           = local.ports.http
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = local.ports.https
  to_port           = local.ports.https
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "alb_egress" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ── App SG — chỉ nhận từ ALB SG ─────────────────────────────────────
resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-sg-app"
  description = "Allow inbound from ALB SG only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-sg-app"
  }
}

resource "aws_vpc_security_group_ingress_rule" "app_from_alb" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = local.ports.app
  to_port                      = local.ports.app
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "app_egress" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

# ── DB SG — chỉ nhận từ App SG ──────────────────────────────────────
resource "aws_security_group" "db" {
  name        = "${local.name_prefix}-sg-db"
  description = "Allow inbound from App SG only"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "${local.name_prefix}-sg-db"
  }
}

resource "aws_vpc_security_group_ingress_rule" "db_from_app_postgres" {
  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = aws_security_group.app.id
  from_port                    = local.ports.db
  to_port                      = local.ports.db
  ip_protocol                  = "tcp"
}

# DB không có egress — isolated by design, deny all outbound