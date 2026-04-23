# 🔍 Bedrock Log Analyzer UI

AI-powered multi-source log analysis system that pulls logs from **AWS CloudWatch**, detects threats and anomalies using rule-based detection, and enhances solutions with **AWS Bedrock** (Claude 3 Haiku / Sonnet).

Built with **Streamlit** for an interactive, real-time analysis dashboard.

---

## ✨ Features

### **🎯 Main Analysis Engine (Multi-Source Correlation)**
- **Advanced Correlation** ⭐ — Correlate logs across multiple sources using trace_id, request_id, session_id, instance_id, and IP
- **Timeline Sequence Detection** — Build attack timelines with delay calculations between events
- **Rule Engine** — Match against detection rules (SSH Brute Force, SQL Injection, Port Scan, etc.)
- **Confidence Scoring** — Multi-factor confidence calculation (severity, sequence logic, anomaly level, correlation strength)
- **AI Context Enhancement** — AI receives full correlation metadata (no "guessing"), focuses on root cause and remediation

### **🔬 Advanced Drill-Down (Single Source)**
- **Deep Dive Analysis** — Detailed investigation of specific log sources
- **Temporal Analysis** — Detect burst attacks and time-based patterns (events/minute, peak activity, attack duration)
- **Context-Aware Rule Detection** — Avoid false positives with positive/negative keyword matching and severity scoring

### **🤖 AI-Powered Analysis**
- **Structured JSON Output** — Strict separation of Evidence vs Inference
- **MITRE ATT&CK Classification** — Map attacks to MITRE framework
- **Actionable Remediation** — Specific AWS CLI commands (not placeholders)
- **Prevention Strategies** — AWS services, configuration changes, monitoring improvements
- **Cost Optimization** — Token reduction (30-50% savings) through intelligent context building

### **📊 Interactive Dashboard**
- **Multi-Tier UI** — Summary (Severity/Impact) → Investigation (Evidence) → Action Plan (Remediation)
- **Correlation Visualization** — View correlated events, timelines, and matched rules
- **Charts & Metrics** — Severity distribution, component distribution, attack metrics
- **Export Results** — Download as JSON or CSV

### **🔧 Technical Features**
- **Multi-Format Log Parsing** — VPC Flow Logs, CloudTrail JSON, modern JSON app logs, classic logs
- **Concurrent Log Ingestion** — Pull from multiple CloudWatch Log Groups without throttling
- **Cross-Region Bedrock Support** — Use APAC/US inference profiles to avoid capacity limits
- **Docker Support** — Containerized deployment with health checks

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  CloudWatch  │────▶│  Log Parser      │────▶│ Pattern Analyzer │
│  Log Groups  │     │  (4 formats)     │     │  + Temporal      │
│              │     │  • VPC Flow      │     │                  │
│  • VPC Flow  │     │  • CloudTrail    │     │  Severity dist.  │
│  • CloudTrail│     │  • JSON App Logs │     │  Component dist. │
│  • App Logs  │     │  • Classic Logs  │     │  Error patterns  │
└──────────────┘     └──────────────────┘     │  ⭐ Attack velocity│
                                               │  ⭐ Burst detection│
                                               └────────┬─────────┘
                                                        │
                                                        ▼
                                              ┌──────────────────┐
                                              │ Rule Detector    │
                                              │ (Context-Aware)  │
                                              │  • Relevancy     │
                                              │  • Context       │
                                              │  ⭐ Severity Score│
                                              │  ⭐ False Positive│
                                              │     Filtering    │
                                              └────────┬─────────┘
                                                       │
                                                       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Streamlit   │◀────│ Bedrock Enhancer │◀────│  AI Context      │
│  Dashboard   │     │  (Claude 3.5)    │     │  (Top samples,   │
│              │     │                  │     │   Suspicious IPs,│
│  • Summary   │     │  Strict JSON:    │     │   Actors, APIs,  │
│  • Analysis  │     │  • Summary       │     │   ⭐ Temporal)   │
│  • Solutions │     │  • Investigation │     └──────────────────┘
└──────────────┘     │  • Action Plan   │
                     └──────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
