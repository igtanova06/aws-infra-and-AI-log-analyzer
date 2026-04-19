# ============================================================
# AWS CloudTrail Configuration
# Track all API calls for security auditing
# ============================================================

# ── 1. S3 BUCKET FOR CLOUDTRAIL ────────────────────────────

resource "aws_s3_bucket" "cloudtrail" {
  bucket = "${local.name_prefix}-cloudtrail-logs"

  tags = {
    Name        = "${local.name_prefix}-cloudtrail-logs"
    Description = "S3 bucket for CloudTrail logs storage"
  }
}

# Versioning cho CloudTrail bucket
resource "aws_s3_bucket_versioning" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption cho CloudTrail bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle rule - xóa logs cũ sau 90 ngày để tiết kiệm chi phí
resource "aws_s3_bucket_lifecycle_configuration" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  rule {
    id     = "delete-old-logs"
    status = "Enabled"

    filter {
      prefix = "AWSLogs/"
    }

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket Policy cho CloudTrail
resource "aws_s3_bucket_policy" "cloudtrail" {
  bucket = aws_s3_bucket.cloudtrail.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# ── 2. CLOUDWATCH LOG GROUP FOR CLOUDTRAIL ─────────────────

resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = "/aws/cloudtrail/logs"
  retention_in_days = 7

  tags = {
    Name        = "${local.name_prefix}-cloudtrail-logs"
    Description = "CloudTrail logs for API activity monitoring"
  }
}

# ── 3. IAM ROLE FOR CLOUDTRAIL ─────────────────────────────

resource "aws_iam_role" "cloudtrail" {
  name = "${local.name_prefix}-cloudtrail-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${local.name_prefix}-cloudtrail-role"
  }
}

# IAM Policy cho CloudTrail để ghi vào CloudWatch Logs
resource "aws_iam_role_policy" "cloudtrail_cloudwatch" {
  name = "${local.name_prefix}-cloudtrail-cloudwatch-policy"
  role = aws_iam_role.cloudtrail.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
      }
    ]
  })
}

# ── 4. CLOUDTRAIL ──────────────────────────────────────────

resource "aws_cloudtrail" "main" {
  name                          = "${local.name_prefix}-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  include_global_service_events = true
  is_multi_region_trail         = false # Single region để tiết kiệm chi phí
  enable_logging                = true

  # Gửi logs đến CloudWatch để AI phân tích
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
  cloud_watch_logs_role_arn  = aws_iam_role.cloudtrail.arn

  # Event selectors - chỉ log management events
  event_selector {
    read_write_type           = "All"
    include_management_events = true

    # Không log data events (S3/Lambda) để tiết kiệm chi phí
    # Nếu cần, uncomment phần dưới:
    # data_resource {
    #   type   = "AWS::S3::Object"
    #   values = ["arn:aws:s3:::${aws_s3_bucket.cloudtrail.id}/*"]
    # }
  }

  tags = {
    Name        = "${local.name_prefix}-cloudtrail"
    Description = "CloudTrail for API activity monitoring and security analysis"
  }

  depends_on = [
    aws_s3_bucket_policy.cloudtrail,
    aws_iam_role_policy.cloudtrail_cloudwatch
  ]
}

# ── 5. CLOUDWATCH METRIC FILTERS ───────────────────────────

# Filter cho AccessDenied events
resource "aws_cloudwatch_log_metric_filter" "access_denied" {
  name           = "${local.name_prefix}-access-denied-count"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ $.errorCode = \"AccessDenied\" || $.errorCode = \"UnauthorizedOperation\" }"

  metric_transformation {
    name      = "AccessDeniedCount"
    namespace = "${local.name_prefix}/Security"
    value     = "1"
    unit      = "Count"
  }
}

# Alarm cho AccessDenied
resource "aws_cloudwatch_metric_alarm" "access_denied" {
  alarm_name          = "${local.name_prefix}-access-denied-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "AccessDeniedCount"
  namespace           = "${local.name_prefix}/Security"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when access denied events exceed threshold"
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${local.name_prefix}-access-denied-alarm"
  }
}

# Filter cho Root Account Usage
resource "aws_cloudwatch_log_metric_filter" "root_usage" {
  name           = "${local.name_prefix}-root-usage-count"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ $.userIdentity.type = \"Root\" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != \"AwsServiceEvent\" }"

  metric_transformation {
    name      = "RootAccountUsageCount"
    namespace = "${local.name_prefix}/Security"
    value     = "1"
    unit      = "Count"
  }
}

# Alarm cho Root Account Usage (CRITICAL)
resource "aws_cloudwatch_metric_alarm" "root_usage" {
  alarm_name          = "${local.name_prefix}-root-usage-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "RootAccountUsageCount"
  namespace           = "${local.name_prefix}/Security"
  period              = 60 # 1 minute - critical alert
  statistic           = "Sum"
  threshold           = 0 # Alert ngay khi có root usage
  alarm_description   = "CRITICAL: Root account is being used"
  treat_missing_data  = "notBreaching"

  tags = {
    Name     = "${local.name_prefix}-root-usage-alarm"
    Severity = "CRITICAL"
  }
}

# Filter cho Console Login Failures
resource "aws_cloudwatch_log_metric_filter" "console_login_failures" {
  name           = "${local.name_prefix}-console-login-failures"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ $.eventName = \"ConsoleLogin\" && $.errorMessage = \"Failed authentication\" }"

  metric_transformation {
    name      = "ConsoleLoginFailures"
    namespace = "${local.name_prefix}/Security"
    value     = "1"
    unit      = "Count"
  }
}

# Alarm cho Console Login Failures (Brute Force Detection)
resource "aws_cloudwatch_metric_alarm" "console_login_failures" {
  alarm_name          = "${local.name_prefix}-console-login-failures-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ConsoleLoginFailures"
  namespace           = "${local.name_prefix}/Security"
  period              = 300
  statistic           = "Sum"
  threshold           = 5 # Alert nếu >5 failed logins trong 5 phút
  alarm_description   = "Possible brute force attack - multiple console login failures"
  treat_missing_data  = "notBreaching"

  tags = {
    Name     = "${local.name_prefix}-console-login-failures-alarm"
    Severity = "HIGH"
  }
}

# ── 6. OUTPUTS ─────────────────────────────────────────────

output "cloudtrail_name" {
  description = "Name of the CloudTrail"
  value       = aws_cloudtrail.main.name
}

output "cloudtrail_s3_bucket" {
  description = "S3 bucket for CloudTrail logs"
  value       = aws_s3_bucket.cloudtrail.id
}

output "cloudtrail_log_group" {
  description = "CloudWatch Log Group for CloudTrail"
  value       = aws_cloudwatch_log_group.cloudtrail.name
}
