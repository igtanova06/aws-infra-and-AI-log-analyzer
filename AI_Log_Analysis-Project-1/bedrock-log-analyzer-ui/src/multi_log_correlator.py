"""
Multi-Log Correlator - Correlate events across multiple log sources
Connects the dots between VPC Flow, CloudTrail, Application, and Database logs
to build a complete attack timeline and root cause analysis.

Example Use Case:
1. VPC Flow: IP 203.0.113.42 → Port 80 (REJECT)
2. CloudTrail: Same IP tries DeleteVpc API (AccessDenied)
3. Application: Same IP sends SQL injection to /api/login.php
4. Database: Connection spike from web tier

Correlator Output: "Coordinated attack from 203.0.113.42 targeting multiple layers"
"""
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime, timedelta
from models import LogEntry, AnalysisData


# ============================================================
# Data Models
# ============================================================

@dataclass
class CorrelationKey:
    """Keys used to correlate logs across sources"""
    ip_addresses: Set[str] = field(default_factory=set)
    user_arns: Set[str] = field(default_factory=set)
    instance_ids: Set[str] = field(default_factory=set)
    api_actions: Set[str] = field(default_factory=set)
    time_window: Optional[Tuple[datetime, datetime]] = None


@dataclass
class CorrelatedEvent:
    """A correlated event across multiple log sources"""
    correlation_id: str                    # Unique ID for this correlation
    primary_actor: str                     # Main IP/user involved
    event_type: str                        # "attack", "misconfiguration", "performance"
    severity: str                          # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    
    # Timeline
    first_seen: str
    last_seen: str
    duration_minutes: float
    
    # Evidence from each source
    vpc_flow_events: List[Dict] = field(default_factory=list)
    cloudtrail_events: List[Dict] = field(default_factory=list)
    application_events: List[Dict] = field(default_factory=list)
    database_events: List[Dict] = field(default_factory=list)
    
    # Analysis
    attack_chain: List[str] = field(default_factory=list)  # Step-by-step attack progression
    affected_resources: Set[str] = field(default_factory=set)
    confidence_score: float = 0.0          # 0-100, how confident we are in correlation
    
    # Summary
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)


@dataclass
class MultiSourceContext:
    """Context built from multiple log sources for AI analysis"""
    correlated_events: List[CorrelatedEvent] = field(default_factory=list)
    cross_source_patterns: List[Dict] = field(default_factory=list)
    timeline_visualization: str = ""
    total_sources_analyzed: int = 0


# ============================================================
# Multi-Log Correlator
# ============================================================

