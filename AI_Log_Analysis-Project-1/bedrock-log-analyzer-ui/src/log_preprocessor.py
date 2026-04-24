"""
Log Preprocessor — Prepare high-quality AI context from parsed logs.

This module sits between pattern analysis (Step 3-4) and Bedrock AI (Step 5).
It scores, ranks, and structures log data so Bedrock receives focused,
relevant evidence instead of raw noisy logs.

Designed for single-log-group analysis (one source type per run).
"""
import re
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from models import LogEntry, AnalysisData


# ---------------------------------------------------------------------------
# Data class: structured context that gets passed to Bedrock
# ---------------------------------------------------------------------------

@dataclass
class AIContext:
    """Structured context built for one log group, sent to Bedrock."""

    source_type: str                           # "vpc_flow" | "cloudtrail" | "app"
    log_group_name: str                        # e.g. "/aws/vpc/flowlogs"
    total_logs_pulled: int                     # how many raw logs were retrieved
    total_logs_after_scoring: int              # how many passed relevance filter

    search_term: str = ""                      # the key term used to extract these logs
    time_range_str: str = ""                   # analysis boundary

    severity_summary: Dict[str, int] = field(default_factory=dict)
    top_patterns: List[Dict] = field(default_factory=list)        # [{pattern, count, component}]
    suspicious_ips: List[Dict] = field(default_factory=list)      # [{ip, count, context}]
    suspicious_users: List[Dict] = field(default_factory=list)    # [{user, count, context}]
    suspicious_apis: List[Dict] = field(default_factory=list)     # [{api, count, context}]
    representative_samples: List[str] = field(default_factory=list)  # curated raw log lines
    within_source_hints: List[str] = field(default_factory=list)  # correlation hints
    
    # NEW: Temporal analysis metrics
    temporal_analysis: Dict = field(default_factory=dict)          # attack velocity, burst detection
    
    # NEW: Multi-source correlation metadata (Priority 1 enhancement)
    correlation_metadata: Optional[Dict] = None                    # correlation context from correlator
    correlated_events_summary: Optional[str] = None                # human-readable summary
    correlation_keys_used: Optional[List[str]] = None              # which keys were used (trace_id, etc)
    is_multi_source: bool = False                                  # single vs multi-source analysis


# ---------------------------------------------------------------------------
# Source type detection
# ---------------------------------------------------------------------------

def detect_source_type(log_group_name: str) -> str:
    """
    Infer log source type from the CloudWatch log group name.
    Returns specific source type for better AI context.
    """
    name_lower = log_group_name.lower()
    
    # Multi-source analysis (contains multiple log groups)
    if 'multi-source' in name_lower or 'multi_source' in name_lower:
        return 'multi_source'
    
    # VPC Flow Logs
    if 'vpc' in name_lower or 'flowlog' in name_lower:
        return 'vpc_flow'
    
    # CloudTrail
    if 'cloudtrail' in name_lower or 'trail' in name_lower:
        return 'cloudtrail'
    
    # Apache/HTTP logs
    if 'httpd' in name_lower or 'apache' in name_lower:
        return 'apache'
    
    # System logs (syslog)
    if 'system' in name_lower or 'syslog' in name_lower:
        return 'syslog'
    
    # RDS/MySQL logs
    if 'rds' in name_lower or 'mysql' in name_lower:
        if 'slowquery' in name_lower or 'slow' in name_lower:
            return 'mysql_slow'
        return 'mysql_error'
    
    # Streamlit/App tier
    if 'streamlit' in name_lower:
        return 'streamlit'
    
    # Default: application logs
    return 'app'


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------

# Severity scores — higher = more interesting to AI
_SEVERITY_SCORES = {
    'CRITICAL': 5,
    'FATAL': 5,
    'ERROR': 4,
    'WARNING': 2,
    'WARN': 2,
    'INFO': 1,
    'DEBUG': 0,
    'UNKNOWN': 1,
}

