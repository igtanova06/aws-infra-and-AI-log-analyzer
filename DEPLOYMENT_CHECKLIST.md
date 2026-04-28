# ✅ DEPLOYMENT CHECKLIST

## 📋 Pre-Deployment

### Environment Setup
- [ ] AWS CLI installed and configured
- [ ] Terraform installed (>= 1.0)
- [ ] Ansible installed (>= 2.9)
- [ ] Python 3.8+ installed
- [ ] MySQL client installed
- [ ] Git installed

### AWS Account
- [ ] AWS account created
- [ ] IAM user with admin permissions
- [ ] AWS credentials configured (`aws configure`)
- [ ] Default region set (ap-southeast-1)
- [ ] Bedrock access enabled
- [ ] Service quotas checked

### Telegram Bot (Optional)
- [ ] Bot created with @BotFather
- [ ] BOT_TOKEN saved
- [ ] CHAT_ID obtained
- [ ] Bot tested with test message

---

## 🏗️ Infrastructure Deployment

### Bootstrap
- [ ] Navigate to `bootstrap/` directory
- [ ] Run `terraform init`
- [ ] Run `terraform apply`
- [ ] S3 bucket created
- [ ] DynamoDB table created
- [ ] Backend configured

### Terraform Infrastructure
- [ ] Navigate to `environments/dev/`
- [ ] Review `terraform.tfvars`
- [ ] Run `terraform init`
- [ ] Run `terraform plan -out=tfplan`
- [ ] Review plan output
- [ ] Run `terraform apply tfplan`
- [ ] Wait for completion (~10-15 min)

### Verify Infrastructure
- [ ] VPC created
- [ ] Subnets created (public, private, db)
- [ ] Internet Gateway created
- [ ] NAT Gateways created (if enabled)
- [ ] Route tables configured
- [ ] Security Groups created
- [ ] EC2 instances running (4 total)
- [ ] RDS instance available
- [ ] ALB created and healthy
- [ ] VPC Endpoints created

### Save Outputs
- [ ] Run `terraform output alb_dns_name`
- [ ] Run `terraform output db_endpoint`
- [ ] Run `terraform output -raw db_password`
- [ ] Save outputs to file: `terraform output -json > ../../scripts/terraform_outputs.json`

---

## 📊 CloudWatch Log Groups

### Create/Verify Log Groups
- [ ] Navigate to `scripts/`
- [ ] Run `chmod +x fix_log_groups.sh`
- [ ] Run `./fix_log_groups.sh`
- [ ] Verify all 9 log groups created:
  - [ ] `/aws/vpc/flowlogs`
  - [ ] `/aws/cloudtrail/logs`
  - [ ] `/aws/ec2/web-tier/system`
  - [ ] `/aws/ec2/web-tier/httpd`
  - [ ] `/aws/ec2/web-tier/application`
  - [ ] `/aws/ec2/app-tier/system`
  - [ ] `/aws/ec2/app-tier/streamlit`
  - [ ] `/aws/rds/mysql/error`
  - [ ] `/aws/rds/mysql/slowquery`

### Verify Log Streams
- [ ] Run `./check_logs.sh`
- [ ] Check each log group has streams
- [ ] Verify recent log events

---

## 💾 Database Deployment

### Deploy Schema
- [ ] Navigate to `scripts/database/`
- [ ] Run `chmod +x deploy_db.sh`
- [ ] Run `./deploy_db.sh`
- [ ] Database connection successful
- [ ] Schema deployed
- [ ] Tables created (6 total)
- [ ] Default data inserted

### Verify Database
- [ ] Connect to RDS: `mysql -h <endpoint> -u admin -p`
- [ ] Check database: `SHOW DATABASES;`
- [ ] Use database: `USE qlsv_system;`
- [ ] Check tables: `SHOW TABLES;`
- [ ] Verify data:
  - [ ] 3 roles
  - [ ] 14 users (1 admin, 3 lecturers, 10 students)
  - [ ] 5 classes
  - [ ] 10 students
  - [ ] 5 enrollments
  - [ ] 4 grades

---

## 🚀 Application Deployment

### Ansible Setup
- [ ] Navigate to `ansible/`
- [ ] Update `inventory/group_vars/all.yml` with DB credentials
- [ ] Test inventory: `ansible-inventory -i inventory/aws_ec2.yml --list`
- [ ] Test connectivity: `ansible all -i inventory/aws_ec2.yml -m ping`

### Deploy Applications
- [ ] Run `ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml`
- [ ] Wait for completion (~10-15 min)
- [ ] Verify playbook success

### Verify Deployments
- [ ] CloudWatch Agent installed on all instances
- [ ] Docker installed on all instances
- [ ] Web app deployed on web tier
- [ ] Log analyzer deployed on app tier
- [ ] All services running

---

## 🌐 Application Access

### Web QLSV (Layer 1)
- [ ] Get ALB DNS: `terraform output alb_dns_name`
- [ ] Open browser: `http://<ALB-DNS>/qlsv`
- [ ] Login page loads
- [ ] Test login with admin/123@
- [ ] Dashboard accessible
- [ ] Test navigation

### AI Log Analyzer (Layer 2)
- [ ] Get app instance ID
- [ ] Run `./scripts/access_app.sh`
- [ ] Port forwarding established
- [ ] Open browser: `http://localhost:8501`
- [ ] Streamlit UI loads
- [ ] Select log groups
- [ ] Run test analysis

---

