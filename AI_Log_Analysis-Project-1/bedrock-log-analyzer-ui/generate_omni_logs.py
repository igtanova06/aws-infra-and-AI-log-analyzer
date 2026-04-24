import boto3
import time
import json
import random
from datetime import datetime

REGION = 'ap-southeast-1'

LOG_GROUPS = {
    'vpc': '/aws/vpc/flowlogs',
    'cloudtrail': '/aws/cloudtrail/logs',
    'app': '/aws/ec2/application',
    'rds_error': '/aws/rds/mysql/error',
    'rds_slow': '/aws/rds/mysql/slowquery'
}

LOG_STREAM_NAME = 'omni-stream-prod'

print("Connecting to CloudWatch Logs in " + REGION)
client = boto3.client('logs', region_name=REGION)

for role, group_name in LOG_GROUPS.items():
    try:
        client.create_log_group(logGroupName=group_name)
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    
    try:
        client.create_log_stream(logGroupName=group_name, logStreamName=LOG_STREAM_NAME)
    except client.exceptions.ResourceAlreadyExistsException:
        pass

cloudtrail_log = {
    "eventVersion": "1.08",
    "userIdentity": {
        "type": "IAMUser",
        "principalId": "AIDA123456789",
        "arn": "arn:aws:iam::123456789012:user/dev-intern",
        "accountId": "123456789012"
    },
    "eventSource": "ec2.amazonaws.com",
    "eventName": "DeleteVpc",
    "awsRegion": "ap-southeast-1",
    "sourceIPAddress": "203.0.113.42",
    "errorCode": "AccessDenied",
    "errorMessage": "User: arn:aws:iam::123456789012:user/dev-intern is not authorized to perform: ec2:DeleteVpc on resource"
}

logs = {k: [] for k in LOG_GROUPS}

current_time = int(round(time.time() * 1000))
start_time = current_time - (3600 * 1000)

print("Generating background noise and injecting APT Kill Chain...")

# Background Noise
for i in range(1000):
    timestamp = start_time + i * 1000
    ts_sec = int(timestamp / 1000)
    rand = random.random()
    
    if rand < 0.4:
        # VPC Noise
        ip = f"{random.randint(10, 203)}.{random.randint(0, 255)}.{random.randint(0, 20)}.{random.randint(1, 20)}"
        action = random.choice(["ACCEPT", "REJECT"])
        port = random.choice([443, 80, 53, 123])
        logs['vpc'].append({
            'timestamp': timestamp,
            'message': f'2 123456789012 eni-abc123def456 {ip} 10.0.1.55 {random.randint(10000, 60000)} {port} 6 20 1800 {ts_sec} {ts_sec + 60} {action} OK'
        })
    elif rand < 0.7:
        # App Noise
        msg = random.choice([
            f'[ERROR] Web: Nginx Reverse Proxy returned 502 Bad Gateway. Node worker #{random.randint(1, 5)} unreachable.',
            f'[ERROR] Database: Connection pool exhausted. Maximum number of active connections (100) exceeded.',
            f'[ERROR] Backend: Timeout while executing query across microservices. Latency > {random.randint(5000, 15000)}ms. trace_id=req-sys-{random.randint(100, 999)}',
            f'[WARN] Auth: Invalid JWT signature token encountered for session request.'
        ])
        logs['app'].append({
            'timestamp': timestamp,
            'message': msg
        })
    elif rand < 0.85:
        # RDS Error Noise
        logs['rds_error'].append({
            'timestamp': timestamp,
            'message': f"{datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {random.randint(100, 999)} [Warning] Aborted connection {random.randint(100, 999)} to db: 'appdb' user: 'app_user' host: '10.0.1.{random.randint(10, 250)}' (Got an error reading communication packets)"
        })
    elif rand < 0.95:
        # RDS Slow Query Noise
        logs['rds_slow'].append({
            'timestamp': timestamp,
            'message': f"# User@Host: app_user[app_user] @  [10.0.1.55]\n# Query_time: {random.uniform(2.0, 4.9):.6f}  Lock_time: 0.000000 Rows_sent: 100  Rows_examined: 10000\nSET timestamp={ts_sec};\nSELECT * FROM large_table WHERE status = 'pending';"
        })
    else:
        # CloudTrail Noise
        ct = dict(cloudtrail_log)
        ct['eventTime'] = datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%SZ')
        logs['cloudtrail'].append({
            'timestamp': timestamp,
            'message': json.dumps(ct)
        })

