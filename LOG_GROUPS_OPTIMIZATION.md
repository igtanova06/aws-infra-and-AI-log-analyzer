# 📊 CloudWatch Log Groups Optimization

## 🎯 Optimization Strategy: "Filter + Structure + Retention"

### Objectives:
1. **Reduce log groups** from 9 → 5 (44% reduction)
2. **Consolidate application logs** using log streams
3. **Optimize retention** based on compliance and business needs
4. **Add metric filters** for proactive monitoring
5. **Reduce costs** by filtering unnecessary logs

---

## 📈 Before vs After Comparison

### **BEFORE (Current Structure)**

```
Infrastructure (2 groups)
├─ /aws/vpc/flowlogs              [7 days]  ✅ Keep
└─ /aws/cloudtrail/logs           [7 days]  ⚠️ Too short for compliance

Web Tier (3 groups) ⚠️ TOO MANY
├─ /aws/ec2/web-tier/system       [7 days]
├─ /aws/ec2/web-tier/httpd        [7 days]
└─ /aws/ec2/web-tier/application  [14 days]

App Tier (2 groups) ⚠️ REDUNDANT
├─ /aws/ec2/app-tier/system       [7 days]  (duplicate of web system logs)
└─ /aws/ec2/app-tier/streamlit    [7 days]

Database (2 groups)
├─ /aws/rds/mysql/error           [7 days]  ✅ Keep
└─ /aws/rds/mysql/slowquery       [14 days] ✅ Keep

TOTAL: 9 log groups
```

### **AFTER (Optimized Structure)**

```
Infrastructure (2 groups)
├─ /aws/vpc/flowlogs              [7 days, REJECT only]  ✅ Optimized
└─ /aws/cloudtrail/logs           [90 days]              ✅ Compliance-ready

Application - CONSOLIDATED (1 group) 🎉
└─ /aws/ec2/application           [14 days]
   ├─ {instance-id}/web/system           (messages, secure)
   ├─ {instance-id}/web/httpd-access     (Apache access)
   ├─ {instance-id}/web/httpd-error      (Apache error)
   ├─ {instance-id}/web/application      (PHP app logs)
   ├─ {instance-id}/app/system           (messages, secure)
   └─ {instance-id}/app/streamlit        (Streamlit logs)

Database (2 groups)
├─ /aws/rds/mysql/error           [7 days]  ✅ Keep
└─ /aws/rds/mysql/slowquery       [14 days] ✅ Keep

TOTAL: 5 log groups (44% reduction)
```

---

## 💰 Cost Savings Analysis

### **Log Ingestion Costs**

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| **Log Groups** | 9 | 5 | 44% fewer |
| **API Calls** | ~450/day | ~250/day | 44% fewer |
| **VPC Flow Logs** | ALL traffic | REJECT only | ~70% reduction |
| **CloudTrail Retention** | 7 days | 90 days | Better compliance |
| **Monthly Cost (estimated)** | $8-10 | $4-5 | **~50% savings** |

### **Cost Breakdown (Monthly)**

```
BEFORE:
- VPC Flow Logs (ALL):        $3.00  (high volume)
- CloudTrail:                  $1.00
- Web Tier (3 groups):         $2.50
- App Tier (2 groups):         $1.50
- Database (2 groups):         $1.00
TOTAL:                         $9.00/month

AFTER:
- VPC Flow Logs (REJECT only): $0.90  (70% reduction)
- CloudTrail:                   $1.20  (longer retention)
- Application (1 group):        $2.00  (consolidated)
- Database (2 groups):          $1.00
TOTAL:                          $5.10/month

SAVINGS: $3.90/month (43%)
```

---

## 🔧 Key Optimizations

### **1. Filter - VPC Flow Logs**

**Before:**
```hcl
traffic_type = "ALL"  # Logs ACCEPT + REJECT + ALL
```

**After:**
```hcl
traffic_type = "REJECT"  # Only log rejected traffic (security focus)
```

