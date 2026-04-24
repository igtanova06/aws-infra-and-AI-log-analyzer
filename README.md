# 🤖 AI-Powered Log Analysis & Security Monitoring System

[![AWS](https://img.shields.io/badge/AWS-Bedrock-orange)](https://aws.amazon.com/bedrock/)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-purple)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Config-Ansible-red)](https://www.ansible.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Hệ thống phát hiện và phân tích tấn công mạng tự động sử dụng AI (AWS Bedrock) với khả năng tương quan logs từ nhiều nguồn và gửi cảnh báo real-time qua Telegram.

---

## 🎯 Tính Năng Chính

### 🏗️ Infrastructure as Code
- **Terraform:** Tự động triển khai VPC, EC2, RDS, ALB, CloudWatch, CloudTrail
- **3-Tier Architecture:** Web → App → Database với security groups theo least-privilege
- **Multi-AZ Deployment:** High availability across 3 availability zones

### ⚙️ Configuration Management
- **Ansible:** Tự động cấu hình EC2, deploy applications, setup monitoring
- **Docker Containerization:** Isolated workloads với resource limits
- **CloudWatch Agent:** Centralized log collection từ tất cả sources

### 📊 Log Collection & Analysis
- **Multi-Source Logs:**
  - VPC Flow Logs (network traffic)
  - CloudTrail (API audit logs)
  - Application Logs (PHP errors, SQL queries)
  - RDS Logs (database errors, slow queries)
- **Real-time Streaming:** Logs → CloudWatch → AI Analysis

### 🤖 AI-Powered Detection
- **AWS Bedrock (Claude 3.5 Sonnet):** Advanced root cause analysis
- **Cross-Source Correlation:** Liên kết events từ nhiều log sources
- **Pattern Recognition:** Clustering, temporal analysis, anomaly detection
- **MITRE ATT&CK Mapping:** Phân loại attack theo framework chuẩn

### 🚨 Attack Detection
- **SQL Injection:** Pattern matching + AI validation
- **Brute Force:** Failed login frequency analysis
- **Port Scanning:** Multiple connection attempts detection
- **Privilege Escalation:** IAM policy abuse detection
- **Data Exfiltration:** Large outbound traffic analysis
- **Multi-Stage Attacks:** Timeline reconstruction với correlation

### 📱 Real-time Alerting
- **Telegram Integration:** Instant alerts qua Telegram Bot
- **Versus Incident Gateway:** Multi-channel alert routing
- **Rich Formatting:** HTML messages với evidence, commands, MITRE mapping
- **Actionable Remediation:** AWS CLI commands để block attackers

---

## 🏛️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Application Load    │
              │  Balancer (ALB)      │
              └──────────┬───────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Web Server  │  │ App Server  │  │ RDS MySQL   │
│ (PHP App)   │  │ (Streamlit) │  │ (Database)  │
│ Port 8080   │  │ Port 80     │  │ Port 3306   │
└─────────────┘  └─────────────┘  └─────────────┘
      │                 │                 │
      └─────────────────┼─────────────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │   CloudWatch Logs    │
              │  • VPC Flow Logs     │
              │  • CloudTrail        │
              │  • Application Logs  │
              │  • RDS Logs          │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  AI Analysis Engine  │
              │  • Log Parsing       │
              │  • Pattern Analysis  │
              │  • Correlation       │
              │  • Bedrock AI        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Versus Incident     │
              │  (Alert Gateway)     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  📱 Telegram Bot     │
              │  Security Alerts     │
              └──────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- AWS Account với Bedrock access
- Terraform >= 1.5
- Ansible >= 2.14
- Python >= 3.9
- Telegram Bot Token

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd AI_Log_Analysis-Project-1
```

### 2. Setup Infrastructure

```bash
cd environments/dev
terraform init
terraform apply
```

### 3. Configure Telegram

```bash
# Tạo bot với @BotFather
# Lấy bot token và chat ID
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

### 4. Deploy Applications

```bash
cd ../../ansible
ansible-playbook playbooks/site.yml
```

### 5. Run Attack Simulation

```bash
cd ../AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui

# Get Web App URL (Layer 1 is public)
export TARGET_URL="http://$(cd ../../environments/dev && terraform output -raw alb_dns_name):8080/api/login.php"

python simulate_attack.py --target $TARGET_URL --attack-type combined
```

### 6. Access Layer 2 via SSM Port Forwarding

⚠️ **Layer 2 (Log Analyzer) chỉ accessible qua AWS SSM Port Forwarding**

```bash
# Install Session Manager Plugin (one-time)
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb

# Get instance ID
export INSTANCE_ID=$(cd environments/dev && terraform output -raw app_instance_id)

# Start port forwarding
aws ssm start-session \
  --target $INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["80"],"localPortNumber":["8080"]}'

# Open browser (in new terminal)
open http://localhost:8080
```

### 7. Analyze Logs

1. Open `http://localhost:8080` in browser (via SSM port forwarding)
2. Configure analysis settings
3. Click **🚀 Analyze Logs**
4. Check Telegram for alerts

---

## 📚 Documentation

- **[Quick Start](docs/QUICK_START.md)** - Truy cập Layer 2 trong 5 phút ⚡
- **[SSM Access Guide](docs/SSM_ACCESS_GUIDE.md)** - Chi tiết về AWS SSM Port Forwarding 🔒
- **[System Architecture](docs/SYSTEM_ARCHITECTURE.md)** - Sơ đồ kiến trúc chi tiết
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Hướng dẫn setup từng bước
- **[Telegram Setup](docs/TELEGRAM_SETUP.md)** - Cấu hình Telegram Bot
- **[Attack Simulation](AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/simulate_attack.py)** - Script tấn công demo

---

## 🎭 Demo Scenarios

### Scenario 1: SQL Injection Attack

```bash
python simulate_attack.py --target $TARGET_URL --attack-type sql --count 10
```

**AI Detection:**
- Attack Type: SQL Injection
- MITRE: T1190 (Exploit Public-Facing Application)
- Evidence: `' OR '1'='1`, `UNION SELECT` patterns
- Action: Block IP, sanitize inputs

### Scenario 2: Brute Force Attack

```bash
python simulate_attack.py --target $TARGET_URL --attack-type brute --count 20
```

**AI Detection:**
- Attack Type: Brute Force
- MITRE: T1110 (Brute Force)
- Evidence: 20 failed login attempts in 40 seconds
- Action: Rate limiting, account lockout

### Scenario 3: Multi-Stage Attack

```bash
python simulate_attack.py --target $TARGET_URL --attack-type combined
```

**AI Detection:**
- Attack Type: Multi-stage (Recon → Exploit → Credential Access)
- MITRE: T1046 (Network Service Scanning), T1190, T1110
- Evidence: Port scan → SQL injection → Brute force
- Action: Block IP, review security posture

---

## 🔍 Attack Detection Examples

### Example 1: SQL Injection + Brute Force

**Logs Collected:**
```
[10:23:45] VPC Flow: 203.0.113.42 → 10.0.11.5:8080 ACCEPT
[10:23:47] App Log: SQL error "UNION SELECT" from 203.0.113.42
[10:24:00] App Log: Failed login attempt #1 from 203.0.113.42
[10:24:02] App Log: Failed login attempt #2 from 203.0.113.42
...
[10:25:30] VPC Flow: 203.0.113.42 → 10.0.11.5:8080 REJECT (blocked)
```

**AI Analysis:**
```
🚨 SECURITY ALERT 🚨

Attack Detected: Multi-stage SQL Injection + Brute Force Attack
Severity: HIGH | Confidence: 95%
Attacker IP: 203.0.113.42

🎯 Affected Components:
• Web Application (High impact)
• Database (Medium impact)

🔍 Root Cause:
Unvalidated user input in login form allows SQL injection.
Attacker exploited this to bypass authentication and attempted
brute force on multiple accounts.

⚡ Immediate Actions:
[P1] Block attacker IP in Security Group
→ aws ec2 revoke-security-group-ingress --group-id sg-xxx --cidr 203.0.113.42/32

[P1] Disable affected user accounts
→ mysql -e "UPDATE users SET status='locked' WHERE last_login_ip='203.0.113.42'"

🛡️ MITRE ATT&CK: T1190, T1110

⏰ Detected: 2026-04-24 10:30:15
```

---

## 💰 Cost Estimation

**Monthly costs (ap-southeast-1):**
- EC2 (2x t3.micro): ~$15
- RDS (db.t3.micro): ~$15
- ALB: ~$20
- CloudWatch Logs (5GB): ~$3
- VPC Flow Logs: ~$5
- Bedrock (Claude 3.5 Sonnet): ~$0.50/analysis
- **Total: ~$60/month**

**Cost optimization:**
- Disable NAT Gateway (saves $32/month)
- Use t3.micro instead of t3.small
- Set CloudWatch log retention to 7 days
- Stop instances when not in use

---

## 🔒 Security Features

### Infrastructure Security
- ✅ 3-tier network isolation
- ✅ Security groups với least-privilege
- ✅ Private subnets cho sensitive workloads
- ✅ **Layer 2 isolated (SSM access only)** ⭐ Zero Trust
- ✅ No public IPs on app/db instances
- ✅ SSM Session Manager (no SSH keys)

### Application Security
- ✅ Docker container isolation
- ✅ Read-only volumes
- ✅ Resource limits (CPU, memory)
- ✅ Non-root user execution

### Monitoring & Detection
- ✅ VPC Flow Logs (network monitoring)
- ✅ CloudTrail (API audit)
- ✅ Application logs (error tracking)
- ✅ Real-time AI analysis
- ✅ MITRE ATT&CK mapping

---

## 🧪 Testing

### Unit Tests

```bash
cd AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui
pytest tests/
```

### Integration Tests

```bash
# Test CloudWatch connectivity
python -c "from cloudwatch_client import CloudWatchClient; print(CloudWatchClient().get_logs('/aws/vpc/flowlogs'))"

# Test Bedrock API
python -c "from bedrock_enhancer import BedrockEnhancer; print(BedrockEnhancer().is_available())"

# Test Telegram integration
python -c "from telegram_notifier import TelegramNotifier; TelegramNotifier().send_test_alert()"
```

---

## 🐛 Troubleshooting

### Issue: Cannot access Layer 2 UI

```bash
# Layer 2 is PRIVATE - must use SSM Port Forwarding
aws ssm start-session \
  --target $(terraform output -raw app_instance_id) \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["80"],"localPortNumber":["8080"]}'

# Then access: http://localhost:8080
# See: docs/SSM_ACCESS_GUIDE.md
```

### Issue: Logs not appearing in CloudWatch

```bash
# Check CloudWatch Agent status
sudo systemctl status amazon-cloudwatch-agent

# Restart agent
sudo systemctl restart amazon-cloudwatch-agent
```

### Issue: Telegram alerts not sending

```bash
# Check Versus Incident logs
docker logs versus-incident

# Test Telegram Bot manually
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}" \
  -d "text=Test"
```

### Issue: Bedrock API errors

```bash
# Check model access
aws bedrock list-foundation-models --region ap-southeast-1

# Enable model access in AWS Console:
# Bedrock → Model access → Request model access
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **AWS Bedrock** - AI-powered analysis
- **Versus Incident** - Multi-channel alerting ([GitHub](https://github.com/VersusControl/versus-incident))
- **MITRE ATT&CK** - Attack classification framework
- **Streamlit** - Interactive UI framework

---

## 📞 Contact

- **Author:** Your Name
- **Email:** your.email@example.com
- **Project Link:** [https://github.com/yourusername/ai-log-analysis](https://github.com/yourusername/ai-log-analysis)

---

## 🗺️ Roadmap

- [x] Infrastructure automation (Terraform)
- [x] Configuration management (Ansible)
- [x] Multi-source log collection
- [x] AI-powered analysis (Bedrock)
- [x] Cross-source correlation
- [x] Telegram alerting
- [ ] GuardDuty integration
- [ ] Slack alerting
- [ ] Email alerting
- [ ] Custom detection rules UI
- [ ] Historical attack analysis
- [ ] Automated remediation
- [ ] Compliance reporting (PCI-DSS, HIPAA)

---

**Built with ❤️ for Security Engineers**

**Version:** 1.0  
**Last Updated:** 2026-04-24
