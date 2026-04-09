import boto3
import time
import json
import random

REGION = 'ap-southeast-1'

# 3 Log Groups riêng rẽ
LOG_GROUPS = {
    'vpc': '/aws/vpc/flowlogs',
    'cloudtrail': '/aws/cloudtrail/logs',
    'app': '/aws/ec2/applogs'
}

LOG_STREAM_NAME = 'omni-stream-prod'

print("Connecting to CloudWatch Logs in " + REGION)
client = boto3.client('logs', region_name=REGION)

# Khởi tạo 3 Log Groups nếu chưa có
for role, group_name in LOG_GROUPS.items():
    try:
        client.create_log_group(logGroupName=group_name)
        print(f"Created Group: {group_name}")
    except client.exceptions.ResourceAlreadyExistsException:
        pass
    
    try:
        client.create_log_stream(logGroupName=group_name, logStreamName=LOG_STREAM_NAME)
        print(f"  Created Stream: {LOG_STREAM_NAME}")
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
    "eventTime": "2026-04-06T21:44:22Z",
    "eventSource": "ec2.amazonaws.com",
    "eventName": "DeleteVpc",
    "awsRegion": "ap-southeast-1",
    "sourceIPAddress": "203.0.113.42",
    "errorCode": "AccessDenied",
    "errorMessage": "User: arn:aws:iam::123456789012:user/dev-intern is not authorized to perform: ec2:DeleteVpc on resource"
}

vpc_logs = []
ct_logs = []
app_logs = []

current_time = int(round(time.time() * 1000))
start_time = current_time - (3600 * 1000)

print("Generating 1000 logs into 3 branches...")
for i in range(1000):
    timestamp = start_time + i * 1000
    rand = random.random()
    
    if rand < 0.7:
        ip = f"{random.randint(10, 203)}.{random.randint(0, 255)}.{random.randint(0, 20)}.{random.randint(1, 20)}"
        vpc_logs.append({
            'timestamp': timestamp,
            'message': f'2 123456789012 eni-abc123def456 {ip} 10.0.1.55 {random.randint(10000, 60000)} 22 6 20 1800 1620140600 1620140660 REJECT OK'
        })
    elif rand < 0.9:
        comps = ['Web', 'Database', 'Backend', 'Auth']
        comp = random.choice(comps)
        
        if comp == 'Web':
            msg = f'[ERROR] Web: Nginx Reverse Proxy returned 502 Bad Gateway. Node worker #{random.randint(1, 5)} unreachable.'
        elif comp == 'Database':
            msg = f'[ERROR] Database: Connection pool exhausted. Maximum number of active connections (100) exceeded.'
        elif comp == 'Backend':
            msg = f'[ERROR] Backend: Timeout while executing query across microservices. Latency > 10000ms.'
        else:
            msg = f'[ERROR] Auth: Invalid JWT signature token encountered for session request.'
            
        app_logs.append({
            'timestamp': timestamp,
            'message': msg
        })
    else:
        ct = dict(cloudtrail_log)
        ct['eventTime'] = f"2026-04-06T{random.randint(10,23):02d}:{random.randint(10,59):02d}:22Z"
        ct_logs.append({
            'timestamp': timestamp,
            'message': json.dumps(ct)
        })

def push_logs(group_name, stream_name, log_events):
    if not log_events:
        return 0
    # Lấy sequence token
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

print("Pushing VPC Flow logs...")
vpc_pushed = push_logs(LOG_GROUPS['vpc'], LOG_STREAM_NAME, vpc_logs)
print("Pushing Application logs...")
app_pushed = push_logs(LOG_GROUPS['app'], LOG_STREAM_NAME, app_logs)
print("Pushing CloudTrail logs...")
ct_pushed = push_logs(LOG_GROUPS['cloudtrail'], LOG_STREAM_NAME, ct_logs)

print(f"DONE! Pushed: VPC={vpc_pushed}, App={app_pushed}, CloudTrail={ct_pushed}.")
