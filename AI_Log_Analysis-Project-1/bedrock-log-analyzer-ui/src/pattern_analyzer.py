"""
Pattern analyzer - Analyze log patterns and trends
Enhanced with temporal analysis for attack detection
"""
from collections import Counter, defaultdict
from typing import List, Optional
from datetime import datetime
from models import LogEntry, AnalysisData, ErrorPattern
from log_parser import LogParser


class PatternAnalyzer:
    """Analyze log entries to extract patterns and insights"""
    
    def __init__(self):
        self.parser = LogParser()
    
    def analyze_log_entries(self, entries: List[LogEntry]) -> AnalysisData:
        """Analyze log entries to extract patterns and insights"""
        total_entries = len(entries)
        severities = Counter()
        components = Counter()
        errors_by_component = defaultdict(list)
        timestamps = []
        
        # Extract data
        for entry in entries:
            if entry.severity:
                severities[entry.severity] += 1
            
            if entry.component:
                components[entry.component] += 1
                if entry.severity in ['ERROR', 'CRITICAL', 'FATAL']:
                    if entry.message:
                        errors_by_component[entry.component].append(entry.message)
            
            if entry.timestamp:
                timestamps.append(entry.timestamp)
        
        # Analyze time patterns (ENHANCED)
        time_pattern = self._analyze_temporal_patterns(entries)
        
        # Find most common error patterns
        error_patterns = []
        for component, errors in errors_by_component.items():
            for error in errors:
                if error and len(error) > 10:  # Only consider substantial errors
                    pattern = self.parser.normalize_pattern(error)
                    error_patterns.append((component, pattern))
        
        common_patterns = Counter(error_patterns).most_common(10)
        
        pattern_list = [
            ErrorPattern(component=comp, pattern=pat, count=count)
            for (comp, pat), count in common_patterns
        ]
        
        return AnalysisData(
            total_entries=total_entries,
            severity_distribution=dict(severities),
            components=dict(components),
            error_patterns=pattern_list,
            time_pattern=time_pattern
        )
    
    def _analyze_temporal_patterns(self, entries: List[LogEntry]) -> Optional[dict]:
        """
        Analyze time-based patterns to detect burst attacks and temporal anomalies.
        Returns dict with temporal metrics or None if insufficient data.
        """
        parsed_timestamps = []
        
        for entry in entries:
            if not entry.timestamp:
                continue
            
            ts = self._parse_timestamp(entry.timestamp)
            if ts:
                parsed_timestamps.append(ts)
        
        if len(parsed_timestamps) < 2:
            # Not enough data for temporal analysis
            return None
        
        parsed_timestamps.sort()
        first_ts = parsed_timestamps[0]
        last_ts = parsed_timestamps[-1]
        duration_seconds = (last_ts - first_ts).total_seconds()
        
        # Avoid division by zero
        if duration_seconds == 0:
            duration_seconds = 1
        
        events_per_minute = (len(parsed_timestamps) / duration_seconds) * 60
        
        # Detect burst pattern (>5 events/min = suspicious)
        is_burst = events_per_minute > 5
        
        # Find peak activity window (1-minute buckets)
        minute_buckets = defaultdict(int)
        for ts in parsed_timestamps:
            bucket_key = ts.replace(second=0, microsecond=0)
            minute_buckets[bucket_key] += 1
        
        peak_minute = max(minute_buckets.items(), key=lambda x: x[1]) if minute_buckets else (None, 0)
        peak_time = peak_minute[0].strftime('%H:%M:%S') if peak_minute[0] else 'N/A'
        peak_count = peak_minute[1]
        
        return {
            'first_occurrence': first_ts.strftime('%Y-%m-%d %H:%M:%S'),
            'last_occurrence': last_ts.strftime('%Y-%m-%d %H:%M:%S'),
            'total_occurrences': len(parsed_timestamps),
            'duration_seconds': round(duration_seconds, 2),
            'duration_minutes': round(duration_seconds / 60, 2),
            'events_per_minute': round(events_per_minute, 2),
            'is_burst_attack': is_burst,
            'peak_activity_time': peak_time,
            'peak_activity_count': peak_count
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """
        Parse various timestamp formats into datetime object.
        Supports: ISO8601, Apache, Syslog, MySQL formats.
        """
        if not timestamp_str:
            return None
        
        # List of common timestamp formats
        formats = [
            '%Y-%m-%d %H:%M:%S',           # 2026-04-22 10:23:45
            '%Y-%m-%dT%H:%M:%S',           # 2026-04-22T10:23:45
            '%Y-%m-%dT%H:%M:%S.%fZ',       # 2026-04-22T10:23:45.123456Z (ISO8601)
            '%Y-%m-%dT%H:%M:%S.%f',        # 2026-04-22T10:23:45.123456
            '%d/%b/%Y:%H:%M:%S',           # 22/Apr/2026:10:23:45 (Apache)
            '%b %d %H:%M:%S',              # Apr 22 10:23:45 (Syslog)
        ]
        
        for fmt in formats:
            try:
                # Handle timezone suffix (Z, +0000)
                clean_ts = timestamp_str.replace('Z', '').split('+')[0].split()[0]
                return datetime.strptime(clean_ts, fmt)
            except ValueError:
                continue
        
        # If all formats fail, return None
        return None