# Security keywords that boost score regardless of source
_SECURITY_KEYWORDS = [
    'denied', 'unauthorized', 'forbidden', 'reject',
    'brute', 'attack', 'exploit', 'escalation',
    'credential', 'password', 'token', 'root',
    'failed', 'invalid', 'suspicious',
]

# VPC high-interest destination ports (SSH, RDP, SMB, DB)
_ATTACK_PORTS = {'22', '3389', '445', '1433', '3306', '5432', '27017'}

# CloudTrail security-sensitive API actions
_SENSITIVE_APIS = [
    'deletevpc', 'createaccesskey', 'deleteaccesskey',
    'putrolepolicy', 'attachrolepolicy', 'createuser',
    'deleteuser', 'stopinstances', 'terminateinstances',
    'disablekey', 'createloginprofile', 'updaterole',
    'deletetrail', 'stoplogging',
]

# Apache attack patterns
_APACHE_ATTACK_PATTERNS = [
    'sql_injection', 'path_traversal', 'xss',
    'union', 'select', 'drop', '../', '/etc/',
]

# Syslog security keywords
_SYSLOG_SECURITY_KEYWORDS = [
    'failed password', 'authentication failure', 'invalid user',
    'ufw block', 'connection refused', 'access denied',
]

# MySQL error codes (high severity)
_MYSQL_CRITICAL_ERRORS = [
    'MY-010334',  # Access denied
    'MY-013360',  # Plugin authentication failed
    'MY-010069',  # Too many connections
    'MY-012574',  # InnoDB error
]


def score_entry(entry: LogEntry, source_type: str) -> int:
    """
    Score a single parsed LogEntry by relevance to AI analysis.
    Higher score = more important for the AI to see.
    Enhanced to support all log group types.
    """
    score = 0

    # --- 1. Severity ---
    severity = (entry.severity or 'UNKNOWN').upper()
    score += _SEVERITY_SCORES.get(severity, 1)

    # --- 2. Security keyword match ---
    text = (entry.message or '').lower() + ' ' + (entry.content or '').lower()
    for kw in _SECURITY_KEYWORDS:
        if kw in text:
            score += 2
            break  # one bonus is enough

    # --- 3. Source-specific signals ---
    if source_type == 'vpc_flow':
        if 'REJECT' in (entry.content or ''):
            score += 3
        # Check for attack-related ports
        for port in _ATTACK_PORTS:
            if f' {port} ' in (entry.content or ''):
                score += 2
                break

    elif source_type == 'cloudtrail':
        content_lower = (entry.content or '').lower()
        # AccessDenied / error code
        if 'accessdenied' in content_lower or 'unauthorizedoperation' in content_lower:
            score += 3
        if 'errorcode' in content_lower or '"errorCode"' in (entry.content or ''):
            score += 2
        # Sensitive API
        for api in _SENSITIVE_APIS:
            if api in content_lower:
                score += 3
                break
        # Root activity
        if '"root"' in (entry.content or '') or ':root' in (entry.content or ''):
            score += 3

    elif source_type == 'apache':
        # HTTP status codes
        if '500' in text or '503' in text or '502' in text:
            score += 3
        if '404' in text or '403' in text or '401' in text:
            score += 1
        # Attack patterns
        for pattern in _APACHE_ATTACK_PATTERNS:
            if pattern in text:
                score += 4
                break

    elif source_type == 'syslog':
        # SSH brute force
        for kw in _SYSLOG_SECURITY_KEYWORDS:
            if kw in text:
                score += 4
                break
        # Firewall blocks
        if 'ufw block' in text or 'denied' in text:
            score += 3

    elif source_type in ['mysql_error', 'mysql_slow']:
        # Critical MySQL errors
        for err_code in _MYSQL_CRITICAL_ERRORS:
            if err_code in text:
                score += 4
                break
        # Slow queries
        if source_type == 'mysql_slow':
            # Extract query time if available
            import re
            time_match = re.search(r'(\d+\.?\d*)s', text)
            if time_match:
                query_time = float(time_match.group(1))
                if query_time >= 10:
                    score += 4
                elif query_time >= 5:
                    score += 2

    elif source_type in ['app', 'streamlit']:
        msg_lower = text
        if 'timeout' in msg_lower or 'exception' in msg_lower:
            score += 2
        if 'brute' in msg_lower or 'failed password' in msg_lower:
            score += 3
        if 'sql injection' in msg_lower:
            score += 4

    elif source_type == 'multi_source':
        # Multi-source: apply scoring from all source types for max coverage
        # VPC signals
        if 'REJECT' in (entry.content or ''):
            score += 3
        for port in _ATTACK_PORTS:
            if f' {port} ' in (entry.content or ''):
                score += 2
                break
        # CloudTrail signals
        content_lower = (entry.content or '').lower()
        if 'accessdenied' in content_lower or 'unauthorizedoperation' in content_lower:
            score += 3
        for api in _SENSITIVE_APIS:
            if api in content_lower:
                score += 3
                break
        # App signals
        if 'timeout' in text or 'exception' in text:
            score += 2
        if 'brute' in text or 'failed password' in text:
            score += 3
        if 'sql injection' in text:
            score += 4

    return score


