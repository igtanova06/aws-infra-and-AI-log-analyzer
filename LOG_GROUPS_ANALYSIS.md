# 📊 CloudWatch Log Groups - Analysis & Recommendations

## 🔍 Cấu Trúc Hiện Tại

### Log Groups Đang Có:
```
1. /aws/vpc/flowlogs          # VPC network traffic
2. /aws/ec2/applogs           # ALL application logs (mixed)
3. /aws/cloudtrail/logs       # AWS API audit trail
4. /aws/rds/instance/.../error
5. /aws/rds/instance/.../general
6. /aws/rds/instance/.../slowquery
```

### Vấn Đề Với `/aws/ec2/applogs`:
Hiện tại **TẤT CẢ** logs từ EC2 đều vào 1 group:
- System logs (messages, secure)
- Web server logs (httpd access/error)
- PHP application logs
- Docker container logs
- Streamlit app logs

**Hậu quả:**
- ❌ Khó filter logs theo loại
- ❌ Khó set retention policy riêng
- ❌ Khó phân quyền access
- ❌ Khó tính cost per service
- ❌ AI analysis bị nhiễu (mix nhiều loại logs)

## ✅ Recommendation: TÁCH LOG GROUPS

### Cấu Trúc Đề Xuất (Best Practice):

```
# Infrastructure Logs
/aws/vpc/flowlogs                    # Network traffic (ACCEPT/REJECT)
/aws/cloudtrail/logs                 # AWS API calls

# Application Logs (by tier)
/aws/ec2/web/system                  # Web tier system logs
/aws/ec2/web/httpd                   # Apache/Nginx logs
/aws/ec2/web/application             # PHP application logs
/aws/ec2/app/system                  # App tier system logs
/aws/ec2/app/streamlit               # Streamlit application logs

# Database Logs
/aws/rds/mysql/error                 # RDS error logs
/aws/rds/mysql/general               # RDS general logs
/aws/rds/mysql/slowquery             # RDS slow queries
```

## 📋 Chi Tiết Từng Log Group

### 1. `/aws/vpc/flowlogs` 🌐
**Mục đích:** Network security monitoring

**Nội dung:**
- Source/Destination IP addresses
- Source/Destination ports
- Protocol (TCP/UDP/ICMP)
- Action (ACCEPT/REJECT)
- Bytes transferred

**Use cases:**
- Detect port scanning
- Identify DDoS attacks
- Monitor network traffic patterns
- Investigate unauthorized access attempts

**Retention:** 7 days (có thể giảm xuống 3 days để tiết kiệm)

**Sample log:**
```
2 123456789012 eni-abc123 203.0.113.42 10.0.4.15 52341 22 6 10 840 1234567890 1234567891 REJECT OK
```

---

### 2. `/aws/cloudtrail/logs` 🔐
**Mục đích:** AWS API audit trail

**Nội dung:**
- Who (userIdentity, principalId)
- What (eventName: CreateUser, DeleteVpc)
- When (eventTime)
- Where (sourceIPAddress, awsRegion)
- Result (errorCode, errorMessage)

**Use cases:**
- Detect privilege escalation
- Monitor resource deletion
- Track IAM changes
- Investigate unauthorized API calls

**Retention:** 7 days (compliance có thể cần 90 days)

**Sample log:**
```json
{
  "eventName": "DeleteVpc",
  "userIdentity": {
    "type": "IAMUser",
    "arn": "arn:aws:iam::123456789012:user/attacker"
  },
  "errorCode": "UnauthorizedOperation"
}
```

---

### 3. `/aws/ec2/web/system` 🖥️
**Mục đích:** Web tier system health

**Nội dung:**
- `/var/log/messages` - System events, kernel messages
- `/var/log/secure` - SSH attempts, sudo commands, authentication

**Use cases:**
- Detect SSH brute force
- Monitor system errors
- Track sudo usage
- Investigate unauthorized access

**Retention:** 7 days

**Sample log:**
```
Apr 21 10:23:45 ip-10-0-4-15 sshd[1234]: Failed password for invalid_user from 203.0.113.42 port 52341 ssh2
```

---

### 4. `/aws/ec2/web/httpd` 🌐
**Mục đích:** Web server access & errors

**Nội dung:**
- `/var/log/httpd/access_log` - HTTP requests (GET, POST, status codes)
- `/var/log/httpd/error_log` - Web server errors, PHP warnings

**Use cases:**
- Monitor HTTP traffic patterns
- Detect web attacks (SQL injection, XSS)
- Track 404/500 errors
- Analyze user behavior

