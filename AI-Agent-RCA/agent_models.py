import os
from langchain_aws import ChatBedrock


def get_model_by_phase(phase: str):
    """
    Returns ChatBedrock configured for the specific phase.
    Uses Claude 3.5 Sonnet for reasoning phases (think, conclusion, final)
    and Claude 3.5 Haiku for execution phases (context, tool, analyze).
    """
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    # Select model based on phase complexity
    if phase in ["think", "conclusion", "final"]:
        # Claude 3.5 Sonnet
        model_id = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        temperature = 0.1
    else:
        # Claude 3.5 Haiku
        model_id = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        temperature = 0.0
        
    kwargs = {
        "model_id": model_id,
        "region_name": region,
        "model_kwargs": {"temperature": temperature}
    }
    return ChatBedrock(**kwargs)  # type: ignore
