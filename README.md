# 🔍 AI-Powered Log Analysis System

> Automated infrastructure deployment with AI-driven security log analysis using AWS Bedrock

[![Terraform](https://img.shields.io/badge/Terraform-1.5+-purple?logo=terraform)](https://www.terraform.io/)
[![Ansible](https://img.shields.io/badge/Ansible-2.9+-red?logo=ansible)](https://www.ansible.com/)
[![AWS](https://img.shields.io/badge/AWS-Cloud-orange?logo=amazon-aws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)](https://www.python.org/)

## 🎯 Project Overview

This project demonstrates a complete DevSecOps pipeline that:
1. **Provisions infrastructure** using Terraform (IaC)
2. **Configures systems** using Ansible (Configuration Management)
3. **Collects logs** from multiple sources (VPC Flow Logs, CloudTrail, Application Logs)
4. **Analyzes security events** using AI (AWS Bedrock with Claude)
5. **Provides root cause analysis** for security incidents

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │   ALB   │ (Public Subnet)
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
   │ Web EC2 │      │ Web EC2 │     │ App EC2 │ (Private Subnet)
   │ (QLSV)  │      │ (QLSV)  │     │(Streamlit)│
   └────┬────┘      └────┬────┘     └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                    ┌────▼────┐
                    │   RDS   │ (DB Subnet)
                    └─────────┘

All Logs → CloudWatch Logs → AI Analysis (Bedrock)
```

## ✨ Features

### Infrastructure (Terraform)
- ✅ 3-tier VPC architecture (public, private, db subnets)
- ✅ Application Load Balancer with path-based routing
- ✅ Auto Scaling Groups for high availability
- ✅ RDS PostgreSQL database
- ✅ VPC Flow Logs for network monitoring
- ✅ CloudTrail for API audit logging
- ✅ CloudWatch Logs centralization
- ✅ IAM roles with least privilege
- ✅ Security Groups with defense in depth
- ✅ VPC Endpoints (SSM, S3) for private connectivity

### Configuration Management (Ansible)
- ✅ Dynamic inventory from AWS EC2 tags
- ✅ SSM-based connection (no SSH keys needed)
- ✅ CloudWatch Agent deployment
- ✅ Docker containerized applications
- ✅ Automated application deployment
- ✅ Idempotent playbooks

### Applications
- ✅ **Streamlit AI Log Analyzer** - AI-powered log analysis with AWS Bedrock
- ✅ **PHP Web QLSV** - Student management system

### Security & Monitoring
- ✅ VPC Flow Logs (network traffic analysis)
- ✅ CloudTrail (AWS API audit trail)
- ✅ CloudWatch Logs (application logs)
- ✅ CloudWatch Alarms (security event detection)
- ✅ Metric filters for suspicious activities
- ✅ AI-powered root cause analysis

## 🚀 Quick Start

### Prerequisites
```bash
# Required tools
- AWS CLI configured
- Terraform >= 1.5
- Ansible >= 2.9
- Python 3.8+
- Session Manager Plugin
```

### 1. Deploy Infrastructure
```bash
cd environments/dev
terraform init
terraform apply
```

### 2. Deploy Applications
```bash
cd ../../ansible
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

### 3. Access Applications

**Web QLSV (via ALB):**
```bash
ALB_DNS=$(cd environments/dev && terraform output -raw alb_dns_name)
echo "http://$ALB_DNS/qlsv"
```

**Streamlit AI Analyzer (via SSM tunnel):**
```bash
INSTANCE_ID=$(aws ec2 describe-instances --filters "Name=tag:Role,Values=app" "Name=instance-state-name,Values=running" --query 'Reservations[0].Instances[0].InstanceId' --output text)

aws ssm start-session --target $INSTANCE_ID --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8501"],"localPortNumber":["8888"]}'

# Open: http://localhost:8888
```

## 🎭 Demo: Attack Detection

### Generate Attack Logs
```bash
bash scripts/generate_attack_logs.sh
# Select: 5 (All attacks)
```

### Analyze with AI
1. Open Streamlit: `http://localhost:8888`
2. Select Log Group: `/aws/ec2/applogs`
3. Search Term: `Failed password`
4. Enable AI Enhancement ✅
5. Click "Analyze Logs"

### Expected Results
- **SSH Brute Force**: 53 failed login attempts detected
- **SQL Injection**: Multiple injection patterns identified
- **Port Scanning**: Systematic port probing detected
- **Unauthorized API**: Failed authentication attempts

AI provides:
- Severity assessment
- Business impact analysis
- Evidence from logs
- Root cause inference
- Immediate containment steps
- Prevention recommendations

## 📊 Log Sources

| Source | Log Group | Content |
|--------|-----------|---------|
| VPC Flow Logs | `/aws/vpc/flowlogs` | Network traffic (ACCEPT/REJECT) |
| Application Logs | `/aws/ec2/applogs` | System logs, app logs, security events |
| CloudTrail | `/aws/cloudtrail/logs` | AWS API calls, IAM changes |

## 🔍 Monitoring

### CloudWatch Alarms
- VPC high rejected connections
- Unauthorized API calls
- Root account usage
- Security group changes
- IAM policy changes

### Metric Filters
- Failed SSH attempts
- SQL injection patterns
- Port scanning activity
- Unauthorized access attempts

## 📁 Project Structure

```
terraform-for-project1/
├── environments/dev/          # Terraform infrastructure
│   ├── main.tf               # VPC, networking
│   ├── compute.tf            # EC2, ASG
│   ├── alb.tf                # Load balancer
│   ├── database.tf           # RDS
│   ├── cloudwatch.tf         # Log groups, Flow Logs
│   ├── cloudtrail.tf         # CloudTrail setup
│   ├── iam.tf                # IAM roles & policies
│   └── security_groups.tf    # Security groups
├── ansible/                   # Configuration management
│   ├── inventory/            # Dynamic inventory
│   ├── playbooks/            # Ansible playbooks
│   ├── roles/                # Reusable roles
│   └── templates/            # Config templates
├── AI_Log_Analysis-Project-1/ # Streamlit app
│   └── bedrock-log-analyzer-ui/
│       ├── streamlit_app.py  # Main UI
│       ├── src/              # Analysis modules
│       └── requirements.txt
├── Web-Project-1/            # PHP web app
│   ├── api/                  # REST API
│   ├── admin/                # Admin panel
│   └── student/              # Student portal
└── scripts/                  # Utility scripts
    └── generate_attack_logs.sh
```

## 📚 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick command reference
- **[PROJECT_AUDIT_REPORT.md](PROJECT_AUDIT_REPORT.md)** - Project status audit
- **[CLOUDWATCH_SETUP_COMPLETE.md](CLOUDWATCH_SETUP_COMPLETE.md)** - CloudWatch setup details
- **[HOW_TO_ACCESS_APPS.md](HOW_TO_ACCESS_APPS.md)** - Application access guide

## 💰 Cost Estimate

**Dev Environment (~$50-70/month):**
- EC2 (4x t3.micro): ~$30/month
- RDS (db.t3.micro): ~$15/month
- ALB: ~$20/month
- CloudWatch Logs: ~$5/month
- Bedrock API: ~$0.01-0.05 per analysis

**Production optimizations:**
- Use Reserved Instances (save 40-60%)
- Enable NAT Gateway only when needed
- Adjust log retention periods
- Use S3 for long-term log storage

## 🔒 Security Best Practices

✅ **Implemented:**
- Private subnets for applications
- SSM for secure access (no SSH keys)
- IAM roles with least privilege
- Security groups with minimal exposure
- VPC Flow Logs for network monitoring
- CloudTrail for audit logging
- Encrypted RDS storage
- S3 bucket encryption

⚠️ **Recommended for Production:**
- Enable AWS GuardDuty
- Add AWS WAF to ALB
- Enable MFA for IAM users
- Implement AWS Config rules
- Add AWS Security Hub
- Enable S3 versioning
- Implement backup strategy

## 🧹 Cleanup

```bash
# Destroy infrastructure
cd environments/dev
terraform destroy

# Destroy bootstrap
cd ../../bootstrap
terraform destroy
```

## 🤝 Contributing

This is a demo project for learning purposes. Feel free to:
- Fork and experiment
- Submit issues
- Suggest improvements
- Share your learnings

## 📝 License

This project is for educational purposes.

## 🙏 Acknowledgments

- AWS for cloud infrastructure
- Terraform for IaC
- Ansible for configuration management
- Anthropic Claude (via AWS Bedrock) for AI analysis
- Streamlit for rapid UI development

## 📞 Support

For issues or questions:
1. Check documentation in `/docs`
2. Review CloudWatch Logs
3. Verify IAM permissions
4. Check Security Group rules

---

**Built with ❤️ for DevSecOps learning**

🚀 **Ready to deploy!** Follow the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) to get started.
