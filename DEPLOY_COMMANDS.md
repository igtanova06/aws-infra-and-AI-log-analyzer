# ⚡ Deploy Commands - Quick Reference

Copy-paste commands để deploy nhanh.

---

## 🚀 Option 1: Full Automated Deploy (WSL2)

```bash
# 1. Cài WSL2 (nếu chưa có)
wsl --install
# Restart máy

# 2. Trong WSL2 Ubuntu, clone repo
cd ~
git clone <your-repo-url>
cd terraform-for-project1

# 3. Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip ansible awscli

# 4. Configure AWS
aws configure

# 5. Run deployment script
chmod +x deploy_phase1.sh
./deploy_phase1.sh
```

**Done!** Script sẽ tự động deploy tất cả.

---

## 🔧 Option 2: Manual Deploy (Step by Step)

### Prerequisites

```powershell
# Check tools
terraform version
aws --version
python --version

# Configure AWS
aws configure
aws sts get-caller-identity
```

### Step 1: Bootstrap

```powershell
cd bootstrap
terraform init
terraform apply -auto-approve
cd ..
```

### Step 2: Infrastructure

```powershell
cd environments/dev
terraform init
terraform plan
terraform apply
# Nhập 'yes'

# Save ALB DNS
$ALB_DNS = terraform output -raw alb_dns_name
echo $ALB_DNS

cd ../..
```

### Step 3: Ansible (WSL2)

```bash
# Trong WSL2
cd /mnt/d/terraform-for-project1/ansible

# Install collections
ansible-galaxy collection install -r requirements.yml

# Set env vars
export AWS_REGION=ap-southeast-1
export ENV_NAME=dev

# Test connection
ansible-inventory -i inventory/aws_ec2.yml --list
ansible role_app -i inventory/aws_ec2.yml -m ping

# Deploy
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

### Step 4: Test

```bash
cd ../AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui

# Generate test logs
python3 generate_vpc_flow_logs.py
python3 generate_cloudtrail_logs.py

# Open browser
echo "Open: http://$ALB_DNS"
```

---

## 🧪 Verification Commands

### Check EC2 Instances

```powershell
aws ec2 describe-instances `
  --filters "Name=tag:Project,Values=p1" "Name=instance-state-name,Values=running" `
  --query "Reservations[].Instances[].[Tags[?Key=='Name'].Value|[0],State.Name,InstanceId]" `
  --output table
```

### Check ALB Health

```powershell
aws elbv2 describe-target-groups --region ap-southeast-1
aws elbv2 describe-target-health --target-group-arn <arn>
```

### Check CloudWatch Logs

```powershell
aws logs describe-log-groups --region ap-southeast-1 | findstr "vpc\|cloudtrail\|applogs"
aws logs tail /aws/vpc/flowlogs --follow --region ap-southeast-1
```

### Check Alarms

```powershell
aws cloudwatch describe-alarms --alarm-name-prefix p1-dev-apse1 --region ap-southeast-1
```

---

## 🔄 Update/Redeploy Commands

### Update Infrastructure

```powershell
cd environments/dev
terraform plan
terraform apply
```

### Redeploy Application

```bash
# WSL2
cd /mnt/d/terraform-for-project1/ansible
ansible-playbook -i inventory/aws_ec2.yml playbooks/deploy_log_analyzer.yml
```

### Update Single EC2

```bash
# Deploy to specific instance
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml --limit p1-dev-apse1-l2-node-1
```

---

## 🗑️ Cleanup Commands

### Destroy Everything

```powershell
# Destroy infrastructure
cd environments/dev
terraform destroy -auto-approve

# Destroy bootstrap
cd ../../bootstrap
terraform destroy -auto-approve
```

### Destroy Specific Resources

```powershell
# Destroy only EC2
terraform destroy -target=aws_autoscaling_group.app

# Destroy only CloudWatch Alarms
terraform destroy -target=aws_cloudwatch_metric_alarm.high_vpc_rejects
```

---

## 🐛 Debug Commands

### SSH into EC2

```powershell
# Get instance ID
aws ec2 describe-instances `
  --filters "Name=tag:Role,Values=app" "Name=instance-state-name,Values=running" `
  --query "Reservations[0].Instances[0].InstanceId" `
  --output text