**Retention:** 7 days

**Sample logs:**
```
# Access log
203.0.113.42 - - [21/Apr/2024:10:23:45 +0000] "GET /admin/users.php HTTP/1.1" 403 1234

# Error log
[Mon Apr 21 10:23:45.123456 2024] [php7:error] [pid 1234] PHP Parse error: syntax error in /var/www/html/login.php on line 42
```

---

### 5. `/aws/ec2/web/application` 📱
**Mục đích:** PHP application business logic

**Nội dung:**
- `/var/log/app/application.log` - Custom app logs
- `/var/log/app/php-error.log` - PHP runtime errors
- Business logic errors (login failures, validation errors)

**Use cases:**
- Debug application errors
- Monitor business logic failures
- Track user actions
- Detect SQL injection attempts

**Retention:** 14 days (business logs cần lâu hơn)

**Sample log:**
```
2024-04-21 10:23:45 [ERROR] SQL Injection attempt detected: username=admin'--
2024-04-21 10:23:46 [WARNING] Failed login attempt for user 'admin' from IP 203.0.113.42
2024-04-21 10:23:47 [INFO] User 'student123' successfully enrolled in course 'CS101'
```

---

### 6. `/aws/ec2/app/system` 🖥️
**Mục đích:** App tier (Streamlit) system health

**Nội dung:**
- System logs from Streamlit instances
- Docker daemon logs
- Container orchestration logs

**Use cases:**
- Monitor Streamlit health
- Debug container issues
- Track resource usage

**Retention:** 7 days

---

### 7. `/aws/ec2/app/streamlit` 🤖
**Mục đích:** Streamlit application logs

**Nội dung:**
- Streamlit app logs
- Bedrock API calls
- AI analysis results
- User interactions

**Use cases:**
- Monitor AI analysis performance
- Track Bedrock API usage/costs
- Debug AI errors
- Analyze user queries

**Retention:** 7 days

**Sample log:**
```
2024-04-21 10:23:45 [INFO] User analyzed log group: /aws/ec2/applogs
2024-04-21 10:23:46 [INFO] Bedrock API call: model=claude-haiku, tokens=1234, cost=$0.0012
2024-04-21 10:23:47 [WARNING] Bedrock API throttled, retrying in 2s
```

---

### 8. `/aws/rds/mysql/error` 🗄️
**Mục đích:** Database errors

**Nội dung:**
- Connection errors
- Query syntax errors
- Deadlocks
- Replication errors

**Use cases:**
- Debug database issues
- Monitor connection pool
- Detect query errors
- Track deadlocks

**Retention:** 7 days

**Sample log:**
```
2024-04-21 10:23:45 [ERROR] Access denied for user 'root'@'10.0.4.15' (using password: YES)
2024-04-21 10:23:46 [ERROR] Deadlock found when trying to get lock; try restarting transaction
```

---

### 9. `/aws/rds/mysql/general` 📝
**Mục đích:** All database queries (verbose)

**Nội dung:**
- All SQL queries executed
- Connection events
- User authentication

**Use cases:**
- Audit database access
- Debug query issues
- Monitor query patterns
- Detect suspicious queries

**Retention:** 3 days (very verbose, expensive)

**⚠️ Warning:** General log is VERY verbose and expensive. Only enable for debugging.

---

### 10. `/aws/rds/mysql/slowquery` 🐌
**Mục đích:** Performance optimization

**Nội dung:**
- Queries exceeding threshold (default: 10s)
- Execution time
- Rows examined
- Query plan

**Use cases:**
- Identify slow queries
- Optimize database performance
- Add missing indexes
- Refactor inefficient queries

**Retention:** 14 days (need history for optimization)

**Sample log:**
```
# Time: 2024-04-21T10:23:45.123456Z
# User@Host: webapp[webapp] @ [10.0.4.15]
# Query_time: 12.345678  Lock_time: 0.000123 Rows_sent: 10000  Rows_examined: 1000000
SELECT * FROM students WHERE created_at > '2020-01-01';
```

---

## 🎯 Recommended Log Group Structure

### Option A: By Service (Recommended for your project)
```
/aws/vpc/flowlogs                    # Network
/aws/cloudtrail/logs                 # AWS API

/aws/ec2/web-tier/system             # Web system logs
/aws/ec2/web-tier/httpd              # Web server logs
/aws/ec2/web-tier/application        # PHP app logs

/aws/ec2/app-tier/system             # App system logs
/aws/ec2/app-tier/streamlit          # Streamlit logs

/aws/rds/mysql/error                 # DB errors
/aws/rds/mysql/slowquery             # DB performance
```