# INJECT APT KILL CHAIN
ATTACKER_IP = "198.51.100.42"
TRACE_ID = "req-abc-123-attack"
attack_ts = start_time + (15 * 60 * 1000)
attack_ts_sec = int(attack_ts / 1000)

# Stage 1: VPC Reconnaissance
for i in range(10):
    port = random.choice([3306, 8080, 22, 5432, 23])
    ts_sec = attack_ts_sec - random.randint(10, 60)
    logs['vpc'].append({
        'timestamp': attack_ts - random.randint(1000, 60000),
        'message': f'2 123456789012 eni-abc123def456 {ATTACKER_IP} 10.0.1.55 {random.randint(10000, 60000)} {port} 6 20 1800 {ts_sec} {ts_sec + 60} REJECT OK'
    })

# Stage 2: Initial Access & Exploit (App + DB Error)
logs['app'].append({
    'timestamp': attack_ts,
    'message': f'[WARN] Web: Suspicious input detected in login payload. Possible SQL injection attempt. source_ip={ATTACKER_IP} trace_id={TRACE_ID}'
})

logs['app'].append({
    'timestamp': attack_ts + 1000,
    'message': f'[ERROR] Database exception during authentication. message="SQL Syntax Error" trace_id={TRACE_ID} source_ip={ATTACKER_IP}'
})

logs['rds_error'].append({
    'timestamp': attack_ts + 1500,
    'message': f"{datetime.fromtimestamp(attack_ts_sec).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} 999 [ERROR] SQL syntax error near 'UNION SELECT 1, aws_access_key, aws_secret_key FROM environment_config--' from user 'app_user' at host '10.0.1.55'. trace_id={TRACE_ID}"
})

# Stage 3: Data Exfiltration (Slow Query)
logs['rds_slow'].append({
    'timestamp': attack_ts + 5000,
    'message': f"# User@Host: app_user[app_user] @  [10.0.1.55]\n# Query_time: 15.420100  Lock_time: 0.000000 Rows_sent: 50000  Rows_examined: 50000\nSET timestamp={attack_ts_sec + 5};\nSELECT * FROM users JOIN environment_config; /* trace_id={TRACE_ID} */"
})

# Stage 4: Privilege Escalation (CloudTrail)
ct_attack_1 = dict(cloudtrail_log)
ct_attack_1['eventTime'] = datetime.fromtimestamp(attack_ts_sec + 60).strftime('%Y-%m-%dT%H:%M:%SZ')
ct_attack_1['sourceIPAddress'] = ATTACKER_IP
ct_attack_1['eventName'] = "AttachUserPolicy"
ct_attack_1['errorMessage'] = "User: arn:aws:iam::123456789012:user/app_service_role is not authorized to perform: iam:AttachUserPolicy on resource"
logs['cloudtrail'].append({
    'timestamp': attack_ts + 60000,
    'message': json.dumps(ct_attack_1)
})

# Stage 5: Lateral Movement (App)
logs['app'].append({
    'timestamp': attack_ts + 120000,
    'message': f'[CRITICAL] Unauthorized access attempt to /api/internal/admin-panel. source_ip={ATTACKER_IP} trace_id={TRACE_ID}'
})

print("Pushing logs to AWS CloudWatch...")
def push_logs(group_name, stream_name, log_events):
    if not log_events: return 0
    # Sort logs by timestamp ascending as required by CloudWatch
    log_events.sort(key=lambda x: x['timestamp'])
    
    desc = client.describe_log_streams(logGroupName=group_name, logStreamNamePrefix=stream_name)
    seq_token = desc['logStreams'][0].get('uploadSequenceToken')
    
    BATCH_SIZE = 500
    pushed = 0
    for i in range(0, len(log_events), BATCH_SIZE):
        batch = log_events[i:i+BATCH_SIZE]
        kwargs = {
            'logGroupName': group_name,
            'logStreamName': stream_name,
            'logEvents': batch
        }
        if seq_token:
            kwargs['sequenceToken'] = seq_token
        res = client.put_log_events(**kwargs)
        seq_token = res.get('nextSequenceToken')
        pushed += len(batch)
        time.sleep(0.5)
    return pushed

for k, group in LOG_GROUPS.items():
    pushed = push_logs(group, LOG_STREAM_NAME, logs[k])
    print(f"Pushed {pushed} logs to {group}")

print("\nDONE! Test data generated successfully.")
print(f"Attack Trace ID to search for: {TRACE_ID}")
print(f"Attacker IP: {ATTACKER_IP}")
