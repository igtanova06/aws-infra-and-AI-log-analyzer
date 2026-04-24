# 🔍 AI-Powered Log Analysis System

Advanced multi-source log correlation and AI-powered root cause analysis system for AWS environments.

## 🎯 Features

- **Multi-Source Correlation** - Correlate events across VPC Flow Logs, CloudTrail, Application Logs, and Database Logs
- **AI-Powered RCA** - Global Root Cause Analysis using AWS Bedrock (Claude 3.5 Sonnet)
- **Advanced Detection** - Rule-based detection with MITRE ATT&CK mapping
- **Real-Time Alerts** - Telegram notifications via Versus Incident gateway
- **Rich Context** - Event abstraction layer for token-efficient AI analysis

## 📋 Prerequisites

- Python 3.11+
- AWS Account with:
  - CloudWatch Logs access
  - Bedrock access (Claude 3.5 Sonnet)
  - IAM permissions for log reading
- Telegram Bot (for alerts)
- Docker (for deployment)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Configuration

Edit `.env`:

```bash
# AWS Configuration
AWS_REGION=ap-southeast-1
AWS_PROFILE=default  # or leave empty for EC2 IAM role

# Bedrock Configuration
BEDROCK_MODEL=apac.anthropic.claude-3-5-sonnet-20240620-v1:0

# Telegram Alert Configuration
TELEGRAM_ALERTS_ENABLED=true
VERSUS_INCIDENT_URL=http://localhost:3000
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Run Locally

```bash
streamlit run streamlit_app.py
```

Open browser: http://localhost:8501

### 4. Run with Docker

```bash
# Build image
docker build -t bedrock-log-analyzer .

# Run container
docker run -d \
  --name log-analyzer \
  -p 8501:8501 \
  -e AWS_REGION=ap-southeast-1 \
  -e TELEGRAM_ALERTS_ENABLED=true \
  -e VERSUS_INCIDENT_URL=http://versus-incident:3000 \
  -v ~/.aws:/root/.aws:ro \
  bedrock-log-analyzer
```

## 🧪 Testing with Attack Simulation

### 1. Deploy Infrastructure

```bash
# Deploy with Terraform + Ansible
cd ../../
terraform -chdir=environments/dev init
terraform -chdir=environments/dev apply

# Configure with Ansible
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
ansible-playbook ansible/playbooks/site.yml
```

### 2. Run Attack Simulation

```bash
# Get ALB DNS from Terraform output
ALB_DNS=$(terraform -chdir=environments/dev output -raw alb_dns_name)

# Run simulation
python simulate_attack.py --target http://${ALB_DNS}:8080
```

### 3. Analyze Logs

1. Wait 2-3 minutes for logs to appear in CloudWatch
2. Open AI Log Analyzer UI (via SSH tunnel if private)
3. Select time range: Last 10 minutes
4. Select all log sources
5. Click "Analyze Logs"
6. Check Telegram for alert

## 📊 Architecture

```
CloudWatch Logs → Parser → Pattern Analyzer → Rule Detector
                                                    ↓
                                          Advanced Correlator
                                                    ↓
                                          Event Abstraction
                                                    ↓
                                          Bedrock AI (RCA)
                                                    ↓
                                          Telegram Alert
```

## 🔧 Advanced Configuration

### Correlation Rules

Edit `correlation_rules.json` to customize detection rules:

```json
{
  "rule_id": "R001",
  "name": "Reconnaissance to Exploit",
  "required_sources": ["vpc_flow", "application"],
  "event_sequence": ["network_reject", "sql_injection"],
  "max_time_gap_seconds": 300,
  "severity": "CRITICAL"
}
```

### Log Sources

Supported log formats:
- VPC Flow Logs
- CloudTrail (JSON)
- Apache Access/Error Logs
- Syslog (SSH, system)
- MySQL Error/Slow Query Logs
- JSON Application Logs

## 📚 Documentation

- [System Architecture](../../docs/SYSTEM_ARCHITECTURE.md)
- [Setup Guide](../../docs/SETUP_GUIDE.md)
- [Telegram Setup](../../docs/TELEGRAM_SETUP.md)
- [DevOps Review](../DEVOPS_REVIEW_AND_RECOMMENDATIONS.md)

## 🐛 Troubleshooting

### No logs found
- Verify CloudWatch log groups exist
- Check IAM permissions
- Verify time range includes log events

### Bedrock errors
- Check model availability in your region
- Verify Bedrock permissions
- Try different model (e.g., claude-3-haiku for on-demand)

### Telegram alerts not working
- Verify Versus Incident is running: `docker ps | grep versus`
- Check environment variables are set
- Test with: `curl http://localhost:3000/health`

## 📝 License

MIT License - See LICENSE file for details

## 👥 Contributors

- DevOps Security Team

## 🔗 Related Projects

- [Versus Incident](https://github.com/versuscontrol/versus-incident) - Alert gateway
- [AWS Bedrock](https://aws.amazon.com/bedrock/) - AI foundation models
