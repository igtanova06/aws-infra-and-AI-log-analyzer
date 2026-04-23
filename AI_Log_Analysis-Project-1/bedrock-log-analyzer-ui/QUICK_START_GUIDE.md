# 🚀 Quick Start Guide - AI Log Analysis System

## 🎯 TL;DR - 2 Minutes to First Analysis

```bash
# 1. Setup (one-time)
./setup.sh && source venv/bin/activate

# 2. Run
streamlit run streamlit_app.py

# 3. In browser (http://localhost:8501)
#    - Default mode: Multi-Source Correlation ✅
#    - Select: VPC + App logs
#    - Click: "Analyze Logs"
#    - Done! 🎉
```

---

## 📋 Two Analysis Modes

### 🎯 **Mode 1: Multi-Source Correlation (MAIN ENGINE)** ⭐ Recommended

**When to use:** 
- 🔍 Discovering unknown threats
- 🎯 Comprehensive security analysis
- 🚨 Detecting sophisticated attacks
- 📊 Regular security audits

**How to use:**
```
1. Select 2-3 log sources:
   ✓ /aws/vpc/flowlogs (network traffic)
   ✓ /aws/ec2/application (app logs)
   ✓ /aws/cloudtrail/logs (API calls) [optional]

2. Search Term: Leave empty (auto-scan) 💡

3. Time Range: Last 1 hour (or custom)

4. Correlation Engine: Advanced ✅

5. Click "🚀 Analyze Logs"
```

**What you get:**
- ✅ Correlated attack patterns (SSH brute force, SQL injection, port scan)
- ✅ Confidence scores (95.2%)
- ✅ Timeline sequences (10:23:45 → 10:27:30)
- ✅ Matched detection rules
- ✅ AI-powered root cause analysis
- ✅ Specific AWS CLI remediation commands

---

### 🔬 **Mode 2: Single Source (ADVANCED DRILL-DOWN)**

**When to use:**
- 🔍 Investigating specific log source
- 📊 Deep dive after discovering threats
- 🎯 Focused analysis with known search term
- 🔬 Detailed forensics

**How to use:**
```
1. Switch to "Single Source (Advanced)" mode

2. Select ONE log source:
   Example: /aws/vpc/flowlogs

3. Search Term: Required! 
   Example: "REJECT" or "203.0.113.42"

4. Time Range: Narrow down to specific window

5. Click "🚀 Analyze Logs"
```

**What you get:**
- ✅ Detailed log entries from one source
- ✅ Pattern clustering
- ✅ Temporal analysis (burst detection)
- ✅ Severity distribution
- ✅ Component breakdown

---

## 🎓 Recommended Workflow

### **Step 1: Discovery (Multi-Source)** 🔍

```
Goal: Find what's wrong

1. Open app → Multi-Source mode (default)
2. Select VPC + App logs
3. Leave search term empty
4. Time: Last 1 hour
5. Analyze

Result: "Found 3 attack patterns"
  • SSH Brute Force (95.2% confidence)
  • SQL Injection (87.5% confidence)
  • Port Scanning (72.3% confidence)
```

### **Step 2: Investigation (Single Source)** 🔬

```
Goal: Understand the details

1. From Step 1, see SSH attack involves VPC logs
2. Switch to Single Source (Advanced)
3. Select /aws/vpc/flowlogs
4. Search: "REJECT" or attacker IP
5. Analyze

Result: "53 REJECT events from 203.0.113.42"
  • Target: Port 22 (SSH)
  • Timeline: 10:23:45 → 10:27:30
  • Detailed packet info
```

### **Step 3: Remediation** 🔧

```
Goal: Fix the issue

From AI recommendations:
1. Copy AWS CLI command
2. Execute in terminal
3. Verify with verification commands
4. Implement prevention measures
```

---

## 🎯 Common Use Cases

### **Use Case 1: Daily Security Audit**

```
Mode: Multi-Source Correlation
Sources: VPC + App + CloudTrail
Search: (empty - auto-scan)
Time: Last 24 hours
Frequency: Daily

Expected: Detect any anomalies or attacks
```

### **Use Case 2: Incident Investigation**

```
Mode: Multi-Source → Single Source
Sources: Start with VPC + App
Search: Start empty, then specific IP/trace_id
Time: Incident window

Workflow:
1. Multi-Source: Discover attack pattern
2. Single Source: Deep dive into each source
3. Correlate findings
4. Remediate
```

### **Use Case 3: Performance Troubleshooting**

```
Mode: Single Source (Advanced)
Source: /aws/ec2/application
Search: "timeout" or "slow query"
Time: Problem window

Expected: Find performance bottlenecks
```

### **Use Case 4: Compliance Audit**

```
Mode: Multi-Source Correlation
Sources: CloudTrail + VPC + App
Search: "root" or "DeleteVpc" or "unauthorized"
Time: Audit period (e.g., last 30 days)

Expected: Find unauthorized access attempts
```

---

## ⚙️ Configuration Tips

### **AWS Credentials**

```bash
# Option 1: AWS CLI profile
aws configure --profile myprofile

# In Streamlit sidebar:
AWS Profile: myprofile

# Option 2: IAM role (if running on EC2)
# No configuration needed - automatic
```

### **Bedrock Model Selection**

| Model | Speed | Cost | Use Case |
|-------|-------|------|----------|
| **Claude 3 Haiku** | ⚡ Fast | $ Low | Daily analysis, quick checks |
| **Claude 3.5 Sonnet (APAC)** | 🐢 Slower | $$ Higher | Complex investigations, detailed RCA |

