import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from schemas import AgentState, IncidentPhase
from schemas.rca import (
    Finding,
    FindingType,
    Hypothesis,
    HypothesisFingerprint,
    HypothesisCategory,
    ValidateHypothesis,
    HypothesisStatus,
    ThinkNodeResult,
    ConclusionHypothesisResult,
    FindingsResult,
    EnrichmentResult,
)
from agent_models import get_model_by_phase
from contexts import CONTEXT_COMPOSER
from tools import ALL_TOOLS
from cmdb import CMDB_MANAGER

# Define system architecture topology from CMDB
SYSTEM_ARCHITECTURE = CMDB_MANAGER.get_topology_summary()


def get_investigation_history_str(state: AgentState) -> str:
    """Formats the investigation history into a clear chronology for the LLM."""
    if not state.investigation_history:
        return "No previous investigations."
    lines = []
    for idx, inv in enumerate(state.investigation_history):
        lines.append(f"--- Investigation #{idx+1} ---")
        hyp = inv.get("hypothesis", {})
        if isinstance(hyp, dict):
            lines.append(f"Hypothesis Category: {hyp.get('category')}")
            lines.append(f"Hypothesis Statement: {hyp.get('description') or hyp.get('desciption')}")
        else:
            lines.append(f"Hypothesis: {str(hyp)}")
        
        conc = inv.get("hypothesis_conclusion", {})
        if isinstance(conc, dict):
            lines.append(f"Conclusion Status: {conc.get('hypothesis_status') or conc.get('status')}")
            lines.append(f"Conclusion Confidence: {conc.get('confidence')}")
            lines.append(f"Conclusion Explanation: {conc.get('reason') or conc.get('explanation')}")
        else:
            lines.append(f"Conclusion: {str(conc)}")
        
        lines.append("Tools Used:")
        for t in inv.get("tools", []):
            if isinstance(t, dict):
                lines.append(f"  - {t.get('name')} (args: {json.dumps(t.get('args'))})")
            else:
                lines.append(f"  - {str(t)}")
            
        lines.append("Findings discovered:")
        findings = inv.get("investigate_findings_from_tool_results", [])
        if findings:
            for f in findings:
                if isinstance(f, dict):
                    lines.append(f"  - [{f.get('type')}] {f.get('finding')} (Source: {f.get('datasource')})")
                else:
                    lines.append(f"  - {str(f)}")
        else:
            lines.append("  - None")
    return "\n".join(lines)


# ----------------------------------------------------------------------
# 1. Context Enrichment Node
# ----------------------------------------------------------------------
async def context_enrichment_node(state: AgentState) -> AgentState:
    """Enriches the investigation with system architecture and initial findings from trigger payload."""
    prompt = CONTEXT_COMPOSER.compose(
        context_names=[
            "security_analyst",
            "aws_architecture",
            "task_initial_assessment",
            "structured_output"
        ],
        variables={
            "alert": json.dumps(state.alert) if isinstance(state.alert, dict) else str(state.alert),
            "system_architecture": SYSTEM_ARCHITECTURE
        }
    )
    
    model = get_model_by_phase("context").with_structured_output(EnrichmentResult)
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        state.add_initial_findings(response.findings)
    except Exception as e:
        state.error = f"Error in context_enrichment_node: {str(e)}"
        
    state.add_system_architecture(SYSTEM_ARCHITECTURE)
    state.set_phase(IncidentPhase.HYPOTHESIS)
    return state


# ----------------------------------------------------------------------
# 2. Think Node
# ----------------------------------------------------------------------
async def think_node(state: AgentState) -> AgentState:
    """Formulates a specific hypothesis based on architecture, alert, and history."""
    state.reset_current_investigation()
    
    prompt = CONTEXT_COMPOSER.compose(
        context_names=[
            "security_analyst",
            "feedback_loop",
            "task_hypothesis",
            "structured_output"
        ],
        variables={
            "current_phase": state.current_phase.value,
            "current_iteration": str(state.current_iteration_count),
            "max_iterations": str(state.max_iterations),
            "initial_findings": json.dumps([f.model_dump() for f in state.initial_findings]) if state.initial_findings else "[]",
            "investigation_history": get_investigation_history_str(state)
        }
    )
    
    model = get_model_by_phase("think").with_structured_output(ThinkNodeResult)
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        state.add_hypothesis(response.hypothesis)
    except Exception as e:
        state.error = f"Error in think_node: {str(e)}"
        fallback = Hypothesis(
            id=f"hyp_{int(datetime.utcnow().timestamp())}",
            fingerprint=HypothesisFingerprint(
                category=HypothesisCategory.SECURITY_ATTACK,
                trigger_mechanism="network_flood",
                primary_service="web_server",
                failure_component="apache"
            ),
            description="Automatic fallback hypothesis due to LLM error.",
            confidence=0.1
        )
        state.add_hypothesis(fallback)
        
    state.set_phase(IncidentPhase.CHOICE_TOOLS)
    return state


