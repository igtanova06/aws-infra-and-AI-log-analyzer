resource "aws_lb" "alb" {
	name               = "${local.name_prefix}-alb"
	internal           = false
	load_balancer_type = "application"
	security_groups    = [aws_security_group.alb.id]
	subnets            = [for subnet in aws_subnet.public : subnet.id]

	enable_deletion_protection = false

	tags = {
		Name = "${local.name_prefix}-alb"
	}
}

resource "aws_lb_target_group" "app" {
	name_prefix     = "p1-tg-" # Tên ngắn lại để AWS thêm mã ngẫu nhiên vào sau
	port     = local.ports.app
	protocol = "HTTP"
	target_type = "instance"
	vpc_id   = aws_vpc.main.id

	health_check {
		enabled             = true
		healthy_threshold   = 3
		interval            = 30
		matcher             = "200-399"
		path                = "/_stcore/health"
		port                = "traffic-port"
		protocol            = "HTTP"
		timeout             = 10
		unhealthy_threshold = 5
	}

	lifecycle {
		create_before_destroy = true
	}

	tags = {
		Name = "${local.name_prefix}-tg"
	}
}

resource "aws_lb_listener" "app" {
	load_balancer_arn = aws_lb.alb.arn
	port = local.ports.http
	protocol = "HTTP"
	default_action {
		type = "forward"
		target_group_arn = aws_lb_target_group.app.arn
	}
}

# ── Target Group cho Web App QLSV (Port 8080) ────────────────────────
resource "aws_lb_target_group" "qlsv" {
	name_prefix     = "qlsv-"
	port     = 8080
	protocol = "HTTP"
	target_type = "instance"
	vpc_id   = aws_vpc.main.id

	health_check {
		enabled             = true
		healthy_threshold   = 3
		interval            = 30
		matcher             = "200-399"
		path                = "/" # Web App PHP thường có index ở gốc
		port                = "traffic-port"
		protocol            = "HTTP"
		timeout             = 10
		unhealthy_threshold = 5
	}

	lifecycle {
		create_before_destroy = true
	}

	tags = {
		Name = "${local.name_prefix}-tg-qlsv"
	}
}

# ── Điều hướng Path /qlsv/* về Web App QLSV ──────────────────────────
resource "aws_lb_listener_rule" "qlsv" {
  listener_arn = aws_lb_listener.app.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.qlsv.id
  }

  condition {
    path_pattern {
      # Gộp lại thành 5 cái để AWS không la mắng nữa
      values = ["/qlsv*", "/api/*", "/admin/*", "/assets/*", "/*.php"] 
    }
  }
}

# Gắn Target Group mới vào ASG