## 📱 Telegram Integration

### Configure Bot
- [ ] Navigate to `AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/`
- [ ] Copy `.env.example` to `.env`
- [ ] Edit `.env` with bot credentials:
  - [ ] TELEGRAM_BOT_TOKEN
  - [ ] TELEGRAM_CHAT_ID
  - [ ] TELEGRAM_ALERTS_ENABLED=true

### Test Bot
- [ ] Run `python3 test_telegram.py`
- [ ] Verify test message received in Telegram
- [ ] Check message formatting

### Test Alert Flow
- [ ] Run log analysis in Streamlit
- [ ] Verify alert sent to Telegram
- [ ] Check alert content

---

## 🔍 Verification & Testing

### Infrastructure Tests
- [ ] All EC2 instances running
- [ ] RDS instance available
- [ ] ALB health checks passing
- [ ] Security groups configured correctly
- [ ] VPC endpoints working

### Application Tests
- [ ] Web app accessible via ALB
- [ ] Database queries working
- [ ] User login/logout working
- [ ] CRUD operations working
- [ ] Log analyzer accessible via SSM
- [ ] AI analysis working
- [ ] Telegram alerts working

### Log Tests
- [ ] Run `./scripts/check_logs.sh`
- [ ] All 9 log groups active
- [ ] Recent log events present
- [ ] CloudWatch Agent running on all instances
- [ ] Logs streaming in real-time

### Performance Tests
- [ ] Web app response time < 500ms
- [ ] Database queries < 100ms
- [ ] Log analysis completes < 30s
- [ ] AI analysis completes < 10s

---

## 📊 Monitoring Setup

### CloudWatch
- [ ] Log groups configured
- [ ] Retention policies set
- [ ] Metrics collecting
- [ ] Alarms configured (optional)

### Application Monitoring
- [ ] Web app logs visible
- [ ] App tier logs visible
- [ ] Database logs visible
- [ ] Error tracking working

---

## 🔐 Security Verification

### Network Security
- [ ] Private subnets isolated
- [ ] Security groups restrictive
- [ ] No unnecessary public IPs
- [ ] VPC endpoints working

### Application Security
- [ ] Passwords hashed
- [ ] SQL injection prevention
- [ ] Session security enabled
- [ ] Input validation working

### Access Control
- [ ] IAM roles configured
- [ ] SSM access working
- [ ] No SSH keys needed
- [ ] Secrets in SSM Parameter Store

---

## 📚 Documentation

### Review Documentation
- [ ] Read `DEPLOYMENT_COMPLETE_GUIDE.md`
- [ ] Read `QUICK_START.md`
- [ ] Read `PROJECT_SUMMARY.md`
- [ ] Read application READMEs
- [ ] Understand architecture

### Create Custom Docs
- [ ] Document custom configurations
- [ ] Document access procedures
- [ ] Document troubleshooting steps
- [ ] Document backup procedures

---

## 🎯 Post-Deployment

### Immediate Tasks
- [ ] Test all functionality
- [ ] Verify monitoring
- [ ] Check costs in AWS Console
- [ ] Set up billing alerts
- [ ] Document any issues

### Short-term Tasks (1 week)
- [ ] Enable HTTPS on ALB
- [ ] Set up CloudWatch Dashboards
- [ ] Configure SNS notifications
- [ ] Implement backup strategy
- [ ] Performance tuning

### Long-term Tasks (1 month)
- [ ] Add WAF rules
- [ ] Implement CI/CD
- [ ] Cost optimization
- [ ] Security hardening
- [ ] Disaster recovery plan

---

## 🐛 Troubleshooting

### If Issues Occur
- [ ] Check `DEPLOYMENT_COMPLETE_GUIDE.md` troubleshooting section
- [ ] Run `./scripts/check_logs.sh`
- [ ] Check CloudWatch Logs
- [ ] Verify Security Groups
- [ ] Check IAM permissions
- [ ] Review Terraform state
- [ ] Check Ansible logs

### Common Issues Checklist
- [ ] Logs not appearing → Run `./scripts/fix_log_groups.sh`
- [ ] Database connection failed → Check security group
- [ ] Ansible connection failed → Check SSM agent
- [ ] Telegram not working → Verify bot token
- [ ] Web app not accessible → Check ALB health
- [ ] AI analysis failed → Check Bedrock permissions

---

## ✅ Final Verification

### System Health
- [ ] All services running
- [ ] All logs streaming
- [ ] All applications accessible
- [ ] All tests passing
- [ ] No errors in logs

### Documentation
- [ ] All credentials saved securely
- [ ] All outputs documented
- [ ] All procedures documented
- [ ] Team trained on access

### Sign-off
- [ ] Infrastructure deployed ✅
- [ ] Applications deployed ✅
- [ ] Monitoring configured ✅
- [ ] Documentation complete ✅
- [ ] Team trained ✅

---

## 🎉 Deployment Complete!

**Date**: _______________
**Deployed by**: _______________
**Environment**: Production / Staging / Dev
**Status**: ✅ READY

### Access Information

**Web QLSV:**
- URL: http://_________________/qlsv
- Admin: admin / 123@

**AI Log Analyzer:**
- Access: SSM Port Forwarding
- Port: 8501

**Database:**
- Endpoint: _________________
- User: admin
- Database: qlsv_system

**Monitoring:**
- CloudWatch: 9 log groups active
- Telegram: Alerts enabled

---

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________

**Next Review Date**: _______________
