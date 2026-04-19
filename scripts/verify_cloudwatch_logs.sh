#!/bin/bash
# Script to verify CloudWatch Logs are working after deployment

set -e

REGION="${AWS_REGION:-ap-southeast-1}"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "CloudWatch Logs Verification Script"
echo "Region: $REGION"
echo "=========================================="
echo ""

# Function to check log group
check_log_group() {
    local log_group=$1
    local description=$2
    
    echo -n "Checking $description ($log_group)... "
    
    if aws logs describe-log-groups \
        --log-group-name-prefix "$log_group" \
        --region "$REGION" \
        --query "logGroups[?logGroupName=='$log_group'].logGroupName" \
        --output text | grep -q "$log_group"; then
        
        # Check if there are any log streams
        stream_count=$(aws logs describe-log-streams \
            --log-group-name "$log_group" \
            --region "$REGION" \
            --max-items 1 \
            --query 'length(logStreams)' \
            --output text 2>/dev/null || echo "0")
        
        if [ "$stream_count" -gt 0 ]; then
            echo -e "${GREEN}✓ EXISTS with logs${NC}"
            
            # Get latest log entry timestamp
            latest=$(aws logs describe-log-streams \
                --log-group-name "$log_group" \
                --region "$REGION" \
                --order-by LastEventTime \
                --descending \
                --max-items 1 \
                --query 'logStreams[0].lastEventTime' \
                --output text 2>/dev/null || echo "0")
            
            if [ "$latest" != "0" ] && [ "$latest" != "None" ]; then
                latest_date=$(date -d @$((latest/1000)) '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "Unknown")
                echo "  └─ Latest log: $latest_date"
            fi
            
            return 0
        else
            echo -e "${YELLOW}⚠ EXISTS but no logs yet${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ NOT FOUND${NC}"
        return 1
    fi
}

# Function to check CloudTrail
check_cloudtrail() {
    echo -n "Checking CloudTrail status... "
    
    trail_name=$(aws cloudtrail list-trails \
        --region "$REGION" \
        --query "Trails[?contains(Name, 'trail')].Name | [0]" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$trail_name" ] && [ "$trail_name" != "None" ]; then
        is_logging=$(aws cloudtrail get-trail-status \
            --name "$trail_name" \
            --region "$REGION" \
            --query 'IsLogging' \
            --output text 2>/dev/null || echo "false")
        
        if [ "$is_logging" == "True" ]; then
            echo -e "${GREEN}✓ ACTIVE and logging${NC}"
            echo "  └─ Trail: $trail_name"
            return 0
        else
            echo -e "${YELLOW}⚠ EXISTS but not logging${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ NOT FOUND${NC}"
        return 1
    fi
}

# Function to check VPC Flow Logs
check_vpc_flow_logs() {
    echo -n "Checking VPC Flow Logs... "
    
    flow_log_count=$(aws ec2 describe-flow-logs \
        --region "$REGION" \
        --query 'length(FlowLogs[?FlowLogStatus==`ACTIVE`])' \
        --output text 2>/dev/null || echo "0")
    
    if [ "$flow_log_count" -gt 0 ]; then
        echo -e "${GREEN}✓ $flow_log_count active flow log(s)${NC}"
        return 0
    else
        echo -e "${RED}✗ No active flow logs${NC}"
        return 1
    fi
}

# Function to check EC2 instances with CloudWatch Agent
check_cloudwatch_agent() {
    echo "Checking CloudWatch Agent on EC2 instances..."
    
    instance_ids=$(aws ec2 describe-instances \
        --region "$REGION" \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[].InstanceId' \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$instance_ids" ]; then
        echo -e "${YELLOW}⚠ No running instances found${NC}"
        return 1
    fi
    
    for instance_id in $instance_ids; do
        instance_name=$(aws ec2 describe-instances \
            --instance-ids "$instance_id" \
            --region "$REGION" \
            --query 'Reservations[0].Instances[0].Tags[?Key==`Name`].Value | [0]' \
            --output text 2>/dev/null || echo "Unknown")
        
        echo -n "  Instance: $instance_name ($instance_id)... "
        
        # Check if CloudWatch Agent is installed via SSM
        agent_status=$(aws ssm send-command \
            --instance-ids "$instance_id" \
            --document-name "AWS-RunShellScript" \
            --parameters 'commands=["systemctl is-active amazon-cloudwatch-agent"]' \
            --region "$REGION" \
            --query 'Command.CommandId' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$agent_status" ]; then
            echo -e "${GREEN}✓ Agent check initiated${NC}"
        else
            echo -e "${YELLOW}⚠ Cannot verify (SSM may not be ready)${NC}"
        fi
    done
}

# Function to show sample logs
show_sample_logs() {
    local log_group=$1
    local description=$2
    
    echo ""
    echo "Sample logs from $description:"
    echo "----------------------------------------"
    
    aws logs tail "$log_group" \
        --region "$REGION" \
        --since 1h \
        --format short \
        --max-items 5 2>/dev/null || echo "No logs available"
    
    echo "----------------------------------------"
}

# Main checks
echo "1. LOG GROUPS"
echo "----------------------------------------"
check_log_group "/aws/vpc/flowlogs" "VPC Flow Logs"
check_log_group "/aws/cloudtrail/logs" "CloudTrail Logs"
check_log_group "/aws/ec2/applogs" "Application Logs (App Tier)"
check_log_group "/aws/ec2/weblogs" "Web Logs (Web Tier)"
echo ""

echo "2. CLOUDTRAIL"
echo "----------------------------------------"
check_cloudtrail
echo ""

echo "3. VPC FLOW LOGS"
echo "----------------------------------------"
check_vpc_flow_logs
echo ""

echo "4. CLOUDWATCH AGENT"
echo "----------------------------------------"
check_cloudwatch_agent
echo ""

# Ask if user wants to see sample logs
echo ""
read -p "Do you want to see sample logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    show_sample_logs "/aws/vpc/flowlogs" "VPC Flow Logs"
    show_sample_logs "/aws/cloudtrail/logs" "CloudTrail"
fi

echo ""
echo "=========================================="
echo "Verification Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If logs are not appearing yet, wait 5-10 minutes"
echo "2. Generate some traffic to create logs"
echo "3. Check CloudWatch Console: https://console.aws.amazon.com/cloudwatch/home?region=$REGION#logsV2:log-groups"
echo "4. For detailed verification, see: CLOUDWATCH_VERIFICATION.md"
