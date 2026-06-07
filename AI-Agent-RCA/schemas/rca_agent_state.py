from pydantic import BaseModel, Field
from typing import Any, List, Optional, Dict
from .rca import (
    IncidentPhase,
    Hypothesis,
    Finding,
    ValidateHypothesis
)


class AgentState(BaseModel):
    # overview
    alert: Any = None
    system_architecture: str = ""

    # metadata
    current_phase: IncidentPhase = IncidentPhase.HYPOTHESIS
    current_iteration_count: int = 0
    max_iterations: int = 5

    # control flow
    should_continue: bool = True
    error: Optional[str] = None

    # current investigation
    hypothesis: Optional[Hypothesis] = None
    tools: List[Any] = Field(default_factory=list)
    tool_results: List[Any] = Field(default_factory=list)
    investigate_findings: List[Finding] = Field(default_factory=list)
    hypothesis_conclusion: Optional[ValidateHypothesis] = None
    is_no_tool_call: bool = False

    # history investigation
    initial_findings: List[Finding] = Field(default_factory=list)
    investigation_history: List[Dict[str, Any]] = Field(default_factory=list)
    validation_count: int = 0
    final_rca: Optional[Dict[str, Any]] = None

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        self.hypothesis = hypothesis

    def add_system_architecture(self, system_architecture: str) -> None:
        self.system_architecture = system_architecture

    def increase_iteration(self) -> None:
        self.current_iteration_count += 1

    def set_phase(self, phase: IncidentPhase) -> None:
        self.current_phase = phase
    
    def add_initial_findings(self, findings: List[Finding]) -> None:
        self.initial_findings.extend(findings)

    def set_current_tools(self, tools: List[Any]) -> None:
        self.tools = tools

    def set_tool_results(self, tool_results: List[Any]) -> None:
        self.tool_results = tool_results

    def set_investigate_findings(self, findings: List[Finding]) -> None:
        self.investigate_findings = findings

    def set_hypothesis_conclusion(self, conclusion: ValidateHypothesis) -> None:
        self.hypothesis_conclusion = conclusion

    def add_investigation(
        self,
        hypothesis: Hypothesis,
        hypothesis_conclusion: ValidateHypothesis,
        tools: List[Any],
        investigate_findings: List[Finding]
    ) -> None:
        self.investigation_history.append({
            "hypothesis": hypothesis.model_dump() if hasattr(hypothesis, "model_dump") else hypothesis,
            "hypothesis_conclusion": hypothesis_conclusion.model_dump() if hasattr(hypothesis_conclusion, "model_dump") else hypothesis_conclusion,
            "tools": tools,
            "investigate_findings_from_tool_results": [f.model_dump() if hasattr(f, "model_dump") else f for f in investigate_findings]
        })

    def reset_current_investigation(self) -> None:
        self.hypothesis = None
        self.tools = []
        self.tool_results = []
        self.investigate_findings = []
        self.hypothesis_conclusion = None
        self.is_no_tool_call = False

    def increase_validate_hypothesis(self) -> None:
        self.validation_count += 1

    def no_tool_call(self) -> None:
        self.is_no_tool_call = True
