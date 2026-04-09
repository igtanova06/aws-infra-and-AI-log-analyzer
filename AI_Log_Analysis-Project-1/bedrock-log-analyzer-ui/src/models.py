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
                    'estimated_cost': s.estimated_cost
                }
                for s in self.solutions
            ],
            'ai_info': asdict(self.ai_info) if self.ai_info else None
        }
    
    def to_json(self):
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
