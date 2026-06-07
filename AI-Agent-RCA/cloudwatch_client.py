"""
CloudWatch Client - Pull logs from AWS CloudWatch
"""
import boto3
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class CloudWatchClient:
    """Client to interact with AWS CloudWatch Logs"""
    
    def __init__(self, region: str = "us-east-1", profile: str = None):
        """
        Initialize CloudWatch client
        
        Args:
            region: AWS region
            profile: AWS profile name (optional)
        """
        self.region = region
        self.profile = profile
        
        try:
            # Nếu profile là 'default' hoặc None, hãy thử dùng default session (quan trọng khi chạy trên EC2)
            if profile and profile != "default":
                session = boto3.Session(profile_name=profile, region_name=region)
            else:
                session = boto3.Session(region_name=region)
                
            self.client = session.client('logs')
            logger.info(f"CloudWatch client initialized for region {region}")
        except Exception as e:
            logger.error(f"Failed to initialize CloudWatch client: {e}")
            raise
    
    def get_logs(
        self,
        log_group: str,
        start_time: datetime,
        end_time: datetime,
        search_term: Optional[str] = None,
        max_matches: int = 1000
    ) -> List[str]:
        """
        Get logs from CloudWatch
        
        Args:
            log_group: Log group name
            start_time: Start time for log query
            end_time: End time for log query
            search_term: Optional search term to filter logs
            max_matches: Maximum number of logs to return
            
        Returns:
            List of log messages
        """
        try:
            logs = []
            
            # Convert datetime to milliseconds since epoch
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            # Get log streams (paginated to avoid missing streams)
            all_streams = []
            paginator = self.client.get_paginator('describe_log_streams')
            for page in paginator.paginate(
                logGroupName=log_group,
                orderBy='LastEventTime',
                descending=True
            ):
                all_streams.extend(page.get('logStreams', []))
            
            if not all_streams:
                logger.warning(f"No log streams found in {log_group}")
                return []
            
            # Get logs from each stream (with pagination per stream)
            for stream in all_streams:
                if len(logs) >= max_matches:
                    break
                
                stream_name = stream['logStreamName']
                
                try:
                    # Paginate get_log_events using nextForwardToken
                    next_token = None
                    while len(logs) < max_matches:
                        kwargs = {
                            'logGroupName': log_group,
                            'logStreamName': stream_name,
                            'startTime': start_ms,
                            'endTime': end_ms,
                            'startFromHead': True
                        }
                        if next_token:
                            kwargs['nextToken'] = next_token
                        
                        events_response = self.client.get_log_events(**kwargs)
                        events = events_response.get('events', [])
                        
                        # No events in this page → done with this stream
                        if not events:
                            break
                        
                        for event in events:
                            if len(logs) >= max_matches:
                                break
                            
                            message = event.get('message', '')
                            # Get CloudWatch timestamp (ms to isoformat)
                            cw_ts = event.get('timestamp')
                            ts_iso = datetime.fromtimestamp(cw_ts / 1000.0).isoformat() if cw_ts else ""
                            
                            log_obj = {
                                'content': message,
                                'timestamp': ts_iso,
                                'file': stream_name
                            }
                            
                            # Filter by search term if provided
                            if search_term:
                                if search_term.lower() in message.lower():
                                    logs.append(log_obj)
                            else:
                                logs.append(log_obj)
                        
                        # Check if there are more pages
                        new_token = events_response.get('nextForwardToken')
                        if new_token == next_token:
                            break  # No more pages
                        next_token = new_token
                
                except Exception as e:
                    logger.warning(f"Error reading stream {stream_name}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(logs)} logs from {log_group}")
            return logs
        
        except Exception as e:
            logger.error(f"Error getting logs from CloudWatch: {e}")
            raise
    
    def list_log_groups(self) -> List[str]:
        """
        List all log groups
        
        Returns:
            List of log group names
        """
        try:
            log_groups = []
            paginator = self.client.get_paginator('describe_log_groups')
            
            for page in paginator.paginate():
                for group in page.get('logGroups', []):
                    log_groups.append(group['logGroupName'])
            
            return sorted(log_groups)
        
        except Exception as e:
            logger.error(f"Error listing log groups: {e}")
            return []
    
    def list_log_streams(self, log_group: str) -> List[str]:
        """
        List log streams in a log group
        
        Args:
            log_group: Log group name
            
        Returns:
            List of log stream names
        """
        try:
            streams = []
            paginator = self.client.get_paginator('describe_log_streams')
            
            for page in paginator.paginate(logGroupName=log_group):
                for stream in page.get('logStreams', []):
                    streams.append(stream['logStreamName'])
            
            return sorted(streams)
        
        except Exception as e:
            logger.error(f"Error listing log streams: {e}")
            return []
