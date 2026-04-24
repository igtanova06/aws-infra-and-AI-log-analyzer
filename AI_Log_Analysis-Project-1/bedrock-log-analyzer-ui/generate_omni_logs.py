"""
Mock Log Generator for AI Log Analysis Testing
Generates realistic attack scenarios in CloudWatch Logs for testing AI detection.

Attack Scenario: DDoS/DoS Attack
- Stage 1: Reconnaissance (port scanning)
- Stage 2: Initial flood (SYN flood)
- Stage 3: Application layer attack (HTTP flood)
- Stage 4: Resource exhaustion (connection pool, memory)
- Stage 5: Service degradation (slow queries, timeouts)

Usage:
    python generate_omni_logs.py
"""
import boto3
import time
import json
import random
from datetime import datetime
import argparse

# Configuration
REGION = 'ap-southeast-1'

LOG_GROUPS = {
    'vpc': '/aws/vpc/flowlogs',
    'cloudtrail': '/aws/cloudtrail/logs',
    'app': '/aws/ec2/application',
    'rds_error': '/aws/rds/mysql/error',
    'rds_slow': '/aws/rds/mysql/slowquery'
}

LOG_STREAM_NAME = 'mock-attack-stream'

print("=" * 70)
print("🚨 MOCK LOG GENERATOR - DDoS/DoS ATTACK SCENARIO")
print("=" * 70)
print(f"Region: {REGION}")
print(f"Log Stream: {LOG_STREAM_NAME}")
print("=" * 70)

print("\n📡 Connecting to CloudWatch Logs...")
client = boto3.client('logs', region_name=REGION)

