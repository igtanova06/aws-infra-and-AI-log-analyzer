from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentPhase(str, Enum):
    HYPOTHESIS = "hypothesis"
    CHOICE_TOOLS = "choice_tools"
    ANALYZE = "analyze"
    CONCLUSION = "conclusion"


class Alert(BaseModel):
    id: str
    source: str  # e.g., cloudwatch, sns, splunk, etc.
    description: str
    severity: Severity
    timestamp: datetime
    raw_data: Any


class FindingType(str, Enum):
    SYMPTOM = "symptom"          # Error observed, can ask "WHY?"
    INTERMEDIATE = "intermediate" # Explains mechanism, can trace deeper
    ROOT_CAUSE = "root_cause"    # Actionable, cannot trace deeper


class Finding(BaseModel):
    finding: str = Field(
        ..., 
        description="Exact data from tool result"
    )
    type: FindingType = Field(
        ..., 
        description="Classification: SYMPTOM, INTERMEDIATE, or ROOT_CAUSE"
    )
    datasource: str = Field(
        ...,
        description="Tool/source that produced this finding. Ex: analyze_log_pattern, check_cross_correlation"
    )
    can_trace_deeper: bool = Field(
        ..., 
        description="Can ask WHY this happened?"
    )
    is_actionable: bool = Field(
        ...,
        description="Can engineer FIX this directly?"
    )
    relevant_to_hypothesis: bool = Field(
        ...,
        description="Does this finding SUPPORT the current hypothesis being validated?"
    )
    classification_reason: str = Field(
        ..., 
        description="Why this finding was classified this way"
    )


class EvidenceType(str, Enum):
    DIRECT_CAUSAL = "direct_causal"
    STRONG_CORRELATION = "strong_correlation"
    WEAK_CORRELATION = "weak_correlation"
    CIRCUMSTANTIAL = "circumstantial"


class Evidence(BaseModel):
    """Evidence supporting a hypothesis"""
    description: str = Field(...)
    evidence_type: EvidenceType = Field(...)
    source_finding_type: FindingType = Field(
        ...,
        description="Type of finding this evidence came from"
    )
    causal_chain: List[str] = Field(
        default_factory=list,
        description="Step-by-step causal links. Empty if no direct causation proven."
    )
    is_shared_symptom: bool = Field(
        False, 
        description="Does this finding appear in other hypotheses?"
    )
    is_relevant: bool = Field(
        True,
        description="Is this evidence relevant to current hypothesis?"
    )


class HypothesisStatus(str, Enum):
    VALIDATE = "validate"
    INVALIDATE = "invalidate"
    INCONCLUSIVE = "inconclusive"


class HypothesisCategory(str, Enum):
    SECURITY_ATTACK = "security_attack"
    MISCONFIGURATION = "misconfiguration"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    APPLICATION_BUG = "application_bug"
    INFRASTRUCTURE = "infrastructure"


class HypothesisFingerprint(BaseModel):
    category: HypothesisCategory
    trigger_mechanism: str = Field(description="What triggered the failure: feature_flag, deployment, traffic, etc.")
    primary_service: str = Field(description="Main affected service name")
    failure_component: str = Field(description="Specific component/method/endpoint failing")


class Hypothesis(BaseModel):
    """RCA Hypothesis"""
    id: str
    fingerprint: HypothesisFingerprint
    description: str = Field(description="Clear, specific hypothesis statement")
    confidence: float = Field(ge=0.0, le=1.0)


class ValidateHypothesis(BaseModel):
    hypothesis_status: HypothesisStatus
    confidence: float = Field(
        description="confidence of conclusion hypothesis status",
        ge=0.0,
        le=1.0
    )
    reason: str = Field(description="explain why conclusion hypothesis status")
    evidence: List[Evidence] = Field(
        description="Only Return evidence if Hypothesis status is validate or invalidate. Evidence support hypothesis status conclusion (get from all_findings)",
        default_factory=list
    )


class EnrichmentResult(BaseModel):
    findings: List[Finding] = Field(default_factory=list)


class ThinkNodeResult(BaseModel):
    hypothesis: Hypothesis = Field(
        description="hypothesis based-on findings"
    )


class FindingsResult(BaseModel):
    findings: List[Finding] = Field(
        default_factory=list,
        description="List of classified findings from tool results"
    )


class ConclusionHypothesisResult(BaseModel):
    validation_result_hypothesis: ValidateHypothesis = Field(
        description="Validation hypothesis's status results"
    )
