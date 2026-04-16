data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-ebs"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── WEB TIER (Presentation - PHP App) ──────────────────────────
resource "aws_launch_template" "web" {
  name_prefix   = "${local.name_prefix}-web-lt-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  iam_instance_profile { name = aws_iam_instance_profile.ec2_instance_profile.name }
  vpc_security_group_ids = [aws_security_group.web.id]
  tag_specifications {
    resource_type = "instance"
    tags = { Name = "${local.name_prefix}-web-node" }
  }
}

resource "aws_autoscaling_group" "web" {
  for_each = tomap({
    "web-1" = aws_subnet.private[0].id
    "web-2" = aws_subnet.private[1].id
  })

  name                = "${local.name_prefix}-asg-${each.key}"
  vpc_zone_identifier = [each.value]
  desired_capacity    = 1
  min_size            = 1
  max_size            = 1
  target_group_arns   = [aws_lb_target_group.qlsv.arn]
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-${each.key}"
    propagate_at_launch = true
  }
}

# ── APP TIER (Logic - Log Analysis) ─────────────────────────────
resource "aws_launch_template" "app" {
  name_prefix   = "${local.name_prefix}-app-lt-"
  image_id      = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
  iam_instance_profile { name = aws_iam_instance_profile.ec2_instance_profile.name }
  vpc_security_group_ids = [aws_security_group.app.id]
  tag_specifications {
    resource_type = "instance"
    tags = { Name = "${local.name_prefix}-app-node" }
  }
}

resource "aws_autoscaling_group" "app" {
  for_each = tomap({
    "app-1" = aws_subnet.private[0].id
    "app-2" = aws_subnet.private[1].id
  })

  name                = "${local.name_prefix}-asg-${each.key}"
  vpc_zone_identifier = [each.value]
  desired_capacity    = 1
  min_size            = 1
  max_size            = 1
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${local.name_prefix}-${each.key}"
    propagate_at_launch = true
  }
}
