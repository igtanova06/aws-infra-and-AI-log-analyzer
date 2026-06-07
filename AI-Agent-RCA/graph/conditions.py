from schemas.rca_agent_state import AgentState


def should_continue_investigation(state: AgentState) -> str:
    """
    Decides whether the agent should propose another hypothesis or finalize.
    - Stop if validation_count >= 3 (we have enough validated hypotheses)
    - Stop if current_iteration_count >= max_iterations
    - Stop if should_continue is False
    """
    if state.validation_count >= 3:
        return "final"
        
    if state.current_iteration_count >= state.max_iterations:
        return "final"
        
    if not state.should_continue:
        return "final"
        
    return "continue"


def is_no_tool_call(state: AgentState) -> str:
    """
    Determines if the agent bypassed tool usage (already has enough evidence).
    Returns 'no_tool' if is_no_tool_call is True, else 'have_tool'.
    """
    if state.is_no_tool_call:
        return "no_tool"
    return "have_tool"