# ---------------------------------------------------------------------------
# Actor extraction helpers
# ---------------------------------------------------------------------------

_IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


def _extract_ips(entries: List[LogEntry]) -> Counter:
    """Count IP addresses across all entries."""
    ip_counter = Counter()
    for entry in entries:
        raw = (entry.content or '') + ' ' + (entry.message or '')
        for ip in _IP_PATTERN.findall(raw):
            # Skip common private/loopback/AWS metadata
            if ip.startswith('127.') or ip == '0.0.0.0' or ip.startswith('169.254.'):
                continue
            # Skip private IPs unless they appear frequently (internal scanning)
            if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                # Only count if appears multiple times (potential internal threat)
                ip_counter[ip] += 1
            else:
                # Public IPs are always interesting
                ip_counter[ip] += 1
    return ip_counter


def _extract_cloudtrail_actors(entries: List[LogEntry]) -> tuple:
    """Extract IAM users and API actions from CloudTrail entries."""
    user_counter = Counter()
    api_counter = Counter()
    for entry in entries:
        try:
            data = json.loads(entry.content or '')
        except Exception:
            continue
        # User/ARN
        uid = data.get('userIdentity', {})
        arn = uid.get('arn', uid.get('principalId', ''))
        if arn:
            user_counter[arn] += 1
        # API action
        event_name = data.get('eventName', '')
        if event_name:
            error_code = data.get('errorCode', '')
            label = f"{event_name} ({error_code})" if error_code else event_name
            api_counter[label] += 1
    return user_counter, api_counter


def _extract_app_components(entries: List[LogEntry]) -> Counter:
    """Extract component names from app log entries."""
    comp_counter = Counter()
    for entry in entries:
        if entry.component:
            comp_counter[entry.component] += 1
    return comp_counter


# ---------------------------------------------------------------------------
# Main preprocessor class
# ---------------------------------------------------------------------------

