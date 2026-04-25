#!/bin/bash
#
# SSM Port Forwarding Script for Layer 2 (Log Analyzer)
# Usage: ./ssm-connect-layer2.sh [local_port]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="${AWS_REGION:-ap-southeast-1}"
TERRAFORM_DIR="${TERRAFORM_DIR:-./environments/dev}"
REMOTE_PORT="80"
LOCAL_PORT="${1:-8080}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AWS SSM Port Forwarding - Layer 2 (Log Analyzer)         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}[1/5]${NC} Checking prerequisites..."

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found!${NC}"
    echo "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

if ! command -v session-manager-plugin &> /dev/null; then
    echo -e "${RED}❌ Session Manager Plugin not found!${NC}"
    echo "Install: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI: $(aws --version | cut -d' ' -f1)${NC}"
echo -e "${GREEN}✅ Session Manager Plugin: Installed${NC}"
echo ""

# Check AWS credentials
echo -e "${YELLOW}[2/5]${NC} Verifying AWS credentials..."

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured!${NC}"
    echo "Run: aws configure"
    exit 1
fi

CALLER_IDENTITY=$(aws sts get-caller-identity --output json)
AWS_ACCOUNT=$(echo $CALLER_IDENTITY | jq -r '.Account')
AWS_USER=$(echo $CALLER_IDENTITY | jq -r '.Arn' | cut -d'/' -f2)

echo -e "${GREEN}✅ Authenticated as: ${AWS_USER}${NC}"
echo -e "${GREEN}✅ Account: ${AWS_ACCOUNT}${NC}"
echo ""

# Get instance ID
echo -e "${YELLOW}[3/5]${NC} Finding Layer 2 instance..."

if [ -d "$TERRAFORM_DIR" ]; then
    # Try to get from Terraform output
    cd "$TERRAFORM_DIR"
    INSTANCE_ID=$(terraform output -raw app_instance_id 2>/dev/null || echo "")
    cd - > /dev/null
fi

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" == "null" ]; then
    # Fallback: search by tag
    echo -e "${YELLOW}   Terraform output not available, searching by tag...${NC}"
    INSTANCE_ID=$(aws ec2 describe-instances \
        --region $REGION \
        --filters "Name=tag:Name,Values=*app*" "Name=instance-state-name,Values=running" \
        --query "Reservations[0].Instances[0].InstanceId" \
        --output text 2>/dev/null || echo "")
fi

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" == "None" ]; then
    echo -e "${RED}❌ Layer 2 instance not found!${NC}"
    echo "Make sure infrastructure is deployed: terraform apply"
    exit 1
fi

echo -e "${GREEN}✅ Found instance: ${INSTANCE_ID}${NC}"
echo ""

# Check SSM connectivity
echo -e "${YELLOW}[4/5]${NC} Checking SSM connectivity..."

SSM_STATUS=$(aws ssm describe-instance-information \
    --region $REGION \
    --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
    --query "InstanceInformationList[0].PingStatus" \
    --output text 2>/dev/null || echo "NotFound")

if [ "$SSM_STATUS" != "Online" ]; then
    echo -e "${RED}❌ Instance not connected to SSM!${NC}"
    echo "Possible issues:"
    echo "  - SSM Agent not running"
    echo "  - IAM role missing AmazonSSMManagedInstanceCore policy"
    echo "  - VPC endpoints not configured"
    exit 1
fi

echo -e "${GREEN}✅ SSM Status: Online${NC}"
echo ""

# Check if port is already in use
echo -e "${YELLOW}[5/5]${NC} Checking local port availability..."

if lsof -Pi :$LOCAL_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}❌ Port ${LOCAL_PORT} is already in use!${NC}"
    echo ""
    echo "Options:"
    echo "  1. Kill existing process: sudo lsof -ti:${LOCAL_PORT} | xargs kill -9"
    echo "  2. Use different port: $0 8081"
    exit 1
fi

echo -e "${GREEN}✅ Port ${LOCAL_PORT} is available${NC}"
echo ""

# Start port forwarding
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Starting Port Forwarding Session                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📡 Remote:${NC} ${INSTANCE_ID}:${REMOTE_PORT}"
echo -e "${GREEN}💻 Local:${NC}  localhost:${LOCAL_PORT}"
echo -e "${GREEN}🌐 Access:${NC} http://localhost:${LOCAL_PORT}"
echo ""
echo -e "${YELLOW}⏹️  Press Ctrl+C to stop${NC}"
echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

# Start session
aws ssm start-session \
    --region $REGION \
    --target $INSTANCE_ID \
    --document-name AWS-StartPortForwardingSession \
    --parameters "{\"portNumber\":[\"${REMOTE_PORT}\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}"

# Cleanup message (shown after Ctrl+C)
echo ""
echo -e "${GREEN}✅ Session terminated${NC}"
