# 🏗️ Kiến Trúc Hệ Thống AI Log Analysis

## 📋 Tổng Quan Dự Án

Hệ thống **AI-Powered Log Analysis & Security Monitoring** tự động phát hiện và phân tích các cuộc tấn công mạng thông qua việc thu thập, tương quan và phân tích logs từ nhiều nguồn khác nhau trên AWS.

---

## 🎯 Luồng Hoạt Động Chính

```
┌─────────────────────────────────────────────────────────────────────┐
│                    1. INFRASTRUCTURE SETUP                          │
│                         (Terraform)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  • VPC với 3-tier architecture (Public/Private/DB subnets)          │
│  • ALB (Application Load Balancer)                                  │
│  • EC2 Instances:                                                   │
│    - Web Server (Layer 1): PHP Student Management App               │
│    - App Server (Layer 2): Streamlit AI Log Analyzer               │
│  • RDS MySQL Database (Isolated subnet)                             │
│  • Security Groups với least-privilege access                       │
│  • VPC Flow Logs → CloudWatch                                       │
│  • CloudTrail → CloudWatch                                          │
│  • SSM Endpoints (Private connectivity)                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                2. CONFIGURATION MANAGEMENT                          │
│                         (Ansible)                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  • Install Docker trên tất cả EC2 instances                         │
│  • Install CloudWatch Agent với custom config                       │
│  • Deploy Web App (PHP) → Port 8080                                 │
│  • Deploy Log Analyzer (Streamlit) → Port 80                        │
│  • Configure log shipping to CloudWatch                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    3. LOG COLLECTION                                │
│                      (CloudWatch)                                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
        ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
        │ VPC Flow     │  │ CloudTrail   │  │ Application  │
        │ Logs         │  │ Logs         │  │ Logs         │
        │              │  │              │  │              │
        │ • Network    │  │ • API calls  │  │ • PHP errors │
        │   traffic    │  │ • IAM events │  │ • App logs   │
        │ • ACCEPT/    │  │ • Resource   │  │ • SQL errors │
        │   REJECT     │  │   changes    │  │              │
        └──────────────┘  └──────────────┘  └──────────────┘
                    │             │             │
                    └─────────────┼─────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  CloudWatch Log Groups:  │
                    │  • /aws/vpc/flowlogs     │
                    │  • /aws/cloudtrail/logs  │
                    │  • /aws/ec2/application  │
                    │  • /aws/rds/mysql/error  │
                    │  • /aws/rds/mysql/slow   │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  🔒 Admin Access Only    │
                    │  AWS SSM Port Forward    │
                    │  localhost:8080 → EC2:80 │
                    └──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    4. AI LOG ANALYSIS ENGINE                        │
│                  (Bedrock + Streamlit UI)                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │  Log Preprocessing   │    │  Pattern Analysis    │
        │                      │    │                      │
        │  • Parse logs        │    │  • Clustering        │
        │  • Normalize format  │    │  • Temporal analysis │
        │  • Extract metadata  │    │  • Frequency count   │
        │  • Tag sources       │    │  • Noise reduction   │
        └──────────────────────┘    └──────────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  Advanced Correlation    │
                    │                          │
                    │  • Cross-source linking  │
                    │  • Timeline construction │
                    │  • Attack pattern match  │
                    │  • Confidence scoring    │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  Rule-Based Detection    │
                    │                          │
                    │  • SQL Injection         │
                    │  • Brute Force           │
                    │  • Port Scanning         │
                    │  • Privilege Escalation  │
                    │  • Data Exfiltration     │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  AI Enhancement          │
                    │  (AWS Bedrock)           │
                    │                          │
                    │  • Claude 3.5 Sonnet     │
                    │  • Global RCA            │
                    │  • MITRE ATT&CK mapping  │
                    │  • Remediation plan      │
                    │  • Impact assessment     │
                    └──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    5. ATTACK DETECTION DEMO                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │  Simulated Attack    │    │  Real-time Detection │
        │                      │    │                      │
        │  • SQL Injection     │───▶│  • VPC Flow: REJECT  │
        │  • Brute Force SSH   │    │  • App: SQL error    │
        │  • Port Scanning     │    │  • Trail: API abuse  │
        └──────────────────────┘    └──────────────────────┘
                                              │
                                              ▼
                                ┌──────────────────────────┐
                                │  AI Root Cause Analysis  │
                                │                          │
                                │  • Attack timeline       │
                                │  • Affected components   │
                                │  • Threat assessment     │
                                │  • Immediate actions     │
                                └──────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    6. ALERT & NOTIFICATION                          │
│                    (Telegram Integration)                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  Versus Incident         │
                    │  (Alert Gateway)         │
                    │                          │
                    │  • Multi-channel alerts  │
                    │  • Custom templates      │
                    │  • Telegram Bot API      │
                    │  • Rich formatting       │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  📱 Telegram Channel     │
                    │                          │
                    │  🚨 Critical Alert       │
                    │  Attack: SQL Injection   │
                    │  IP: 203.0.113.42        │
                    │  Severity: HIGH          │
                    │  Action: Block IP now    │
                    └──────────────────────────┘
```

