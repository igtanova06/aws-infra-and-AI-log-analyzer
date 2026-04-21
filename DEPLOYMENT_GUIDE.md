# 🚀 Deployment Guide - AI Log Analysis System

## 📋 Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.5
- Ansible >= 2.9
- Python 3.8+
- Session Manager Plugin for AWS CLI

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │   ALB   │ (Public)
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
   │ Web EC2 │      │ Web EC2 │     │ App EC2 │ (Private)
   │ (QLSV)  │      │ (QLSV)  │     │(Streamlit)│
   └────┬────┘      └────┬────┘     └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                    ┌────▼────┐
                    │   RDS   │ (Private)
                    └─────────┘

All logs → CloudWatch Logs → AI Analysis
```

## 📊 Log Flow

```
EC2 Instances → CloudWatch Agent → CloudWatch Logs
VPC Traffic   → VPC Flow Logs    → CloudWatch Logs
AWS API Calls → CloudTrail       → CloudWatch Logs
                                      ↓
                            AI Log Analyzer (Bedrock)
                                      ↓
                            Root Cause Analysis
```

## 🎯 Phase 1: Infrastructure Setup (Terraform)

### Step 1: Bootstrap S3 Backend

```bash
cd bootstrap
terraform init
terraform apply
```

### Step 2: Deploy Infrastructure

```bash
cd ../environments/dev

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Apply infrastructure
terraform apply
```

**Resources created:**
- ✅ VPC with 3-tier architecture
- ✅ ALB with path-based routing
- ✅ Auto Scaling Groups (2 web + 2 app)
- ✅ RDS PostgreSQL
- ✅ CloudWatch Log Groups
- ✅ VPC Flow Logs
- ✅ CloudTrail
- ✅ IAM Roles & Policies
- ✅ Security Groups
- ✅ VPC Endpoints (SSM, S3)

### Step 3: Verify Infrastructure

```bash
# Get outputs
terraform output

# Expected outputs:
# - alb_dns_name
# - vpc_id
# - cloudwatch_log_groups
# - cloudtrail_info
```

## 🔧 Phase 2: Configuration & Deployment (Ansible)

### Step 1: Install Ansible Collections

```bash
cd ../../ansible
ansible-galaxy collection install -r requirements.yml
```

### Step 2: Verify Dynamic Inventory

```bash
# Test inventory
ansible-inventory -i inventory/aws_ec2.yml --graph

# Expected output:
# @all:
#   |--@aws_ec2:
#   |  |--p1-dev-apse1-l1-node-1
#   |  |--p1-dev-apse1-l1-node-2
#   |  |--p1-dev-apse1-l2-node-1
#   |  |--p1-dev-apse1-l2-node-2
```

### Step 3: Deploy Applications

```bash
# Run full deployment
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml

# Or run individual playbooks:
ansible-playbook -i inventory/aws_ec2.yml playbooks/install_cloudwatch_agent.yml
ansible-playbook -i inventory/aws_ec2.yml playbooks/install_docker.yml
ansible-playbook -i inventory/aws_ec2.yml playbooks/deploy_log_analyzer.yml
ansible-playbook -i inventory/aws_ec2.yml playbooks/deploy_web_app.yml
```

**What gets deployed:**
1. ✅ CloudWatch Agent (all instances)
2. ✅ Docker & Docker Compose
3. ✅ Streamlit AI Log Analyzer (app tier)
4. ✅ PHP Web QLSV (web tier)

## 🌐 Phase 3: Access Applications

### Option 1: Web QLSV (Public via ALB)

```bash
# Get ALB DNS
cd environments/dev
ALB_DNS=$(terraform output -raw alb_dns_name)

# Access Web QLSV
echo "Web QLSV: http://$ALB_DNS/qlsv"
echo "Admin Panel: http://$ALB_DNS/admin/"
echo "API: http://$ALB_DNS/api/"
```

Open in browser: `http://<ALB-DNS>/qlsv`

### Option 2: Streamlit AI Analyzer (SSM Tunnel)

```bash
# Get app instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Role,Values=app" "Name=instance-state-name,Values=running" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Create SSM tunnel
aws ssm start-session \
  --target $INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8501"],"localPortNumber":["8888"]}'

# In another terminal or browser
# Open: http://localhost:8888
```

**Why SSM tunnel for Streamlit?**
- Streamlit runs on private subnet (no public IP)
- More secure - only users with AWS SSM permissions can access
- No need to expose port 8501 to internet

## 📊 Phase 4: Verify CloudWatch Logs

### Check Log Groups

```bash
# List log groups
aws logs describe-log-groups --query 'logGroups[*].logGroupName'

# Expected:
# - /aws/vpc/flowlogs
# - /aws/ec2/applogs
# - /aws/cloudtrail/logs
```

