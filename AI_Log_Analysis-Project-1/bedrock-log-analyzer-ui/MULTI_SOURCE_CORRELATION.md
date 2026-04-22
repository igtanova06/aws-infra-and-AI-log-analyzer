# 🧩 Multi-Source Log Correlation

## 📖 Overview

**MultiLogCorrelator** kết nối các mảnh ghép từ nhiều log sources để xây dựng bức tranh toàn cảnh về attacks, misconfigurations, và performance issues.

### **Vấn Đề Hiện Tại:**
```
❌ Phân tích từng log group riêng biệt
❌ Không thấy được mối liên hệ giữa các layers
❌ Miss coordinated attacks
❌ Khó root cause analysis

Example:
- VPC Flow: IP 203.0.113.42 bị REJECT
- CloudTrail: (không biết IP này làm gì)
- Application: (không biết IP này tấn công)
→ Kết luận: 3 vấn đề riêng biệt ❌
```

### **Giải Pháp: Multi-Source Correlation**
```
✅ Correlate logs across 2-4 sources
✅ Identify common actors (IPs, users, instances)
✅ Build attack timeline
✅ Root cause analysis

Example:
- VPC Flow: IP 203.0.113.42 → Port 80 REJECT (10:23)
- CloudTrail: Same IP tries DeleteVpc API AccessDenied (10:24)
- Application: Same IP sends SQL injection to /api/login.php (10:25)
→ Kết luận: Coordinated multi-layer attack from 203.0.113.42 ✅
```

---

## 🎯 Use Cases

### **Use Case 1: Coordinated Attack Detection**

**Scenario:** Hacker tấn công nhiều layers cùng lúc

**Log Sources:**
1. VPC Flow Logs: `203.0.113.42 → Port 22 REJECT` (15 attempts)
2. Application Logs: `203.0.113.42 → SQL Injection in /api/login.php` (12 attempts)
3. CloudTrail: `203.0.113.42 → DeleteVpc API AccessDenied` (3 attempts)

**Correlation Output:**
```json
{
  "correlation_id": "CORR-203-0-113-42",
  "primary_actor": "203.0.113.42",
  "event_type": "coordinated_attack",
  "severity": "CRITICAL",
  "confidence_score": 95.0,
  
  "attack_chain": [
    "1. Network Layer: 15 SSH connection attempts (REJECTED)",
    "2. Application Layer: 12 SQL injection attempts",
    "3. API Layer: 3 AWS API calls (AccessDenied)"
  ],
  
  "summary": "Coordinated Multi-Layer Attack detected from 203.0.113.42. Activity observed across 3 log sources. Attack progression: 3 stages identified.",
  
  "recommendations": [
    "🚨 IMMEDIATE: Block IP in WAF and Security Groups",
    "🔍 INVESTIGATE: Check for data exfiltration attempts",
    "🛡️ HARDEN: Enable AWS GuardDuty for threat detection"
  ]
}
```

---

### **Use Case 2: Application-Database Issue**

**Scenario:** Web app slow → Database connection pool exhausted

**Log Sources:**
1. Application Logs: `ERROR: Connection timeout to database` (50 errors)
2. Database Logs: `Too many connections (max: 100)` (20 errors)
3. VPC Flow Logs: `10.0.4.15 → 10.0.7.10:3306 ACCEPT` (high volume)

**Correlation Output:**
```json
{
  "event_type": "application_database_issue",
  "severity": "HIGH",
  "confidence_score": 85.0,
  
  "attack_chain": [
    "1. Application Layer: 50 database connection timeouts",
    "2. Database Layer: 20 'too many connections' errors",
    "3. Network Layer: High connection volume to DB"
  ],
  
  "recommendations": [
    "🔍 INVESTIGATE: Check database connection pool settings",
    "📊 ANALYZE: Review slow query logs",
    "📈 SCALE: Consider increasing RDS instance size"
  ]
}
```

---

### **Use Case 3: Unauthorized Access Attempt**

**Scenario:** User tries to access resources without permission

**Log Sources:**
1. CloudTrail: `arn:aws:iam::123:user/dev-intern → DeleteVpc AccessDenied` (5 attempts)
2. VPC Flow Logs: `10.0.4.25 → 10.0.1.10:443 REJECT` (3 attempts)
3. Application Logs: `User dev-intern tried to access /admin/delete` (2 attempts)