**Benefits:**
- ✅ 70% reduction in log volume
- ✅ Focus on security events only
- ✅ Easier to spot attacks
- ✅ Lower ingestion costs

---

### **2. Structure - Consolidated Application Logs**

**Before:** 5 separate log groups
```
/aws/ec2/web-tier/system
/aws/ec2/web-tier/httpd
/aws/ec2/web-tier/application
/aws/ec2/app-tier/system
/aws/ec2/app-tier/streamlit
```

**After:** 1 log group with structured log streams
```
/aws/ec2/application
  ├─ i-abc123/web/system
  ├─ i-abc123/web/httpd-access
  ├─ i-abc123/web/httpd-error
  ├─ i-abc123/web/application
  ├─ i-def456/app/system
  └─ i-def456/app/streamlit
```

**Benefits:**
- ✅ Easier to query across all application logs
- ✅ Single CloudWatch Insights query for correlation
- ✅ Fewer API calls (1 group vs 5 groups)
- ✅ Centralized metric filters
- ✅ Better log correlation by instance ID

---

### **3. Retention - Compliance-Aware**

| Log Type | Before | After | Reason |
|----------|--------|-------|--------|
| **CloudTrail** | 7 days | 90 days | Compliance requirement (audit trail) |
| **VPC Flow** | 7 days | 7 days | Security analysis (short-term) |
| **Application** | 7-14 days | 14 days | Business logs (standardized) |
| **Database** | 7-14 days | 7-14 days | Performance tuning |

**Compliance Standards:**
- **PCI-DSS:** Requires 90 days audit logs
- **HIPAA:** Requires 6 years (use S3 archival)
- **SOC 2:** Requires 90 days minimum

---

## 📊 Metric Filters (NEW)

### **Filter 1: Web HTTP Errors**
```hcl
pattern = "[time, request_id, ip, method, uri, status_code=4* || status_code=5*, ...]"
```
**Tracks:** 4xx and 5xx HTTP errors  
**Alarm:** >50 errors in 5 minutes

### **Filter 2: Application Errors**
```hcl
pattern = "?ERROR ?CRITICAL ?FATAL"
```
**Tracks:** Application-level errors  
**Alarm:** >20 errors in 5 minutes

### **Filter 3: Security Events**
```hcl
pattern = "?\"Failed password\" ?\"SQL injection\" ?\"authentication failure\" ?\"brute force\" ?\"unauthorized\""
```
**Tracks:** Security-related events  
**Alarm:** >10 events in 5 minutes (HIGH severity)

---

## 🚀 Migration Guide

### **Step 1: Backup Current Configuration**
```bash
# Export current log groups
aws logs describe-log-groups --region ap-southeast-1 > log_groups_backup.json

# Export metric filters
aws logs describe-metric-filters --region ap-southeast-1 > metric_filters_backup.json
```

### **Step 2: Apply New Terraform Configuration**
```bash
cd environments/dev

# Rename old file
mv cloudwatch.tf cloudwatch_old.tf

# Use optimized version
mv cloudwatch_optimized.tf cloudwatch.tf

# Plan changes
terraform plan

# Apply (will create new log group, old ones remain)
terraform apply
```

### **Step 3: Update CloudWatch Agent Configuration**
```bash
cd ansible

# Update playbook to use new config
ansible-playbook -i inventory/aws_ec2.yml playbooks/install_cloudwatch_agent.yml \
  -e cloudwatch_config_template=cloudwatch_agent_config_optimized.json.j2
```

### **Step 4: Verify Log Ingestion**
```bash
# Check new log group
aws logs describe-log-streams \
  --log-group-name /aws/ec2/application \
  --order-by LastEventTime \
  --descending \
  --max-items 10

# Verify log streams structure
# Should see: i-xxx/web/system, i-xxx/web/httpd-access, etc.
```

