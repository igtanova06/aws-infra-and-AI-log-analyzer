#!/bin/bash
# ============================================================
# Phase 1 Deployment Script - CloudWatch Logging Infrastructure
# ============================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION="${AWS_REGION:-ap-southeast-1}"
ENV_NAME="${ENV_NAME:-dev}"
TERRAFORM_DIR="environments/dev"
ANSIBLE_DIR="ansible"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Phase 1: CloudWatch Logging Infrastructure Deployment    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================================
# Step 1: Prerequisites Check
# ============================================================
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS CLI found${NC}"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ AWS credentials configured${NC}"

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Terraform found ($(terraform version -json | jq -r '.terraform_version'))${NC}"

# Check Ansible
if ! command -v ansible &> /dev/null; then
    echo -e "${RED}❌ Ansible not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Ansible found ($(ansible --version | head -n1))${NC}"

echo ""

# ============================================================
# Step 2: Bootstrap S3 Backend (if needed)
# ============================================================
echo -e "${YELLOW}[2/6] Checking S3 backend...${NC}"

BUCKET_NAME="p1-bootstrap-apse1-tfstate"
if aws s3 ls "s3://${BUCKET_NAME}" 2>&1 | grep -q 'NoSuchBucket'; then
    echo -e "${YELLOW}⚠️  S3 backend not found. Creating bootstrap infrastructure...${NC}"
    cd bootstrap
    terraform init
    terraform apply -auto-approve
    cd ..
    echo -e "${GREEN}✅ Bootstrap infrastructure created${NC}"
else
    echo -e "${GREEN}✅ S3 backend exists${NC}"
fi

echo ""

# ============================================================
# Step 3: Deploy Terraform Infrastructure
# ============================================================
echo -e "${YELLOW}[3/6] Deploying Terraform infrastructure...${NC}"

cd "$TERRAFORM_DIR"

# Initialize Terraform
echo -e "${BLUE}  → terraform init${NC}"
terraform init

# Validate configuration
echo -e "${BLUE}  → terraform validate${NC}"
terraform validate

# Plan
echo -e "${BLUE}  → terraform plan${NC}"
terraform plan -out=tfplan

# Apply
echo -e "${BLUE}  → terraform apply${NC}"
read -p "Do you want to apply these changes? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${RED}❌ Deployment cancelled${NC}"
    exit 1
fi

terraform apply tfplan
rm tfplan

echo -e "${GREEN}✅ Terraform infrastructure deployed${NC}"

# Get outputs
ALB_DNS=$(terraform output -raw alb_dns_name 2>/dev/null || echo "N/A")
VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || echo "N/A")

cd ../..
echo ""

# ============================================================
# Step 4: Install Ansible Collections
# ============================================================
echo -e "${YELLOW}[4/6] Installing Ansible collections...${NC}"

cd "$ANSIBLE_DIR"
ansible-galaxy collection install -r requirements.yml
echo -e "${GREEN}✅ Ansible collections installed${NC}"

echo ""

# ============================================================
# Step 5: Wait for EC2 Instances
# ============================================================
echo -e "${YELLOW}[5/6] Waiting for EC2 instances to be ready...${NC}"

echo -e "${BLUE}  → Waiting 60 seconds for instances to initialize...${NC}"
sleep 60

# Test inventory
echo -e "${BLUE}  → Testing Ansible inventory${NC}"
ansible-inventory -i inventory/aws_ec2.yml --list > /dev/null 2>&1 || {
    echo -e "${RED}❌ Failed to load inventory. Check AWS credentials and EC2 instances.${NC}"
    exit 1
}

# Test connectivity
echo -e "${BLUE}  → Testing SSM connectivity${NC}"
MAX_RETRIES=5
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if ansible role_app -i inventory/aws_ec2.yml -m ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ EC2 instances are reachable via SSM${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}⚠️  Retry $RETRY_COUNT/$MAX_RETRIES - waiting 30 seconds...${NC}"
            sleep 30
        else
            echo -e "${RED}❌ Failed to connect to EC2 instances after $MAX_RETRIES attempts${NC}"
            exit 1
        fi
    fi
done

echo ""

# ============================================================
# Step 6: Deploy with Ansible
# ============================================================
echo -e "${YELLOW}[6/6] Deploying application with Ansible...${NC}"

export AWS_REGION="$AWS_REGION"
export ENV_NAME="$ENV_NAME"

ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml

echo -e "${GREEN}✅ Ansible deployment completed${NC}"

cd ..
echo ""

# ============================================================
# Deployment Summary
# ============================================================
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Phase 1 Deployment Completed! 🎉                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "  • VPC ID: ${GREEN}${VPC_ID}${NC}"
echo -e "  • ALB DNS: ${GREEN}${ALB_DNS}${NC}"
echo -e "  • Region: ${GREEN}${AWS_REGION}${NC}"
echo -e "  • Environment: ${GREEN}${ENV_NAME}${NC}"
echo ""
echo -e "${BLUE}📋 Log Groups Created:${NC}"
echo -e "  • ${GREEN}/aws/vpc/flowlogs${NC} - VPC Flow Logs"
echo -e "  • ${GREEN}/aws/cloudtrail/logs${NC} - CloudTrail Events"
echo -e "  • ${GREEN}/aws/ec2/applogs${NC} - Application Logs"
echo ""
echo -e "${BLUE}🔍 Next Steps:${NC}"
echo -e "  1. Generate test logs:"
echo -e "     ${YELLOW}cd AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui${NC}"
echo -e "     ${YELLOW}python3 generate_vpc_flow_logs.py${NC}"
echo -e "     ${YELLOW}python3 generate_cloudtrail_logs.py${NC}"
echo ""
echo -e "  2. Access AI Log Analyzer:"
echo -e "     ${YELLOW}http://${ALB_DNS}${NC}"
echo ""
echo -e "  3. Test analysis:"
echo -e "     - Select log group: ${GREEN}/aws/vpc/flowlogs${NC}"
echo -e "     - Search term: ${GREEN}REJECT${NC}"
echo -e "     - Click 'Analyze Logs'"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo -e "  • Full guide: ${YELLOW}PHASE1_DEPLOYMENT_GUIDE.md${NC}"
echo -e "  • Project audit: ${YELLOW}PROJECT_AUDIT_REPORT.md${NC}"
echo ""
echo -e "${GREEN}✨ Happy analyzing! ✨${NC}"
