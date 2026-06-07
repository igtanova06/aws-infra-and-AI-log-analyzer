"""
Data models for log analysis
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from enum import Enum
import json


class IssueType(Enum):
    """Types of issues that can be detected"""
    CONNECTION = "connection"
    PERMISSION = "permission"
    RESOURCE = "resource"
    DATABASE = "database"
    SECURITY = "security"
    GENERAL = "general"


@dataclass
class LogEntry:
    """Represents a single log entry"""
    file: str
    line_number: int
    content: str
    timestamp: Optional[str] = None
    severity: Optional[str] = None
    component: Optional[str] = None
    message: Optional[str] = None


@dataclass
class ErrorPattern:
    """Represents a pattern found in error logs"""
    component: str
    pattern: str
    count: int


@dataclass
class AnalysisData:
    """Results from log analysis"""
    total_entries: int
    severity_distribution: Dict[str, int]
    components: Dict[str, int]
    error_patterns: List[ErrorPattern]
    time_pattern: Optional[Dict] = None


@dataclass
class Solution:
    """Represents a solution to a detected issue"""
    problem: str
    solution: str
    issue_type: IssueType = IssueType.GENERAL
    affected_components: List[str] = field(default_factory=list)
    ai_enhanced: bool = False
    tokens_used: Optional[int] = None
    estimated_cost: Optional[float] = None
    structured_solution: Optional[dict] = field(default=None)


@dataclass
class Metadata:
    """Metadata about the analysis"""
    timestamp: str
    search_term: str
    log_directory: str
    total_files_searched: int
    total_matches: int


@dataclass
class AIInfo:
    """Information about AI enhancement"""
    ai_enhancement_used: bool
    bedrock_model_used: Optional[str] = None
    total_tokens_used: Optional[int] = None
    estimated_total_cost: Optional[float] = None
    api_calls_made: Optional[int] = None


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    metadata: Metadata
    matches: List[LogEntry]
    analysis: AnalysisData
    solutions: List[Solution]
    ai_info: Optional[AIInfo] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'metadata': asdict(self.metadata),
            'matches': [asdict(m) for m in self.matches],
            'analysis': {
                'total_entries': self.analysis.total_entries,
                'severity_distribution': self.analysis.severity_distribution,
                'components': self.analysis.components,
                'error_patterns': [asdict(p) for p in self.analysis.error_patterns],
                'time_pattern': self.analysis.time_pattern
            },
            'solutions': [
                {
                    'problem': s.problem,
                    'solution': s.solution,
                    'issue_type': s.issue_type.value,
                    'affected_components': s.affected_components,
                    'ai_enhanced': s.ai_enhanced,
                    'tokens_used': s.tokens_used,
                    'estimated_cost': s.estimated_cost,
                    'structured_solution': s.structured_solution
                }
                for s in self.solutions
            ],
            'ai_info': asdict(self.ai_info) if self.ai_info else None
        }
    
    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================
# Event Abstraction Layer — signals, not raw logs
# ============================================================

@dataclass
class EventSignal:
    """
    Abstracted security event — compact, token-efficient.
    Replaces raw log lines in AI context to stay within token limits.
    """
    event_type: str              # "port_scan_burst", "sql_injection", "api_deny"
    source: str                  # "/aws/vpc/flowlogs"
    severity: str                # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    count: int                   # number of raw events this represents
    time_window: str             # "12:46:33 → 12:47:30 (57s)"
    actors: List[str] = field(default_factory=list)  # IPs, users, ARNs
    targets: List[str] = field(default_factory=list)  # destination IPs, resources
    indicators: Dict = field(default_factory=dict)    # ports, paths, queries
    anomaly_score: float = 0.0   # 0.0 - 1.0 (how abnormal vs baseline)
    description: str = ""        # human-readable summary


@dataclass
class GlobalRCA:
    """
    Result from Global Root Cause Analysis.
    AI sees the FULL picture once and produces this comprehensive report.
    """
    # Incident Story (TL;DR)
    incident_story: List[str] = field(default_factory=list)  # ordered timeline sentences
    
    # Threat Assessment with confidence
    threat_assessment: Dict = field(default_factory=dict)
    # Example: {
    #   "severity": "Critical",
    #   "confidence": 0.87,
    #   "reasoning": "3 sources corroborate, IP matches across VPC+App+CloudTrail",
    #   "scope": "VPC, Application, IAM"
    # }
    
    # AI-generated narrative
    attack_narrative: str = ""
    
    # Affected components with impact
    affected_components: List[Dict] = field(default_factory=list)
    # [{component, impact_level, evidence}]
    
    # Root cause
    root_cause: str = ""
    
    # MITRE mapping
    mitre_mapping: Dict = field(default_factory=dict)
    
    # Immediate actions (AWS CLI commands)
    immediate_actions: List[Dict] = field(default_factory=list)
    # [{action, command, priority}]
    
    # Remediation plan
    remediation_plan: Dict = field(default_factory=dict)
    # {short_term: [...], medium_term: [...], long_term: [...]}
    
    # Raw AI response for debugging
    raw_ai_response: Dict = field(default_factory=dict)
    
    # Cost tracking
    tokens_used: int = 0
    cost: float = 0.0


@dataclass
class DeepDiveResult:
    """
    Result from Deep Dive into a single log group.
    Enriched with Global RCA context so AI explains rather than guesses.
    """
    log_group: str
    
    # Component-level analysis
    component_summary: str = ""
    specific_findings: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metrics that ground the AI analysis
    component_metrics: Dict = field(default_factory=dict)
    # {error_rate, anomaly_score, severity_distribution}
    
    anomalies: List[Dict] = field(default_factory=list)
    # [{pattern, count, baseline, anomaly_score}]
    
    # Reference back to global context
    global_rca_reference: str = ""
    
    # Raw AI response
    raw_ai_response: Dict = field(default_factory=dict)
    
    # Cost tracking
    tokens_used: int = 0
    cost: float = 0.0
