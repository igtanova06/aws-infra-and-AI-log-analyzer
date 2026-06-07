from .registry import ContextRegistry
from .composer import ContextComposer

CONTEXT_REGISTRY = ContextRegistry()
CONTEXT_COMPOSER = ContextComposer(CONTEXT_REGISTRY)

__all__ = [
    'CONTEXT_REGISTRY',
    'CONTEXT_COMPOSER'
]
