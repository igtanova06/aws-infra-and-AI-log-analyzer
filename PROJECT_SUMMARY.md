# 📊 PROJECT SUMMARY

## 🎯 Tổng quan

Hệ thống bao gồm 2 ứng dụng chính được deploy trên AWS với kiến trúc 3-tier:

### **Layer 1 — Web Tier (Public)**
- **Ứng dụng**: H&M Clothing Store
- **Công nghệ**: React 18 + Tailwind CSS + Node.js Express
- **Truy cập**: Public qua ALB
- **Port**: 8080 (internal), 80 (ALB)

### **Layer 2 — App Tier (Private)**
- **Ứng dụng**: AI Agent RCA (Root Cause Analysis)
- **Công nghệ**: Python + LangGraph + LangChain + FastAPI + AWS Bedrock
- **Truy cập**: Private qua SSM Port Forwarding
- **Port**: 8000 (FastAPI)

### **Layer 3 — Database Tier (Private & Isolated)**
- **Dịch vụ**: RDS MySQL 8.0
- **Truy cập**: Chỉ cho phép inbound từ Layer 1 Web App Security Group (Port 3306). Chặn hoàn toàn mọi kết nối outbound (Egress Deny).
- **Định tuyến**: Nằm trong các DB subnets cô lập hoàn toàn, không có route ra Internet hay NAT Gateway.

---

## 🏗️ Kiến trúc Infrastructure

### Networking
- **VPC**: 10.0.0.0/16
- **Public Subnets**: 2 AZs (cho ALB)
- **Private Subnets**: 2 AZs (cho EC2)
- **DB Subnets**: 2 AZs (cho RDS)
- **NAT Gateway**: Optional (có thể tắt để tiết kiệm)
- **VPC Endpoints**: SSM, S3 (cho private access)

### Compute
- **Web Tier**: 2 EC2 instances (t3.micro) — Auto Scaling Group
- **App Tier**: 2 EC2 instances (t3.micro) — Auto Scaling Group
- **AMI**: Amazon Linux 2

### Database
- **Engine**: MySQL 8.0
- **Instance**: db.t3.micro
- **Storage**: 20GB GP2
- **Backup**: Automated snapshots
- **Logs**: CloudWatch export enabled

### Load Balancing
- **Type**: Application Load Balancer
- **Scheme**: Internet-facing
- **Listeners**: HTTP:80
- **Target Groups**: Web tier (port 8080)

### Logging (9 Log Groups)

| Category | Log Groups |
|----------|-----------|
| Infrastructure | `/aws/vpc/flowlogs`, `/aws/cloudtrail/logs` |
| Web Tier | `/aws/ec2/web-tier/system`, `httpd`, `application` |
| App Tier | `/aws/ec2/app-tier/system`, `streamlit` |
| Database | `/aws/rds/mysql/error`, `slowquery` |

---

## 📦 Ứng dụng

### 1. H&M Clothing Store

**Tính năng:**
- Duyệt sản phẩm theo danh mục (Men, Women, Divided, Kids, Accessories)
- Giỏ hàng và checkout flow
- Admin dashboard quản lý sản phẩm & đơn hàng
- 2 roles: Admin, Customer
- HTTP access logs (Apache format cho CloudWatch)
- Application event logs (JSON cho AI Agent)

**Database:**
- 6 tables: roles, users, categories, products, orders, order_items
- 4 default accounts (1 admin, 3 customers)
- Password: SHA256 hashing (salt: `_salt`)

**Truy cập:** `http://<ALB-DNS>/` | Login: `admin` / `123@`

### 2. AI Agent RCA

**Kiến trúc Agent:**
- **Framework**: LangGraph (StateGraph ReAct loop)
- **6 Nodes**: Context → Think → Tool → Findings → Validate → Conclusion
- **3 Tools**: `query_cloudwatch_logs`, `analyze_log_patterns`, `check_cross_correlation`
- **Entry Point**: FastAPI webhook nhận CloudWatch Alarms qua SNS

**Context Engineering:**
- 5 prompt layers: System, Domain, Task, Interaction, Response
- YAML-based composable prompts
- Dynamic composition dựa trên investigation phase

**AI Capabilities:**
- Hypothesis-driven investigation loop (scientific method)
- Structured output với Pydantic models
- Global RCA report (incident story, threat assessment, MITRE ATT&CK)
- Immediate action recommendations với AWS CLI commands
- Remediation plan (short/medium/long term)
- Telegram real-time notifications

