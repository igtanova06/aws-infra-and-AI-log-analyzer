#!/usr/bin/env python3
"""
Generate CloudTrail-like logs for testing
Simulates security events and suspicious API calls
"""
import boto3
import time
import json
from datetime import datetime

# Configuration
LOG_GROUP_NAME = "/aws/cloudtrail/logs"
REGION = "ap-southeast-1"

def create_log_group_if_not_exists(client, log_group_name):
    """Create log group if it doesn't exist"""
    try:
        client.create_log_group(logGroupName=log_group_name)
        print(f"✅ Created log group: {log_group_name}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"ℹ️  Log group already exists: {log_group_name}")

def create_log_stream(client, log_group_name, stream_name):
    """Create log stream"""
    try:
        client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=stream_name
        )
        print(f"✅ Created log stream: {stream_name}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"ℹ️  Log stream already exists: {stream_name}")

def generate_cloudtrail_event(event_name, error_code=None, user_arn=None, source_ip=None):
    """Generate CloudTrail event JSON"""
    event = {
        "eventVersion": "1.08",
        "userIdentity": {
            "type": "IAMUser",
            "principalId": "AIDAI23HXS4EXAMPLE",
            "arn": user_arn or "arn:aws:iam::123456789012:user/dev-intern",
            "accountId": "123456789012",
            "userName": "dev-intern"
        },
        "eventTime": datetime.utcnow().isoformat() + "Z",
        "eventSource": "ec2.amazonaws.com",
        "eventName": event_name,
        "awsRegion": REGION,
        "sourceIPAddress": source_ip or "203.0.113.42",
        "userAgent": "aws-cli/2.13.0",
        "requestParameters": {},
        "responseElements": None,
        "requestID": f"example-request-{int(time.time())}",
        "eventID": f"example-event-{int(time.time())}",
        "readOnly": False,
        "eventType": "AwsApiCall",
        "managementEvent": True,
        "recipientAccountId": "123456789012"
    }
    
    if error_code:
        event["errorCode"] = error_code
        event["errorMessage"] = f"{error_code}: User is not authorized to perform this action"
    
    return json.dumps(event)

def main():
    print("🚀 Starting CloudTrail Logs Generator...")
    
    client = boto3.client('logs', region_name=REGION)
    
    # Create log group and stream
    create_log_group_if_not_exists(client, LOG_GROUP_NAME)
    
    stream_name = f"test-stream-{int(time.time())}"
    create_log_stream(client, LOG_GROUP_NAME, stream_name)
    
    logs = []
    timestamp = int(time.time() * 1000)
    
    print("\n📝 Generating security event scenarios...")
    
    # Scenario 1: Privilege Escalation Attempts
    print("  🔴 Scenario 1: Privilege Escalation Attempts")
    escalation_actions = [
        "CreateUser",
        "AttachUserPolicy",
        "PutUserPolicy",
        "CreateAccessKey",
        "UpdateAssumeRolePolicy"
    ]
    for i, action in enumerate(escalation_actions):
        for attempt in range(3):
            log = generate_cloudtrail_event(
                event_name=action,
                error_code="AccessDenied",
                user_arn="arn:aws:iam::123456789012:user/dev-intern"
            )
            logs.append({
                'timestamp': timestamp + (i * 3 + attempt) * 1000,
                'message': log
            })
    
    # Scenario 2: Resource Deletion Attempts
    print("  🔴 Scenario 2: Unauthorized Resource Deletion")
    deletion_actions = [
        "DeleteVpc",
        "DeleteSubnet",
        "DeleteSecurityGroup",
        "TerminateInstances",
        "DeleteDBInstance"
    ]
    for i, action in enumerate(deletion_actions):
        for attempt in range(2):
            log = generate_cloudtrail_event(
                event_name=action,
                error_code="AccessDenied",
                user_arn="arn:aws:iam::123456789012:user/contractor"
            )
            logs.append({
                'timestamp': timestamp + (len(logs)) * 1000,
                'message': log
            })
    
    # Scenario 3: Root Account Usage (CRITICAL)
    print("  🔴 Scenario 3: Root Account Usage")
    root_actions = ["ConsoleLogin", "GetCallerIdentity", "ListUsers"]
    for action in root_actions:
        log = generate_cloudtrail_event(
            event_name=action,
            user_arn="arn:aws:iam::123456789012:root"
        )
        # Modify to show root user
        log_dict = json.loads(log)
        log_dict["userIdentity"]["type"] = "Root"
        log_dict["userIdentity"]["userName"] = "root"
        logs.append({
            'timestamp': timestamp + (len(logs)) * 1000,
            'message': json.dumps(log_dict)
        })
    
    # Scenario 4: Console Login Failures (Brute Force)
    print("  🔴 Scenario 4: Console Login Brute Force")
    suspicious_ips = ["203.0.113.42", "198.51.100.88", "192.0.2.123"]
    for i in range(10):
        log = generate_cloudtrail_event(
            event_name="ConsoleLogin",
            error_code="Failed authentication",
            source_ip=suspicious_ips[i % len(suspicious_ips)]
        )
        logs.append({
            'timestamp': timestamp + (len(logs)) * 1000,
            'message': log
        })
    
    # Scenario 5: Successful Actions (Normal)
    print("  ✅ Scenario 5: Normal API Calls")
    normal_actions = ["DescribeInstances", "DescribeSecurityGroups", "GetObject"]
    for action in normal_actions:
        for i in range(3):
            log = generate_cloudtrail_event(
                event_name=action,
                user_arn="arn:aws:iam::123456789012:user/admin"
            )
            logs.append({
                'timestamp': timestamp + (len(logs)) * 1000,
                'message': log
            })
    
    # Scenario 6: Data Exfiltration Attempt
    print("  🔴 Scenario 6: Suspicious S3 Access")
    for i in range(5):
        log = generate_cloudtrail_event(
            event_name="GetObject",
            source_ip="203.0.113.42",
            user_arn="arn:aws:iam::123456789012:user/temp-contractor"
        )
        logs.append({
            'timestamp': timestamp + (len(logs)) * 1000,
            'message': log
        })
    
    # Send logs to CloudWatch
    print(f"\n📤 Sending {len(logs)} log entries to CloudWatch...")
    
    batch_size = 100
    for i in range(0, len(logs), batch_size):
        batch = logs[i:i + batch_size]
        try:
            client.put_log_events(
                logGroupName=LOG_GROUP_NAME,
                logStreamName=stream_name,
                logEvents=batch
            )
            print(f"  ✅ Sent batch {i//batch_size + 1}/{(len(logs)-1)//batch_size + 1}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ❌ Error sending batch: {e}")
    
    print(f"\n✅ Successfully generated {len(logs)} CloudTrail events!")
    print(f"📊 Log Group: {LOG_GROUP_NAME}")
    print(f"📊 Log Stream: {stream_name}")
    print("\n🔍 Summary:")
    print(f"  - Privilege Escalation: {len(escalation_actions) * 3} AccessDenied events")
    print(f"  - Resource Deletion: {len(deletion_actions) * 2} AccessDenied events")
    print(f"  - Root Account Usage: {len(root_actions)} events (CRITICAL)")
    print(f"  - Login Failures: 10 events")
    print(f"  - Normal Actions: {len(normal_actions) * 3} events")
    print(f"  - S3 Access: 5 events")
    print(f"\n💡 Now run the Streamlit app and search for 'AccessDenied' to see the analysis!")

if __name__ == "__main__":
    main()
