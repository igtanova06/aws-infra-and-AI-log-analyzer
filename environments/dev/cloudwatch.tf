# ============================================================
# CloudWatch Logs Infrastructure
# ============================================================

# ── 1. VPC FLOW LOGS ────────────────────────────────────────

# Log Group cho VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/flowlogs"
  retention_in_days = 7 # Giữ logs 7 ngày để tiết kiệm chi phí

  tags = {
    Name        = "${local.name_prefix}-vpc-flow-logs"
    Description = "VPC Flow Logs for network traffic analysis"
  }
}

# IAM Role cho VPC Flow Logs
resource "aws_iam_role" "vpc_flow_logs_role" {
  name = "${local.name_prefix}-vpc-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-vpc-flow-logs-role"
  }
}

# IAM Policy cho VPC Flow Logs
resource "aws_iam_role_policy" "vpc_flow_logs_policy" {
  name = "${local.name_prefix}-vpc-flow-logs-policy"
  role = aws_iam_role.vpc_flow_logs_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# VPC Flow Log Resource
resource "aws_flow_log" "main" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs_role.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn
  traffic_type    = "ALL" # Capture ALL traffic (ACCEPT + REJECT)
  vpc_id          = aws_vpc.main.id

  tags = {
    Name        = "${local.name_prefix}-vpc-flow-log"
    Description = "Capture all VPC traffic for security analysis"
  }
}

# ── 2. APPLICATION LOGS ─────────────────────────────────────

# Log Group cho Application Logs (từ EC2)
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ec2/applogs"
  retention_in_days = 7

  tags = {
    Name        = "${local.name_prefix}-app-logs"
    Description = "Application logs from EC2 instances"
  }
}

# Log Group cho Web Tier Logs
resource "aws_cloudwatch_log_group" "web_logs" {
  name              = "/aws/ec2/weblogs"
  retention_in_days = 7

  tags = {
    Name        = "${local.name_prefix}-web-logs"
    Description = "Web tier application logs"
  }
}

# ── 3. CLOUDWATCH ALARMS ────────────────────────────────────

# Alarm cho High Error Rate trong VPC Flow Logs
resource "aws_cloudwatch_log_metric_filter" "vpc_reject_filter" {
  name           = "${local.name_prefix}-vpc-reject-count"
  log_group_name = aws_cloudwatch_log_group.vpc_flow_logs.name
  pattern        = "[version, account, eni, source, destination, srcport, destport, protocol, packets, bytes, windowstart, windowend, action=REJECT, flowlogstatus]"

  metric_transformation {
    name      = "VPCRejectCount"
    namespace = "${local.name_prefix}/VPC"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_vpc_rejects" {
  alarm_name          = "${local.name_prefix}-high-vpc-rejects"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "VPCRejectCount"
  namespace           = "${local.name_prefix}/VPC"
  period              = 300 # 5 minutes
  statistic           = "Sum"
  threshold           = 100 # Alert nếu >100 REJECT trong 5 phút
  alarm_description   = "Alert when VPC rejects exceed threshold"
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${local.name_prefix}-high-vpc-rejects-alarm"
  }
}

# Metric Filter cho Application Errors
resource "aws_cloudwatch_log_metric_filter" "app_error_filter" {
  name           = "${local.name_prefix}-app-error-count"
  log_group_name = aws_cloudwatch_log_group.app_logs.name
  pattern        = "ERROR"

  metric_transformation {
    name      = "ApplicationErrorCount"
    namespace = "${local.name_prefix}/Application"
    value     = "1"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_app_errors" {
  alarm_name          = "${local.name_prefix}-high-app-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApplicationErrorCount"
  namespace           = "${local.name_prefix}/Application"
  period              = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "Alert when application errors exceed threshold"
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${local.name_prefix}-high-app-errors-alarm"
  }
}

# ── 4. SNS TOPIC (Optional - cho CloudWatch Alarms) ────────

resource "aws_sns_topic" "cloudwatch_alarms" {
  name = "${local.name_prefix}-cloudwatch-alarms"

  tags = {
    Name        = "${local.name_prefix}-cloudwatch-alarms-topic"
    Description = "SNS topic for CloudWatch alarm notifications"
  }
}

# Output SNS Topic ARN để có thể subscribe email/SMS sau
output "cloudwatch_alarms_topic_arn" {
  description = "SNS Topic ARN for CloudWatch alarms - subscribe email/SMS to receive alerts"
  value       = aws_sns_topic.cloudwatch_alarms.arn
}