---

## 🔍 Chi Tiết Các Thành Phần

### 1️⃣ Infrastructure Layer (Terraform)

**File:** `environments/dev/`

```
VPC Architecture:
├── Public Subnets (3 AZs)
│   └── ALB (Load Balancer)
├── Private Subnets (3 AZs)
│   ├── Web Server EC2 (Layer 1) - Public via ALB
│   └── App Server EC2 (Layer 2) - PRIVATE ONLY (SSM Access)
└── DB Subnets (3 AZs)
    └── RDS MySQL (Isolated)

Security Groups:
├── ALB SG: Allow 80/443 from Internet
├── Web SG: Allow 8080 from ALB only
├── App SG: NO INBOUND from ALB (Private access only)
└── DB SG: Allow 3306 from App SG only

Access Methods:
├── Layer 1 (Web): http://<ALB_DNS>:8080 (Public)
├── Layer 2 (App): AWS SSM Port Forwarding (Admin only)
└── Database: Private connection from App only

Logging:
├── VPC Flow Logs → CloudWatch
├── CloudTrail → CloudWatch
└── CloudWatch Agent → Application Logs
```

**Đánh giá:** ✅ **XUẤT SẮC** - Architecture tuân thủ best practices:
- 3-tier separation (Web/App/DB)
- Least-privilege security groups
- Private subnets cho sensitive workloads
- **Layer 2 isolated (SSM access only)** ⭐ Zero Trust Architecture
- Centralized logging

---

### 2️⃣ Configuration Management (Ansible)

**File:** `ansible/playbooks/`

```yaml
Playbook Execution Order:
1. ec2_setup (Base configuration)
2. install_cloudwatch_agent.yml
3. install_docker.yml
4. deploy_log_analyzer.yml (Streamlit AI)
5. deploy_web_app.yml (PHP App)
```

**Đánh giá:** ✅ **Đúng** - Automation đầy đủ:
- Idempotent playbooks
- Proper role separation
- CloudWatch Agent với custom config
- Docker containerization

---

### 3️⃣ Log Collection Pipeline

**Sources:**

| Log Type | Source | CloudWatch Group | Purpose |
|----------|--------|------------------|---------|
| **Network** | VPC Flow Logs | `/aws/vpc/flowlogs` | Detect port scanning, DDoS, network attacks |
| **API Audit** | CloudTrail | `/aws/cloudtrail/logs` | Track IAM abuse, resource changes |
| **Application** | EC2 Docker | `/aws/ec2/application` | Detect SQL injection, app errors |
| **Database** | RDS MySQL | `/aws/rds/mysql/error` | Database errors, slow queries |

**Đánh giá:** ✅ **Đúng** - Comprehensive logging:
- Multi-source correlation capability
- Real-time streaming to CloudWatch
- Structured log format

---

### 4️⃣ AI Analysis Engine

**File:** `AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/`

#### 🧠 Analysis Pipeline:

```python
Step 1: Log Retrieval
├── CloudWatchClient.get_logs()
├── Time range filtering
└── Multi-source parallel fetch

Step 2: Parsing & Normalization
├── LogParser.parse_log_entry()
├── Extract: timestamp, severity, message, IP, user
└── Tag with source component

Step 3: Pattern Analysis
├── PatternAnalyzer.analyze_log_entries()
├── Clustering similar errors
├── Temporal analysis (burst detection)
└── Noise reduction (90%+ compression)

Step 4: Advanced Correlation
├── AdvancedCorrelator.correlate_multi_source()
├── Link events by: IP, trace_id, session_id
├── Timeline construction with delays
├── Attack pattern matching (correlation_rules.json)
└── Confidence scoring

Step 5: Rule-Based Detection
├── RuleBasedDetector.detect_issues()
├── SQL Injection patterns
├── Brute force detection
├── Port scanning
└── Privilege escalation

Step 6: AI Enhancement (Bedrock)
├── BedrockEnhancer.generate_global_rca()
├── Model: Claude 3.5 Sonnet
├── Unified context with event signals
├── MITRE ATT&CK mapping
├── Root cause analysis
└── Actionable remediation plan
```

