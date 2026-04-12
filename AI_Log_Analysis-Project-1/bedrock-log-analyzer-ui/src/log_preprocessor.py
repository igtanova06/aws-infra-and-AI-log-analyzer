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


# ---------------------------------------------------------------------------
# Source type detection
# ---------------------------------------------------------------------------

def detect_source_type(log_group_name: str) -> str:
    """
    Infer log source type from the CloudWatch log group name.
    Returns 'vpc_flow', 'cloudtrail', or 'app'.
    """
    name_lower = log_group_name.lower()
    if 'vpc' in name_lower or 'flowlog' in name_lower:
        return 'vpc_flow'
    if 'cloudtrail' in name_lower or 'trail' in name_lower:
        return 'cloudtrail'
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


def score_entry(entry: LogEntry, source_type: str) -> int:
    """
    Score a single parsed LogEntry by relevance to AI analysis.
    Higher score = more important for the AI to see.
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

    elif source_type == 'app':
        msg_lower = text
        if 'timeout' in msg_lower or 'exception' in msg_lower:
            score += 2
        if 'brute' in msg_lower or 'failed password' in msg_lower:
            score += 3

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
            # Skip common private/loopback
            if ip.startswith('127.') or ip == '0.0.0.0':
                continue
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
        time_range_str: str = ""
    ) -> AIContext:
        """
        Build structured AIContext from parsed entries and pattern analysis.

        Args:
            entries: list of parsed LogEntry objects from one log group
            analysis: AnalysisData from PatternAnalyzer
            log_group_name: the CloudWatch log group being analyzed

        Returns:
            AIContext ready to be consumed by BedrockEnhancer
        """
        source_type = detect_source_type(log_group_name)

        # --- Score every entry ---
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

        return AIContext(
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
        )

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
        These are presented as hints, not conclusions.
        """
        hints = []

        # Hint: repeated IPs with high counts
        for ip, count in ip_counts.most_common(3):
            if count >= 5:
                hints.append(
                    f"IP {ip} appears {count} times — may indicate repeated "
                    f"{'connection attempts' if source_type == 'vpc_flow' else 'activity'}"
                )

        # Hint: same user triggering multiple error types (CloudTrail)
        if source_type == 'cloudtrail' and len(suspicious_apis) >= 2:
            api_names = [a['api'] for a in suspicious_apis[:3]]
            hints.append(
                f"Multiple security-relevant API actions detected: {', '.join(api_names)}. "
                "This may indicate intentional probing or misconfigured permissions."
            )

        # Hint: high error concentration in one component (App)
        if source_type == 'app' and analysis.components:
            total = sum(analysis.components.values())
            for comp, count in analysis.components.items():
                ratio = count / total if total > 0 else 0
                if ratio > 0.5 and count >= 5:
                    hints.append(
                        f"Component '{comp}' accounts for {ratio:.0%} of all log entries — "
                        "may be the primary failure point"
                    )

        return hints