# Create log groups and streams
for role, group_name in LOG_GROUPS.items():
    try:
        client.create_log_group(logGroupName=group_name)
        print(f"  ✅ Created log group: {group_name}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"  ℹ️  Log group exists: {group_name}")
    
    try:
        client.create_log_stream(logGroupName=group_name, logStreamName=LOG_STREAM_NAME)
        print(f"  ✅ Created log stream: {LOG_STREAM_NAME}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"  ℹ️  Log stream exists: {LOG_STREAM_NAME}")

# CloudTrail template
cloudtrail_log = {
    "eventVersion": "1.08",
    "userIdentity": {
        "type": "IAMUser",
        "principalId": "AIDA123456789",
        "arn": "arn:aws:iam::123456789012:user/app-service",
        "accountId": "123456789012"
    },
    "eventSource": "ec2.amazonaws.com",
    "eventName": "DescribeInstances",
    "awsRegion": "ap-southeast-1",
    "sourceIPAddress": "10.0.1.55",
    "errorCode": None,
    "errorMessage": None
}

logs = {k: [] for k in LOG_GROUPS}

current_time = int(round(time.time() * 1000))
start_time = current_time - (30 * 60 * 1000)  # 30 minutes ago

print("\n📊 Generating logs...")
print("  - Background noise: 500 events")
print("  - DDoS attack: 5 stages")
print("  - Time window: 30 minutes")

# ============================================================
# BACKGROUND NOISE (Normal Operations)
# ============================================================
print("\n🔊 Generating background noise...")
for i in range(500):
    timestamp = start_time + i * 2000  # Every 2 seconds
    ts_sec = int(timestamp / 1000)
    rand = random.random()
    
    if rand < 0.4:
        # VPC Normal Traffic
        ip = f"10.0.{random.randint(1, 3)}.{random.randint(10, 250)}"
        port = random.choice([443, 80, 8080])
        logs['vpc'].append({
            'timestamp': timestamp,
            'message': f'2 123456789012 eni-abc123def456 {ip} 10.0.1.55 {random.randint(10000, 60000)} {port} 6 5 500 {ts_sec} {ts_sec + 1} ACCEPT OK'
        })
    elif rand < 0.7:
        # App Normal Logs
        msg = random.choice([
            '[INFO] Web: Request processed successfully. path=/api/students_list status=200 duration=45ms',
            '[INFO] Auth: User login successful. user=student123 session_id=sess-' + str(random.randint(1000, 9999)),
            '[INFO] Database: Query executed. table=students rows=25 duration=12ms',
        ])
        logs['app'].append({
            'timestamp': timestamp,
            'message': msg
        })
    elif rand < 0.85:
        # RDS Normal Operations
        logs['rds_error'].append({
            'timestamp': timestamp,
            'message': f"{datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {random.randint(100, 999)} [Note] Connection established from 10.0.1.55"
        })
    else:
        # CloudTrail Normal API Calls
        ct = dict(cloudtrail_log)
        ct['eventTime'] = datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%SZ')
        ct['eventName'] = random.choice(['DescribeInstances', 'GetObject', 'ListBuckets'])
        logs['cloudtrail'].append({
            'timestamp': timestamp,
            'message': json.dumps(ct)
        })

print(f"  ✅ Generated {sum(len(v) for v in logs.values())} background events")

# ============================================================
# DDOS/DOS ATTACK SCENARIO
# ============================================================
print("\n🚨 Injecting DDoS/DoS attack scenario...")

ATTACKER_IPS = [
    "203.0.113.42",   # Primary attacker
    "203.0.113.43",   # Botnet node 1
    "203.0.113.44",   # Botnet node 2
    "198.51.100.10",  # Botnet node 3
    "198.51.100.11",  # Botnet node 4
]
TRACE_ID = "req-ddos-attack-001"
attack_start = start_time + (10 * 60 * 1000)  # Attack starts at minute 10

# ============================================================
# STAGE 1: RECONNAISSANCE (Minute 10-11)
# ============================================================
print("  📍 Stage 1: Reconnaissance (port scanning)")
recon_start = attack_start
for i in range(15):
    attacker_ip = random.choice(ATTACKER_IPS[:2])  # Only 2 IPs for recon
    port = random.choice([80, 443, 8080, 22, 3306, 3389])
    ts = recon_start + (i * 2000)
    ts_sec = int(ts / 1000)
    
    logs['vpc'].append({
        'timestamp': ts,
        'message': f'2 123456789012 eni-abc123def456 {attacker_ip} 10.0.1.55 {random.randint(10000, 60000)} {port} 6 1 40 {ts_sec} {ts_sec + 1} REJECT OK'
    })

# ============================================================
# STAGE 2: SYN FLOOD (Minute 11-13) - HIGH VOLUME
# ============================================================
print("  📍 Stage 2: SYN Flood (network layer attack)")
syn_flood_start = attack_start + (60 * 1000)
for i in range(200):  # 200 SYN packets in 2 minutes
    attacker_ip = random.choice(ATTACKER_IPS)
    ts = syn_flood_start + (i * 600)  # Every 0.6 seconds
    ts_sec = int(ts / 1000)
    
    logs['vpc'].append({
        'timestamp': ts,
        'message': f'2 123456789012 eni-abc123def456 {attacker_ip} 10.0.1.55 {random.randint(10000, 60000)} 80 6 1 40 {ts_sec} {ts_sec} REJECT OK'
    })

# ============================================================
# STAGE 3: HTTP FLOOD (Minute 13-16) - APPLICATION LAYER
# ============================================================
print("  📍 Stage 3: HTTP Flood (application layer attack)")
http_flood_start = attack_start + (3 * 60 * 1000)

# VPC accepts (connections established)
for i in range(150):
    attacker_ip = random.choice(ATTACKER_IPS)
    ts = http_flood_start + (i * 1200)  # Every 1.2 seconds
    ts_sec = int(ts / 1000)
    
    logs['vpc'].append({
        'timestamp': ts,
        'message': f'2 123456789012 eni-abc123def456 {attacker_ip} 10.0.1.55 {random.randint(10000, 60000)} 8080 6 50 5000 {ts_sec} {ts_sec + 1} ACCEPT OK'
    })

# Application logs (HTTP requests)
for i in range(150):
    attacker_ip = random.choice(ATTACKER_IPS)
    ts = http_flood_start + (i * 1200)
    path = random.choice(['/api/students_list', '/api/login', '/api/me', '/'])
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[WARN] Web: High request rate detected. source_ip={attacker_ip} path={path} user_agent=Mozilla/5.0 (compatible; DDoSBot/1.0)'
    })

# ============================================================
# STAGE 4: RESOURCE EXHAUSTION (Minute 16-18)
# ============================================================
print("  📍 Stage 4: Resource Exhaustion (connection pool, memory)")
resource_exhaustion_start = attack_start + (6 * 60 * 1000)

# Connection pool exhaustion (ENHANCED with more details)
for i in range(20):
    ts = resource_exhaustion_start + (i * 3000)
    ts_sec = int(ts / 1000)
    waiting_conns = random.randint(50, 200)
    
    # Application layer - Connection pool errors
    logs['app'].append({
        'timestamp': ts,
        'message': f'[ERROR] ConnectionPool: Pool exhausted. active=100/100 idle=0 waiting={waiting_conns} max_wait_time=30000ms trace_id={TRACE_ID}'
    })
    
    # Application layer - Thread pool exhaustion
    logs['app'].append({
        'timestamp': ts + 200,
        'message': f'[ERROR] ThreadPool: All worker threads busy. active=200/200 queued={random.randint(100, 500)} rejected={random.randint(10, 50)} trace_id={TRACE_ID}'
    })
    
    # Database layer - Too many connections
    logs['rds_error'].append({
        'timestamp': ts + 500,
        'message': f"{datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {random.randint(100, 999)} [ERROR] [MY-010069] Too many connections. Current: 100, Max: 100, Rejected: {random.randint(5, 20)}"
    })
    
    # Database layer - Connection refused
    logs['rds_error'].append({
        'timestamp': ts + 800,
        'message': f"{datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {random.randint(100, 999)} [ERROR] [MY-010051] Connection refused from 10.0.1.55: max_connections reached"
    })

