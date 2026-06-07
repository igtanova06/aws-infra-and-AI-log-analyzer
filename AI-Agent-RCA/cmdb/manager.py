import os
import json
from typing import Dict, Any, List, Optional


class CMDBManager:
    """Manages system topology configuration and dependency mapping for root cause analysis."""
    
    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "topology.json")
            
        self.config_path = config_path
        self.topology = self._load_topology()

    def _load_topology(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Fallback topology if file is missing/corrupt
        return {
            "infrastructure_nodes": [],
            "services": [],
            "network_zones": {}
        }

    def get_topology_summary(self) -> str:
        """Returns a formatted Markdown summary of the system architecture topology."""
        lines = [
            "Project 1 Topology & Context (from CMDB):",
            "\n1. Infrastructure Nodes:"
        ]
        for node in self.topology.get("infrastructure_nodes", []):
            lines.append(
                f"  - {node.get('name')} ({node.get('ip')}) | "
                f"Role: {node.get('role')} | "
                f"Running: {', '.join(node.get('services', []))}"
            )
            
        lines.append("\n2. Service Details & Dependencies:")
        for service in self.topology.get("services", []):
            deps = service.get("depends_on", [])
            dep_str = f"depends on {', '.join(deps)}" if deps else "no dependencies"
            lines.append(f"  - Service: {service.get('name')} (Port: {service.get('port')}) | {dep_str}")
            lines.append(f"    Description: {service.get('description')}")
            lines.append(f"    Associated Log Groups: {', '.join(service.get('log_groups', []))}")
            
        lines.append("\n3. AWS Infrastructure Components:")
        lines.append("  - VPC Flow Logs: Captures connection network traffic (ACCEPT/REJECT) on ENI interfaces.")
        lines.append("  - CloudTrail Logs: Captures AWS API calls (Describe, RunInstances, CreateSecurityGroup, etc.).")
        
        return "\n".join(lines)

    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        for service in self.topology.get("services", []):
            if service.get("name") == service_name:
                return service
        return None

    def get_affected_components(self, failed_service: str) -> List[str]:
        """Calculates blast radius (which upstream services depend on the failed service)."""
        affected = [failed_service]
        
        # Simple BFS/DFS to traverse dependency graph upstream
        added = True
        while added:
            added = False
            for service in self.topology.get("services", []):
                name = service.get("name")
                if name not in affected:
                    # If this service depends on any service currently marked as affected
                    if any(dep in affected for dep in service.get("depends_on", [])):
                        affected.append(name)
                        added = True
                        
        return affected


# Singleton instance
CMDB_MANAGER = CMDBManager()
