import boto3
import time

log_group_name = '/aws/lambda/my-function'
log_stream_name = 'test-stream-error'
region = 'ap-southeast-1'

print("Connecting to CloudWatch Logs in " + region)
client = boto3.client('logs', region_name=region)

try:
    client.create_log_group(logGroupName=log_group_name)
    print("Created Log Group: " + log_group_name)
except client.exceptions.ResourceAlreadyExistsException:
    print("Log Group already exists.")

try:
    client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    print("Created Log Stream: " + log_stream_name)
except client.exceptions.ResourceAlreadyExistsException:
    print("Log Stream already exists.")

timestamp = int(round(time.time() * 1000))

log_events = [
    {
        'timestamp': timestamp,
        'message': '[INFO] System started successfully and ready to process new transactions.'
    },
    {
        'timestamp': timestamp + 1000,
        'message': '[WARNING] SSH: Failed password for invalid user admin from 192.168.1.100 port 44321 ssh2'
    },
    {
        'timestamp': timestamp + 2000,
        'message': '[WARNING] SSH: Failed password for invalid user root from 192.168.1.100 port 44321 ssh2'
    },
    {
        'timestamp': timestamp + 3000,
        'message': '[WARNING] SSH: Failed password for invalid user ubuntu from 192.168.1.100 port 44321 ssh2'
    },
    {
        'timestamp': timestamp + 4000,
        'message': '[WARNING] SSH: Failed password for invalid user ec2-user from 192.168.1.100 port 44321 ssh2'
    },
    {
        'timestamp': timestamp + 5000,
        'message': '[CRITICAL] SSH: Accepted password for root from 192.168.1.100 port 44321 ssh2. Possible brute force success.'
    },
    {
        'timestamp': timestamp + 6000,
        'message': '[ERROR] App: Unauthorized privilege escalation attempt detected. User root accessed sensitive credentials database.'
    }
]

kwargs = {
    'logGroupName': log_group_name,
    'logStreamName': log_stream_name,
    'logEvents': log_events,
}

response = client.describe_log_streams(logGroupName=log_group_name, logStreamNamePrefix=log_stream_name)
if 'uploadSequenceToken' in response['logStreams'][0]:
    kwargs['sequenceToken'] = response['logStreams'][0]['uploadSequenceToken']

response = client.put_log_events(**kwargs)

print(f"Successfully pushed {len(log_events)} log events to CloudWatch!")