### Tail Logs

```bash
# VPC Flow Logs
aws logs tail /aws/vpc/flowlogs --follow

# Application Logs
aws logs tail /aws/ec2/applogs --follow

# CloudTrail
aws logs tail /aws/cloudtrail/logs --follow
```

## 🎭 Phase 5: Demo Attack Scenarios

### Generate Attack Logs

```bash
# Run attack simulation
bash scripts/generate_attack_logs.sh

# Select scenario:
# 1. SSH Brute Force Attack
# 2. SQL Injection Attempts
# 3. Port Scanning
# 4. Unauthorized API Access
# 5. All of the above
```

### Analyze with AI

1. **Open Streamlit** (via SSM tunnel): `http://localhost:8888`

2. **Configure Analysis:**
   - Log Group: `/aws/ec2/applogs`
   - Search Term: `Failed password` (for SSH attacks)
   - Time Range: Last 1 hour
   - Enable AI Enhancement: ✅

3. **Click "Analyze Logs"**

4. **Review Results:**
   - Summary tab: Overview of issues
   - Analysis tab: Pattern detection
   - Solutions tab: AI-powered root cause analysis

### Expected AI Output

For SSH Brute Force:
```
🚨 SSH Brute Force Attack Detected

Severity: High
Business Impact: Potential unauthorized access

Evidence From Logs:
- 53 failed login attempts from IP 203.0.113.42
- Targeting common usernames (root, admin, ubuntu)
- High frequency (50 attempts in 5 seconds)

AI Inference:
- Automated brute force attack
- Attacker using dictionary/common username list
- Source IP: 203.0.113.42 (suspicious)

Immediate Containment:
Block IP 203.0.113.42 in Security Group

Next Best Command:
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --ip-permissions IpProtocol=-1,FromPort=0,ToPort=65535,IpRanges='[{CidrIp=203.0.113.42/32,Description="Blocked by AI"}]'

Prevention:
- Enable fail2ban
- Use SSH key authentication only
- Implement rate limiting
```

## 🔍 Phase 6: Monitoring & Alerts

### CloudWatch Alarms

Check active alarms:
```bash
aws cloudwatch describe-alarms --query 'MetricAlarms[*].[AlarmName,StateValue]'
```

**Pre-configured alarms:**
- VPC high rejected connections
- Unauthorized API calls
- Root account usage
- Security group changes
- IAM policy changes

### View Metrics

```bash
# VPC Flow Logs metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/VPC \
  --metric-name PacketsDropped \
  --dimensions Name=VpcId,Value=<vpc-id> \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

## 🧹 Cleanup

### Destroy Infrastructure

```bash
# Destroy dev environment
cd environments/dev
terraform destroy

# Destroy bootstrap
cd ../../bootstrap
terraform destroy
```

**Note:** CloudWatch Logs and S3 buckets may need manual deletion if they contain data.

## 🐛 Troubleshooting

### Issue: CloudWatch Agent not sending logs

```bash
# SSH into instance via SSM
aws ssm start-session --target <instance-id>

# Check agent status
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a query -m ec2 -c default

# Check agent logs
sudo tail -f /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

### Issue: Streamlit not accessible

```bash
# Check if container is running
aws ssm start-session --target <instance-id>
sudo docker ps

# Check container logs
sudo docker logs bedrock-log-analyzer

# Restart container
sudo docker restart bedrock-log-analyzer
```

### Issue: No logs in CloudWatch

```bash
# Verify IAM permissions
aws iam get-role-policy \
  --role-name p1-dev-apse1-ec2-role \
  --policy-name p1-dev-apse1-cloudwatch-agent-policy

# Check VPC Flow Logs status
aws ec2 describe-flow-logs --filter "Name=resource-id,Values=<vpc-id>"
```

## 📚 Additional Resources

- [AWS CloudWatch Logs Documentation](https://docs.aws.amazon.com/cloudwatch/latest/logs/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Ansible AWS Collections](https://docs.ansible.com/ansible/latest/collections/amazon/aws/)

## 🎯 Success Criteria

- ✅ All EC2 instances healthy in ALB target groups
- ✅ CloudWatch Agent running on all instances
- ✅ Logs flowing to CloudWatch Log Groups
- ✅ VPC Flow Logs capturing network traffic
- ✅ CloudTrail recording API calls
- ✅ Streamlit accessible via SSM tunnel
- ✅ Web QLSV accessible via ALB
- ✅ AI analysis working with Bedrock
- ✅ Attack scenarios detected by AI

## 📞 Support

For issues or questions:
1. Check CloudWatch Logs for errors
2. Review Terraform/Ansible output
3. Verify IAM permissions
4. Check Security Group rules
