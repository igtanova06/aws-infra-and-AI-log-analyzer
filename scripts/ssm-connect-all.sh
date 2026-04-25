#!/bin/bash
#
# SSM Port Forwarding Script - Multiple Ports
# Forwards both Streamlit UI (80) and Versus Incident (3000)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REGION="${AWS_REGION:-ap-southeast-1}"
TERRAFORM_DIR="${TERRAFORM_DIR:-./environments/dev}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AWS SSM Port Forwarding - All Services                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get instance ID
echo -e "${YELLOW}Finding Layer 2 instance...${NC}"

if [ -d "$TERRAFORM_DIR" ]; then
    cd "$TERRAFORM_DIR"
    INSTANCE_ID=$(terraform output -raw app_instance_id 2>/dev/null || echo "")
    cd - > /dev/null
fi

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" == "null" ]; then
    INSTANCE_ID=$(aws ec2 describe-instances \
        --region $REGION \
        --filters "Name=tag:Name,Values=*app*" "Name=instance-state-name,Values=running" \
        --query "Reservations[0].Instances[0].InstanceId" \
        --output text 2>/dev/null || echo "")
fi

if [ -z "$INSTANCE_ID" ] || [ "$INSTANCE_ID" == "None" ]; then
    echo -e "${RED}❌ Instance not found!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found: ${INSTANCE_ID}${NC}"
echo ""

# Create log directory
LOG_DIR="/tmp/ssm-sessions"
mkdir -p "$LOG_DIR"

# Start Streamlit UI forwarding (background)
echo -e "${YELLOW}Starting Streamlit UI forwarding (port 8080)...${NC}"
aws ssm start-session \
    --region $REGION \
    --target $INSTANCE_ID \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["80"],"localPortNumber":["8080"]}' \
    > "$LOG_DIR/streamlit.log" 2>&1 &
PID_STREAMLIT=$!

sleep 2

# Start Versus Incident forwarding (background)
echo -e "${YELLOW}Starting Versus Incident forwarding (port 3000)...${NC}"
aws ssm start-session \
    --region $REGION \
    --target $INSTANCE_ID \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["3000"],"localPortNumber":["3000"]}' \
    > "$LOG_DIR/versus.log" 2>&1 &
PID_VERSUS=$!

sleep 2

# Check if processes are running
if ! ps -p $PID_STREAMLIT > /dev/null; then
    echo -e "${RED}❌ Failed to start Streamlit forwarding${NC}"
    cat "$LOG_DIR/streamlit.log"
    exit 1
fi

if ! ps -p $PID_VERSUS > /dev/null; then
    echo -e "${RED}❌ Failed to start Versus Incident forwarding${NC}"
    cat "$LOG_DIR/versus.log"
    exit 1
fi

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Port Forwarding Active                                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✅ Streamlit UI:${NC}      http://localhost:8080"
echo -e "${GREEN}✅ Versus Incident:${NC}   http://localhost:3000"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo -e "   Streamlit:  tail -f $LOG_DIR/streamlit.log"
echo -e "   Versus:     tail -f $LOG_DIR/versus.log"
echo ""
echo -e "${YELLOW}⏹️  Press Ctrl+C to stop all sessions${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping sessions...${NC}"
    kill $PID_STREAMLIT 2>/dev/null || true
    kill $PID_VERSUS 2>/dev/null || true
    echo -e "${GREEN}✅ All sessions terminated${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for user interrupt
wait