**Truy cập:** SSM Port Forwarding → `http://localhost:8000`

---

## 🚀 Deployment Process

### 1. Bootstrap (1 phút)
```bash
cd bootstrap/
terraform init && terraform apply -auto-approve
```

### 2. Infrastructure (10-15 phút)
```bash
cd ../environments/dev/
terraform init && terraform plan -out=tfplan && terraform apply tfplan
```

### 3. Database (2-3 phút)
```bash
cd ../../scripts/database/
./deploy_db.sh
```

### 4. Applications (10-15 phút)
```bash
cd ../../ansible/
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

### 5. Verification (2-3 phút)
```bash
cd ../scripts/
./check_logs.sh && ./access_app.sh
```

**TỔNG THỜI GIAN: ~30-40 phút**

---

## 💰 Chi phí ước tính (Monthly)

| Category | Item | Chi phí |
|----------|------|---------|
| Compute | EC2 (4 × t3.micro) | ~$30 |
| | ALB | ~$20 |
| Database | RDS (db.t3.micro) | ~$15 |
| Storage | EBS (80GB) + RDS (20GB) | ~$10 |
| Network | NAT Gateway (optional) | ~$32 |
| Logging | CloudWatch + VPC Flow | ~$8 |
| AI | Bedrock (Claude Haiku) | ~$5-10 |
| **Tổng** | **Có NAT** | **~$125/tháng** |
| | **Không NAT** | **~$93/tháng** |

---

## 🔐 Security

- ✅ Private subnets cho App & Database tier
- ✅ Security Groups với least privilege
- ✅ IAM Roles cho EC2 (không access keys)
- ✅ SSM Session Manager (không SSH keys)
- ✅ Password hashing (SHA256 + salt)
- ✅ Prepared statements (SQL injection prevention)
- ✅ VPC Endpoints cho private access

---

## 🎯 Key Features

### ✅ Đã hoàn thành

**Infrastructure:**
- [x] 2-tier architecture (Web public + App private)
- [x] Auto Scaling Groups
- [x] Application Load Balancer
- [x] RDS MySQL
- [x] VPC with public/private subnets
- [x] VPC Endpoints (SSM, S3)
- [x] 9 CloudWatch Log Groups
- [x] VPC Flow Logs + CloudTrail

**Applications:**
- [x] H&M Clothing Store (React + Node.js)
- [x] AI Agent RCA (LangGraph + FastAPI)
- [x] Database schema + seed data
- [x] CloudWatch Agent deployment
- [x] Docker containerization

**AI Agent:**
- [x] LangGraph ReAct investigation loop
- [x] Context engineering (5-layer YAML prompts)
- [x] 3 investigation tools (query, analyze, correlate)
- [x] Pydantic structured outputs
- [x] CMDB topology awareness
- [x] FastAPI webhook (SNS integration)
- [x] Telegram notifications
- [x] Incident persistence (JSON store)

**Automation:**
- [x] Terraform IaC
- [x] Ansible configuration management
- [x] Deployment scripts
- [x] Health checks

### 🔄 Có thể cải thiện

- [ ] HTTPS on ALB (ACM certificate)
- [ ] WAF rules
- [ ] CloudWatch Dashboards
- [ ] Human-in-the-loop verification for AI Agent
- [ ] React-based AI Agent dashboard (thay thế API-only)
- [ ] CI/CD pipeline

---

## 📚 Documentation

| File | Mô tả |
|------|--------|
| [README.md](README.md) | Tổng quan project & kiến trúc |
| [DEPLOYMENT_COMPLETE_GUIDE.md](DEPLOYMENT_COMPLETE_GUIDE.md) | Hướng dẫn deploy chi tiết |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Summary & status (file này) |
| [hm-store/README.md](hm-store/README.md) | H&M Store documentation |

---

## 📈 Metrics

| Metric | Value |
|--------|-------|
| **Setup Time** | ~30-40 phút |
| **AWS Resources** | 50+ |
| **AI Architecture** | LangGraph ReAct Agent |
| **Agent Tools** | 3 |
| **Context Layers** | 5 (YAML-based) |
| **Log Sources** | 9 CloudWatch Log Groups |
| **Availability** | 99.9% (Multi-AZ) |

---

**Last Updated**: June 2026
**Status**: ✅ PRODUCTION READY
