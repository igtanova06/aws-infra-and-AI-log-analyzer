"""
Pattern analyzer - Analyze log patterns and trends
"""
from collections import Counter, defaultdict
from typing import List
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
        
        # Analyze time patterns
        time_pattern = None
        if timestamps:
            try:
                timestamps = sorted(timestamps)
                time_pattern = {
                    'first_occurrence': timestamps[0],
                    'last_occurrence': timestamps[-1],
                    'total_occurrences': len(timestamps)
                }
            except Exception:
                pass
        
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
