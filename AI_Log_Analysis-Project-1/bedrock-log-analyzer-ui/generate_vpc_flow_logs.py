#!/usr/bin/env python3
"""
Generate VPC Flow Logs for testing
Simulates various network attack patterns
"""
import boto3
import time
from datetime import datetime
import random

# Configuration
LOG_GROUP_NAME = "/aws/vpc/flowlogs"
REGION = "ap-southeast-1"

# Attack scenarios
ATTACK_IPS = [
    "203.0.113.42",  # Suspicious IP 1
    "198.51.100.88", # Suspicious IP 2
    "192.0.2.123",   # Suspicious IP 3
]

INTERNAL_IPS = [
    "10.0.4.10",
    "10.0.4.11",
    "10.0.5.10",
    "10.0.5.11",
]

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

def generate_vpc_flow_log(source_ip, dest_ip, dest_port, action, protocol=6):
    """
    Generate VPC Flow Log entry
    Format: version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
    """
    timestamp = int(time.time())
    return (
        f"2 123456789012 eni-abc123 {source_ip} {dest_ip} "
        f"{random.randint(40000, 65000)} {dest_port} {protocol} "
        f"{random.randint(1, 100)} {random.randint(100, 10000)} "
        f"{timestamp - 60} {timestamp} {action} OK"
    )

def main():
    print("🚀 Starting VPC Flow Logs Generator...")
    
    client = boto3.client('logs', region_name=REGION)
    
    # Create log group and stream
    create_log_group_if_not_exists(client, LOG_GROUP_NAME)
    
    stream_name = f"test-stream-{int(time.time())}"
    create_log_stream(client, LOG_GROUP_NAME, stream_name)
    
    logs = []
    timestamp = int(time.time() * 1000)
    
    print("\n📝 Generating attack scenarios...")
    
    # Scenario 1: SSH Brute Force Attack (50 attempts)
    print("  🔴 Scenario 1: SSH Brute Force Attack")
    for i in range(50):
        log = generate_vpc_flow_log(
            source_ip=random.choice(ATTACK_IPS),
            dest_ip=random.choice(INTERNAL_IPS),
            dest_port=22,
            action="REJECT"
        )
        logs.append({
            'timestamp': timestamp + i * 1000,
            'message': log
        })
    
    # Scenario 2: RDP Brute Force Attack (30 attempts)
    print("  🔴 Scenario 2: RDP Brute Force Attack")
    for i in range(30):
        log = generate_vpc_flow_log(
            source_ip=random.choice(ATTACK_IPS),
            dest_ip=random.choice(INTERNAL_IPS),
            dest_port=3389,
            action="REJECT"
        )
        logs.append({
            'timestamp': timestamp + (50 + i) * 1000,
            'message': log
        })
    
    # Scenario 3: Port Scanning (multiple ports)
    print("  🔴 Scenario 3: Port Scanning")
    suspicious_ports = [21, 23, 25, 80, 443, 3306, 5432, 6379, 27017]
    for port in suspicious_ports:
        for i in range(5):
            log = generate_vpc_flow_log(
                source_ip=ATTACK_IPS[0],
                dest_ip=INTERNAL_IPS[0],
                dest_port=port,
                action="REJECT"
            )
            logs.append({
                'timestamp': timestamp + (80 + len(logs)) * 1000,
                'message': log
            })
    
    # Scenario 4: Normal traffic (ACCEPT)
    print("  ✅ Scenario 4: Normal Traffic")
    for i in range(20):
        log = generate_vpc_flow_log(
            source_ip="10.0.1.100",
            dest_ip=random.choice(INTERNAL_IPS),
            dest_port=random.choice([80, 443]),
            action="ACCEPT"
        )
        logs.append({
            'timestamp': timestamp + (len(logs)) * 1000,
            'message': log
        })
    
    # Scenario 5: Database Connection Attempts (REJECT)
    print("  🔴 Scenario 5: Unauthorized Database Access")
    for i in range(15):
        log = generate_vpc_flow_log(
            source_ip=random.choice(ATTACK_IPS),
            dest_ip=INTERNAL_IPS[0],
            dest_port=5432,  # PostgreSQL
            action="REJECT"
        )
        logs.append({
            'timestamp': timestamp + (len(logs)) * 1000,
            'message': log
        })
    
    # Send logs to CloudWatch
    print(f"\n📤 Sending {len(logs)} log entries to CloudWatch...")
    
    # CloudWatch has a limit of 10,000 events per batch
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
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"  ❌ Error sending batch: {e}")
    
    print(f"\n✅ Successfully generated {len(logs)} VPC Flow Logs!")
    print(f"📊 Log Group: {LOG_GROUP_NAME}")
    print(f"📊 Log Stream: {stream_name}")
    print("\n🔍 Summary:")
    print(f"  - SSH Brute Force: 50 REJECT events")
    print(f"  - RDP Brute Force: 30 REJECT events")
    print(f"  - Port Scanning: {len(suspicious_ports) * 5} REJECT events")
    print(f"  - Database Access: 15 REJECT events")
    print(f"  - Normal Traffic: 20 ACCEPT events")
    print(f"\n💡 Now run the Streamlit app and search for 'REJECT' to see the analysis!")

if __name__ == "__main__":
    main()