**Đánh giá:** ✅ **Đúng** - Sophisticated analysis:
- Multi-stage pipeline
- Cross-source correlation (KEY FEATURE)
- AI-powered root cause analysis
- MITRE framework integration

---

### 5️⃣ Attack Detection Capabilities

**Supported Attack Types:**

| Attack Type | Detection Method | Data Sources |
|-------------|------------------|--------------|
| **SQL Injection** | Pattern matching + AI | App logs, DB errors |
| **Brute Force** | Failed login frequency | VPC Flow (REJECT), App logs |
| **Port Scanning** | Multiple port attempts | VPC Flow Logs |
| **Privilege Escalation** | IAM policy changes | CloudTrail |
| **Data Exfiltration** | Large outbound traffic | VPC Flow Logs |
| **API Abuse** | Suspicious API calls | CloudTrail |

**Correlation Example:**
```
Attack: SQL Injection + Brute Force
├── T+0s: VPC Flow: 203.0.113.42 → Port 8080 (ACCEPT)
├── T+2s: App Log: SQL error "UNION SELECT" from 203.0.113.42
├── T+5s: VPC Flow: Multiple REJECT from 203.0.113.42
└── T+10s: CloudTrail: AccessDenied for user "attacker"

AI Analysis:
→ Attack Type: Multi-stage web application attack
→ MITRE: T1190 (Exploit Public-Facing Application)
→ Root Cause: Unvalidated user input in login form
→ Action: Block IP 203.0.113.42 in Security Group
```

**Đánh giá:** ✅ **Đúng** - Real attack detection:
- Cross-source correlation
- Timeline reconstruction
- Evidence-based analysis

---

### 6️⃣ Alert & Notification (Telegram)

**Integration với Versus Incident:**

```python
# Tích hợp vào bedrock_enhancer.py hoặc streamlit_app.py

import requests

def send_telegram_alert(attack_info):
    """
    Gửi cảnh báo qua Telegram sử dụng Versus Incident
    """
    versus_url = "http://versus-incident:3000/api/incidents"
    
    payload = {
        "attack_name": attack_info["attack_name"],
        "severity": attack_info["severity"],
        "attacker_ip": attack_info["attacker_ip"],
        "affected_components": attack_info["affected_components"],
        "root_cause": attack_info["root_cause"],
        "immediate_action": attack_info["immediate_action"],
        "evidence": attack_info["evidence"][:3],  # Top 3 log entries
        "timestamp": attack_info["timestamp"]
    }
    
    response = requests.post(versus_url, json=payload)
    return response.status_code == 200
```

**Telegram Template:** `config/telegram_message.tmpl`

```html
🚨 <b>SECURITY ALERT</b> 🚨

<b>Attack Detected:</b> {{.attack_name}}
<b>Severity:</b> {{.severity}}
<b>Attacker IP:</b> <code>{{.attacker_ip}}</code>

<b>🎯 Affected Components:</b>
{{range .affected_components}}• {{.}}
{{end}}

<b>🔍 Root Cause:</b>
{{.root_cause}}

<b>⚡ Immediate Action:</b>
<code>{{.immediate_action}}</code>

<b>📋 Evidence:</b>
{{range .evidence}}• {{.}}
{{end}}

<b>⏰ Detected:</b> {{.timestamp}}

<i>Powered by AI Log Analyzer</i>
```

**Đánh giá:** ⚠️ **Cần bổ sung** - Chưa có integration code:
- Cần thêm `send_telegram_alert()` function
- Trigger alert sau khi AI analysis hoàn thành
- Configure Versus Incident container

---

## 📊 Đánh Giá Tổng Thể

### ✅ Điểm Mạnh

1. **Architecture Design:**
   - 3-tier separation đúng chuẩn
   - Security groups theo least-privilege
   - Centralized logging

2. **AI Analysis:**
   - Multi-source correlation (VPC + CloudTrail + App)
   - Advanced pattern detection
   - MITRE ATT&CK framework
   - Root cause analysis với Bedrock

3. **Automation:**
   - Terraform IaC
   - Ansible configuration management
   - Docker containerization

4. **Detection Capabilities:**
   - SQL Injection
   - Brute Force
   - Port Scanning
   - Privilege Escalation
   - Cross-source attack chains

### ⚠️ Cần Bổ Sung

1. **Telegram Integration:**
   - ❌ Chưa có code gửi alert
   - ❌ Chưa deploy Versus Incident container
   - ❌ Chưa có Telegram Bot token config