class MultiLogCorrelator:
    """
    Correlate events across multiple CloudWatch log groups.
    Builds a unified timeline and identifies cross-source attack patterns.
    """
    
    def __init__(self):
        self.ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        self.instance_pattern = re.compile(r'\b(i-[a-f0-9]{8,17})\b')
        self.arn_pattern = re.compile(r'arn:aws:[^:]+:[^:]*:[^:]*:[^/]+/[^\s"]+')
        
    def correlate_multi_source(
        self,
        log_sources: Dict[str, Tuple[List[LogEntry], AnalysisData]]
    ) -> MultiSourceContext:
        """
        Correlate logs from multiple sources.
        
        Args:
            log_sources: Dict mapping log_group_name → (entries, analysis)
                Example: {
                    "/aws/vpc/flowlogs": (vpc_entries, vpc_analysis),
                    "/aws/cloudtrail/logs": (ct_entries, ct_analysis),
                    "/aws/ec2/application": (app_entries, app_analysis),
                }
        
        Returns:
            MultiSourceContext with correlated events
        """
        # Step 1: Extract correlation keys from each source
        correlation_keys = self._extract_correlation_keys(log_sources)
        
        # Step 2: Find overlapping actors (IPs, users, instances)
        overlapping_actors = self._find_overlapping_actors(correlation_keys)
        
        # Step 3: Build correlated events for each actor
        correlated_events = []
        for actor in overlapping_actors:
            event = self._build_correlated_event(actor, log_sources, correlation_keys)
            if event:
                correlated_events.append(event)
        
        # Step 4: Identify cross-source patterns
        cross_patterns = self._identify_cross_source_patterns(log_sources, correlated_events)
        
        # Step 5: Build timeline visualization
        timeline = self._build_timeline_visualization(correlated_events)
        
        return MultiSourceContext(
            correlated_events=correlated_events,
            cross_source_patterns=cross_patterns,
            timeline_visualization=timeline,
            total_sources_analyzed=len(log_sources)
        )
    
    # ---- Internal Methods ----
    
    def _extract_correlation_keys(
        self,
        log_sources: Dict[str, Tuple[List[LogEntry], AnalysisData]]
    ) -> Dict[str, CorrelationKey]:
        """Extract correlation keys (IPs, users, instances) from each source"""
        keys_by_source = {}
        
        for log_group, (entries, analysis) in log_sources.items():
            key = CorrelationKey()
            
            # Extract IPs
            for entry in entries:
                text = (entry.content or '') + ' ' + (entry.message or '')
                ips = self.ip_pattern.findall(text)
                key.ip_addresses.update(ips)
            
            # Extract instance IDs
            for entry in entries:
                text = (entry.content or '') + ' ' + (entry.message or '')
                instances = self.instance_pattern.findall(text)
                key.instance_ids.update(instances)
            
            # Extract ARNs (CloudTrail specific)
            if 'cloudtrail' in log_group.lower():
                for entry in entries:
                    arns = self.arn_pattern.findall(entry.content or '')
                    key.user_arns.update(arns)
            
            # Extract API actions (CloudTrail specific)
            if 'cloudtrail' in log_group.lower():
                import json
                for entry in entries:
                    try:
                        data = json.loads(entry.content or '{}')
                        if 'eventName' in data:
                            key.api_actions.add(data['eventName'])
                    except:
                        pass
            
            keys_by_source[log_group] = key
        
        return keys_by_source
    
    def _find_overlapping_actors(
        self,
        correlation_keys: Dict[str, CorrelationKey]
    ) -> List[str]:
        """Find actors (IPs/users) that appear in multiple log sources"""
        # Count how many sources each IP appears in
        ip_sources = defaultdict(set)
        for source, keys in correlation_keys.items():
            for ip in keys.ip_addresses:
                # Filter out private/internal IPs
                if not (ip.startswith('10.') or ip.startswith('192.168.') or 
                       ip.startswith('172.') or ip.startswith('127.')):
                    ip_sources[ip].add(source)
        
        # Return IPs that appear in 2+ sources (suspicious)
        overlapping = [ip for ip, sources in ip_sources.items() if len(sources) >= 2]
        return overlapping
    
    def _build_correlated_event(
        self,
        actor: str,
        log_sources: Dict[str, Tuple[List[LogEntry], AnalysisData]],
        correlation_keys: Dict[str, CorrelationKey]
    ) -> Optional[CorrelatedEvent]:
        """Build a correlated event for a specific actor"""
        vpc_events = []
        cloudtrail_events = []
        app_events = []
        db_events = []
        
        all_timestamps = []
        
        # Collect events from each source
        for log_group, (entries, analysis) in log_sources.items():
            for entry in entries:
                text = (entry.content or '') + ' ' + (entry.message or '')
                
                # Check if this entry involves the actor
                if actor not in text:
                    continue
                
                event_data = {
                    'timestamp': entry.timestamp,
                    'message': entry.message or entry.content[:200],
                    'severity': entry.severity,
                    'component': entry.component
                }
                
                # Categorize by source
                if 'vpc' in log_group.lower() or 'flowlog' in log_group.lower():
                    vpc_events.append(event_data)
                elif 'cloudtrail' in log_group.lower():
                    cloudtrail_events.append(event_data)
                elif 'rds' in log_group.lower() or 'mysql' in log_group.lower():
                    db_events.append(event_data)
                else:
                    app_events.append(event_data)
                
                # Collect timestamps
                if entry.timestamp:
                    all_timestamps.append(entry.timestamp)
        
        # Need events from at least 2 sources to correlate
        sources_count = sum([
            len(vpc_events) > 0,
            len(cloudtrail_events) > 0,
            len(app_events) > 0,
            len(db_events) > 0
        ])
        
        if sources_count < 2:
            return None
        
        # Calculate timeline
        if not all_timestamps:
            return None
        
        first_seen = min(all_timestamps)
        last_seen = max(all_timestamps)
        
        # Calculate duration (simplified - assumes timestamps are strings)
        duration_minutes = 5.0  # Placeholder
        
        # Determine event type and severity
        event_type, severity = self._classify_correlated_event(
            vpc_events, cloudtrail_events, app_events, db_events
        )
        
        # Build attack chain
        attack_chain = self._build_attack_chain(
            vpc_events, cloudtrail_events, app_events, db_events
        )
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(
            sources_count, len(vpc_events + cloudtrail_events + app_events + db_events)
        )
        
        # Generate summary
        summary = self._generate_correlation_summary(
            actor, event_type, sources_count, attack_chain
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(event_type, attack_chain)
        
        return CorrelatedEvent(
            correlation_id=f"CORR-{actor.replace('.', '-')}",
            primary_actor=actor,
            event_type=event_type,
            severity=severity,
            first_seen=first_seen,
            last_seen=last_seen,
            duration_minutes=duration_minutes,
            vpc_flow_events=vpc_events,
            cloudtrail_events=cloudtrail_events,
            application_events=app_events,
            database_events=db_events,
            attack_chain=attack_chain,
            confidence_score=confidence,
            summary=summary,
            recommendations=recommendations
        )
    
    def _classify_correlated_event(
        self,
        vpc_events: List[Dict],
        cloudtrail_events: List[Dict],
        app_events: List[Dict],
        db_events: List[Dict]
    ) -> Tuple[str, str]:
        """Classify the type and severity of correlated event"""
        # Check for attack patterns
        has_vpc_rejects = any('REJECT' in str(e.get('message', '')) for e in vpc_events)
        has_access_denied = any('denied' in str(e.get('message', '')).lower() for e in cloudtrail_events)
        has_app_errors = any(e.get('severity') in ['ERROR', 'CRITICAL'] for e in app_events)
        has_sql_injection = any('injection' in str(e.get('message', '')).lower() for e in app_events)
        
        # Determine event type
        if has_sql_injection or (has_vpc_rejects and has_app_errors):
            event_type = "coordinated_attack"
            severity = "CRITICAL"
        elif has_access_denied and has_vpc_rejects:
            event_type = "unauthorized_access_attempt"
            severity = "HIGH"
        elif has_app_errors and db_events:
            event_type = "application_database_issue"
            severity = "MEDIUM"
        else:
            event_type = "suspicious_activity"
            severity = "MEDIUM"
        
        return event_type, severity
    
    def _build_attack_chain(
        self,
        vpc_events: List[Dict],
        cloudtrail_events: List[Dict],
        app_events: List[Dict],
        db_events: List[Dict]
    ) -> List[str]:
        """Build step-by-step attack progression"""
        chain = []
        
        if vpc_events:
            chain.append(f"1. Network Layer: {len(vpc_events)} connection attempts detected")
        
        if cloudtrail_events:
            chain.append(f"2. API Layer: {len(cloudtrail_events)} AWS API calls made")
        
        if app_events:
            chain.append(f"3. Application Layer: {len(app_events)} application events triggered")
        
        if db_events:
            chain.append(f"4. Database Layer: {len(db_events)} database operations affected")
        
        return chain
    
    def _calculate_confidence_score(self, sources_count: int, total_events: int) -> float:
        """Calculate confidence score (0-100) for correlation"""
        # More sources + more events = higher confidence
        source_score = min(sources_count * 25, 50)  # Max 50 points
        event_score = min(total_events * 2, 50)     # Max 50 points
        return source_score + event_score
    
    def _generate_correlation_summary(
        self,
        actor: str,
        event_type: str,
        sources_count: int,
        attack_chain: List[str]
    ) -> str:
        """Generate human-readable summary"""
        event_names = {
            "coordinated_attack": "Coordinated Multi-Layer Attack",
            "unauthorized_access_attempt": "Unauthorized Access Attempt",
            "application_database_issue": "Application-Database Issue",
            "suspicious_activity": "Suspicious Activity"
        }
        
        name = event_names.get(event_type, "Unknown Event")
        
        return (
            f"{name} detected from {actor}. "
            f"Activity observed across {sources_count} log sources. "
            f"Attack progression: {len(attack_chain)} stages identified."
        )
    
    def _generate_recommendations(self, event_type: str, attack_chain: List[str]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if event_type == "coordinated_attack":
            recommendations.extend([
                "🚨 IMMEDIATE: Block IP in WAF and Security Groups",
                "🔍 INVESTIGATE: Check for data exfiltration attempts",
                "🛡️ HARDEN: Enable AWS GuardDuty for threat detection",
                "📊 MONITOR: Set up CloudWatch alarm for similar patterns"
            ])
        elif event_type == "unauthorized_access_attempt":
            recommendations.extend([
                "🔐 REVIEW: IAM policies and permissions",
                "🚨 ALERT: Notify security team immediately",
                "📝 AUDIT: Check CloudTrail for successful actions",
                "🛡️ ENFORCE: Enable MFA for all users"
            ])
        elif event_type == "application_database_issue":
            recommendations.extend([
                "🔍 INVESTIGATE: Check database connection pool settings",
                "📊 ANALYZE: Review slow query logs",
                "⚡ OPTIMIZE: Add database indexes if needed",
                "📈 SCALE: Consider increasing RDS instance size"
            ])
        else:
            recommendations.extend([
                "🔍 INVESTIGATE: Review full logs for context",
                "📊 MONITOR: Set up alerts for this pattern",
                "📝 DOCUMENT: Record findings for future reference"
            ])
        
        return recommendations
    
    def _identify_cross_source_patterns(
        self,
        log_sources: Dict[str, Tuple[List[LogEntry], AnalysisData]],
        correlated_events: List[CorrelatedEvent]
    ) -> List[Dict]:
        """Identify patterns that span multiple log sources"""
        patterns = []
        
        # Pattern 1: VPC REJECT → Application Error
        vpc_rejects = 0
        app_errors = 0
        for log_group, (entries, analysis) in log_sources.items():
            if 'vpc' in log_group.lower():
                vpc_rejects = sum(1 for e in entries if 'REJECT' in (e.content or ''))
            elif 'application' in log_group.lower() or 'ec2' in log_group.lower():
                app_errors = analysis.severity_distribution.get('ERROR', 0)
        
        if vpc_rejects > 10 and app_errors > 5:
            patterns.append({
                'pattern': 'Network blocks correlate with application errors',
                'confidence': 'HIGH',
                'description': f'{vpc_rejects} VPC REJECTs followed by {app_errors} app errors',
                'implication': 'Possible DDoS or network-based attack affecting application'
            })
        
        # Pattern 2: CloudTrail AccessDenied → Multiple Sources
        if len(correlated_events) >= 2:
            patterns.append({
                'pattern': 'Multi-source coordinated activity',
                'confidence': 'HIGH',
                'description': f'{len(correlated_events)} actors active across multiple layers',
                'implication': 'Coordinated attack or widespread misconfiguration'
            })
        
        return patterns
    
    def _build_timeline_visualization(self, correlated_events: List[CorrelatedEvent]) -> str:
        """Build ASCII timeline visualization"""
        if not correlated_events:
            return "No correlated events to visualize"
        
        lines = ["=" * 80]
        lines.append("CORRELATED EVENTS TIMELINE")
        lines.append("=" * 80)
        
        for i, event in enumerate(correlated_events, 1):
            lines.append(f"\n[{i}] {event.summary}")
            lines.append(f"    Actor: {event.primary_actor}")
            lines.append(f"    Severity: {event.severity} | Confidence: {event.confidence_score:.0f}%")
            lines.append(f"    Timeline: {event.first_seen} → {event.last_seen}")
            lines.append(f"    Sources: VPC({len(event.vpc_flow_events)}) | "
                        f"CloudTrail({len(event.cloudtrail_events)}) | "
                        f"App({len(event.application_events)}) | "
                        f"DB({len(event.database_events)})")
            
            if event.attack_chain:
                lines.append("    Attack Chain:")
                for step in event.attack_chain:
                    lines.append(f"      {step}")
        
        lines.append("\n" + "=" * 80)
        return "\n".join(lines)