**Correlation Output:**
```json
{
  "event_type": "unauthorized_access_attempt",
  "severity": "HIGH",
  "confidence_score": 90.0,
  
  "attack_chain": [
    "1. API Layer: 5 AWS API calls (AccessDenied)",
    "2. Network Layer: 3 connection attempts (REJECTED)",
    "3. Application Layer: 2 unauthorized access attempts"
  ],
  
  "recommendations": [
    "🔐 REVIEW: IAM policies and permissions",
    "🚨 ALERT: Notify security team immediately",
    "🛡️ ENFORCE: Enable MFA for all users"
  ]
}
```

---

## 🔧 How It Works

### **Step 1: Extract Correlation Keys**

```python
# From each log source, extract:
- IP addresses (203.0.113.42, 10.0.4.15)
- User ARNs (arn:aws:iam::123:user/dev-intern)
- Instance IDs (i-abc123, i-def456)
- API actions (DeleteVpc, StopInstances)
- Timestamps (for timeline)
```

### **Step 2: Find Overlapping Actors**

```python
# Find actors that appear in 2+ sources
VPC Flow:     [203.0.113.42, 10.0.4.15]
CloudTrail:   [203.0.113.42]
Application:  [203.0.113.42, 192.168.1.1]

Overlapping:  [203.0.113.42]  ← This actor appears in 3 sources!
```

### **Step 3: Build Correlated Event**

```python
# For each overlapping actor, collect:
- All events from VPC Flow involving this actor
- All events from CloudTrail involving this actor
- All events from Application involving this actor
- Build timeline: first_seen → last_seen
- Calculate confidence score
```

### **Step 4: Classify Event Type**

```python
# Based on patterns:
if has_sql_injection and has_vpc_rejects:
    event_type = "coordinated_attack"
    severity = "CRITICAL"
elif has_access_denied and has_vpc_rejects:
    event_type = "unauthorized_access_attempt"
    severity = "HIGH"
elif has_app_errors and has_db_errors:
    event_type = "application_database_issue"
    severity = "MEDIUM"
```

### **Step 5: Generate Recommendations**

```python
# Based on event type, provide actionable steps
if event_type == "coordinated_attack":
    recommendations = [
        "Block IP in WAF",
        "Enable GuardDuty",
        "Check for data exfiltration"
    ]
```

---

## 📊 Confidence Score Calculation

```python
confidence_score = source_score + event_score

# Source Score (max 50 points)
- 2 sources: 25 points
- 3 sources: 50 points
- 4 sources: 50 points

# Event Score (max 50 points)
- 1-10 events: 2 points each
- 11-25 events: 50 points
- 25+ events: 50 points

Examples:
- 2 sources, 5 events:  25 + 10 = 35% (LOW confidence)
- 3 sources, 15 events: 50 + 30 = 80% (HIGH confidence)
- 4 sources, 30 events: 50 + 50 = 100% (VERY HIGH confidence)
```

---

## 🎨 UI Integration

### **Streamlit App Changes**

#### **1. Add Analysis Mode Selector**
```python
analysis_mode = st.sidebar.radio(
    "Select Mode",
    ["Single Source", "Multi-Source Correlation"]
)
```

#### **2. Multi-Select for Log Groups**
```python
if analysis_mode == "Multi-Source Correlation":
    selected_log_groups = st.sidebar.multiselect(
        "Log Groups (chọn 2-4 nguồn)",
        options=LOG_GROUP_OPTIONS,
        default=["/aws/vpc/flowlogs", "/aws/ec2/application"]
    )
```

#### **3. New Tab: Correlation**
```python
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Summary",
    "📊 Analysis",
    "🔧 Solutions",
    "🧩 Correlation"  # NEW
])

with tab4:
    if st.session_state.multi_source_context:
        # Display correlated events
        for event in multi_source_context.correlated_events:
            st.subheader(f"🚨 {event.summary}")
            st.metric("Confidence", f"{event.confidence_score:.0f}%")
            
            # Attack chain
            st.markdown("**Attack Chain:**")
            for step in event.attack_chain:
                st.markdown(f"- {step}")
            
            # Recommendations
            st.markdown("**Recommendations:**")
            for rec in event.recommendations:
                st.markdown(f"- {rec}")
```

---

## 🚀 Implementation Steps

### **Step 1: Install MultiLogCorrelator**
```bash
# Already created: src/multi_log_correlator.py
# No additional dependencies needed
```

### **Step 2: Update Streamlit App**

Add to imports:
```python
from multi_log_correlator import MultiLogCorrelator, MultiSourceContext
```