class LogPreprocessor:
    """
    Prepares structured AIContext from parsed log entries.
    Designed for single-log-group analysis.
    """

    def __init__(self, max_samples: int = 8):
        """
        Args:
            max_samples: max representative log samples to include in context
        """
        self.max_samples = max_samples

    def prepare_ai_context(
        self,
        entries: List[LogEntry],
        analysis: AnalysisData,
        log_group_name: str,
        search_term: str = "",
        time_range_str: str = "",
        correlation_metadata: Optional[Dict] = None  # NEW: correlation context
    ) -> AIContext:
        """
        Build structured AIContext from parsed entries and pattern analysis.

        Args:
            entries: list of parsed LogEntry objects from one log group
            analysis: AnalysisData from PatternAnalyzer
            log_group_name: the CloudWatch log group being analyzed
            correlation_metadata: (Optional) correlation context from AdvancedCorrelator

        Returns:
            AIContext ready to be consumed by BedrockEnhancer
        """
        source_type = detect_source_type(log_group_name)

        # --- Score every entry ---
        if source_type == 'multi_source':
            # Per-entry scoring: each entry scored by its own source type
            scored = []
            for e in entries:
                entry_source = detect_source_type(e.component or '')
                scored.append((score_entry(e, entry_source), e))
        else:
            scored = [(score_entry(e, source_type), e) for e in entries]
        scored.sort(key=lambda x: x[0], reverse=True)

        # --- Severity summary (from analysis, already computed) ---
        severity_summary = dict(analysis.severity_distribution)

        # --- Top patterns ---
        top_patterns = [
            {'pattern': p.pattern, 'count': p.count, 'component': p.component}
            for p in analysis.error_patterns[:5]
        ]

        # --- Suspicious IPs ---
        ip_counts = _extract_ips(entries)
        suspicious_ips = [
            {'ip': ip, 'count': count, 'context': 'frequent'}
            for ip, count in ip_counts.most_common(5)
            if count >= 2
        ]

        # --- Source-specific actor extraction ---
        suspicious_users = []
        suspicious_apis = []
        if source_type == 'cloudtrail':
            user_counts, api_counts = _extract_cloudtrail_actors(entries)
            suspicious_users = [
                {'user': u, 'count': c, 'context': 'error-associated'}
                for u, c in user_counts.most_common(5)
            ]
            suspicious_apis = [
                {'api': a, 'count': c, 'context': 'called'}
                for a, c in api_counts.most_common(5)
            ]

        # --- Representative samples (diverse, high-scoring) ---
        samples = self._select_samples(scored, source_type)

        # --- Within-source correlation hints ---
        hints = self._build_hints(source_type, ip_counts, suspicious_users, suspicious_apis, analysis)

        # --- Temporal analysis (NEW) ---
        temporal_analysis = analysis.time_pattern or {}

        # --- Build base context ---
        context = AIContext(
            source_type=source_type,
            log_group_name=log_group_name,
            total_logs_pulled=len(entries),
            total_logs_after_scoring=len([s for s, _ in scored if s >= 3]),
            search_term=search_term,
            time_range_str=time_range_str,
            severity_summary=severity_summary,
            top_patterns=top_patterns,
            suspicious_ips=suspicious_ips,
            suspicious_users=suspicious_users,
            suspicious_apis=suspicious_apis,
            representative_samples=samples,
            within_source_hints=hints,
            temporal_analysis=temporal_analysis,
        )

        # --- Add correlation metadata if available (Priority 1 enhancement) ---
        if correlation_metadata:
            context.is_multi_source = True
            context.correlation_metadata = correlation_metadata
            context.correlation_keys_used = correlation_metadata.get('correlation_keys_used', [])
            
            # Build human-readable summary of correlated events
            correlated_events = correlation_metadata.get('correlated_events', [])
            if correlated_events:
                summary_lines = [
                    f"🔗 MULTI-SOURCE CORRELATION DETECTED ({len(correlated_events)} attack patterns):",
                    ""
                ]
                for i, event in enumerate(correlated_events[:5], 1):
                    summary_lines.append(
                        f"{i}. {event.attack_name} "
                        f"(Confidence: {event.confidence_score:.1f}%, "
                        f"Sources: {len(event.sources)}, "
                        f"Events: {len(event.timeline)})"
                    )
                    summary_lines.append(f"   Correlation keys: {', '.join(k for k, v in event.correlation_keys.items() if v)}")
                    ts_start = event.timeline[0].timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(event.timeline[0].timestamp, 'strftime') else str(event.timeline[0].timestamp)
                    ts_end = event.timeline[-1].timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(event.timeline[-1].timestamp, 'strftime') else str(event.timeline[-1].timestamp)
                    summary_lines.append(f"   Timeline: {ts_start} → {ts_end}")
                    if event.matched_rules:
                        summary_lines.append(f"   Matched rules: {', '.join(event.matched_rules[:3])}")
                    summary_lines.append("")
                
                context.correlated_events_summary = "\n".join(summary_lines)

        return context

    # ---- internal helpers ----

    def _select_samples(
        self,
        scored: list,
        source_type: str
    ) -> List[str]:
        """
        Pick representative log samples for the AI prompt using a diverse strategy.
        Selects based on severity, actors, and patterns, adding 'Why' metadata.
        """
        seen_patterns = set()
        samples = []
        
        def _add_sample(entry_tuple_list, reason, quota):
            count = 0
            for score, entry in entry_tuple_list:
                if count >= quota:
                    break
                raw = (entry.content or '').strip()
                if not raw:
                    continue
                
                # Enhanced dedup: normalize digits and IP-like structures
                fingerprint = re.sub(r'\d+', '<NUM>', raw[:120])
                if fingerprint in seen_patterns:
                    continue
                seen_patterns.add(fingerprint)
                
                # Truncate very long log lines for prompt efficiency
                truncated = raw if len(raw) <= 350 else raw[:350] + '...<TRUNCATED>'
                sample_text = f"[Selected because: {reason}] {truncated}"
                samples.append(sample_text)
                count += 1

        # 1. High severity (Score >= 4)
        high_sev = [(s, e) for s, e in scored if s >= 4]
        _add_sample(high_sev, "Highest severity/Critical error", 3)
        
        # 2. Suspicious Actors (IPs or specific user ARNs based on keyword)
        actors = []
        for s, e in scored:
            text = (e.content or '').lower() + (e.message or '').lower()
            if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text) or 'arn:aws:' in text or 'root' in text:
                actors.append((s, e))
        _add_sample(actors, "Contains suspicious actor (IP/User)", 2)
        
        # 3. Repeated Patterns (Score 2-3)
        patterns = [(s, e) for s, e in scored if 2 <= s <= 3]
        _add_sample(patterns, "Frequent error pattern", 2)
        
        # 4. Context / Baseline (Score 0-1)
        context = [(s, e) for s, e in scored if s <= 1]
        _add_sample(context, "Context / baseline activity", 1)
        
        # Fallback if we didn't fill the quota
        if len(samples) < self.max_samples:
            _add_sample(scored, "High relevance fallback", self.max_samples - len(samples))
            
        return samples

    def _build_hints(
        self,
        source_type: str,
        ip_counts: Counter,
        suspicious_users: list,
        suspicious_apis: list,
        analysis: AnalysisData
    ) -> List[str]:
        """
        Build within-source correlation hints.
        Enhanced to support all log group types and temporal patterns.
        """
        hints = []

        # Hint: repeated IPs with high counts
        for ip, count in ip_counts.most_common(3):
            if count >= 5:
                context = "connection attempts" if source_type == 'vpc_flow' else "requests"
                if source_type == 'apache':
                    context = "HTTP requests"
                elif source_type == 'syslog':
                    context = "SSH attempts"
                hints.append(
                    f"IP {ip} appears {count} times — may indicate repeated {context}"
                )

        # Hint: same user triggering multiple error types (CloudTrail)
        if source_type == 'cloudtrail' and len(suspicious_apis) >= 2:
            api_names = [a['api'] for a in suspicious_apis[:3]]
            hints.append(
                f"Multiple security-relevant API actions detected: {', '.join(api_names)}. "
                "This may indicate intentional probing or misconfigured permissions."
            )

        # Hint: high error concentration in one component (App)
        if source_type in ['app', 'streamlit'] and analysis.components:
            total = sum(analysis.components.values())
            for comp, count in analysis.components.items():
                ratio = count / total if total > 0 else 0
                if ratio > 0.5 and count >= 5:
                    hints.append(
                        f"Component '{comp}' accounts for {ratio:.0%} of all log entries — "
                        "may be the primary failure point"
                    )

        # Hint: Apache attack patterns
        if source_type == 'apache':
            attack_count = sum(1 for p in analysis.error_patterns if any(
                x in p.pattern.lower() for x in ['attack', 'injection', 'traversal', 'xss']
            ))
            if attack_count >= 2:
                hints.append(
                    f"Detected {attack_count} different attack patterns in HTTP logs — "
                    "possible coordinated attack or vulnerability scanning"
                )

        # Hint: SSH brute force patterns
        if source_type == 'syslog':
            failed_auth_count = sum(1 for p in analysis.error_patterns if 
                'failed password' in p.pattern.lower() or 'authentication failure' in p.pattern.lower()
            )
            if failed_auth_count >= 1:
                total_attempts = sum(p.count for p in analysis.error_patterns if 
                    'failed password' in p.pattern.lower()
                )
                if total_attempts >= 10:
                    hints.append(
                        f"Detected {total_attempts} failed authentication attempts — "
                        "likely SSH brute force attack"
                    )

        # Hint: MySQL slow queries
        if source_type == 'mysql_slow':
            slow_count = len(analysis.error_patterns)
            if slow_count >= 3:
                hints.append(
                    f"Found {slow_count} different slow query patterns — "
                    "may indicate missing indexes or inefficient queries"
                )

        # Hint: MySQL connection issues
        if source_type == 'mysql_error':
            conn_errors = sum(1 for p in analysis.error_patterns if 
                'access denied' in p.pattern.lower() or 'connection' in p.pattern.lower()
            )
            if conn_errors >= 1:
                hints.append(
                    "Database connection/authentication errors detected — "
                    "check credentials and connection pool settings"
                )

        # NEW: Temporal pattern hints
        if analysis.time_pattern:
            tp = analysis.time_pattern
            if tp.get('is_burst_attack'):
                hints.append(
                    f"⚠️ BURST ATTACK DETECTED: {tp.get('events_per_minute', 0):.1f} events/minute "
                    f"over {tp.get('duration_minutes', 0):.1f} minutes. "
                    f"Peak activity at {tp.get('peak_activity_time', 'N/A')} with {tp.get('peak_activity_count', 0)} events."
                )
            elif tp.get('events_per_minute', 0) > 2:
                hints.append(
                    f"Elevated activity: {tp.get('events_per_minute', 0):.1f} events/minute "
                    f"(duration: {tp.get('duration_minutes', 0):.1f} min)"
                )

        return hints


