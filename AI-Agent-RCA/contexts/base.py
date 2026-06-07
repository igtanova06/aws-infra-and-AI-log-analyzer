from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class ContextLayer(str, Enum):
    SYSTEM = "system"
    DOMAIN = "domain"
    TASK = "task"
    INTERACTION = "interaction"
    RESPONSE = "response"


class ContextBlock(BaseModel):
    name: str
    layer: ContextLayer
    content: str
    priority: int = Field(default=50, ge=0, le=100) # higher --> front-tier
    conditions: Optional[Dict[str, Any]] = None 
    
    def render(self, variables: Dict[str, Any] = None) -> str:
        """Render content with variables (Jinja2-style)"""
        if not variables:
            return self.content

        result = self.content
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            result = result.replace(placeholder, str(value))

        return result
