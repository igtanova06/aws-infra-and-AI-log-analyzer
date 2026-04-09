"""
Log parser - Parse log entries into structured data
"""
import re
import json
from typing import Optional
from models import LogEntry


class LogParser:
    """Parse log entries into structured data"""
    
    def __init__(self):
        self.timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})')
        self.severity_pattern = re.compile(r'\b(ERROR|INFO|WARNING|DEBUG|CRITICAL|WARN|FATAL)\b', re.IGNORECASE)
        self.component_pattern = re.compile(r'^\[([^\]]+)\]|^([^:]+):')
        self.uuid_pattern = re.compile(r'\b[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b')
        # Regex cho VPC Flow Log
        self.vpc_flow_pattern = re.compile(r'^\d+ \d+ eni-[a-f0-9]+ (\S+) (\S+) (\d+) (\d+) (\d+) \d+ \d+ \d+ \d+ (ACCEPT|REJECT) (OK|NODATA|SKIPDATA)')
    
    def parse_log_entry(self, match) -> Optional[LogEntry]:
        """Parse a log line into structured data"""
        if isinstance(match, str):
            line = match
            file_name = ""
            line_num = 0
        else:
            line = match.get('content', '')
            file_name = match.get('file', '')
            line_num = match.get('line_number', 0)
        
        if not line:
            return None
        
        entry = LogEntry(
            file=file_name,
            line_number=line_num,
            content=line
        )
        
        # 1. AI Parsing: CloudTrail JSON format
        try:
            json_data = json.loads(line)
            if 'eventVersion' in json_data and 'eventName' in json_data:
                entry.component = 'CloudTrail'
                entry.timestamp = json_data.get('eventTime', '')
                
                error_code = json_data.get('errorCode', '')
                error_message = json_data.get('errorMessage', '')
                usr_ident = json_data.get('userIdentity', {})
                arn = usr_ident.get('arn', usr_ident.get('principalId', 'Unknown'))
                
                # Force nhãn ERROR nếu phát sinh rủi ro để AI vào cuộc
                if error_code or error_message or 'AccessDenied' in str(json_data):
                    entry.severity = 'ERROR'
                else:
                    entry.severity = 'INFO'
                    
                entry.message = f"AWS API {json_data.get('eventName')} called by {arn} - Error: {error_code} {error_message}"
                return entry
        except Exception:
            pass

        # 2. AI Parsing: VPC Flow Logs format
        vpc_match = self.vpc_flow_pattern.search(line)
        if vpc_match:
            entry.component = 'VPC_Network'
            src_ip = vpc_match.group(1)
            dst_ip = vpc_match.group(2)
            src_port = vpc_match.group(3)
            dst_port = vpc_match.group(4)
            protocol = vpc_match.group(5)
            action = vpc_match.group(6)
            
            # Giao cho AI xử lý các Connection bị REJECT
            if action == 'REJECT':
                entry.severity = 'ERROR'
            else:
                entry.severity = 'INFO'
                
            entry.message = f"VPC Flow: Connection {action} from {src_ip}:{src_port} to {dst_ip}:{dst_port} (Protocol: {protocol})"
            return entry

        # 3. Fallback: Classic Application Log parsing
        # Extract timestamp
        timestamp_match = self.timestamp_pattern.search(line)
        if timestamp_match:
            entry.timestamp = timestamp_match.group(1)
        
        # Extract severity
        severity_match = self.severity_pattern.search(line)
        if severity_match:
            entry.severity = severity_match.group(1).upper()
        else:
            entry.severity = "UNKNOWN"
        
        # Extract component and message
        if timestamp_match:
            remainder = line[timestamp_match.end():].strip()
        else:
            remainder = line
        
        if severity_match:
            component_msg = remainder.replace(severity_match.group(0), "", 1).strip()
            
            component_match = self.component_pattern.search(component_msg)
            if component_match:
                component = component_match.group(1) or component_match.group(2)
                entry.component = component.strip()
                
                if component_match.group(1):  
                    entry.message = component_msg[component_match.end():].strip()
                else:  
                    entry.message = component_msg[component_match.end():].strip()
            else:
                entry.message = component_msg
        else:
            entry.message = remainder
        
        return entry
    
    def normalize_pattern(self, text: str) -> str:
        """Normalize a log message to find patterns"""
        text = self.uuid_pattern.sub('<ID>', text)
        text = re.sub(r'\d+', '<NUM>', text)
        text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', text)
        return text
