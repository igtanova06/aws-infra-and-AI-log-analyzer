# ============================================================
# CloudWatch Logs Infrastructure - OPTIMIZED
# Strategy: Filter + Structure + Retention
# Reduced from 9 → 5 log groups (44% reduction)
# ============================================================

# ── Infrastructure Log Groups (KEEP AS-IS) ──────────────────

# VPC Flow Logs - Network traffic analysis
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/flowlogs"
  retention_in_days = 7

  tags = {
    Name        = "${local.name_prefix}-vpc-flowlogs"
    Environment = var.env
    ManagedBy   = "Terraform"
    Purpose     = "Network security analysis"
  }
}

# CloudTrail Logs - AWS API audit trail
resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = "/aws/cloudtrail/logs"
  retention_in_days = 90  # Compliance requirement - increased from 7

  tags = {
    Name        = "${local.name_prefix}-cloudtrail-logs"
    Environment = var.env
    ManagedBy   = "Terraform"
    Purpose     = "Audit & compliance"
  }
}

# ── Application Tier Logs (CONSOLIDATED) ───────────────────

# Consolidated Web + App Logs
# Combines: web-tier/system, web-tier/httpd, web-tier/application, app-tier/system
# Strategy: Use log streams to separate sources within one group
resource "aws_cloudwatch_log_group" "application_logs" {
  name              = "/aws/ec2/application"
  retention_in_days = 14  # Business-critical logs

  tags = {
    Name        = "${local.name_prefix}-application-logs"
    Environment = var.env
    ManagedBy   = "Terraform"
    Purpose     = "Web + App tier consolidated logs"
    LogStreams  = "web-system, web-httpd, web-app, app-system, app-streamlit"
  }
}

# Log Stream Structure within /aws/ec2/application:
# - {instance-id}/web/system      → /var/log/messages, /var/log/secure
# - {instance-id}/web/httpd       → /var/log/httpd/access_log, error_log
# - {instance-id}/web/application → /var/www/html/logs/app.log
# - {instance-id}/app/system      → /var/log/messages
# - {instance-id}/app/streamlit   → /app/logs/streamlit.log

# ── Database Log Groups (KEEP AS-IS) ────────────────────────

# RDS MySQL - Error Logs
resource "aws_cloudwatch_log_group" "rds_error" {
  name              = "/aws/rds/mysql/error"
  retention_in_days = 7

  tags = {
    Name        = "${local.name_prefix}-rds-error-logs"
    Environment = var.env
    ManagedBy   = "Terraform"
    Purpose     = "Database error tracking"
  }
}

# RDS MySQL - Slow Query Logs
resource "aws_cloudwatch_log_group" "rds_slowquery" {
  name              = "/aws/rds/mysql/slowquery"
  retention_in_days = 14  # Performance optimization needs longer retention

  tags = {
    Name        = "${local.name_prefix}-rds-slowquery-logs"
    Environment = var.env
    ManagedBy   = "Terraform"
    Purpose     = "Database performance analysis"
  }
}

# ── Metric Filters for Consolidated Logs ───────────────────

# Filter 1: Web HTTP Errors (4xx, 5xx)
resource "aws_cloudwatch_log_metric_filter" "web_http_errors" {
  name           = "${local.name_prefix}-web-http-errors"
  log_group_name = aws_cloudwatch_log_group.application_logs.name
  
  # Match Apache/Nginx error logs with status codes 4xx or 5xx
  pattern = "[time, request_id, ip, method, uri, status_code=4* || status_code=5*, ...]"

  metric_transformation {
    name      = "WebHTTPErrors"
    namespace = "${local.name_prefix}/Application"
    value     = "1"
    default_value = 0
    
    dimensions = {
      Environment = var.env
      Tier        = "Web"
    }
  }
}

# Filter 2: Application Errors (ERROR, CRITICAL, FATAL)
resource "aws_cloudwatch_log_metric_filter" "app_errors" {
  name           = "${local.name_prefix}-app-errors"
  log_group_name = aws_cloudwatch_log_group.application_logs.name
  
  # Match log lines with ERROR, CRITICAL, or FATAL severity
  pattern = "?ERROR ?CRITICAL ?FATAL"

  metric_transformation {
    name      = "ApplicationErrors"
    namespace = "${local.name_prefix}/Application"
    value     = "1"
    default_value = 0
    
    dimensions = {
      Environment = var.env
    }
  }
}

# Filter 3: Security Events (SSH failures, SQL injection, etc.)
resource "aws_cloudwatch_log_metric_filter" "security_events" {
  name           = "${local.name_prefix}-security-events"
  log_group_name = aws_cloudwatch_log_group.application_logs.name
  
  # Match security-related keywords
  pattern = "?\"Failed password\" ?\"SQL injection\" ?\"authentication failure\" ?\"brute force\" ?\"unauthorized\""

  metric_transformation {
    name      = "SecurityEvents"
    namespace = "${local.name_prefix}/Security"
    value     = "1"
    default_value = 0
    
    dimensions = {
      Environment = var.env
    }
  }
}