**Recommendation:** Start with Haiku, upgrade to Sonnet for complex cases.

### **Time Range Selection**

| Range | Use Case | Performance |
|-------|----------|-------------|
| **Last 1 hour** | Real-time monitoring | ⚡ Fast |
| **Last 6 hours** | Recent incident investigation | 🟢 Good |
| **Last 24 hours** | Daily audit | 🟡 Moderate |
| **Last 7 days** | Weekly review | 🔴 Slow (use specific search term) |

**Tip:** For long time ranges, use specific search terms to reduce log volume.

---

## 🐛 Troubleshooting

### **Problem: No logs found**

```
✓ Check log group names exist in CloudWatch
✓ Verify time range includes logs
✓ Try removing search term (auto-scan)
✓ Check AWS credentials and permissions
```

### **Problem: Bedrock error**

```
✓ Verify IAM permissions include bedrock:InvokeModel
✓ Check model is enabled in your region
✓ Try switching to different model (Haiku vs Sonnet)
✓ Check if you hit rate limits (use APAC/US cross-region)
```

### **Problem: Slow analysis**

```
✓ Reduce time range
✓ Use specific search term
✓ Select fewer log sources (2-3 max)
✓ Use Single Source mode for focused analysis
```

### **Problem: Too many false positives**

```
✓ Use Advanced correlation engine (not Basic)
✓ Narrow time range to incident window
✓ Use specific search terms
✓ Review correlation confidence scores
```

---

## 📊 Understanding Results

### **Correlation Tab (Multi-Source)**

```
🚨 SSH Brute Force Attack (Confidence: 95.2%)

Confidence: 95.2% ← Multi-factor score
Severity: HIGH ← Based on impact
Sources: 2 ← VPC + App logs
Events: 53 ← Total correlated events

Correlation Keys:
- ip: 203.0.113.42 ← Matched across sources
- instance_id: i-abc123 ← Matched
- trace_id: req-xyz789 ← Matched

Timeline: ← Sequence of events
1. [10:23:45] VPC: REJECT 203.0.113.42:54321 → 10.0.1.50:22
2. [10:23:46] App: Failed password for admin (+1.0s)
...

Matched Rules: ← Detection rules triggered
- SSH Brute Force Attack
```

### **Solutions Tab (AI Enhanced)**

```
🎯 Attack Classification
MITRE: T1110.001 - Password Guessing
Threat Actor: Automated bot
Stage: Initial Access

🔴 Severity: High | Confidence: Confirmed
Impact: Attacker attempting SSH access...

🔥 Immediate Containment:
Block IP 203.0.113.42 in Network ACL

[AWS CLI command here] ← Copy and execute

🔍 Investigation:
Timeline: 10:23:45 → 10:27:30 (3m 45s)
Attempts: 53 total, 14.5/min
Success Rate: 0%

Evidence: ← What we saw in logs
- VPC REJECT events
- App failed password logs

Inference: ← AI analysis
- Automated attack (high frequency)
- Common usernames (admin, root)
- Attack blocked by Security Group

🔧 Full Action Plan:
1. Execute containment command
2. Verify block is active
3. Review Security Group rules
4. Check for successful access
5. Rotate SSH keys if needed
6. Install fail2ban

Prevention: ← How to stop this
- Enable GuardDuty
- Restrict SSH to VPN only
- Disable password auth
- CloudWatch Alarms
```

---

## 💡 Pro Tips

### **Tip 1: Start Broad, Then Narrow**
```
1. Multi-Source + empty search → Discover
2. Single Source + specific search → Investigate
```

### **Tip 2: Use Correlation Keys**
```
If you see trace_id in logs:
- Use it as search term
- Get perfect correlation across sources
```

### **Tip 3: Time Range Strategy**
```
Real-time: Last 1 hour
Investigation: Narrow to incident window
Audit: Last 24 hours with specific search
```

### **Tip 4: Export Results**
```
JSON: Full data for automation
CSV: Summary for reports/spreadsheets
```

### **Tip 5: Cost Optimization**
```
- Use Haiku for daily checks ($0.00025/1K tokens)
- Use Sonnet for complex cases ($0.003/1K tokens)
- Empty search term = auto-scan = more tokens
- Specific search = fewer tokens = lower cost
```

---

## 📚 Learn More

- **Detailed Workflow:** `AI_WORKFLOW_REAL_EXAMPLE.md`
- **Refactoring Details:** `ANALYSIS_MODE_REFACTORING.md`
- **Full Documentation:** `README.md`
- **Changelog:** `CHANGELOG.md`

---

## 🎯 Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  🎯 MULTI-SOURCE (Main Engine) - DEFAULT MODE           │
├─────────────────────────────────────────────────────────┤
│  When: Discovering threats, daily audits                │
│  Sources: 2-3 (VPC + App + CloudTrail)                  │
│  Search: Empty (auto-scan)                              │
│  Result: Correlated attack patterns                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  🔬 SINGLE SOURCE (Advanced) - DRILL-DOWN MODE          │
├─────────────────────────────────────────────────────────┤
│  When: Investigating specific source                    │
│  Sources: 1 (specific log group)                        │
│  Search: Required (IP, keyword, trace_id)               │
│  Result: Detailed log analysis                          │
└─────────────────────────────────────────────────────────┘

Workflow: Multi-Source (Discover) → Single Source (Investigate)
```

---

**Happy Analyzing! 🚀**

Need help? Check the docs or review example scenarios above.