Add to analysis logic:
```python
# After analyzing each log group individually
if analysis_mode == "Multi-Source Correlation" and len(selected_log_groups) >= 2:
    # Build log_sources dict
    log_sources = {}
    for log_group in selected_log_groups:
        log_sources[log_group] = (matches, analysis)
    
    # Correlate
    correlator = MultiLogCorrelator()
    multi_context = correlator.correlate_multi_source(log_sources)
    st.session_state.multi_source_context = multi_context
```

### **Step 3: Add Correlation Tab**

See UI Integration section above.

### **Step 4: Test**

```bash
# Test with 2 log groups
python generate_omni_logs.py  # Generate test data
streamlit run streamlit_app.py

# In UI:
1. Select "Multi-Source Correlation"
2. Choose: /aws/vpc/flowlogs + /aws/ec2/application
3. Search term: "REJECT" or "error"
4. Click "Analyze Logs"
5. Go to "Correlation" tab
```

---

## 📈 Benefits

| Feature | Single Source | Multi-Source Correlation |
|---------|---------------|--------------------------|
| **Attack Detection** | Basic | Advanced (coordinated attacks) |
| **Root Cause** | Limited | Comprehensive |
| **False Positives** | Higher | Lower (cross-validation) |
| **Context** | Single layer | Multi-layer |
| **Confidence** | Medium | High (cross-source validation) |
| **Actionability** | Generic | Specific (targeted recommendations) |

---

## 🎓 Best Practices

### **1. Choose Complementary Sources**
```
✅ GOOD combinations:
- VPC Flow + Application (network + app layer)
- CloudTrail + Application (API + app layer)
- Application + Database (app + data layer)
- VPC + CloudTrail + Application (full stack)

❌ BAD combinations:
- VPC Flow + VPC Flow (redundant)
- Database Error + Database Slow Query (too similar)
```

### **2. Use Appropriate Time Windows**
```
✅ Short window (1-2 hours) for:
- Attack detection
- Real-time incidents

✅ Longer window (6-24 hours) for:
- Performance analysis
- Trend identification
```

### **3. Filter Noise**
```
✅ Use specific search terms:
- "REJECT" for VPC Flow
- "ERROR" for Application
- "AccessDenied" for CloudTrail

❌ Avoid generic terms:
- "" (empty - too much noise)
- "INFO" (too many results)
```

---

## 🔍 Example Queries

### **Query 1: Find Coordinated Attacks**
```
Sources: VPC Flow + Application + CloudTrail
Search: "REJECT" OR "injection" OR "denied"
Time: Last 1 hour
```

### **Query 2: Database Performance Issues**
```
Sources: Application + Database
Search: "timeout" OR "slow" OR "connection"
Time: Last 6 hours
```

### **Query 3: Unauthorized Access**
```
Sources: CloudTrail + Application
Search: "AccessDenied" OR "unauthorized" OR "forbidden"
Time: Last 24 hours
```

---

## 📞 Troubleshooting

### **Issue: No Correlated Events Found**

**Possible Causes:**
1. No overlapping actors between sources
2. Time windows don't overlap
3. Search terms too specific

**Solutions:**
- Widen time window
- Use broader search terms
- Check if logs exist in all sources

### **Issue: Low Confidence Scores**

**Possible Causes:**
1. Only 2 sources selected
2. Few events per source
3. Weak correlation

**Solutions:**
- Add more log sources (3-4)
- Widen time window to get more events
- Use more specific search terms

### **Issue: Too Many Correlated Events**

**Possible Causes:**
1. Search term too broad
2. Time window too long
3. High-traffic environment

**Solutions:**
- Use specific search terms
- Narrow time window
- Filter by severity (ERROR only)

---

## 🎯 Roadmap

### **Phase 1: Basic Correlation** ✅
- [x] Extract correlation keys
- [x] Find overlapping actors
- [x] Build correlated events
- [x] Generate recommendations

### **Phase 2: Advanced Features** (Future)
- [ ] Machine learning for pattern detection
- [ ] Anomaly detection across sources
- [ ] Predictive analysis
- [ ] Auto-remediation suggestions
- [ ] Integration with AWS Security Hub

### **Phase 3: Visualization** (Future)
- [ ] Interactive timeline graph
- [ ] Network topology visualization
- [ ] Attack flow diagrams
- [ ] Real-time correlation dashboard

---

## 📚 References

- [AWS CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)
