"""
Log parser - Parse log entries into structured data
Enhanced to support all log group types:
- VPC Flow Logs
- CloudTrail JSON
- Apache Access/Error Logs
- Syslog (SSH, kernel, system)
- MySQL Error Logs
- MySQL Slow Query Logs
- Application Logs
"""
import re
import json
from typing import Optional
from models import LogEntry


class LogParser:
    """Parse log entries into structured data"""
    
    def __init__(self):
        # Generic patterns
        self.timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})')
        self.severity_pattern = re.compile(r'\b(ERROR|INFO|WARNING|DEBUG|CRITICAL|WARN|FATAL)\b', re.IGNORECASE)
        self.component_pattern = re.compile(r'^\[([^\]]+)\]|^([^:]+):')
        self.uuid_pattern = re.compile(r'\b[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\b')
        
        # VPC Flow Log pattern
        self.vpc_flow_pattern = re.compile(r'^\d+ \d+ eni-[a-f0-9]+ (\S+) (\S+) (\d+) (\d+) (\d+) \d+ \d+ \d+ \d+ (ACCEPT|REJECT) (OK|NODATA|SKIPDATA)')
        
        # Apache Access Log pattern
        # Format: 192.168.1.1 - - [22/Apr/2026:10:23:45 +0000] "GET /api/login.php HTTP/1.1" 404 512
        self.apache_access_pattern = re.compile(
            r'^(\S+) \S+ \S+ \[([^\]]+)\] "(\S+) (\S+) \S+" (\d+) (\S+)'
        )
        
        # Apache Error Log pattern
        # Format: [Mon Apr 22 10:23:45.123456 2026] [core:error] [pid 1234] [client 192.168.1.1:52341] File does not exist: /var/www/html/test.php
        self.apache_error_pattern = re.compile(
            r'^\[([^\]]+)\] \[([^\]]+)\] \[pid (\d+)\] (?:\[client ([^\]]+)\] )?(.+)'
        )
        
        # Syslog pattern (SSH, kernel, system)
        # Format: Apr 22 10:23:45 hostname sshd[1234]: Failed password for root from 203.0.113.42 port 52341 ssh2
        self.syslog_pattern = re.compile(
            r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}) (\S+) ([^\[]+)\[?(\d+)?\]?: (.+)'
        )
        
        # MySQL Error Log pattern
        # Format: 2026-04-22T10:23:45.123456Z 0 [ERROR] [MY-010334] Access denied for user 'root'@'10.0.4.15'
        self.mysql_error_pattern = re.compile(
            r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) \d+ \[(\w+)\] \[([^\]]+)\] (.+)'
        )
        
        # MySQL Slow Query pattern
        # Format: # Query_time: 5.234  Lock_time: 0.001 Rows_sent: 1000 Rows_examined: 5000
        self.mysql_slow_query_pattern = re.compile(
            r'# Query_time: ([\d.]+)\s+Lock_time: ([\d.]+)\s+Rows_sent: (\d+)\s+Rows_examined: (\d+)'
        )
    
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
        
        # 1. Modern JSON Application Logs (Streamlit, Node.js, etc.)
        try:
            json_data = json.loads(line)
            # Check for common JSON log fields (not CloudTrail)
            if 'level' in json_data and 'message' in json_data and 'eventVersion' not in json_data:
                entry.component = json_data.get('component', json_data.get('logger', 'App'))
                entry.timestamp = json_data.get('timestamp', json_data.get('time', ''))
                
                # Map log levels to severity
                level = json_data.get('level', 'INFO').upper()
                severity_map = {
                    'FATAL': 'CRITICAL',
                    'ERROR': 'ERROR',
                    'WARN': 'WARNING',
                    'WARNING': 'WARNING',
                    'INFO': 'INFO',
                    'DEBUG': 'DEBUG',
                    'TRACE': 'DEBUG'
                }
                entry.severity = severity_map.get(level, level)
                
                # Extract message and context
                message = json_data.get('message', '')
                error = json_data.get('error', json_data.get('exception', ''))
                if error:
                    entry.message = f"{message} | Error: {error}"
                else:
                    entry.message = message
                
                return entry
        except Exception:
            pass
        
        # 2. CloudTrail JSON format
        try:
            json_data = json.loads(line)
            if 'eventVersion' in json_data and 'eventName' in json_data:
                entry.component = 'CloudTrail'
                entry.timestamp = json_data.get('eventTime', '')
                
                error_code = json_data.get('errorCode', '')
                error_message = json_data.get('errorMessage', '')
                usr_ident = json_data.get('userIdentity', {})
                arn = usr_ident.get('arn', usr_ident.get('principalId', 'Unknown'))
                
                if error_code or error_message or 'AccessDenied' in str(json_data):
                    entry.severity = 'ERROR'
                else:
                    entry.severity = 'INFO'
                    
                entry.message = f"AWS API {json_data.get('eventName')} called by {arn} - Error: {error_code} {error_message}"
                return entry
        except Exception:
            pass

        # 2. VPC Flow Logs format
        vpc_match = self.vpc_flow_pattern.search(line)
        if vpc_match:
            entry.component = 'VPC_Network'
            src_ip = vpc_match.group(1)
            dst_ip = vpc_match.group(2)
            src_port = vpc_match.group(3)
            dst_port = vpc_match.group(4)
            protocol = vpc_match.group(5)
            action = vpc_match.group(6)
            
            if action == 'REJECT':
                entry.severity = 'ERROR'
            else:
                entry.severity = 'INFO'
                
            entry.message = f"VPC Flow: Connection {action} from {src_ip}:{src_port} to {dst_ip}:{dst_port} (Protocol: {protocol})"
            return entry

        # 3. Apache Access Log format
        apache_access_match = self.apache_access_pattern.search(line)
        if apache_access_match:
            entry.component = 'Apache_Access'
            ip = apache_access_match.group(1)
            timestamp = apache_access_match.group(2)
            method = apache_access_match.group(3)
            path = apache_access_match.group(4)
            status = apache_access_match.group(5)
            size = apache_access_match.group(6)
            
            entry.timestamp = timestamp
            status_code = int(status)
            
            # Classify severity by HTTP status code
            if status_code >= 500:
                entry.severity = 'ERROR'
            elif status_code >= 400:
                entry.severity = 'WARNING'
            else:
                entry.severity = 'INFO'
            
            # Detect attack patterns in URL
            attack_indicators = []
            path_lower = path.lower()
            if any(x in path_lower for x in ['union', 'select', 'drop', 'insert', '--', "'"]):
                attack_indicators.append('SQL_INJECTION')
            if any(x in path_lower for x in ['../', '..\\', '/etc/', '/passwd']):
                attack_indicators.append('PATH_TRAVERSAL')
            if any(x in path_lower for x in ['<script', 'javascript:', 'onerror=']):
                attack_indicators.append('XSS')
            
            attack_str = f" [ATTACK: {','.join(attack_indicators)}]" if attack_indicators else ""
            entry.message = f"HTTP {status} {method} {path} from {ip} ({size} bytes){attack_str}"
            return entry

        # 4. Apache Error Log format
        apache_error_match = self.apache_error_pattern.search(line)
        if apache_error_match:
            entry.component = 'Apache_Error'
            timestamp = apache_error_match.group(1)
            level = apache_error_match.group(2)
            pid = apache_error_match.group(3)
            client = apache_error_match.group(4) or 'unknown'
            message = apache_error_match.group(5)
            
            entry.timestamp = timestamp
            
            # Map Apache log level to severity
            if 'error' in level.lower() or 'crit' in level.lower():
                entry.severity = 'ERROR'
            elif 'warn' in level.lower():
                entry.severity = 'WARNING'
            else:
                entry.severity = 'INFO'
            
            entry.message = f"[{level}] [pid {pid}] [client {client}] {message}"
            return entry

        # 5. Syslog format (SSH, kernel, system)
        syslog_match = self.syslog_pattern.search(line)
        if syslog_match:
            timestamp = syslog_match.group(1)
            hostname = syslog_match.group(2)
            process = syslog_match.group(3).strip()
            pid = syslog_match.group(4) or ''
            message = syslog_match.group(5)
            
            entry.component = f'Syslog_{process}'
            entry.timestamp = timestamp
            
            # Detect security events
            message_lower = message.lower()
            if any(x in message_lower for x in ['failed password', 'authentication failure', 'invalid user']):
                entry.severity = 'ERROR'
                entry.message = f"[SSH_BRUTE_FORCE] {message}"
            elif 'ufw block' in message_lower or 'denied' in message_lower:
                entry.severity = 'WARNING'
                entry.message = f"[FIREWALL_BLOCK] {message}"
            elif any(x in message_lower for x in ['error', 'fatal', 'critical']):
                entry.severity = 'ERROR'
                entry.message = message
            elif 'warning' in message_lower:
                entry.severity = 'WARNING'
                entry.message = message
            else:
                entry.severity = 'INFO'
                entry.message = message
            
            return entry

        # 6. MySQL Error Log format
        mysql_error_match = self.mysql_error_pattern.search(line)
        if mysql_error_match:
            entry.component = 'MySQL_Error'
            timestamp = mysql_error_match.group(1)
            level = mysql_error_match.group(2)
            error_code = mysql_error_match.group(3)
            message = mysql_error_match.group(4)
            
            entry.timestamp = timestamp
            
            # Map MySQL log level to severity
            if level.upper() in ['ERROR', 'FATAL']:
                entry.severity = 'ERROR'
            elif level.upper() == 'WARNING':
                entry.severity = 'WARNING'
            else:
                entry.severity = 'INFO'
            
            entry.message = f"[{error_code}] {message}"
            return entry

        # 7. MySQL Slow Query format
        slow_query_match = self.mysql_slow_query_pattern.search(line)
        if slow_query_match:
            entry.component = 'MySQL_SlowQuery'
            query_time = float(slow_query_match.group(1))
            lock_time = float(slow_query_match.group(2))
            rows_sent = slow_query_match.group(3)
            rows_examined = slow_query_match.group(4)
            
            # Classify severity by query time
            if query_time >= 10:
                entry.severity = 'ERROR'
            elif query_time >= 5:
                entry.severity = 'WARNING'
            else:
                entry.severity = 'INFO'
            
            entry.message = f"Slow query: {query_time}s (lock: {lock_time}s, sent: {rows_sent}, examined: {rows_examined})"
            return entry

        # 8. Fallback: Classic Application Log parsing
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