chmod +x setup.sh
./setup.sh
source venv/bin/activate
```

The setup script will:
- Create a Python virtual environment
- Install all dependencies
- Create `.env` from template
- Verify AWS CLI and credentials

### 2. Configure AWS Credentials

```bash
aws configure
# Or use IAM role if running on EC2
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

```ini
# .env
AWS_REGION=ap-southeast-1
AWS_PROFILE=default
BEDROCK_MODEL=anthropic.claude-3-haiku-20240307-v1:0
MAX_TOKENS=2000
TEMPERATURE=0.3
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### 4. Run the Application

```bash
streamlit run streamlit_app.py
```

Open **http://localhost:8501** in your browser.

---

## 🎯 Recommended Workflow

### **Step 1: Discovery (Multi-Source - Main Engine)** 🔍

```
1. Open app → Default mode: Multi-Source Correlation ✅
2. Select 2-3 log sources:
   ✓ /aws/vpc/flowlogs
   ✓ /aws/ec2/application
   ✓ /aws/cloudtrail/logs (optional)
3. Leave Search Term empty (auto-scan for anomalies)
4. Time Range: Last 1 hour
5. Correlation Engine: Advanced (Trace ID + Timeline)
6. Click "🚀 Analyze Logs"

Expected Results:
  ✅ Correlated attack patterns detected:
     • SSH Brute Force (Confidence: 95.2%)
     • SQL Injection (Confidence: 87.5%)
     • Port Scanning (Confidence: 72.3%)
```

### **Step 2: Investigation (Single Source - Advanced)** 🔬

```
1. From Step 1 results, identify specific source to investigate
2. Switch to "Single Source (Advanced)" mode
3. Select log group: /aws/vpc/flowlogs
4. Search Term: "REJECT" or specific IP "203.0.113.42"
5. Time Range: Keep same or narrow down
6. Click "🚀 Analyze Logs"

Expected Results:
  ✅ Deep dive into VPC logs:
     • 53 REJECT events from IP 203.0.113.42
     • Target port: 22 (SSH)
     • Detailed timeline per packet
     • Source/Dest IPs, Ports, Protocols