# Memory exhaustion (ENHANCED with metrics)
for i in range(15):
    ts = resource_exhaustion_start + (i * 4000)
    heap_usage = random.randint(95, 99)
    
    # Application layer - Memory critical
    logs['app'].append({
        'timestamp': ts,
        'message': f'[CRITICAL] Memory: Heap usage critical. used={heap_usage}% ({heap_usage * 40}MB/4096MB) gc_time={random.randint(5000, 15000)}ms trace_id={TRACE_ID}'
    })
    
    # Application layer - GC overhead
    logs['app'].append({
        'timestamp': ts + 500,
        'message': f'[ERROR] GC: Overhead limit exceeded. gc_cycles={random.randint(50, 100)} gc_time_ratio={random.uniform(0.85, 0.98):.2f} trace_id={TRACE_ID}'
    })

# CPU exhaustion (NEW - adds more evidence)
for i in range(10):
    ts = resource_exhaustion_start + (i * 5000)
    cpu_usage = random.randint(95, 100)
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[CRITICAL] CPU: Usage critical. cpu={cpu_usage}% load_avg={random.uniform(8.0, 15.0):.2f} context_switches={random.randint(50000, 100000)} trace_id={TRACE_ID}'
    })

# Network saturation (NEW - shows network layer impact)
for i in range(8):
    ts = resource_exhaustion_start + (i * 6000)
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[ERROR] Network: Socket buffer full. tcp_backlog={random.randint(500, 1000)}/1024 dropped_packets={random.randint(50, 200)} trace_id={TRACE_ID}'
    })

# ============================================================
# STAGE 5: SERVICE DEGRADATION (Minute 18-20)
# ============================================================
print("  📍 Stage 5: Service Degradation (timeouts, slow queries)")
degradation_start = attack_start + (8 * 60 * 1000)

# Application timeouts (ENHANCED with more context)
for i in range(30):
    ts = degradation_start + (i * 2000)
    attacker_ip = random.choice(ATTACKER_IPS)
    duration = random.randint(30000, 60000)
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[ERROR] HTTP: Request timeout. method=GET path=/api/students_list duration={duration}ms source_ip={attacker_ip} status=504 trace_id={TRACE_ID}'
    })
    
    # Add corresponding database timeout
    logs['rds_error'].append({
        'timestamp': ts + 100,
        'message': f"{datetime.fromtimestamp(int(ts/1000)).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {random.randint(100, 999)} [ERROR] [MY-010081] Query execution timeout. query_time={duration}ms max_execution_time=30000ms"
    })

# Slow queries (database under stress) - ENHANCED
for i in range(10):
    ts = degradation_start + (i * 6000)
    ts_sec = int(ts / 1000)
    query_time = random.uniform(15.0, 30.0)
    lock_time = random.uniform(5.0, 10.0)
    
    logs['rds_slow'].append({
        'timestamp': ts,
        'message': f"# User@Host: app_user[app_user] @  [10.0.1.55]\n# Query_time: {query_time:.6f}  Lock_time: {lock_time:.6f} Rows_sent: 0  Rows_examined: 100000\n# Rows_affected: 0  Bytes_sent: 0\nSET timestamp={ts_sec};\nSELECT * FROM students WHERE status = 'active'; /* trace_id={TRACE_ID} */"
    })
    
    # Add lock wait timeout errors
    logs['rds_error'].append({
        'timestamp': ts + 500,
        'message': f"{datetime.fromtimestamp(ts_sec).strftime('%Y-%m-%dT%H:%M:%S.%fZ')} {random.randint(100, 999)} [ERROR] [MY-010071] Lock wait timeout exceeded. wait_time={lock_time:.2f}s table=students"
    })

# Service unavailable (ENHANCED with health check failures)
for i in range(10):
    ts = degradation_start + (i * 5000)
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[CRITICAL] HTTP: Service unavailable. status=503 reason="Backend connection failed" upstream=10.0.1.55:8080 trace_id={TRACE_ID}'
    })
    
    # Health check failures
    logs['app'].append({
        'timestamp': ts + 200,
        'message': f'[ERROR] HealthCheck: Endpoint failed. path=/health status=503 response_time={random.randint(5000, 10000)}ms consecutive_failures={random.randint(3, 10)}'
    })

