# 🚀 HƯỚNG DẪN DEPLOY HOÀN CHỈNH

## 📋 MỤC LỤC
1. [Tổng quan kiến trúc](#tổng-quan-kiến-trúc)
2. [Chuẩn bị môi trường](#chuẩn-bị-môi-trường)
3. [Deploy Infrastructure (Terraform)](#deploy-infrastructure-terraform)
4. [Deploy Database](#deploy-database)
5. [Deploy Applications (Ansible)](#deploy-applications-ansible)
6. [Kiểm tra Log Groups](#kiểm-tra-log-groups)
7. [Truy cập ứng dụng](#truy-cập-ứng-dụng)
8. [Troubleshooting](#troubleshooting)

---

## 🏗️ TỔNG QUAN KIẾN TRÚC

### **Layer 1 — Web Tier (Public Access via ALB)**
- **Ứng dụng**: H&M Clothing Store (React + Node.js)
- **Truy cập**: `http://<ALB-DNS-NAME>/`
- **Port**: 8080 (internal), 80 (ALB)
- **Log Groups**:
  - `/aws/ec2/web-tier/system` — System logs (messages, secure)
  - `/aws/ec2/web-tier/httpd` — Apache-format access logs (Node container stdout)
  - `/aws/ec2/web-tier/application` — Express application logs (JSON)

### **Layer 2 — App Tier (Private — SSM Access Only)**
- **Ứng dụng**: AI Agent RCA (LangGraph + FastAPI)
- **Truy cập**: SSM Port Forwarding → `http://localhost:8000`
- **Port**: 8000 (FastAPI)
- **Webhook**: `POST /webhook/cloudwatch` — nhận CloudWatch Alarms qua SNS
- **Log Groups**:
  - `/aws/ec2/app-tier/system` — System logs
  - `/aws/ec2/app-tier/streamlit` — AI Agent application logs

### **Infrastructure Logs**
- `/aws/vpc/flowlogs` — VPC Flow Logs
- `/aws/cloudtrail/logs` — CloudTrail API logs

### **Database Logs**
- `/aws/rds/mysql/error` — MySQL error logs
- `/aws/rds/mysql/slowquery` — Slow query logs

**TỔNG CỘNG: 9 LOG GROUPS**

---

## 🔧 CHUẨN BỊ MÔI TRƯỜNG

### 1. Cài đặt công cụ
```bash
# Terraform
terraform --version  # >= 1.0

# Ansible
ansible --version    # >= 2.9

# AWS CLI
aws --version        # >= 2.0

# Python (cho Ansible)
python3 --version    # >= 3.8
```

### 2. Cấu hình AWS Credentials
```bash
aws configure --profile default
aws sts get-caller-identity --profile default
```

### 3. Cấu hình Telegram Bot (cho AI Alerts)
```bash
# Tạo bot mới với @BotFather trên Telegram
# Lấy BOT_TOKEN và CHAT_ID

# Lưu vào file .env trong AI-Agent-RCA/
cd AI-Agent-RCA/
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_ALERTS_ENABLED=true
EOF
```

---

## 🏗️ DEPLOY INFRASTRUCTURE (TERRAFORM)

### Bước 1: Bootstrap S3 Backend
```bash
cd bootstrap/
terraform init
terraform plan
terraform apply -auto-approve
```

### Bước 2: Deploy Dev Environment
```bash
cd ../environments/dev/
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Bước 3: Lưu outputs quan trọng
```bash
terraform output alb_dns_name
terraform output db_endpoint
terraform output -raw db_password
terraform output -json > terraform_outputs.json
```

**⏱️ Thời gian**: ~10-15 phút

---

## 💾 DEPLOY DATABASE

### Bước 1: Chạy deployment script
```bash
cd ../../scripts/database/
chmod +x deploy_db.sh
./deploy_db.sh
```

Script sẽ tự động:
- Lấy DB credentials từ Terraform outputs
- Test kết nối database
- Import schema (`hm-store/database/complete_setup.sql`)
- Hiển thị summary (Users, Categories, Products, Orders)

### Tài khoản mặc định
- **Admin**: `admin` / `123@`
- **Customers**: `customer01`, `customer02`, `customer03` / `123@`

**⏱️ Thời gian**: ~2-3 phút

---

## 🚀 DEPLOY APPLICATIONS (ANSIBLE)

### Bước 1: Test Ansible Inventory
```bash
cd ../../ansible/
ansible-inventory -i inventory/aws_ec2.yml --list
ansible all -i inventory/aws_ec2.yml -m ping
```

### Bước 2: Deploy toàn bộ
```bash
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

### Hoặc deploy từng phần
```bash
# CloudWatch Agent
ansible-playbook -i inventory/aws_ec2.yml playbooks/install_cloudwatch_agent.yml

# Docker
ansible-playbook -i inventory/aws_ec2.yml playbooks/install_docker.yml

# Web App (H&M Store)
ansible-playbook -i inventory/aws_ec2.yml playbooks/deploy_web_app.yml

# AI Agent RCA
ansible-playbook -i inventory/aws_ec2.yml playbooks/deploy_log_analyzer.yml
```

**⏱️ Thời gian**: ~10-15 phút

---

## 📊 KIỂM TRA LOG GROUPS

```bash
cd ../scripts/
chmod +x check_logs.sh
./check_logs.sh
```

Script kiểm tra trạng thái 9 log groups:

| Category | Log Groups |
|----------|-----------|
| 🏗️ Infrastructure | `/aws/vpc/flowlogs`, `/aws/cloudtrail/logs` |
| 🌐 Web Tier | `/aws/ec2/web-tier/system`, `httpd`, `application` |
| 🤖 App Tier | `/aws/ec2/app-tier/system`, `streamlit` |
| 💾 Database | `/aws/rds/mysql/error`, `slowquery` |

---

## 🌐 TRUY CẬP ỨNG DỤNG

### Layer 1 — H&M Store (Public)
```bash
ALB_DNS=$(cd environments/dev && terraform output -raw alb_dns_name)
echo "🌐 H&M Store: http://$ALB_DNS/"
curl -I http://$ALB_DNS/
```

**Truy cập**: Mở browser → `http://<ALB-DNS>/`

### Layer 2 — AI Agent RCA (Private — SSM)
```bash
APP_INSTANCE=$(aws ec2 describe-instances \
    --filters "Name=tag:Role,Values=app" "Name=instance-state-name,Values=running" \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

# Port forwarding
aws ssm start-session \
    --target $APP_INSTANCE \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["8000"],"localPortNumber":["8000"]}'
```

**API Endpoints**:
- `GET /api/status` — Health check
- `POST /api/test-alert` — Trigger test investigation
- `POST /webhook/cloudwatch` — Nhận CloudWatch Alarms (từ SNS)

---

## 🔧 TROUBLESHOOTING

### 1. Terraform Errors
```bash
# S3 bucket already exists
cd bootstrap/
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate*
terraform init && terraform apply

# Resource already exists
terraform import aws_vpc.main <vpc-id>
```

### 2. Ansible Connection Issues
```bash
# Kiểm tra SSM agent
aws ssm describe-instance-information

# Restart SSM agent
aws ssm send-command \
    --instance-ids <instance-id> \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["sudo systemctl restart amazon-ssm-agent"]'
```

### 3. Database Connection Issues
```bash
# Kiểm tra từ EC2
aws ssm start-session --target <web-instance-id>
mysql -h <db-endpoint> -u admin -p
```

### 4. CloudWatch Logs Not Appearing
```bash
# Trên EC2 instance
sudo systemctl status amazon-cloudwatch-agent
sudo tail -f /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

---

## 📝 CHECKLIST DEPLOY

### Pre-deployment
- [ ] AWS credentials configured
- [ ] Terraform installed (>= 1.0)
- [ ] Ansible installed (>= 2.9)
- [ ] Telegram bot created (optional)

### Infrastructure
- [ ] Bootstrap S3 backend
- [ ] Deploy Terraform (VPC, EC2, RDS, ALB)
- [ ] Verify outputs (ALB DNS, DB endpoint)

### Database
- [ ] Deploy schema via `deploy_db.sh`
- [ ] Verify tables created (6 tables)

### Applications
- [ ] Deploy CloudWatch Agent
- [ ] Deploy Docker
- [ ] Deploy H&M Store (Web Tier)
- [ ] Deploy AI Agent RCA (App Tier)

### Verification
- [ ] H&M Store accessible via ALB
- [ ] AI Agent accessible via SSM
- [ ] All 9 log groups receiving logs
- [ ] Telegram alerts working (test via `/api/test-alert`)

---

**Happy Deploying! 🚀**
