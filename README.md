# 🏗️ AWS Infrastructure & AI-Powered RCA Agent

> **Hệ thống hạ tầng AWS 3-tier với AI Agent tự động phân tích nguyên nhân gốc rễ (Root Cause Analysis)**

[![Terraform](https://img.shields.io/badge/Terraform-v1.0+-623CE4?logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Ansible-v2.9+-EE0000?logo=ansible&logoColor=white)](https://www.ansible.com/)
[![AWS](https://img.shields.io/badge/AWS-ap--southeast--1-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Framework-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![Bedrock](https://img.shields.io/badge/AWS_Bedrock-Claude_AI-4B0082)](https://aws.amazon.com/bedrock/)

---

## 📋 Mục lục

- [Tổng quan](#-tổng-quan)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Cấu trúc project](#-cấu-trúc-project)
- [Ứng dụng](#-ứng-dụng)
- [AI Agent RCA](#-ai-agent-rca)
- [Log Collection & Observability](#-log-collection--observability)
- [Hướng dẫn Deploy](#-hướng-dẫn-deploy)
- [Truy cập ứng dụng](#-truy-cập-ứng-dụng)
- [Chi phí ước tính](#-chi-phí-ước-tính)
- [Bảo mật](#-bảo-mật)

---

## 🎯 Tổng quan

Dự án triển khai một hệ thống hạ tầng **AWS 3-tier** hoàn chỉnh sử dụng **Infrastructure as Code (IaC)** với Terraform và Ansible, bao gồm:

1. **Web Tier (Public) — Layer 1:** H&M Clothing Store (React + Node.js), truy cập public thông qua Application Load Balancer (ALB).
2. **App Tier (Private) — Layer 2:** AI Agent RCA (LangGraph + AWS Bedrock + FastAPI), nhận các cảnh báo (alarms) thời gian thực từ CloudWatch qua SNS webhook, truy cập nội bộ (private) thông qua cơ chế AWS SSM Port Forwarding.
3. **Database Tier (Private & Isolated) — Layer 3:** Hệ thống cơ sở dữ liệu RDS MySQL 8.0, được cấu hình cô lập hoàn toàn (Private Subnets, không có route ra Internet hay NAT Gateway), chỉ chấp nhận các kết nối Inbound MySQL từ Layer 1 Web App và chặn hoàn toàn mọi traffic Outbound (Egress).

Hệ thống tích hợp **AI-powered Root Cause Analysis Agent** — một agent tự chủ sử dụng LangGraph với investigation loop theo phương pháp khoa học, tự động nhận CloudWatch Alarms, truy vấn log, đặt giả thuyết, kiểm chứng, và tạo báo cáo RCA toàn diện kèm remediation actions.

---

## 🏗️ Kiến trúc hệ thống

```
                          Internet Users
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Internet Gateway  │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │         ALB         │
                    │   (Internet-facing) │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │   AZ: ap-southeast-1a│   AZ: ap-southeast-1b│
        │                      │                       │
   ┌────┴─────────────────┐  ┌─┴───────────────────┐  │
   │  WEB TIER (Public)   │  │  WEB TIER (Public)  │  │
   │  H&M Store           │  │  H&M Store          │  │
   │  React + Node.js     │  │  React + Node.js    │  │
   └──────────────────────┘  └─────────────────────┘  │
                                                       │
   ┌──────────────────────┐  ┌─────────────────────┐  │
   │  APP TIER (Private)  │  │  APP TIER (Private) │  │
   │  AI Agent RCA        │  │  AI Agent RCA       │  │
   │  LangGraph + FastAPI │  │  LangGraph + FastAPI│  │
   └──────────────────────┘  └─────────────────────┘  │
                                                       │
   ┌──────────────────────┐  ┌─────────────────────┐  │
   │  DB TIER (Private)   │  │  DB TIER (Standby)  │  │
   │  RDS MySQL Primary   │◄─┤  RDS MySQL          │  │
   └──────────────────────┘  └─────────────────────┘  │
        └──────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────┐
   │           EVENT-DRIVEN AI INVESTIGATION             │
   │                                                      │
   │  CloudWatch Alarms ──► SNS ──► Webhook (FastAPI)    │
   │                                      │               │
   │                               LangGraph Agent        │
   │                          (Hypothesis → Tool → RCA)   │
   │                                      │               │
   │                                      ▼               │
   │                            Telegram Alerts           │
   │                          + Incident Reports          │
   └─────────────────────────────────────────────────────┘
```

### Đặc điểm kiến trúc

| Tiêu chí | Chi tiết |
|-----------|----------|
| **High Availability** | Deploy trên 2 Availability Zones, Auto Scaling Groups |
| **Security** | Private subnets cho App & DB, không public IP, IAM roles, Security Groups |
| **Access** | Web tier qua ALB, AI Agent qua SSM Port Forwarding (không public exposure) |
| **Observability** | 9 CloudWatch Log Groups, VPC Flow Logs, CloudTrail |
| **AI Architecture** | LangGraph ReAct agent với context engineering, YAML-based prompt management |

---

## 🛠️ Công nghệ sử dụng

| Layer | Công nghệ |
|-------|-----------|
| **Infrastructure as Code** | Terraform v1.0+ |
| **Configuration Management** | Ansible v2.9+ |
| **Cloud Provider** | AWS (ap-southeast-1) |
| **Compute** | EC2 (t3.micro), Auto Scaling Groups |
| **Database** | RDS MySQL 8.0 |
| **Load Balancing** | Application Load Balancer |
| **Web Application** | React 18 + Node.js Express (Docker) |
| **AI Agent Framework** | LangGraph (StateGraph ReAct loop) |
| **AI/ML** | AWS Bedrock (Claude 3 Haiku / Sonnet) |
| **AI API** | FastAPI (webhook receiver) |
| **Context Engineering** | YAML-based composable prompt system |
| **Monitoring** | CloudWatch Logs + Alarms, VPC Flow Logs, CloudTrail |
| **Alerting** | Telegram Bot API (via SNS → webhook chain) |
| **Container** | Docker (multi-stage builds) |
| **Access Management** | AWS SSM Session Manager |

---

## 📁 Cấu trúc project

```
terraform-for-project1/
│
├── 📂 environments/
│   └── dev/                      # Terraform cho môi trường dev
│       ├── main.tf               # VPC, Subnets, Gateways
│       ├── compute.tf            # EC2, Auto Scaling Groups
│       ├── database.tf           # RDS MySQL
│       ├── alb.tf                # Application Load Balancer
│       ├── security_groups.tf    # Security Groups
│       ├── iam.tf                # IAM Roles & Policies
│       ├── cloudwatch.tf         # CloudWatch Log Groups & Alarms
│       ├── cloudtrail.tf         # CloudTrail
│       ├── variables.tf          # Input variables
│       ├── outputs.tf            # Output values
│       └── backend.tf            # S3 remote state
│
├── 📂 bootstrap/
│   └── main.tf                   # S3 bucket & DynamoDB for Terraform state
│
├── 📂 ansible/
│   ├── ansible.cfg               # Ansible configuration
│   ├── inventory/                # Dynamic inventory (aws_ec2)
│   ├── playbooks/                # Deployment playbooks
│   │   ├── site.yml              # Master playbook
│   │   ├── install_docker.yml
│   │   ├── install_cloudwatch_agent.yml
│   │   ├── deploy_web_app.yml
│   │   └── deploy_log_analyzer.yml
│   ├── roles/                    # Ansible roles
│   └── templates/                # Jinja2 templates
│
├── 📂 hm-store/                  # H&M Clothing Store (Web Tier)
│   ├── backend/
│   │   └── src/
│   │       ├── index.js          # Express API + HTTP access logger
│   │       └── db.js             # MySQL connection pool
│   ├── frontend/
│   │   └── src/
│   │       ├── App.jsx           # React E-commerce UI
│   │       ├── index.css         # Tailwind + custom styling
│   │       └── main.jsx          # React entrypoint
│   ├── database/
│   │   └── complete_setup.sql    # Full schema + seed data
│   └── Dockerfile                # Multi-stage Docker build
│
├── 📂 AI-Agent-RCA/              # AI Root Cause Analysis Agent
│   ├── main.py                   # CLI test runner
│   ├── api.py                    # FastAPI webhook (SNS/CloudWatch)
│   ├── tools.py                  # LangChain tools (CloudWatch, correlator)
│   ├── agent_models.py           # LLM model selector by phase
│   ├── cloudwatch_client.py      # CloudWatch Logs API client
│   ├── incident_store.py         # JSON-based incident persistence
│   ├── correlation_rules.json    # Cross-source correlation rules
│   ├── graph/                    # LangGraph state machine
│   │   ├── builder.py            # Graph assembly & compilation
│   │   ├── nodes.py              # Node logic (think, tool, findings, etc.)
│   │   └── conditions.py         # Conditional edges
│   ├── schemas/                  # Pydantic state & data models
│   ├── contexts/                 # Context engineering (prompt composition)
│   │   ├── composer.py           # Multi-layer prompt composer
│   │   ├── registry.py           # Context block registry
│   │   ├── system/               # System-level prompts (YAML)
│   │   ├── domain/               # Domain knowledge prompts
│   │   ├── task/                  # Task-specific prompts
│   │   ├── interaction/          # Feedback loop prompts
│   │   └── response/             # Output format prompts
│   ├── cmdb/                     # Infrastructure topology (CMDB)
│   └── src/                      # Processing modules
│       ├── log_parser.py         # Multi-format log parser
│       ├── pattern_analyzer.py   # Error pattern clustering
│       ├── advanced_correlator.py # Cross-source event correlation
│       └── telegram_notifier.py  # Telegram alert sender
│
├── 📂 scripts/
│   ├── deploy_all.sh             # Full deployment script
│   ├── check_logs.sh             # Verify CloudWatch log groups
│   ├── fix_log_groups.sh         # Fix log group issues
│   ├── access_app.sh             # Access applications
│   └── database/
│       └── deploy_db.sh          # Database deployment
│
├── DEPLOYMENT_COMPLETE_GUIDE.md  # Complete deployment instructions
├── PROJECT_SUMMARY.md            # Project summary & status
└── README.md                     # ← Bạn đang đây
```

---

## 📦 Ứng dụng

### 1. 🛍️ H&M Clothing Store (Web Tier)

Ứng dụng e-commerce thời trang H&M full-stack.

| Feature | Mô tả |
|---------|--------|
| Duyệt sản phẩm | Hiển thị sản phẩm theo danh mục (Men, Women, Kids, etc.) |
| Giỏ hàng | Thêm/xóa sản phẩm, cập nhật số lượng |
| Đặt hàng | Checkout flow hoàn chỉnh |
| Quản lý Admin | Dashboard quản lý sản phẩm, đơn hàng |
| Phân quyền | 2 roles: Admin, Customer |
| Security Logging | HTTP access logs (Apache format) + application event logs (JSON) |

**Công nghệ:** React 18 + Tailwind CSS + Node.js Express + MySQL (Docker)
**Database:** 6 tables — roles, users, categories, products, orders, order_items
**Tài khoản mặc định:** `admin` / `123@`, `customer01-03` / `123@`

> 📖 Xem chi tiết tại [hm-store/README.md](hm-store/README.md)

---

### 2. 🤖 AI Agent RCA (App Tier)

Agent AI tự chủ thực hiện Root Cause Analysis sử dụng **LangGraph** (ReAct loop) với **AWS Bedrock** (Claude AI).

| Feature | Mô tả |
|---------|--------|
| Event-driven | Nhận CloudWatch Alarms qua SNS → FastAPI webhook |
| LangGraph Agent | Investigation loop: Hypothesis → Tool → Findings → Validate |
| Context Engineering | YAML-based composable prompt system (5 layers) |
| Tool-use | 3 tools: `query_cloudwatch_logs`, `analyze_log_patterns`, `check_cross_correlation` |
| Structured Output | Pydantic-enforced JSON responses cho mọi node |
| CMDB Integration | System topology awareness cho accurate RCA |
| Telegram Alerts | Real-time notifications khi phát hiện incident |
| Incident Store | JSON-based persistence cho investigation history |

#### LangGraph Investigation Flow

```
START → Context Enrichment → Think (Hypothesis)
                                ↓
                            Tool Node ──── (no tool) ───→ Validate
                                ↓
                          Findings Node
                                ↓
                          Validate Node
                           ↙         ↘
                    (continue)      (final)
                        ↓              ↓
                      Think        Conclusion → END
```

**Công nghệ:** Python + LangGraph + LangChain + FastAPI + AWS Bedrock + Docker

---

## 📊 Log Collection & Observability

Hệ thống thu thập logs từ **9 CloudWatch Log Groups**:

| # | Log Group | Nguồn | Loại dữ liệu |
|---|-----------|-------|---------------|
| 1 | `/aws/vpc/flowlogs` | VPC | Network traffic (ACCEPT/REJECT) |
| 2 | `/aws/cloudtrail/logs` | CloudTrail | API activity |
| 3 | `/aws/ec2/web-tier/system` | Web EC2 | System logs (messages, secure) |
| 4 | `/aws/ec2/web-tier/httpd` | Web EC2 | Apache-format access logs (từ Node.js stdout) |
| 5 | `/aws/ec2/web-tier/application` | Web EC2 | Express application logs (JSON) |
| 6 | `/aws/ec2/app-tier/system` | App EC2 | System logs |
| 7 | `/aws/ec2/app-tier/streamlit` | App EC2 | AI Agent application logs |
| 8 | `/aws/rds/mysql/error` | RDS | MySQL error logs |
| 9 | `/aws/rds/mysql/slowquery` | RDS | Slow query logs |

---

## 🚀 Hướng dẫn Deploy

### Yêu cầu

- AWS CLI v2.0+ (configured)
- Terraform v1.0+
- Ansible v2.9+
- Python 3.8+
- Session Manager Plugin (cho SSM)

### Quy trình deploy (~30-40 phút)

#### Bước 1: Bootstrap S3 Backend (~1 phút)
```bash
cd bootstrap/
terraform init
terraform apply -auto-approve
```

#### Bước 2: Deploy Infrastructure (~10-15 phút)
```bash
cd ../environments/dev/
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

#### Bước 3: Deploy Database (~2-3 phút)
```bash
cd ../../scripts/database/
chmod +x deploy_db.sh
./deploy_db.sh
```

#### Bước 4: Deploy Applications (~10-15 phút)
```bash
cd ../../ansible/
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

#### Bước 5: Verify (~2-3 phút)
```bash
cd ../scripts/
./check_logs.sh
./access_app.sh
```

> 📖 Hướng dẫn chi tiết: [DEPLOYMENT_COMPLETE_GUIDE.md](DEPLOYMENT_COMPLETE_GUIDE.md)

---

## 🌐 Truy cập ứng dụng

### H&M Store (Public)

```bash
# Lấy ALB DNS
cd environments/dev/
terraform output alb_dns_name

# Truy cập
http://<ALB-DNS>/
```

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `123@` |
| Customer | `customer01`, `customer02`, `customer03` | `123@` |

### AI Agent RCA (Private — SSM Port Forwarding)

```bash
# Port forwarding qua SSM
aws ssm start-session \
    --target <instance-id> \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["8000"],"localPortNumber":["8000"]}'

# Test API
curl http://localhost:8000/api/status

# Trigger test alert
curl -X POST http://localhost:8000/api/test-alert
```

---

## 💰 Chi phí ước tính (Monthly)

| Dịch vụ | Chi phí |
|---------|---------|
| EC2 (4 × t3.micro) | ~$30 |
| ALB | ~$20 |
| RDS (db.t3.micro) | ~$15 |
| EBS Storage (80GB) | ~$8 |
| NAT Gateway (optional) | ~$32 |
| CloudWatch Logs | ~$5 |
| VPC Flow Logs | ~$3 |
| Bedrock (Claude Haiku) | ~$5-10 |
| **Tổng (có NAT)** | **~$125/tháng** |
| **Tổng (không NAT)** | **~$93/tháng** |

---

## 🔐 Bảo mật

### Network Security
- ✅ Private subnets cho App & Database tier
- ✅ Security Groups với least privilege
- ✅ Không public IP trên app/db instances
- ✅ VPC Endpoints cho SSM, S3 (private access)

### Access Control
- ✅ IAM Roles cho EC2 (không access keys)
- ✅ SSM Session Manager (không SSH keys)
- ✅ RDS trong private subnet
- ✅ Secrets qua SSM Parameter Store

### Application Security
- ✅ Password hashing (SHA256 + salt)
- ✅ Prepared statements (chống SQL Injection)
- ✅ Session security
- ✅ Input validation

### Monitoring & Detection
- ✅ 9 CloudWatch Log Groups
- ✅ VPC Flow Logs
- ✅ CloudTrail (API audit)
- ✅ AI Agent tự động investigate khi alarm trigger
- ✅ Telegram alerts real-time

---

## 🏆 Highlights

| Metric | Value |
|--------|-------|
| **Setup Time** | ~30-40 phút |
| **AWS Resources** | 50+ resources |
| **AI Architecture** | LangGraph ReAct Agent |
| **Log Sources** | 9 CloudWatch Log Groups |
| **Agent Tools** | 3 (query, analyze, correlate) |
| **Context Layers** | 5 (system, domain, task, interaction, response) |
| **Availability** | 99.9% (Multi-AZ) |

---

<p align="center">
  <b>Made with ❤️ using Terraform + Ansible + LangGraph + AWS Bedrock</b>
</p>