### Option B: By Log Type (Alternative)
```
/aws/infrastructure/network          # VPC Flow Logs
/aws/infrastructure/api              # CloudTrail

/aws/application/system              # All system logs
/aws/application/web                 # All web logs
/aws/application/business            # All business logic

/aws/database/error                  # DB errors
/aws/database/performance            # DB performance
```

## 💡 Recommendation: Option A

**Lý do:**
1. ✅ **Clear separation** - Dễ phân quyền (web team chỉ xem web logs)
2. ✅ **Cost tracking** - Biết chính xác cost per tier
3. ✅ **Retention policy** - Set khác nhau cho từng tier
4. ✅ **AI analysis** - Focused analysis, ít nhiễu
5. ✅ **Scalability** - Dễ thêm tier mới (cache, queue, etc.)

## 📊 Cost Comparison

### Current (1 group for all):
```
/aws/ec2/applogs: 5GB/day × $0.50/GB = $2.50/day = $75/month
```

### Proposed (separated):
```
/aws/ec2/web-tier/system:      0.5GB/day × $0.50 = $0.25/day
/aws/ec2/web-tier/httpd:       2.0GB/day × $0.50 = $1.00/day
/aws/ec2/web-tier/application: 1.0GB/day × $0.50 = $0.50/day
/aws/ec2/app-tier/streamlit:   1.5GB/day × $0.50 = $0.75/day

Total: $2.50/day = $75/month (SAME COST)
```

**Benefit:** Same cost, but better organization!

## 🔧 Implementation Plan

### Phase 1: Create New Log Groups (Terraform)
```hcl
# environments/dev/cloudwatch.tf
resource "aws_cloudwatch_log_group" "web_system" {
  name              = "/aws/ec2/web-tier/system"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "web_httpd" {
  name              = "/aws/ec2/web-tier/httpd"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "web_application" {
  name              = "/aws/ec2/web-tier/application"
  retention_in_days = 14  # Business logs need longer retention
}

resource "aws_cloudwatch_log_group" "app_streamlit" {
  name              = "/aws/ec2/app-tier/streamlit"
  retention_in_days = 7
}
```

### Phase 2: Update CloudWatch Agent Config
```json
{
  "file_path": "/var/log/messages",
  "log_group_name": "/aws/ec2/web-tier/system",
  "log_stream_name": "{instance_id}/messages"
},
{
  "file_path": "/var/log/httpd/access_log",
  "log_group_name": "/aws/ec2/web-tier/httpd",
  "log_stream_name": "{instance_id}/access"
},
{
  "file_path": "/var/log/app/application.log",
  "log_group_name": "/aws/ec2/web-tier/application",
  "log_stream_name": "{instance_id}/app"
}
```

### Phase 3: Update Streamlit App
Update log group dropdown to include new groups:
```python
LOG_GROUP_OPTIONS = [
    "/aws/vpc/flowlogs",
    "/aws/cloudtrail/logs",
    "/aws/ec2/web-tier/system",
    "/aws/ec2/web-tier/httpd",
    "/aws/ec2/web-tier/application",
    "/aws/ec2/app-tier/streamlit",
    "/aws/rds/mysql/error",
    "/aws/rds/mysql/slowquery",
]
```

## 🎯 Migration Strategy

### Option 1: Clean Cut (Recommended for dev)
1. Create new log groups
2. Update CloudWatch Agent config
3. Restart agent
4. Delete old `/aws/ec2/applogs` after 7 days

### Option 2: Gradual Migration (For production)
1. Create new log groups
2. Send logs to BOTH old and new groups (7 days)
3. Verify new groups working
4. Stop sending to old group
5. Delete old group after retention period

## 📝 Summary

### Current Structure:
```
❌ /aws/ec2/applogs (everything mixed)
```

### Recommended Structure:
```
✅ /aws/ec2/web-tier/system
✅ /aws/ec2/web-tier/httpd
✅ /aws/ec2/web-tier/application
✅ /aws/ec2/app-tier/streamlit
✅ /aws/rds/mysql/error
✅ /aws/rds/mysql/slowquery
```

### Benefits:
1. ✅ Better organization
2. ✅ Easier troubleshooting
3. ✅ Granular access control
4. ✅ Per-service cost tracking
5. ✅ Flexible retention policies
6. ✅ Focused AI analysis
7. ✅ Same total cost

---

**Recommendation: TÁCH LOG GROUPS theo service tier!**

Bạn muốn mình implement cấu trúc mới này không?