### **Step 5: Update AI Log Analyzer**
```python
# Update streamlit_app.py log group options
LOG_GROUP_OPTIONS = [
    "/aws/vpc/flowlogs",
    "/aws/cloudtrail/logs",
    "/aws/ec2/application",        # NEW - consolidated
    "/aws/rds/mysql/error",
    "/aws/rds/mysql/slowquery",
]
```

### **Step 6: Delete Old Log Groups (After 7 Days)**
```bash
# Wait 7 days to ensure no data loss
# Then delete old log groups
aws logs delete-log-group --log-group-name /aws/ec2/web-tier/system
aws logs delete-log-group --log-group-name /aws/ec2/web-tier/httpd
aws logs delete-log-group --log-group-name /aws/ec2/web-tier/application
aws logs delete-log-group --log-group-name /aws/ec2/app-tier/system
aws logs delete-log-group --log-group-name /aws/ec2/app-tier/streamlit
```

---

## 🔍 Querying Consolidated Logs

### **CloudWatch Insights Queries**

#### **Query 1: All Web HTTP Errors**
```sql
fields @timestamp, @message
| filter @logStream like /web\/httpd/
| filter @message like /HTTP\/1\.[01]\" [45]\d{2}/
| sort @timestamp desc
| limit 100
```

#### **Query 2: Security Events Across All Tiers**
```sql
fields @timestamp, @logStream, @message
| filter @message like /(?i)(failed password|sql injection|brute force|unauthorized)/
| stats count() by @logStream
| sort count desc
```

#### **Query 3: Application Errors by Instance**
```sql
fields @timestamp, @logStream, @message
| filter @message like /(?i)(error|critical|fatal)/
| parse @logStream /(?<instance_id>i-[a-z0-9]+)\/(?<tier>\w+)\/(?<log_type>\w+)/
| stats count() by instance_id, tier
| sort count desc
```

#### **Query 4: Correlation - Web + App Logs**
```sql
fields @timestamp, @logStream, @message
| filter @logStream like /i-abc123/  # Specific instance
| sort @timestamp desc
| limit 200
```

---

## 📋 Checklist

### **Pre-Migration**
- [ ] Backup current log groups configuration
- [ ] Review retention requirements with compliance team
- [ ] Test new CloudWatch Agent config on 1 instance
- [ ] Update monitoring dashboards

### **Migration**
- [ ] Apply new Terraform configuration
- [ ] Deploy new CloudWatch Agent config
- [ ] Verify log ingestion for 24 hours
- [ ] Test CloudWatch Insights queries
- [ ] Update AI Log Analyzer config

### **Post-Migration**
- [ ] Monitor costs for 1 week
- [ ] Verify metric filters are working
- [ ] Test CloudWatch Alarms
- [ ] Delete old log groups after 7 days
- [ ] Update documentation

---

## 🎓 Best Practices

### **1. Log Stream Naming Convention**
```
{instance-id}/{tier}/{log-type}

Examples:
- i-0abc123def456/web/system
- i-0abc123def456/web/httpd-access
- i-0abc123def456/app/streamlit
```

### **2. Retention Policy**
```
Audit logs (CloudTrail):     90 days
Security logs (VPC Flow):    7 days
Application logs:            14 days
Database logs:               7-14 days
```

### **3. Metric Filters**
- Create filters for actionable metrics only
- Use alarms for critical events
- Avoid over-alerting (alert fatigue)

### **4. Cost Optimization**
- Filter logs at source (VPC Flow: REJECT only)
- Use appropriate retention periods
- Archive old logs to S3 (cheaper)
- Use CloudWatch Insights sparingly (pay per query)

---

## 📞 Support

**Questions?**
- Terraform issues: Check `terraform plan` output
- CloudWatch Agent: Check `/opt/aws/amazon-cloudwatch-agent/logs/`
- Log ingestion: Use `aws logs tail` command

**Rollback Plan:**
```bash
# Restore old configuration
mv cloudwatch_old.tf cloudwatch.tf
terraform apply
```