# ----------------------------------------------------------------------
# 3. Tool Node (Selects and executes a tool)
# ----------------------------------------------------------------------
async def tool_node(state: AgentState) -> AgentState:
    """Decides on the best tool to validate the current hypothesis and executes it."""
    prompt = CONTEXT_COMPOSER.compose(
        context_names=[
            "security_analyst",
            "feedback_loop",
            "task_select_tool",
            "structured_output"
        ],
        variables={
            "current_phase": state.current_phase.value,
            "current_iteration": str(state.current_iteration_count),
            "max_iterations": str(state.max_iterations),
            "initial_findings": json.dumps([f.model_dump() for f in state.initial_findings]) if state.initial_findings else "[]",
            "investigation_history": get_investigation_history_str(state),
            "hypothesis": state.hypothesis.model_dump_json() if state.hypothesis else "None"
        }
    )
    
    model = get_model_by_phase("tool")
    model_with_tools = model.bind_tools(ALL_TOOLS)
    
    try:
        response = model_with_tools.invoke([HumanMessage(content=prompt)])
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Inject alert details into tools automatically to bind window calculations
            if "alert_signals_json" not in tool_args and state.alert:
                tool_args["alert_signals_json"] = json.dumps(state.alert)
                
            state.set_current_tools([{"name": tool_name, "args": tool_args}])
            
            # Retrieve and execute tool
            tool_fn = next((t for t in ALL_TOOLS if t.name == tool_name), None)
            if tool_fn:
                result = tool_fn.invoke(tool_args)
                state.set_tool_results([{"tool": tool_name, "args": tool_args, "result": str(result)}])
                state.is_no_tool_call = False
            else:
                state.set_tool_results([{"tool": tool_name, "args": tool_args, "result": f"Error: Tool {tool_name} not found."}])
                state.is_no_tool_call = True
        else:
            state.is_no_tool_call = True
    except Exception as e:
        state.error = f"Error in tool_node: {str(e)}"
        state.is_no_tool_call = True
        
    state.set_phase(IncidentPhase.ANALYZE)
    return state


# ----------------------------------------------------------------------
# 4. Findings Node (Extracts and Classifies Findings)
# ----------------------------------------------------------------------
async def findings_node(state: AgentState) -> AgentState:
    """Classifies tool outputs into Symptom, Intermediate, or Root Cause categories."""
    prompt = CONTEXT_COMPOSER.compose(
        context_names=[
            "security_analyst",
            "feedback_loop",
            "task_classify_findings",
            "structured_output"
        ],
        variables={
            "current_phase": state.current_phase.value,
            "current_iteration": str(state.current_iteration_count),
            "max_iterations": str(state.max_iterations),
            "initial_findings": json.dumps([f.model_dump() for f in state.initial_findings]) if state.initial_findings else "[]",
            "investigation_history": get_investigation_history_str(state),
            "hypothesis": state.hypothesis.model_dump_json() if state.hypothesis else "None",
            "tool_results": json.dumps(state.tool_results) if state.tool_results else "[]"
        }
    )
    
    model = get_model_by_phase("analyze").with_structured_output(FindingsResult)
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        state.set_investigate_findings(response.findings)
    except Exception as e:
        state.error = f"Error in findings_node: {str(e)}"
        
    return state


# ----------------------------------------------------------------------
# 5. Conclusion Hypothesis Node (Validates current hypothesis)
# ----------------------------------------------------------------------
async def conclusion_hypothesis_node(state: AgentState) -> AgentState:
    """Performs validation scoring matrix on the current hypothesis and appends to history."""
    prompt = CONTEXT_COMPOSER.compose(
        context_names=[
            "security_analyst",
            "feedback_loop",
            "task_validate_hypothesis",
            "structured_output"
        ],
        variables={
            "current_phase": state.current_phase.value,
            "current_iteration": str(state.current_iteration_count),
            "max_iterations": str(state.max_iterations),
            "initial_findings": json.dumps([f.model_dump() for f in state.initial_findings]) if state.initial_findings else "[]",
            "investigation_history": get_investigation_history_str(state),
            "hypothesis": state.hypothesis.model_dump_json() if state.hypothesis else "None",
            "current_findings": json.dumps([f.model_dump() for f in state.investigate_findings]) if state.investigate_findings else "[]"
        }
    )
    
    model = get_model_by_phase("conclusion").with_structured_output(ConclusionHypothesisResult)
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        val_result = response.validation_result_hypothesis
        
        state.set_hypothesis_conclusion(val_result)
        
        if val_result.hypothesis_status == HypothesisStatus.VALIDATE:
            state.increase_validate_hypothesis()
            
        state.add_investigation(
            hypothesis=state.hypothesis,
            hypothesis_conclusion=val_result,
            tools=state.tools,
            investigate_findings=state.investigate_findings
        )
    except Exception as e:
        state.error = f"Error in conclusion_hypothesis_node: {str(e)}"
        fallback_val = ValidateHypothesis(
            hypothesis_status=HypothesisStatus.INCONCLUSIVE,
            confidence=0.0,
            reason=f"LLM validation error: {str(e)}",
            evidence=[]
        )
        state.set_hypothesis_conclusion(fallback_val)
        state.add_investigation(
            hypothesis=state.hypothesis,
            hypothesis_conclusion=fallback_val,
            tools=state.tools,
            investigate_findings=state.investigate_findings
        )
        
    state.increase_iteration()
    state.set_phase(IncidentPhase.CONCLUSION)
    return state


