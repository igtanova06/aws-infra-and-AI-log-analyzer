from langgraph.graph import StateGraph, START, END
from schemas.rca_agent_state import AgentState
from .nodes import (
    context_enrichment_node,
    think_node,
    tool_node,
    findings_node,
    conclusion_hypothesis_node,
    conclusion_node,
)
from .conditions import (
    should_continue_investigation,
    is_no_tool_call,
)


def create_rca_agent() -> StateGraph:
    """Assembles and compiles the LangGraph ReAct state machine."""
    workflow = StateGraph(AgentState)
    
    # Register all nodes
    workflow.add_node("context", context_enrichment_node)
    workflow.add_node("think", think_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("findings", findings_node)
    workflow.add_node("validate", conclusion_hypothesis_node)
    workflow.add_node("conclusion", conclusion_node)
    
    # Define primary execution path
    workflow.add_edge(START, "context")
    workflow.add_edge("context", "think")
    workflow.add_edge("think", "tool")
    
    # Conditional edge from tool node: skip findings if no tool is executed
    workflow.add_conditional_edges(
        "tool",
        is_no_tool_call,
        {
            "no_tool": "validate",
            "have_tool": "findings",
        }
    )
    
    workflow.add_edge("findings", "validate")
    
    # Conditional edge from validate node: continue loops or finalize
    workflow.add_conditional_edges(
        "validate",
        should_continue_investigation,
        {
            "continue": "think",
            "final": "conclusion",
        }
    )
    
    workflow.add_edge("conclusion", END)
    
    return workflow.compile()

# Compile global graph instance
INVESTIGATION_GRAPH = create_rca_agent()