# ── IAM Role for VPC Flow Logs ─────────────────────────────

resource "aws_iam_role" "flow_logs" {
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

resource "aws_iam_role_policy" "flow_logs" {
  name = "${local.name_prefix}-vpc-flow-logs-policy"
  role = aws_iam_role.flow_logs.id

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

# ── VPC Flow Logs ───────────────────────────────────────────

resource "aws_flow_log" "main" {
  vpc_id          = aws_vpc.main.id
  traffic_type    = "REJECT"  # OPTIMIZED: Only log rejected traffic (security focus)
  iam_role_arn    = aws_iam_role.flow_logs.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs.arn

  tags = {
    Name        = "${local.name_prefix}-vpc-flow-log"
    Environment = var.env
  }
}

# ── IAM Policy for EC2 to Write CloudWatch Logs ────────────

resource "aws_iam_policy" "cloudwatch_agent_policy" {
  name        = "${local.name_prefix}-cloudwatch-agent-policy"
  description = "Allow EC2 instances to write logs to CloudWatch (optimized)"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          # Consolidated application log group
          aws_cloudwatch_log_group.application_logs.arn,
          "${aws_cloudwatch_log_group.application_logs.arn}:*",
          # Infrastructure log groups
          aws_cloudwatch_log_group.vpc_flow_logs.arn,
          "${aws_cloudwatch_log_group.vpc_flow_logs.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-cloudwatch-agent-policy"
  }
}

resource "aws_iam_role_policy_attachment" "cloudwatch_agent_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.cloudwatch_agent_policy.arn
}

# ── CloudWatch Alarms ───────────────────────────────────────

# Alarm 1: High HTTP Error Rate
resource "aws_cloudwatch_metric_alarm" "high_http_errors" {
  alarm_name          = "${local.name_prefix}-high-http-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "WebHTTPErrors"
  namespace           = "${local.name_prefix}/Application"
  period              = "300"
  statistic           = "Sum"
  threshold           = "50"
  alarm_description   = "Alert when HTTP errors exceed 50 in 5 minutes"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Environment = var.env
    Tier        = "Web"
  }

  tags = {
    Name        = "${local.name_prefix}-http-errors-alarm"
    Environment = var.env
  }
}

# Alarm 2: Security Events Detected
resource "aws_cloudwatch_metric_alarm" "security_events" {
  alarm_name          = "${local.name_prefix}-security-events"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "SecurityEvents"
  namespace           = "${local.name_prefix}/Security"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Alert when security events exceed 10 in 5 minutes"
  treat_missing_data  = "notBreaching"

  dimensions = {
    Environment = var.env
  }

  tags = {
    Name        = "${local.name_prefix}-security-alarm"
    Environment = var.env
    Severity    = "HIGH"
  }
}

# Alarm 3: VPC Rejected Connections
resource "aws_cloudwatch_metric_alarm" "vpc_rejected_connections" {
  alarm_name          = "${local.name_prefix}-vpc-high-rejects"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "PacketsDropped"
  namespace           = "AWS/VPC"
  period              = "300"
  statistic           = "Sum"
  threshold           = "100"
  alarm_description   = "Alert when VPC rejects more than 100 packets in 5 minutes"
  treat_missing_data  = "notBreaching"

  dimensions = {
    VpcId = aws_vpc.main.id
  }

  tags = {
    Name        = "${local.name_prefix}-vpc-rejects-alarm"
    Environment = var.env
  }
}

# ── Outputs ─────────────────────────────────────────────────

output "cloudwatch_log_groups" {
  description = "CloudWatch Log Groups created (optimized structure)"
  value = {
    # Infrastructure (2 groups)
    vpc_flow_logs = aws_cloudwatch_log_group.vpc_flow_logs.name
    cloudtrail    = aws_cloudwatch_log_group.cloudtrail.name
    
    # Application - Consolidated (1 group replaces 5 groups)
    application = aws_cloudwatch_log_group.application_logs.name
    
    # Database (2 groups)
    rds_error     = aws_cloudwatch_log_group.rds_error.name
    rds_slowquery = aws_cloudwatch_log_group.rds_slowquery.name
  }
}

output "optimization_summary" {
  description = "Log groups optimization summary"
  value = {
    before = {
      total_groups = 9
      structure    = "Separate groups per tier and log type"
    }
    after = {
      total_groups = 5
      structure    = "Consolidated application logs with log streams"
      reduction    = "44% fewer log groups"
    }
    benefits = [
      "Reduced management overhead",
      "Lower CloudWatch Logs API costs",
      "Easier querying with CloudWatch Insights",
      "Centralized metric filters",
      "Better log correlation"
    ]
  }
}