# ----------------------------------------------------------------------
# 6. Conclusion Node (Compiles Final RCA Report)
# ----------------------------------------------------------------------
class ThreatAssessment(BaseModel):
    severity: str = Field(description="Incident severity level (CRITICAL, HIGH, MEDIUM, LOW)")
    confidence: float = Field(description="Overall confidence in this assessment (0.0-1.0)")
    reasoning: str = Field(description="Detailed reason for this threat classification")
    scope: str = Field(description="Blast radius / scope of affected components")

class AffectedComponent(BaseModel):
    component: str = Field(description="Name of the affected service/component")
    impact_level: str = Field(description="Impact level: HIGH, MEDIUM, LOW")
    evidence: str = Field(description="Evidence proving this component was affected")

class ImmediateAction(BaseModel):
    action: str = Field(description="Description of security mitigation step")
    command: str = Field(description="AWS CLI command or script command to block or mitigate this specific issue")
    priority: str = Field(description="Priority of action: HIGH, MEDIUM, LOW")

class RemediationPlan(BaseModel):
    short_term: List[str] = Field(description="Steps to implement in the next 24 hours")
    medium_term: List[str] = Field(description="Steps to implement in the next 7 days")
    long_term: List[str] = Field(description="Longer-term architectural or process remediations")

class GlobalRCAPydantic(BaseModel):
    incident_story: List[str] = Field(description="Chronological narrative lines of the incident sequence")
    threat_assessment: ThreatAssessment = Field(description="Overall threat assessment")
    attack_narrative: str = Field(description="Full narrative report detailing how the issue unfolded")
    affected_components: List[AffectedComponent] = Field(description="List of all affected services")
    root_cause: str = Field(description="Actionable single root cause statement")
    mitre_mapping: Dict[str, List[str]] = Field(description="MITRE ATT&CK framework mapping. Keys: tactics, techniques")
    immediate_actions: List[ImmediateAction] = Field(description="AWS CLI immediate commands to run")
    remediation_plan: RemediationPlan = Field(description="Structured remediation steps")


async def conclusion_node(state: AgentState) -> AgentState:
    """Synthesizes the entire history and initial findings into a comprehensive global RCA report."""
    prompt = CONTEXT_COMPOSER.compose(
        context_names=[
            "security_analyst",
            "feedback_loop",
            "task_conclude",
            "structured_output"
        ],
        variables={
            "current_phase": state.current_phase.value,
            "current_iteration": str(state.current_iteration_count),
            "max_iterations": str(state.max_iterations),
            "initial_findings": json.dumps([f.model_dump() for f in state.initial_findings]) if state.initial_findings else "[]",
            "investigation_history": get_investigation_history_str(state)
        }
    )
    
    model = get_model_by_phase("final").with_structured_output(GlobalRCAPydantic)
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        state.final_rca = response.model_dump()
    except Exception as e:
        state.error = f"Error in conclusion_node: {str(e)}"
        state.final_rca = {
            "incident_story": ["Failed to compile narrative due to LLM error."],
            "threat_assessment": {
                "severity": "CRITICAL",
                "confidence": 0.0,
                "reasoning": f"LLM error: {str(e)}",
                "scope": "Unknown"
            },
            "attack_narrative": f"An error occurred during final RCA compilation: {str(e)}",
            "affected_components": [],
            "root_cause": "Unknown (RCA Generation failed)",
            "mitre_mapping": {"tactics": [], "techniques": []},
            "immediate_actions": [],
            "remediation_plan": {"short_term": [], "medium_term": [], "long_term": []}
        }
        
    return state
