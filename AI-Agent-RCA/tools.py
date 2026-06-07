import os
import sys
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from langchain_core.tools import tool

# Import local modules using package paths
from cloudwatch_client import CloudWatchClient
from src.log_parser import LogParser
from src.pattern_analyzer import PatternAnalyzer
from src.advanced_correlator import AdvancedCorrelator


def _get_anchor_time(alert_signals_json: Optional[str]) -> datetime:
    """Helper to parse trigger/alarm timestamp from alert metadata."""
    if alert_signals_json:
        try:
            data = json.loads(alert_signals_json)
            if isinstance(data, dict):
                # Standard SNS message wrapping a CloudWatch Alarm
                if "Message" in data and isinstance(data["Message"], str):
                    try:
                        inner_data = json.loads(data["Message"])
                        if isinstance(inner_data, dict) and "StateChangeTime" in inner_data:
                            return datetime.fromisoformat(inner_data["StateChangeTime"].replace("Z", "+00:00"))
                    except Exception:
                        pass
                
                # Check direct fields
                for field_name in ["StateChangeTime", "timestamp", "eventTime"]:
                    if field_name in data:
                        return datetime.fromisoformat(data[field_name].replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.utcnow()


@tool
def query_cloudwatch_logs(
    log_group: str,
    time_range_minutes: int = 5,
    search_term: Optional[str] = None,
    alert_signals_json: Optional[str] = None
) -> str:
    """
    Query AWS CloudWatch logs for a specific log group around the alert trigger time.
    Use this to pull raw log messages for debugging and validation.
    """
    try:
        client = CloudWatchClient()
        anchor = _get_anchor_time(alert_signals_json)
        start_time = anchor - timedelta(minutes=time_range_minutes)
        end_time = anchor + timedelta(minutes=time_range_minutes)
        
        raw_logs = client.get_logs(
            log_group=log_group,
            start_time=start_time,
            end_time=end_time,
            search_term=search_term
        )
        if not raw_logs:
            return f"No logs found in log group '{log_group}' from {start_time} to {end_time}."
            
        formatted = []
        for log in raw_logs[:100]:  # Limit output size to prevent context overflow
            formatted.append(f"[{log.get('timestamp')}] {log.get('file')} - {log.get('content')}")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error querying CloudWatch logs: {str(e)}"


@tool
def analyze_log_patterns(
    log_group: str,
    alert_signals_json: Optional[str] = None
) -> str:
    """
    Analyze patterns, frequency, and temporal clusters of errors in a specific log group.
    Use this to identify recurring error signatures or anomalies.
    """
    try:
        client = CloudWatchClient()
        anchor = _get_anchor_time(alert_signals_json)
        start_time = anchor - timedelta(minutes=10)
        end_time = anchor + timedelta(minutes=10)
        
        raw_logs = client.get_logs(
            log_group=log_group,
            start_time=start_time,
            end_time=end_time
        )
        if not raw_logs:
            return f"No logs found in log group '{log_group}' for pattern analysis."
            
        parser = LogParser()
        entries = []
        for raw in raw_logs:
            entry = parser.parse_log_entry(raw)
            if entry:
                entries.append(entry)
                
        analyzer = PatternAnalyzer()
        analysis_data = analyzer.analyze_log_entries(entries)
        
        output = [
            f"Pattern Analysis for {log_group}:",
            f"- Total logs parsed: {analysis_data.total_entries}",
            f"- Unique error patterns: {len(analysis_data.error_patterns)}",
            "\nSeverity Distribution:"
        ]
        for sev, count in analysis_data.severity_distribution.items():
            output.append(f"  {sev}: {count}")
            
        output.append("\nTop Error Patterns:")
        for pattern in analysis_data.error_patterns[:5]:
            output.append(f"  [{pattern.component}] {pattern.pattern} (Count: {pattern.count})")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error analyzing log patterns: {str(e)}"


@tool
def check_cross_correlation(
    time_window_seconds: int = 300,
    alert_signals_json: Optional[str] = None
) -> str:
    """
    Correlate log signals across multiple log groups to discover multi-stage attacks or cross-service dependencies.
    Use this when looking for the global root cause of an incident.
    """
    try:
        client = CloudWatchClient()
        log_groups = client.list_log_groups()
        if not log_groups:
            return "No CloudWatch log groups found in this AWS region."
            
        anchor = _get_anchor_time(alert_signals_json)
        start_time = anchor - timedelta(seconds=time_window_seconds)
        end_time = anchor + timedelta(seconds=time_window_seconds)
        
        parser = LogParser()
        analyzer = PatternAnalyzer()
        correlator = AdvancedCorrelator()
        
        log_sources = {}
        for lg in log_groups:
            raw_logs = client.get_logs(
                log_group=lg,
                start_time=start_time,
                end_time=end_time
            )
            if raw_logs:
                entries = []
                for r in raw_logs:
                    entry = parser.parse_log_entry(r)
                    if entry:
                        entries.append(entry)
                if entries:
                    analysis_data = analyzer.analyze_log_entries(entries)
                    log_sources[lg] = (entries, analysis_data)
                    
        if not log_sources:
            return f"No log entries found in any log groups within the time window around {anchor}."
            
        correlated_events = correlator.correlate_advanced(log_sources)
        if not correlated_events:
            return "No correlated attack patterns or cross-service anomalies detected."
            
        output = ["Cross-Source Correlation Results:"]
        for event in correlated_events:
            output.append(f"\n[CORRELATION KEY] {event.correlation_key}")
            output.append(f"- Match Rule: {event.rule_name}")
            output.append(f"- Confidence Score: {event.confidence_score:.2f}")
            output.append(f"- Description: {event.description}")
            output.append("- Event Sequence:")
            for step in event.sequence.events:
                output.append(f"  [{step.timestamp}] [{step.source}] ({step.severity}) {step.message}")
                
        return "\n".join(output)
    except Exception as e:
        return f"Error executing correlation analysis: {str(e)}"


# Export list of available tools
ALL_TOOLS = [
    query_cloudwatch_logs,
    analyze_log_patterns,
    check_cross_correlation
]