# ============================================================
# Event Abstraction Layer — signals, not raw logs
# ============================================================

def extract_event_signals(
    entries: List[LogEntry],
    analysis: AnalysisData,
    correlated_events: list = None,
    per_source_entries: Dict[str, List[LogEntry]] = None,
) -> list:
    """
    Convert raw patterns + correlation into compact EventSignal objects.
    AI receives signals (structured, small) instead of raw logs (bloated, noisy).
    
    Returns list of dicts (serializable EventSignals).
    """
    from models import EventSignal
    signals = []
    
    # --- 1. Signals from error patterns (PatternAnalyzer output) ---
    for pattern in analysis.error_patterns[:15]:  # cap at 15 patterns
        # Detect event type from pattern text
        p_lower = pattern.pattern.lower()
        event_type = "error"
        severity = "MEDIUM"
        anomaly_score = min(pattern.count / 50.0, 1.0)  # normalize
        
        if any(kw in p_lower for kw in ['reject', 'denied', 'refused']):
            event_type = "network_reject"
            severity = "HIGH"
        elif any(kw in p_lower for kw in ['injection', 'union select', 'xss', 'traversal']):
            event_type = "attack_attempt"
            severity = "CRITICAL"
            anomaly_score = max(anomaly_score, 0.9)
        elif any(kw in p_lower for kw in ['timeout', 'unreachable', 'connection reset']):
            event_type = "connection_failure"
            severity = "HIGH"
        elif any(kw in p_lower for kw in ['accessdenied', 'unauthorized', 'forbidden']):
            event_type = "access_denied"
            severity = "HIGH"
        elif any(kw in p_lower for kw in ['slow query', 'query_time']):
            event_type = "slow_query"
            severity = "MEDIUM"
        elif any(kw in p_lower for kw in ['aborted connection', 'too many connection']):
            event_type = "database_stress"
            severity = "HIGH"
        
        # Extract IPs from pattern
        actors = list(set(_IP_PATTERN.findall(pattern.pattern)))
        
        signals.append({
            'event_type': event_type,
            'source': pattern.component,
            'severity': severity,
            'count': pattern.count,
            'description': pattern.pattern[:150],
            'actors': actors[:3],
            'anomaly_score': round(anomaly_score, 2),
        })
    
    # --- 2. Signals from correlated attacks (AdvancedCorrelator output) ---
    if correlated_events:
        for event in correlated_events:
            # Build time window string
            if event.timeline:
                ts_start = event.timeline[0].timestamp
                ts_end = event.timeline[-1].timestamp
                ts_fmt = lambda t: t.strftime('%H:%M:%S') if hasattr(t, 'strftime') else str(t)
                duration = (ts_end - ts_start).total_seconds() if hasattr(ts_end, '__sub__') else 0
                time_window = f"{ts_fmt(ts_start)} -> {ts_fmt(ts_end)} ({duration:.0f}s)"
            else:
                time_window = "unknown"
            
            # Extract actors from timeline
            actors = list(set(t.actor for t in event.timeline if t.actor))[:5]
            
            signals.append({
                'event_type': f"correlated_attack:{event.attack_name}",
                'source': ', '.join(event.sources),
                'severity': event.severity,
                'count': len(event.timeline),
                'time_window': time_window,
                'actors': actors,
                'targets': [],
                'indicators': {
                    'matched_rules': event.matched_rules or [],
                    'correlation_keys': {k: v for k, v in event.correlation_keys.items() if v},
                },
                'anomaly_score': round(event.confidence_score / 100.0, 2),
                'description': event.ai_recommendation[:200] if event.ai_recommendation else event.attack_name,
            })
    
    # --- 3. Per-source anomaly signals ---
    if per_source_entries:
        for source, source_entries in per_source_entries.items():
            source_type = detect_source_type(source)
            
            # Count severities
            sev_dist = Counter(
                (e.severity or 'UNKNOWN').upper() for e in source_entries
            )
            error_count = sev_dist.get('ERROR', 0) + sev_dist.get('CRITICAL', 0)
            total = len(source_entries)
            error_rate = error_count / total if total > 0 else 0
            
            if error_rate > 0.3:  # More than 30% errors = anomaly
                signals.append({
                    'event_type': 'high_error_rate',
                    'source': source,
                    'severity': 'HIGH' if error_rate > 0.5 else 'MEDIUM',
                    'count': error_count,
                    'description': f"Error rate {error_rate:.0%} ({error_count}/{total} entries)",
                    'anomaly_score': round(min(error_rate * 1.5, 1.0), 2),
                })
    
    return signals


