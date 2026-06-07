from typing import List, Dict, Any, Optional
from .base import ContextBlock, ContextLayer
from .registry import ContextRegistry

class ContextComposer:
    """Compose dynamic prompts from multiple context blocks."""
    
    LAYER_ORDER = [
        ContextLayer.SYSTEM,
        ContextLayer.DOMAIN,
        ContextLayer.TASK,
        ContextLayer.INTERACTION,
        ContextLayer.RESPONSE,
    ]
    
    def __init__(self, registry: ContextRegistry):
        self.registry = registry
    
    def compose(
        self,
        context_names: List[str],
        variables: Dict[str, Any] = None,
        state: Dict[str, Any] = None  # LangGraph state to evaluate conditions
    ) -> str:
        """
        Compose final prompt from list of context names.
        
        Args:
            context_names: List of context block names to include
            variables: Variables to render templates
            state: Current state to evaluate conditions
        """
        blocks = []
        
        for name in context_names:
            block = self.registry.get(name)
            if block and self._should_include(block, state):
                blocks.append(block)
        
        # Sort by layer order, then by priority (descending) within the same layer
        blocks.sort(key=lambda b: (
            self.LAYER_ORDER.index(b.layer),
            -b.priority  # Higher priority first
        ))
        
        # Render and join
        sections = []
        current_layer = None
        
        for block in blocks:
            if block.layer != current_layer:
                current_layer = block.layer
                sections.append(f"\n<!-- {current_layer.value.upper()} CONTEXT -->")
            
            rendered = block.render(variables=variables)
            sections.append(rendered)
        
        return "\n\n".join(sections)
    
    def _should_include(self, block: ContextBlock, state: Dict) -> bool:
        """Check conditions to decide if block should be included."""
        if not block.conditions or not state:
            return True
        
        for key, expected in block.conditions.items():
            actual = state.get(key)
            if actual != expected:
                return False
        return True