# Load balancer errors (NEW - shows infrastructure impact)
for i in range(15):
    ts = degradation_start + (i * 3000)
    attacker_ip = random.choice(ATTACKER_IPS)
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[ERROR] ALB: Target unhealthy. target=10.0.1.55:8080 health_status=unhealthy reason="Connection timeout" source_ip={attacker_ip}'
    })

# Circuit breaker triggered (NEW - shows defensive mechanism)
for i in range(5):
    ts = degradation_start + (i * 10000)
    
    logs['app'].append({
        'timestamp': ts,
        'message': f'[WARN] CircuitBreaker: State changed to OPEN. service=database failure_rate={random.uniform(0.8, 0.95):.2f} threshold=0.5 trace_id={TRACE_ID}'
    })

# CloudTrail - Auto Scaling triggered (defensive response)
ct_autoscale = dict(cloudtrail_log)
ct_autoscale['eventTime'] = datetime.fromtimestamp(int((degradation_start + 30000) / 1000)).strftime('%Y-%m-%dT%H:%M:%SZ')
ct_autoscale['eventName'] = "SetDesiredCapacity"
ct_autoscale['userIdentity']['type'] = "AssumedRole"
ct_autoscale['userIdentity']['arn'] = "arn:aws:sts::123456789012:assumed-role/AutoScaling-Role"
logs['cloudtrail'].append({
    'timestamp': degradation_start + 30000,
    'message': json.dumps(ct_autoscale)
})

print(f"  ✅ Injected DDoS attack: {sum(len(v) for v in logs.values()) - 500} attack events")
print(f"  📊 Attack summary:")
print(f"     - Attacker IPs: {len(ATTACKER_IPS)}")
print(f"     - Attack duration: 10 minutes")
print(f"     - VPC REJECTs: ~215 events")
print(f"     - HTTP requests: ~150 events")
print(f"     - Resource errors: ~100 events (connection pool, memory, CPU, network)")
print(f"     - Service degradation: ~100 events (timeouts, slow queries, health checks)")
print(f"     - Total attack events: ~565 events")

# ============================================================
# PUSH LOGS TO CLOUDWATCH
# ============================================================
print("\n📤 Pushing logs to AWS CloudWatch...")

def push_logs(group_name, stream_name, log_events):
    """Push log events to CloudWatch in batches"""
    if not log_events:
        return 0
    
    # Sort logs by timestamp ascending (CloudWatch requirement)
    log_events.sort(key=lambda x: x['timestamp'])
    
    # Get sequence token
    desc = client.describe_log_streams(logGroupName=group_name, logStreamNamePrefix=stream_name)
    seq_token = desc['logStreams'][0].get('uploadSequenceToken')
    
    # Push in batches
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
        
        try:
            res = client.put_log_events(**kwargs)
            seq_token = res.get('nextSequenceToken')
            pushed += len(batch)
            print(f"  ✅ Pushed batch {i//BATCH_SIZE + 1}: {len(batch)} events")
        except Exception as e:
            print(f"  ❌ Error pushing batch: {e}")
        
        time.sleep(0.5)  # Rate limiting
    
    return pushed

# Push logs for each log group
total_pushed = 0
for k, group in LOG_GROUPS.items():
    print(f"\n📂 Pushing to {group}...")
    pushed = push_logs(group, LOG_STREAM_NAME, logs[k])
    total_pushed += pushed
    print(f"  ✅ Total pushed: {pushed} events")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 70)
print("✅ MOCK LOG GENERATION COMPLETE")
print("=" * 70)
print(f"\n📊 Summary:")
print(f"  - Total events pushed: {total_pushed}")
print(f"  - Background noise: ~500 events")
print(f"  - DDoS attack events: ~450 events")
print(f"  - Attack duration: 10 minutes (minute 10-20)")
print(f"\n🎯 Attack Details:")
print(f"  - Attack Type: DDoS/DoS (5 stages)")
print(f"  - Trace ID: {TRACE_ID}")
print(f"  - Attacker IPs: {', '.join(ATTACKER_IPS)}")
print(f"  - Primary Target: 10.0.1.55:8080")
print(f"\n📋 Next Steps:")
print(f"  1. Wait 1-2 minutes for logs to be indexed")
print(f"  2. Open Streamlit UI: streamlit run streamlit_app.py")
print(f"  3. Select time range: Last 30 minutes")
print(f"  4. Select all log sources")
print(f"  5. Click 'Analyze Logs'")
print(f"  6. Expected detection:")
print(f"     - Correlation Rule R007: Denial of Service")
print(f"     - MITRE ATT&CK: T1498 (Network DoS)")
print(f"     - Severity: CRITICAL")
print(f"     - Confidence: HIGH (85%+)")
print("=" * 70)
