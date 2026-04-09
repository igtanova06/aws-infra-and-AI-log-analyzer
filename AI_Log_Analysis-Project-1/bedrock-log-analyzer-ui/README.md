# 🔍 Bedrock Log Analyzer UI

AI-powered multi-source log analysis system that pulls logs from **AWS CloudWatch**, detects threats and anomalies using rule-based detection, and enhances solutions with **AWS Bedrock** (Claude 3 Haiku / Sonnet).

Built with **Streamlit** for an interactive, real-time analysis dashboard.

---

## ✨ Features

- **Multi-Source Log Ingestion** — Concurrently pull logs from multiple CloudWatch Log Groups (VPC Flow Logs, CloudTrail, Application Logs) to prevent throttling
- **Multi-Format Log Parsing** — Automatically detect and parse VPC Flow Logs, CloudTrail JSON events, and classic application logs
- **Rule-Based Issue Detection** — Detect connection, permission, resource, database, and security issues using keyword-based rules
- **AI-Enhanced Solutions** — Leverage AWS Bedrock (Claude 3) for root cause analysis, step-by-step troubleshooting, and prevention strategies
- **Interactive Dashboard** — 3-tab UI with Summary, Analysis, and Solutions views
- **Severity & Component Charts** — Visualize error distribution across severity levels and components
- **Export Results** — Download analysis results as JSON or CSV
- **Docker Support** — Containerized deployment with health checks

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  CloudWatch  │────▶│  Log Parser      │────▶│ Pattern Analyzer │
│  Log Groups  │     │  (3 formats)     │     │                  │
│              │     │  • VPC Flow      │     │  Severity dist.  │
│  • VPC Flow  │     │  • CloudTrail    │     │  Component dist. │
│  • CloudTrail│     │  • App Logs      │     │  Error patterns  │
│  • App Logs  │     └──────────────────┘     └────────┬─────────┘
└──────────────┘                                       │
                                                       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Streamlit   │◀────│ Bedrock Enhancer │◀────│  Rule Detector   │
│  Dashboard   │     │  (Claude 3)      │     │                  │
│              │     │                  │     │  • Connection    │
│  • Summary   │     │  Root cause      │     │  • Permission    │
│  • Analysis  │     │  Troubleshooting │     │  • Resource      │
│  • Solutions │     │  Prevention      │     │  • Security      │
└──────────────┘     └──────────────────┘     └──────────────────┘
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

## ⚙️ Configuration (Sidebar)

| Setting | Description | Default |
|---------|-------------|---------|
| **AWS Region** | AWS region for CloudWatch & Bedrock | `ap-southeast-1` |
| **AWS Profile** | AWS CLI profile name | `default` |
| **Log Groups** | CloudWatch Log Groups (one per line or comma-separated) | VPC, CloudTrail, App Logs |
| **Hours Back** | Time range to query (1–168 hours) | `1` |
| **Search Term** | Keyword filter for log messages | `error` |
| **Max Matches** | Maximum log entries to pull (10–1000) | `500` |
| **Enable AI** | Toggle Bedrock AI enhancement | `true` |
| **Bedrock Model** | AI model selection | Claude 3 Haiku |

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

| Model | Speed | Intelligence | Cost per Analysis |
|-------|-------|-------------|-------------------|
| **Claude 3 Haiku** | ⚡ Ultra-fast | Good | ~$0.005 |
| **Claude 3 Sonnet** | 🐢 Slower | Excellent | ~$0.025 |

> **Recommendation:** Use **Claude 3 Haiku** for daily operations (fast & cheap). Switch to **Claude 3 Sonnet** for deep investigation of complex incidents.

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
│   └── bedrock_enhancer.py    # AWS Bedrock AI enhancement
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