2. **Real-time Alerting:**
   - ❌ Hiện tại chỉ có manual analysis qua UI
   - ❌ Cần thêm automated trigger

3. **Attack Simulation:**
   - ❌ Chưa có script tấn công demo
   - ❌ Cần tạo `generate_attack_logs.py`

---

## 🚀 Khuyến Nghị Cải Tiến

### 1. Thêm Telegram Alert Integration

**File mới:** `AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/src/telegram_notifier.py`

```python
import requests
import os
from typing import Dict

class TelegramNotifier:
    def __init__(self):
        self.versus_url = os.getenv("VERSUS_INCIDENT_URL", "http://localhost:3000")
        
    def send_alert(self, global_rca: Dict, correlated_events: list):
        """Gửi cảnh báo khi phát hiện attack"""
        if not global_rca:
            return
            
        payload = {
            "attack_name": global_rca.get("incident_story", ["Unknown"])[0],
            "severity": global_rca.get("threat_assessment", {}).get("severity", "Unknown"),
            "root_cause": global_rca.get("root_cause", "N/A"),
            "immediate_actions": global_rca.get("immediate_actions", []),
            "affected_components": [c.get("component") for c in global_rca.get("affected_components", [])],
            "evidence": [e.message for e in correlated_events[:3]] if correlated_events else []
        }
        
        try:
            response = requests.post(
                f"{self.versus_url}/api/incidents",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}")
            return False
```

### 2. Deploy Versus Incident Container

**File mới:** `ansible/playbooks/deploy_versus_incident.yml`

```yaml
---
- name: Deploy Versus Incident Alert Gateway
  hosts: role_app
  become: yes
  tasks:
    - name: Run Versus Incident container
      community.docker.docker_container:
        name: versus-incident
        image: ghcr.io/versuscontrol/versus-incident:latest
        state: started
        restart_policy: unless-stopped
        ports:
          - "3000:3000"
        env:
          TELEGRAM_ENABLE: "true"
          TELEGRAM_BOT_TOKEN: "{{ telegram_bot_token }}"
          TELEGRAM_CHAT_ID: "{{ telegram_chat_id }}"
        volumes:
          - /home/ec2-user/versus-config:/app/config:ro
```

### 3. Attack Simulation Script

**File mới:** `AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/simulate_attack.py`

```python
"""
Simulate SQL Injection + Brute Force attack for demo
"""
import requests
import time

TARGET_URL = "http://your-alb-dns/login.php"
ATTACKER_IP = "203.0.113.42"  # Simulated

def simulate_sql_injection():
    """Simulate SQL injection attempts"""
    payloads = [
        "' OR '1'='1",
        "admin' --",
        "' UNION SELECT NULL--",
    ]
    
    for payload in payloads:
        requests.post(TARGET_URL, data={"username": payload, "password": "test"})
        time.sleep(2)

def simulate_brute_force():
    """Simulate brute force login"""
    for i in range(20):
        requests.post(TARGET_URL, data={"username": "admin", "password": f"pass{i}"})
        time.sleep(1)

if __name__ == "__main__":
    print("🚨 Starting attack simulation...")
    simulate_sql_injection()
    simulate_brute_force()
    print("✅ Attack simulation complete. Check logs in 2-3 minutes.")
```

---

## 📝 Kết Luận

### Luồng Phân Tích Hiện Tại: ✅ **ĐÃ ĐÚNG**

```
Terraform → Ansible → Logs → CloudWatch → AI Analysis → RCA
```

### Cần Bổ Sung: ⚠️ **Telegram Alert**

```
AI Analysis → Versus Incident → Telegram Bot → 📱 Alert
```

### Demo Flow Hoàn Chỉnh:

```
1. ✅ Setup infrastructure (Terraform)
2. ✅ Deploy apps (Ansible)
3. ✅ Collect logs (CloudWatch)
4. ✅ AI analysis (Bedrock)
5. ⚠️ Simulate attack (Cần thêm script)
6. ⚠️ Send alert (Cần thêm Telegram integration)
```

---

## 🎯 Next Steps

1. **Thêm Telegram Integration:**
   - Deploy Versus Incident container
   - Tạo Telegram Bot
   - Integrate vào `streamlit_app.py`

2. **Tạo Attack Simulation:**
   - Script SQL Injection
   - Script Brute Force
   - Script Port Scanning

3. **Testing:**
   - Run attack simulation
   - Verify logs in CloudWatch
   - Confirm AI detection
   - Check Telegram alert

---

**Tác giả:** AI Log Analysis System  
**Ngày:** 2026-04-24  
**Version:** 1.0
