"""
Telegram Notifier - Send security alerts via Versus Incident
"""
import requests
import os
from typing import Dict, List, Optional
from datetime import datetime
import json


class TelegramNotifier:
    """
    Send security alerts to Telegram via Versus Incident gateway
    """
    
    def __init__(self, versus_url: str = None):
        """
        Initialize Telegram notifier
        
        Args:
            versus_url: URL of Versus Incident service (default: from env or localhost)
        """
        self.versus_url = versus_url or os.getenv("VERSUS_INCIDENT_URL", "http://localhost:3000")
        self.enabled = os.getenv("TELEGRAM_ALERTS_ENABLED", "false").lower() == "true"
        
        # Direct Telegram API configuration (RECOMMENDED)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.use_direct_telegram = bool(self.bot_token and self.chat_id)
        
        if self.enabled and not self.use_direct_telegram:
            print("[Telegram] ⚠️ Warning: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Using Versus Incident fallback.")
        
    def send_attack_alert(
        self, 
        global_rca: Dict = None,
        correlated_events: List = None,
        analysis_metadata: Dict = None
    ) -> bool:
        """
        Send attack detection alert to Telegram
        
        Args:
            global_rca: Global Root Cause Analysis from Bedrock
            correlated_events: List of correlated attack events
            analysis_metadata: Additional metadata (time range, sources, etc.)
            
        Returns:
            bool: True if alert sent successfully
        """
        if not self.enabled:
            print("[Telegram] Alerts disabled. Set TELEGRAM_ALERTS_ENABLED=true to enable.")
            return False
            
        if not global_rca:
            print("[Telegram] No RCA data to send")
            return False
        
        # Build alert payload
        payload = self._build_alert_payload(global_rca, correlated_events, analysis_metadata)
        
        # Try direct Telegram API first if configured (RECOMMENDED)
        if self.use_direct_telegram:
            success = self._send_direct_telegram(payload)
            if success:
                return True
            else:
                print("[Telegram] ⚠️ Direct Telegram failed, trying Versus Incident fallback...")
        
        # Fallback to Versus Incident service
        try:
            response = requests.post(
                f"{self.versus_url}/api/incidents",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[Telegram] ✅ Alert sent successfully via Versus")
                return True
            else:
                print(f"[Telegram] ❌ Failed to send alert: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[Telegram] ❌ Connection error: {e}")
            print(f"[Telegram] 💡 Tip: Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID for direct Telegram API")
            return False
    
    def _send_direct_telegram(self, payload: Dict) -> bool:
        """
        Send alert directly to Telegram API (bypass Versus Incident)
        
        Args:
            payload: Alert payload
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Format message for Telegram
            message = self._format_telegram_message(payload)
            
            # Send to Telegram API
            telegram_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            response = requests.post(
                telegram_url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[Telegram] ✅ Alert sent directly to Telegram")
                return True
            else:
                print(f"[Telegram] ❌ Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"[Telegram] ❌ Direct Telegram error: {e}")
            return False
    
    def _format_telegram_message(self, payload: Dict) -> str:
        """
        Format alert payload as Telegram message
        
        Args:
            payload: Alert payload
            
        Returns:
            str: Formatted message
        """
        import html
        
        attack_name = payload.get("attack_name", "Unknown Attack")
        severity = payload.get("severity", "Unknown")
        confidence = payload.get("confidence", "N/A")
        attacker_ip = payload.get("attacker_ip", "Unknown")
        root_cause = payload.get("root_cause", "N/A")
        
        # Escape HTML entities to prevent parsing errors
        attack_name = html.escape(attack_name)
        root_cause = html.escape(root_cause[:500])
        attacker_ip = html.escape(attacker_ip)
        
        # Severity emoji
        severity_emoji = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢"
        }.get(severity, "⚪")
        
        message = f"""🚨 <b>SECURITY ALERT</b> 🚨

{severity_emoji} <b>{attack_name}</b>

<b>Severity:</b> {severity}
<b>Confidence:</b> {confidence}
<b>Attacker IP:</b> {attacker_ip}

<b>🔍 Root Cause:</b>
{root_cause}

<b>⏰ Detected:</b> {payload.get('timestamp', 'N/A')}
<b>📊 Logs Analyzed:</b> {payload.get('total_logs_analyzed', 0)}
"""
        
        # Add affected components
        components = payload.get("affected_components", [])
        if components:
            message += f"\n<b>🏗️ Affected Components:</b>\n"
            for comp in components[:3]:
                comp_escaped = html.escape(str(comp))
                message += f"  • {comp_escaped}\n"
        
        # Add immediate actions
        actions = payload.get("immediate_actions", [])
        if actions:
            message += f"\n<b>🔥 Immediate Actions:</b>\n"
            for action in actions[:3]:
                action_escaped = html.escape(str(action)[:200])  # Limit length
                message += f"  • {action_escaped}\n"
        
        # Add MITRE techniques
        mitre = payload.get("mitre_techniques", "")
        if mitre and mitre != "N/A":
            mitre_escaped = html.escape(str(mitre))
            message += f"\n<b>🗺️ MITRE ATT&CK:</b> {mitre_escaped}\n"
        
        return message
    
    def _build_alert_payload(
        self, 
        global_rca: Dict,
        correlated_events: List,
        metadata: Dict
    ) -> Dict:
        """
        Build alert payload for Versus Incident
        
        Returns:
            Dict with alert data matching Telegram template
        """
        # Extract key information from Global RCA
        incident_story = global_rca.get("incident_story", [])
        attack_name = incident_story[0] if incident_story else "Unknown Security Incident"
        
        threat_assessment = global_rca.get("threat_assessment", {})
        severity = threat_assessment.get("severity", "Unknown")
        confidence = threat_assessment.get("confidence", 0)
        
        # Extract attacker IPs from correlated events
        attacker_ips = []
        if correlated_events:
            for event in correlated_events:
                correlation_keys = event.correlation_keys or {}
                if correlation_keys.get("source_ip"):
                    attacker_ips.append(correlation_keys["source_ip"])
        
        # Deduplicate IPs
        attacker_ips = list(set(attacker_ips))
        attacker_ip_str = ", ".join(attacker_ips[:3]) if attacker_ips else "Unknown"
        
        # Extract affected components
        affected_components = []
        for comp in global_rca.get("affected_components", []):
            component_name = comp.get("component", "Unknown")
            impact_level = comp.get("impact_level", "Unknown")
            affected_components.append(f"{component_name} ({impact_level} impact)")
        
        # Extract root cause
        root_cause = global_rca.get("root_cause", "Root cause analysis in progress...")
        
        # Extract immediate actions
        immediate_actions = global_rca.get("immediate_actions", [])
        action_commands = []
        for action in immediate_actions[:3]:  # Top 3 actions
            priority = action.get("priority", "P2")
            action_text = action.get("action", "N/A")
            command = action.get("command", "")
            
            if command:
                action_commands.append(f"[{priority}] {action_text}\n→ {command}")
            else:
                action_commands.append(f"[{priority}] {action_text}")
        
        # Extract evidence from correlated events
        evidence = []
        if correlated_events:
            for event in correlated_events[:2]:  # Top 2 events
                timeline = event.timeline or []
                for entry in timeline[:2]:  # Top 2 entries per event
                    timestamp = entry.timestamp.strftime('%H:%M:%S') if hasattr(entry.timestamp, 'strftime') else str(entry.timestamp)
                    source = entry.source or "Unknown"
                    message = (entry.message or "")[:100]  # Truncate long messages
                    evidence.append(f"[{timestamp}] {source}: {message}")
        
        # MITRE ATT&CK mapping
        mitre_mapping = global_rca.get("mitre_mapping", {})
        mitre_techniques = mitre_mapping.get("techniques", [])
        mitre_str = ", ".join(mitre_techniques[:3]) if mitre_techniques else "N/A"
        
        # Build payload
        payload = {
            "attack_name": attack_name,
            "severity": severity,
            "confidence": f"{confidence * 100:.0f}%" if isinstance(confidence, float) else str(confidence),
            "attacker_ip": attacker_ip_str,
            "affected_components": affected_components,
            "root_cause": root_cause,
            "immediate_actions": action_commands,
            "evidence": evidence,
            "mitre_techniques": mitre_str,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "time_range": metadata.get("time_range", "N/A") if metadata else "N/A",
            "total_logs_analyzed": metadata.get("total_logs", 0) if metadata else 0,
            "correlation_count": len(correlated_events) if correlated_events else 0
        }
        
        return payload
    
    def send_test_alert(self) -> bool:
        """
        Send a test alert to verify Telegram integration
        
        Returns:
            bool: True if test alert sent successfully
        """
        test_payload = {
            "attack_name": "🧪 Test Alert - System Check",
            "severity": "INFO",
            "confidence": "100%",
            "attacker_ip": "N/A (Test)",
            "affected_components": ["Telegram Integration"],
            "root_cause": "This is a test alert to verify Telegram integration is working correctly.",
            "immediate_actions": ["No action required - this is a test"],
            "evidence": ["Test alert generated at " + datetime.now().isoformat()],
            "mitre_techniques": "N/A",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "time_range": "N/A",
            "total_logs_analyzed": 0,
            "correlation_count": 0
        }
        
        # Use direct Telegram if configured
        if self.use_direct_telegram:
            return self._send_direct_telegram(test_payload)
        
        # Fallback to Versus Incident
        try:
            response = requests.post(
                f"{self.versus_url}/api/incidents",
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"[Telegram] ✅ Test alert sent successfully")
                return True
            else:
                print(f"[Telegram] ❌ Test alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[Telegram] ❌ Test alert error: {e}")
            return False


# Convenience function for quick alerts
def send_alert(global_rca: Dict, correlated_events: List = None, metadata: Dict = None) -> bool:
    """
    Quick function to send alert without instantiating class
    
    Args:
        global_rca: Global RCA from Bedrock
        correlated_events: Correlated attack events
        metadata: Analysis metadata
        
    Returns:
        bool: True if sent successfully
    """
    notifier = TelegramNotifier()
    return notifier.send_attack_alert(global_rca, correlated_events, metadata)