def build_unified_context(
    per_source_entries: Dict[str, List[LogEntry]],
    analysis: AnalysisData,
    correlated_events: list = None,
    time_range_str: str = "",
) -> dict:
    """
    Build ONE compact, unified context for Global RCA.
    Contains signals (not raw logs), per-source summaries, and correlation results.
    
    Returns a dict that can be serialized into the AI prompt.
    """
    # --- Per-source summaries ---
    source_summaries = {}
    all_entries = []
    for source, entries in per_source_entries.items():
        all_entries.extend(entries)
        sev_dist = Counter((e.severity or 'UNKNOWN').upper() for e in entries)
        error_count = sev_dist.get('ERROR', 0) + sev_dist.get('CRITICAL', 0)
        total = len(entries)
        
        # Extract top IPs for this source
        ip_counts = _extract_ips(entries)
        top_ips = [{'ip': ip, 'count': c} for ip, c in ip_counts.most_common(3)]
        
        source_summaries[source] = {
            'total_entries': total,
            'error_count': error_count,
            'error_rate': f"{(error_count / total * 100):.1f}%" if total > 0 else "0%",
            'severity_distribution': dict(sev_dist),
            'top_ips': top_ips,
        }
    
    # --- Extract event signals ---
    signals = extract_event_signals(
        entries=all_entries,
        analysis=analysis,
        correlated_events=correlated_events,
        per_source_entries=per_source_entries,
    )
    
    # --- Build incident timeline from correlated events ---
    incident_timeline = []
    if correlated_events:
        for event in correlated_events:
            for t_event in event.timeline:
                ts_str = t_event.timestamp.strftime('%H:%M:%S') if hasattr(t_event.timestamp, 'strftime') else str(t_event.timestamp)
                incident_timeline.append({
                    'time': ts_str,
                    'source': t_event.source,
                    'event': t_event.event_type,
                    'actor': t_event.actor,
                    'message': (t_event.message or '')[:100],
                })
        incident_timeline.sort(key=lambda x: x['time'])
    
    # --- Top suspicious IPs (global) ---
    global_ip_counts = _extract_ips(all_entries)
    suspicious_ips = [
        {'ip': ip, 'count': c, 'is_external': not (ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'))}
        for ip, c in global_ip_counts.most_common(5)
        if c >= 2
    ]
    
    # --- Select a few critical raw samples (max 5, only highest severity) ---
    critical_samples = []
    for e in all_entries:
        if (e.severity or '').upper() in ('CRITICAL', 'ERROR', 'FATAL'):
            text = (e.content or '').strip()
            if text and len(critical_samples) < 5:
                truncated = text[:250] + '...' if len(text) > 250 else text
                critical_samples.append(f"[{e.component}] {truncated}")
    
    return {
        'source_count': len(per_source_entries),
        'total_logs': len(all_entries),
        'time_range': time_range_str,
        'source_summaries': source_summaries,
        'signals': signals,
        'incident_timeline': incident_timeline[:20],  # cap at 20 events
        'suspicious_ips': suspicious_ips,
        'critical_samples': critical_samples,
        'correlation_count': len(correlated_events) if correlated_events else 0,
    }


def build_deep_dive_context(
    log_group: str,
    entries: List[LogEntry],
    analysis: AnalysisData,
    global_rca_summary: str = "",
) -> dict:
    """
    Build enriched context for Deep Dive into a single log group.
    Includes metrics + anomalies + raw samples + global RCA reference.
    AI explains (based on known context), not guesses.
    """
    source_type = detect_source_type(log_group)
    
    # --- Component metrics ---
    sev_dist = Counter((e.severity or 'UNKNOWN').upper() for e in entries)
    error_count = sev_dist.get('ERROR', 0) + sev_dist.get('CRITICAL', 0)
    total = len(entries)
    
    # --- Anomalies (patterns with unusual counts) ---
    anomalies = []
    for pattern in analysis.error_patterns[:10]:
        if pattern.component == log_group or not pattern.component:
            p_lower = pattern.pattern.lower()
            is_security = any(kw in p_lower for kw in [
                'inject', 'denied', 'reject', 'brute', 'attack',
                'unauthorized', 'exploit', 'traversal'
            ])
            anomalies.append({
                'pattern': pattern.pattern[:120],
                'count': pattern.count,
                'is_security_relevant': is_security,
                'anomaly_score': round(min(pattern.count / 20.0, 1.0), 2),
            })
    
    # --- Top raw samples (most relevant, max 8) ---
    scored = []
    for e in entries:
        entry_source = detect_source_type(e.component or log_group)
        s = score_entry(e, entry_source)
        scored.append((s, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    
    raw_samples = []
    seen = set()
    for score, e in scored:
        text = (e.content or '').strip()
        if not text:
            continue
        fingerprint = re.sub(r'\d+', '<N>', text[:80])
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        truncated = text[:300] + '...' if len(text) > 300 else text
        raw_samples.append(truncated)
        if len(raw_samples) >= 8:
            break
    
    # --- Extract IPs ---
    ip_counts = _extract_ips(entries)
    top_ips = [{'ip': ip, 'count': c} for ip, c in ip_counts.most_common(5)]
    
    return {
        'log_group': log_group,
        'source_type': source_type,
        'global_rca_summary': global_rca_summary,
        'component_metrics': {
            'total_entries': total,
            'error_count': error_count,
            'error_rate': f"{(error_count / total * 100):.1f}%" if total > 0 else "0%",
            'severity_distribution': dict(sev_dist),
        },
        'anomalies': anomalies,
        'top_ips': top_ips,
        'raw_samples': raw_samples,
    }
