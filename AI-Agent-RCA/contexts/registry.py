import yaml
from pathlib import Path
from typing import Dict, List
from .base import ContextBlock, ContextLayer


class ContextRegistry:
    """Central registry loading and managing all YAML context blocks."""
    
    def __init__(self, contexts_dir: str = None):
        if contexts_dir is None:
            self._contexts_dir = Path(__file__).parent
        else:
            self._contexts_dir = Path(contexts_dir)
        self._registry: Dict[str, ContextBlock] = {}
        self._load_all()
    
    def _load_all(self):
        """Load all .yaml files from contexts directory structure."""
        for layer in ContextLayer:
            layer_dir = self._contexts_dir / layer.value
            if layer_dir.exists():
                for yaml_file in layer_dir.glob("*.yaml"):
                    self._load_file(yaml_file, layer)
    
    def _load_file(self, path: Path, layer: ContextLayer):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        block = ContextBlock(
            name=data.get("name", path.stem),
            layer=layer,
            content=data["content"],
            priority=data.get("priority", 50),
            conditions=data.get("conditions")
        )
        self._registry[block.name] = block
    
    def get(self, name: str) -> ContextBlock:
        return self._registry.get(name)
    
    def get_by_layer(self, layer: ContextLayer) -> List[ContextBlock]:
        return [b for b in self._registry.values() if b.layer == layer]
    
    def list_all(self) -> List[str]:
        return list(self._registry.keys())
