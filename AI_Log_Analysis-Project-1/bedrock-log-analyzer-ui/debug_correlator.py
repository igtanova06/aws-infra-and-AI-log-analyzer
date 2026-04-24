import sys
import os
sys.path.append(os.path.abspath('src'))
from datetime import datetime, timedelta
from advanced_correlator import AdvancedCorrelator
from cloudwatch_client import CloudWatchClient
from log_parser import LogParser

REGION = 'ap-southeast-1'
LOG_GROUPS = [
    '/aws/vpc/flowlogs',
    '/aws/ec2/application',
    '/aws/rds/mysql/error',
    '/aws/rds/mysql/slowquery',
    '/aws/cloudtrail/logs'
]

client = CloudWatchClient(region=REGION)
end_time = datetime.now()
start_time = end_time - timedelta(hours=1)

log_entries = []
parser = LogParser()

for group in LOG_GROUPS:
    print(f"Fetching {group}...")
    try:
        raw_logs = client.get_logs(
            log_group=group,
            start_time=start_time,
            end_time=end_time,
            max_matches=100000
        )
        for log in raw_logs:
            entry = parser.parse_log_entry(log)
            if entry:
                entry.component = group
                log_entries.append(entry)
    except Exception as e:
        print(e)

print(f"Total parsed: {len(log_entries)}")

correlator = AdvancedCorrelator(rules_config_path='correlation_rules.json')
events = correlator.correlate_multi_source(log_entries, None, 3600)

print(f"Found {len(events)} correlated events")
for e in events:
    print(f"[{e.attack_name}] keys: {e.primary_correlation_key} sources: {e.sources}")
    for t in e.timeline:
        print(f"  {t.timestamp} | {t.source} | {t.event_type} | {t.actor}")