```

---

## ⚙️ Configuration (Sidebar)

### **Analysis Mode** 🎯

| Mode | Description | Use Case |
|------|-------------|----------|
| **Multi-Source Correlation** (Default) | Main analysis engine - correlate logs from 2-4 sources | **Recommended:** Discover sophisticated attack patterns across infrastructure |
| **Single Source (Advanced)** | Deep dive into one specific log group | Advanced investigation after discovering threats |

### **Settings**

| Setting | Description | Default |
|---------|-------------|---------|
| **AWS Region** | AWS region for CloudWatch & Bedrock | `ap-southeast-1` |
| **AWS Profile** | AWS CLI profile name | `default` |
| **Log Sources** | CloudWatch Log Groups (2-4 for Multi-Source, 1 for Single Source) | VPC + App logs |
| **Search Term** | Keyword filter (Optional for Multi-Source, Required for Single Source) | Auto-scan |
| **Time Range** | Specific Start Date/Time and End Date/Time | `Last 1 Hour` |
| **Correlation Engine** | Basic (IP-based) or Advanced (Trace ID + Timeline + Rules) | `Advanced` |
| **Enable AI** | Toggle Bedrock AI enhancement | `true` |
| **Bedrock Model** | AI model selection (Cross-Region supported) | Claude 3 Haiku |

### Default Log Groups

```
/aws/vpc/flowlogs
/aws/cloudtrail/logs
/aws/ec2/applogs
```

---

## 🔐 IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🤖 Supported AI Models

Inference routes include **Cross-Region Inference Profiles (`apac.` and `us.`)** to prevent On-Demand capacity limits.

| Model ID | Speed | Intelligence | Notes |
|-------|-------|-------------|-------------------|
| `anthropic.claude-3-haiku...` | ⚡ Ultra-fast | Good | Standard on-demand limit |
| `apac.anthropic.claude-3-5-sonnet...` | 🐢 Slower | Excellent | Uses APAC Cross-Region routing |
| `us.anthropic.claude-3-5-sonnet...` | 🐢 Slower | Excellent | Uses US Cross-Region routing |

> **Recommendation:** Use **Claude 3 Haiku** for daily quick checks. Switch to **APAC Claude 3.5 Sonnet** (`apac.*`) for highly complex investigations to avoid AWS throughput errors.

---

## 📊 Log Format Support

### VPC Flow Logs
```
2 123456789012 eni-abc123 203.0.113.42 10.0.1.55 44321 22 6 20 1800 1620140600 1620140660 REJECT OK
```
- Auto-detected via regex pattern
- `REJECT` actions are flagged as `ERROR` severity
- Parsed fields: Source IP, Dest IP, Ports, Protocol, Action

### CloudTrail Events (JSON)
```json
{
  "eventName": "DeleteVpc",
  "errorCode": "AccessDenied",
  "userIdentity": { "arn": "arn:aws:iam::123456789012:user/dev-intern" }
}
```
- Auto-detected by `eventVersion` + `eventName` keys
- Events with `errorCode` or `AccessDenied` are flagged as `ERROR`
- Extracts: API action, caller ARN, error details

### Application Logs
```
[ERROR] Database: Connection pool exhausted. Maximum connections (100) exceeded.
```
- Parsed via regex for timestamp, severity, component, message
- Supports: `ERROR`, `WARNING`, `INFO`, `DEBUG`, `CRITICAL`, `FATAL`

---

## 🧪 Test Log Generators

Two scripts are included to generate test data in CloudWatch:

### `generate_test_logs.py`
Pushes 7 simulated security events (SSH brute force attack scenario) to a single log group.

```bash
python generate_test_logs.py
```

### `generate_omni_logs.py`
Generates **1,000 logs** distributed across 3 log groups for stress testing:

```bash
python generate_omni_logs.py
```

| Log Group | Content | Distribution |
|-----------|---------|-------------|
| `/aws/vpc/flowlogs` | VPC Flow Logs (REJECT) | ~70% |
| `/aws/ec2/applogs` | Application errors (Web, DB, Backend, Auth) | ~20% |
| `/aws/cloudtrail/logs` | CloudTrail AccessDenied events | ~10% |

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t bedrock-analyzer .

# Run
docker run -p 8501:8501 \
  -e AWS_REGION=ap-southeast-1 \
  -v ~/.aws:/root/.aws \
  bedrock-analyzer
```

The container includes a health check at `http://localhost:8501/_stcore/health`.

---

## 🔧 Troubleshooting

### AWS Credentials Error
```bash
aws sts get-caller-identity
```

### Port Already in Use
```bash
streamlit run streamlit_app.py --server.port=8502
```

### Bedrock Access Denied
1. Verify IAM permissions include `bedrock:InvokeModel`
2. Check that the selected model is enabled in your AWS region
3. Ensure the region supports Bedrock (see [AWS Bedrock regions](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html))

### No Logs Found
1. Verify the log group names exist in CloudWatch
2. Check the time range — logs may be outside the selected window
3. Try removing the search term filter to see all logs

---

## 📁 Project Structure

```
bedrock-log-analyzer-ui/
├── streamlit_app.py           # Main Streamlit UI (368 lines)
├── cloudwatch_client.py       # CloudWatch API integration
├── generate_test_logs.py      # Security attack scenario generator
├── generate_omni_logs.py      # 1000-log multi-source stress test
├── src/                       # Core analysis engine
│   ├── __init__.py            # Package exports
│   ├── models.py              # Data models (LogEntry, Solution, etc.)
│   ├── log_parser.py          # Multi-format log parser (VPC/CT/App)
│   ├── pattern_analyzer.py    # Pattern extraction & statistics
│   ├── rule_detector.py       # Rule-based issue detection
│   ├── log_preprocessor.py    # Data scoring & contextual sampling
│   └── bedrock_enhancer.py    # AWS Bedrock AI enhancement (Strict JSON)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── setup.sh                   # Automated setup script
├── Dockerfile                 # Docker container config
└── .gitignore                 # Git ignore rules
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | ≥ 1.28.0 | Web UI framework |
| `boto3` | ≥ 1.34.0 | AWS SDK (CloudWatch + Bedrock) |
| `python-dotenv` | ≥ 1.0.0 | Environment variable management |
| `dataclasses-json` | ≥ 0.6.0 | Data serialization |

---

## 📄 License

MIT