# Start SSM session
aws ssm start-session --target <instance-id> --region ap-southeast-1
```

### Check Docker Containers

```bash
# Trong EC2
sudo docker ps
sudo docker logs log-analyzer-ui
sudo docker logs -f log-analyzer-ui  # Follow logs
```

### Check CloudWatch Agent

```bash
# Trong EC2
sudo systemctl status amazon-cloudwatch-agent
sudo tail -f /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

### Check Ansible Logs

```bash
# Verbose mode
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml -vvv
```

---

## 📊 Monitoring Commands

### CloudWatch Logs Insights

```powershell
# Query VPC Flow Logs
aws logs start-query `
  --log-group-name /aws/vpc/flowlogs `
  --start-time (Get-Date).AddHours(-1).ToUniversalTime().ToString("o") `
  --end-time (Get-Date).ToUniversalTime().ToString("o") `
  --query-string "fields @timestamp, srcaddr, dstaddr, action | filter action = 'REJECT' | stats count() by srcaddr | sort count desc"
```

### Get Alarm History

```powershell
aws cloudwatch describe-alarm-history `
  --alarm-name p1-dev-apse1-high-vpc-rejects `
  --region ap-southeast-1 `
  --max-records 10
```

---

## 🔐 Security Commands

### Check IAM Permissions

```powershell
# Check EC2 role
aws iam get-role --role-name p1-dev-apse1-ec2-role

# Check attached policies
aws iam list-attached-role-policies --role-name p1-dev-apse1-ec2-role

# Check inline policies
aws iam list-role-policies --role-name p1-dev-apse1-ec2-role
```

### Check Security Groups

```powershell
aws ec2 describe-security-groups `
  --filters "Name=tag:Project,Values=p1" `
  --query "SecurityGroups[].[GroupName,GroupId]" `
  --output table
```

---

## 💰 Cost Commands

### Get Current Month Cost

```powershell
aws ce get-cost-and-usage `
  --time-period Start=(Get-Date -Day 1 -Format yyyy-MM-dd),End=(Get-Date -Format yyyy-MM-dd) `
  --granularity MONTHLY `
  --metrics BlendedCost `
  --group-by Type=TAG,Key=Project
```

---

## 🎯 Quick Fixes

### Restart Application

```bash
# SSH vào EC2
aws ssm start-session --target <instance-id>

# Restart container
sudo docker restart log-analyzer-ui
```

### Force Ansible Reconnect

```bash
# Clear Ansible cache
rm -rf ~/.ansible/tmp/*

# Retry connection
ansible role_app -i inventory/aws_ec2.yml -m ping
```

### Unlock Terraform State

```powershell
# Get lock ID from error message
terraform force-unlock <lock-id>
```

---

## 📋 Useful Aliases (WSL2)

Add to `~/.bashrc`:

```bash
# Terraform shortcuts
alias tf='terraform'
alias tfi='terraform init'
alias tfp='terraform plan'
alias tfa='terraform apply'
alias tfd='terraform destroy'

# Ansible shortcuts
alias ap='ansible-playbook'
alias ai='ansible-inventory'

# AWS shortcuts
alias awsp='aws sts get-caller-identity'
alias ec2ls='aws ec2 describe-instances --query "Reservations[].Instances[].[Tags[?Key=='\''Name'\''].Value|[0],State.Name,InstanceId]" --output table'

# Project shortcuts
alias cdp='cd /mnt/d/terraform-for-project1'
alias cda='cd /mnt/d/terraform-for-project1/ansible'
alias cdt='cd /mnt/d/terraform-for-project1/environments/dev'
```

Reload:
```bash
source ~/.bashrc
```

---

## 🚀 One-Liner Deploy

```bash
# Full deploy in one command (WSL2)
cd ~/terraform-for-project1 && \
cd bootstrap && terraform init && terraform apply -auto-approve && \
cd ../environments/dev && terraform init && terraform apply -auto-approve && \
cd ../../ansible && ansible-galaxy collection install -r requirements.yml && \
export AWS_REGION=ap-southeast-1 && export ENV_NAME=dev && \
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

---

**Copy-paste và go!** 🚀
