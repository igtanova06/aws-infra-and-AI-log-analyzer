"""
Bedrock enhancer - Enhance solutions using AWS Bedrock
"""
import boto3
import json
import re
from typing import List, Tuple, Dict
from models import Solution


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class BedrockEnhancer:
    """Enhance solutions using AWS Bedrock"""
    
    def __init__(self, region: str = "us-east-1", model: str = "us.amazon.nova-micro-v1:0"):
        """
        Initialize Bedrock enhancer
        
        Args:
            region: AWS region
            model: Bedrock model ID
        """
        self.region = region
        self.model_id = model
        self.client = None
        
        try:
            self.client = boto3.client('bedrock-runtime', region_name=region)
        except Exception as e:
            print(f"Warning: Could not initialize Bedrock client: {e}")
    
    def is_available(self) -> bool:
        """Check if Bedrock is available"""
        return self.client is not None
    
    def enhance_solutions(
        self, 
        solutions: List[Solution], 
        log_examples: List[str] = None,
        ai_context = None,
        max_batch_size: int = 1   # 1 issue per call prevents output truncation
    ) -> Tuple[List[Solution], Dict]:
        """
        Enhance solutions using AWS Bedrock
        
        Args:
            solutions: List of basic solutions
            log_examples: Sample log entries for context (legacy, used if ai_context is None)
            ai_context: Structured AIContext from LogPreprocessor (preferred)
            max_batch_size: Maximum solutions per API call
            
        Returns:
            Tuple of (enhanced solutions, usage stats)
        """
        if not self.is_available():
            return solutions, {
                "ai_enhancement_used": False,
                "error": "Bedrock client not available"
            }
        
        enhanced_solutions = []
        total_tokens = 0
        total_cost = 0.0
        api_calls = 0
        
        # Process solutions in batches
        for i in range(0, len(solutions), max_batch_size):
            batch = solutions[i:i + max_batch_size]
            
            try:
                enhanced_batch, tokens, cost = self._enhance_batch(
                    batch, log_examples=log_examples, ai_context=ai_context
                )
                enhanced_solutions.extend(enhanced_batch)
                total_tokens += tokens
                total_cost += cost
                api_calls += 1
            except Exception as e:
                print(f"Error enhancing batch: {e}")
                # Truyền thẳng lỗi cho UI hiển thị thay vì âm thầm trả Basic Solutions
                return solutions, {
                    "ai_enhancement_used": False,
                    "error": f"Bedrock API Failed: {str(e)}"
                }
        
        # Safety check: verify that solutions were actually enhanced
        actually_enhanced = any(s.ai_enhanced for s in enhanced_solutions)
        
        if not actually_enhanced:
            return enhanced_solutions, {
                "ai_enhancement_used": False,
                "error": "Bedrock responded but AI could not parse the response. Solutions shown are basic (non-AI)."
            }
        
        usage_stats = {
            "ai_enhancement_used": True,
            "bedrock_model_used": self.model_id,
            "total_tokens_used": total_tokens,
            "estimated_total_cost": total_cost,
            "api_calls_made": api_calls
        }
        
        return enhanced_solutions, usage_stats
    
    def _enhance_batch(
        self, 
        solutions: List[Solution], 
        log_examples: List[str] = None,
        ai_context = None
    ) -> Tuple[List[Solution], int, float]:
        """Enhance a batch of solutions with accurate cost tracking"""
        
        # Build prompt — prefer structured AIContext over flat examples
        prompt = self._build_prompt(solutions, log_examples=log_examples, ai_context=ai_context)
        
        # Call Bedrock API with retry
        response = self._call_bedrock(prompt)
        
        # Parse response
        enhanced_solutions = self._parse_response(solutions, response)
        
        # Calculate tokens and cost accurately
        usage = response.get('usage', {})
        total_tokens = usage.get('total_tokens', 0)
        input_tokens = usage.get('input_tokens')
        output_tokens = usage.get('output_tokens')
        
        # Use accurate cost calculation if we have input/output split
        if input_tokens and output_tokens:
            cost = self._calculate_cost(total_tokens, input_tokens, output_tokens)
            print(f"[Bedrock Cost] Input: {input_tokens} tokens, Output: {output_tokens} tokens, Cost: ${cost:.4f}")
        else:
            cost = self._calculate_cost(total_tokens)
            print(f"[Bedrock Cost] Total: {total_tokens} tokens, Cost: ${cost:.4f} (estimated)")
        
        return enhanced_solutions, total_tokens, cost
    
    def _build_prompt(self, solutions: List[Solution], log_examples: List[str] = None, ai_context = None) -> str:
        """
        Build prompt for Bedrock.
        If ai_context (AIContext) is provided, builds a rich source-aware prompt.
        Otherwise falls back to legacy flat-examples prompt.
        """
        # ---- Rich prompt when AIContext is available ----
        if ai_context is not None:
            return self._build_rich_prompt(solutions, ai_context)
        
        # ---- Legacy fallback prompt ----
        prompt = "You are a log analysis expert. Enhance the following solutions with detailed, actionable recommendations.\n\n"
        
        if log_examples:
            prompt += "Sample log entries:\n"
            for i, example in enumerate(log_examples[:3], 1):
                prompt += f"{i}. {example}\n"
            prompt += "\n"
        
        prompt += "Solutions to enhance:\n\n"
        for i, solution in enumerate(solutions, 1):
            prompt += f"{i}. Problem: {solution.problem}\n"
            prompt += f"   Current solution: {solution.solution}\n"
            prompt += f"   Affected components: {', '.join(solution.affected_components)}\n\n"
        
        prompt += (
            "For each solution, provide:\n"
            "1. A detailed explanation of the root cause\n"
            "2. Step-by-step troubleshooting steps\n"
            "3. Specific commands or configurations to check\n"
            "4. Prevention strategies\n\n"
            "Format your response as JSON array with this structure:\n"
            "[\n"
            "  {\n"
            '    "problem": "original problem",\n'
            '    "enhanced_solution": "detailed solution text"\n'
            "  }\n"
            "]\n"
        )
        
        return prompt
    
    def _build_rich_prompt(self, solutions: List[Solution], ctx) -> str:
        """
        Build a source-aware prompt using structured AIContext.
        Produces a 7-part analysis output format for the demo.
        Enhanced with better attack pattern recognition.
        """
        # Source type label for the AI
        source_labels = {
            'vpc_flow': 'AWS VPC Flow Logs (network traffic records)',
            'cloudtrail': 'AWS CloudTrail (API audit logs)',
            'app': 'Application Logs (server/service logs)',
        }
        source_label = source_labels.get(ctx.source_type, 'Log data')
        
        prompt = (
            "You are an expert AWS security and log analysis engineer specializing in threat detection and incident response.\n\n"
            "# ANALYSIS CONTEXT\n"
            f"Source Type: {source_label}\n"
            f"Log Group: {ctx.log_group_name}\n"
            f"Search Term: '{ctx.search_term}'\n"
            f"Time Range: {ctx.time_range_str}\n"
            f"Total Logs: {ctx.total_logs_pulled} | High-Relevance: {ctx.total_logs_after_scoring}\n\n"
        )
        
        # Severity summary with attack indicators
        if ctx.severity_summary:
            prompt += "# SEVERITY DISTRIBUTION\n"
            total_events = sum(ctx.severity_summary.values())
            for sev, count in sorted(ctx.severity_summary.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_events * 100) if total_events > 0 else 0
                prompt += f"  • {sev}: {count} ({percentage:.1f}%)\n"
            prompt += "\n"
        
        # Top error patterns with attack classification
        if ctx.top_patterns:
            prompt += "# TOP ERROR PATTERNS (Most Frequent)\n"
            for i, p in enumerate(ctx.top_patterns, 1):
                # Classify pattern as potential attack
                pattern_lower = p['pattern'].lower()
                attack_indicator = ""
                if any(kw in pattern_lower for kw in ['failed', 'denied', 'unauthorized', 'reject', 'brute']):
                    attack_indicator = " ⚠️ ATTACK INDICATOR"
                prompt += f"  {i}. [{p['component']}] {p['pattern']} (count: {p['count']}){attack_indicator}\n"
            prompt += "\n"
        
        # Suspicious actors with threat level
        if ctx.suspicious_ips:
            prompt += "# SUSPICIOUS IP ADDRESSES\n"
            for item in ctx.suspicious_ips:
                threat_level = "HIGH" if item['count'] >= 10 else "MEDIUM" if item['count'] >= 5 else "LOW"
                prompt += f"  • {item['ip']} - {item['count']} occurrences [Threat: {threat_level}]\n"
            prompt += "\n"
        
        if ctx.suspicious_users:
            prompt += "# SUSPICIOUS USERS/IDENTITIES\n"
            for item in ctx.suspicious_users:
                prompt += f"  • {item['user']} - {item['count']} actions\n"
            prompt += "\n"
        
        if ctx.suspicious_apis:
            prompt += "# API ACTIONS OBSERVED\n"
            for item in ctx.suspicious_apis:
                # Highlight dangerous APIs
                api_lower = item['api'].lower()
                danger_flag = ""
                if any(kw in api_lower for kw in ['delete', 'terminate', 'stop', 'disable', 'remove']):
                    danger_flag = " 🔴 DESTRUCTIVE"
                elif any(kw in api_lower for kw in ['create', 'attach', 'put', 'update']):
                    danger_flag = " 🟡 MODIFICATION"
                prompt += f"  • {item['api']} (count: {item['count']}){danger_flag}\n"
            prompt += "\n"
        
        # Within-source hints
        if ctx.within_source_hints:
            prompt += "# CORRELATION INSIGHTS\n"
            for hint in ctx.within_source_hints:
                prompt += f"  • {hint}\n"
            prompt += "\n"
        
        # NEW: Multi-source correlation context (Priority 1 enhancement)
        if ctx.is_multi_source and ctx.correlated_events_summary:
            prompt += "# 🔗 MULTI-SOURCE CORRELATION CONTEXT (CRITICAL)\n\n"
            prompt += "⚠️ IMPORTANT: These events are ALREADY CORRELATED across multiple log sources.\n"
            prompt += "DO NOT re-discover correlations. The correlator has already:\n"
            prompt += f"  • Linked events using: {', '.join(ctx.correlation_keys_used or ['trace_id', 'request_id', 'session_id', 'IP'])}\n"
            prompt += "  • Detected timeline sequences with delay calculations\n"
            prompt += "  • Matched against detection rules\n"
            prompt += "  • Calculated multi-factor confidence scores\n\n"
            prompt += ctx.correlated_events_summary
            prompt += "\n"
            prompt += "YOUR FOCUS SHOULD BE:\n"
            prompt += "  1. ROOT CAUSE ANALYSIS - Why did this attack succeed?\n"
            prompt += "  2. BUSINESS IMPACT - What's at risk?\n"
            prompt += "  3. ACTIONABLE REMEDIATION - Specific steps with AWS CLI commands\n"
            prompt += "  4. PREVENTION - How to stop this from happening again\n\n"
            prompt += "DO NOT waste effort re-discovering what the correlator already found.\n"
            prompt += "Leverage the correlation context to provide DEEPER insights.\n\n"
        
        # Temporal analysis (attack velocity, burst detection)
        if ctx.temporal_analysis:
            tp = ctx.temporal_analysis
            prompt += "# TEMPORAL ANALYSIS\n"
            prompt += f"  • First Occurrence: {tp.get('first_occurrence', 'N/A')}\n"
            prompt += f"  • Last Occurrence: {tp.get('last_occurrence', 'N/A')}\n"
            prompt += f"  • Duration: {tp.get('duration_minutes', 0):.1f} minutes\n"
            prompt += f"  • Total Events: {tp.get('total_occurrences', 0)}\n"
            prompt += f"  • Event Rate: {tp.get('events_per_minute', 0):.1f} events/minute\n"
            prompt += f"  • Peak Activity: {tp.get('peak_activity_time', 'N/A')} ({tp.get('peak_activity_count', 0)} events)\n"
            if tp.get('is_burst_attack'):
                prompt += "  ⚠️ BURST ATTACK PATTERN DETECTED — High event velocity suggests automated attack\n"
            prompt += "\n"
        
        # Representative samples with context
        if ctx.representative_samples:
            prompt += "# REPRESENTATIVE LOG SAMPLES (Highest Relevance)\n"
            for i, sample in enumerate(ctx.representative_samples, 1):
                prompt += f"{i}. {sample}\n"
            prompt += "\n"
        
        # Detected issues to enhance
        prompt += "# DETECTED SECURITY ISSUES\n\n"
        for i, solution in enumerate(solutions, 1):
            prompt += f"## Issue {i}: {solution.problem}\n"
            prompt += f"Basic Analysis: {solution.solution}\n"
            prompt += f"Affected Components: {', '.join(solution.affected_components)}\n"
            prompt += f"Issue Type: {solution.issue_type.value}\n\n"
        
        # Attack-specific guidance
        attack_guidance = {
            'vpc_flow': (
                "# ATTACK PATTERNS TO DETECT\n"
                "• Port Scanning: Multiple connection attempts to different ports from same IP\n"
                "• Brute Force: High frequency of REJECT events to SSH (22), RDP (3389)\n"
                "• DDoS: Abnormally high traffic volume from multiple IPs\n"
                "• Lateral Movement: Internal IP scanning after initial compromise\n"
                "• Data Exfiltration: Large outbound traffic to suspicious destinations\n\n"
            ),
            'cloudtrail': (
                "# ATTACK PATTERNS TO DETECT\n"
                "• Privilege Escalation: CreateAccessKey, AttachRolePolicy by non-admin\n"
                "• Resource Destruction: DeleteVpc, TerminateInstances, StopLogging\n"
                "• Credential Theft: GetPasswordData, CreateLoginProfile\n"
                "• Reconnaissance: Multiple DescribeInstances, ListBuckets calls\n"
                "• Persistence: CreateUser, PutRolePolicy for backdoor access\n\n"
            ),
            'app': (
                "# ATTACK PATTERNS TO DETECT\n"
                "• SQL Injection: Malformed queries, UNION SELECT patterns\n"
                "• Authentication Bypass: Multiple failed login attempts\n"
                "• Path Traversal: ../ patterns in file access logs\n"
                "• Command Injection: Shell metacharacters in input\n"
                "• Session Hijacking: Token reuse, expired session access\n\n"
            ),
            'multi_source': (
                "# CROSS-SOURCE ATTACK PATTERNS TO DETECT\n"
                "• Coordinated Attack: Same IP appears in VPC REJECT + Application exploit + CloudTrail API abuse\n"
                "• Kill Chain Progression: Network reconnaissance → Application exploit → Privilege escalation → Data exfiltration\n"
                "• Lateral Movement: Internal IPs appearing across VPC flow + Application logs\n"
                "• Multi-Layer Brute Force: Failed SSH in VPC + Failed auth in App + AccessDenied in CloudTrail\n"
                "• APT Indicators: Low-and-slow activity across multiple sources over extended time period\n"
                "• Infrastructure Compromise: Database connection spikes correlated with application attack patterns\n\n"
            )
        }
        prompt += attack_guidance.get(ctx.source_type, "")
        
        # Enhanced analysis instructions with MANDATORY 5 Why
        prompt += (
            "# YOUR TASK: COMPREHENSIVE SECURITY ANALYSIS\n\n"
            "Analyze each issue using the MITRE ATT&CK framework and provide:\n\n"
            "1. **THREAT CLASSIFICATION**\n"
            "   - Attack technique (e.g., T1498 Network DoS, T1110 Brute Force, T1078 Valid Accounts)\n"
            "   - Threat actor profile (script kiddie, APT, insider)\n"
            "   - Attack stage (reconnaissance, initial access, persistence, impact, etc.)\n"
            "   ⚠️ CRITICAL: Match MITRE technique to ACTUAL attack type:\n"
            "      • DoS/DDoS → TA0040 Impact + T1498 Network Denial of Service\n"
            "      • Brute Force → TA0001 Initial Access + T1110 Brute Force\n"
            "      • Exploit → TA0001 Initial Access + T1190 Exploit Public-Facing Application\n\n"
            "2. **EVIDENCE-BASED ANALYSIS**\n"
            "   - Quote EXACT log entries that prove the attack\n"
            "   - Identify attack timeline (first seen, peak activity, last seen)\n"
            "   - Calculate attack metrics (attempts/minute, success rate)\n"
            "   ⚠️ CRITICAL: Use CONSERVATIVE language for inferred data:\n"
            "      • BAD: '500 concurrent connections' (if not explicitly in logs)\n"
            "      • GOOD: 'High volume of incoming connections (~500 requests observed within short time window)'\n"
            "      • BAD: 'No WAF configured' (if no WAF info in logs)\n"
            "      • GOOD: 'No evidence of WAF or rate limiting observed in logs'\n\n"
            "3. **IMPACT ASSESSMENT**\n"
            "   - Severity: Critical/High/Medium/Low with justification\n"
            "   - Blast radius: Which systems/data are at risk\n"
            "   - Business impact: Downtime, data loss, compliance violation\n\n"
            "4. **ROOT CAUSE ANALYSIS (MANDATORY 5 WHY)**\n"
            "   ⚠️ CRITICAL: You MUST perform a 5 Why analysis to find the TRUE root cause.\n"
            "   Do NOT stop at symptoms like 'attack happened' or 'DoS detected'.\n"
            "   Dig deeper with each 'Why?' to find the TECHNICAL FAILURE first, then PROCESS GAP.\n\n"
            "   🎯 CRITICAL RULE: Root Cause vs WHY #5\n"
            "   • Root Cause = TECHNICAL failure (log-based, e.g., 'connection pool exhausted')\n"
            "   • WHY #5 = PROCESS GAP (missing control in deployment/operations)\n"
            "   • These are DIFFERENT things! Do NOT call WHY #5 'root cause'!\n\n"
            "   Example of GOOD 5 Why:\n"
            "   WHY #1: Why did service degrade? → Because connection pool exhausted (100/100)\n"
            "   WHY #2: Why did pool exhaust? → Because high volume of incoming connections (~500 requests observed)\n"
            "   WHY #3: Why did connections succeed? → Because no evidence of rate limiting in logs\n"
            "   WHY #4: Why no rate limiting? → Because ALB deployed without WAF\n"
            "   WHY #5: Why deployed without WAF? → ⭐ PROCESS GAP: Missing security controls in deployment checklist (e.g., WAF, rate limiting)\n"
            "   ROOT CAUSE: Connection pool exhausted (100/100) due to high connection volume\n\n"
            "   Example of BAD 5 Why (DO NOT DO THIS):\n"
            "   WHY #1: Why did incident occur? → Because of DoS attack ❌ (This is a symptom!)\n"
            "   WHY #5: ROOT CAUSE = Missing WAF ❌ (This is WHY #5, NOT root cause!)\n"
            "   ROOT CAUSE: DoS attack ❌ (This is NOT a root cause!)\n\n"
            "5. **ATTACK PROGRESSION (SIGNATURE)**\n"
            "   Identify the full attack chain if multiple stages detected:\n"
            "   1. Reconnaissance: Port scanning via VPC REJECT events\n"
            "   2. Network Flood: High-frequency connection attempts\n"
            "   3. Application Flood: Increased HTTP request rate\n"
            "   4. Resource Exhaustion: Connection pool saturation\n"
            "   5. Service Degradation: Timeouts and HTTP 500 errors\n\n"
            "6. **IMMEDIATE RESPONSE**\n"
            "   - Containment: Block attacker IPs (if multiple IPs, block all or use rate limiting)\n"
            "   - Scaling: Increase connection pool, scale up instances (strategic response)\n"
            "   - Rate Limiting: Enable rate limiting on ALB/WAF (strategic response)\n"
            "   - Verification: Command to confirm attack stopped\n"
            "   - Evidence preservation: Logs to save for forensics\n"
            "   ⚠️ CRITICAL: Prioritize STRATEGIC actions (rate limiting, scaling) over TACTICAL (block single IP)\n\n"
        )
        
        # Critical rules
        prompt += (
            "# CRITICAL RULES\n"
            "✓ Use ACTUAL values from logs (IPs, usernames, timestamps)\n"
            "✓ Provide EXECUTABLE commands (not placeholders)\n"
            "✓ Reference SPECIFIC log entries as evidence\n"
            "✓ Calculate METRICS from the data (frequency, duration)\n"
            "✓ Explain WHY this is an attack (not just what happened)\n"
            "✓ KEEP IT CONCISE. Use maximum 1-2 short sentences for text fields.\n"
            "✓ Limit `evidence_from_logs` array to MAXIMUM 3 entries.\n"
            "✓ MITRE ATT&CK Mapping: MUST match the actual attack type:\n"
            "   • DoS/DDoS → TA0040 Impact + T1498 Network Denial of Service (NOT T1190!)\n"
            "   • Port 3306 attacks → T1190 Exploit or T1078 Valid Accounts (NOT RDP!)\n"
            "   • Brute Force → TA0001 Initial Access + T1110 Brute Force\n"
            "✓ INCIDENT RESPONSE: NEVER block internal/destination IPs (e.g., 10.x.x.x, 172.x.x.x, 192.168.x.x). ALWAYS block the external SOURCE/ATTACKER IP.\n"
            "✓ EVIDENCE WORDING: Use conservative language for inferred data:\n"
            "   • 'High volume of connections (~500 observed)' NOT '500 concurrent connections'\n"
            "   • 'No evidence of WAF in logs' NOT 'No WAF configured'\n"
            "✓ ROOT CAUSE vs WHY #5: These are DIFFERENT!\n"
            "   • Root Cause = Technical failure (e.g., 'connection pool exhausted')\n"
            "   • WHY #5 = Process gap (e.g., 'Missing security controls in deployment checklist')\n"
            "✗ NO generic advice without evidence\n"
            "✗ NO placeholder values like <instance-id>\n"
            "✗ NO assumptions not supported by logs\n"
            "✗ DO NOT call WHY #5 'root cause' - it's a PROCESS GAP!\n\n"
        )
        
        # JSON schema with 5 Why structure
        prompt += (
            "# OUTPUT FORMAT\n"
            "Return ONLY a valid JSON array (no markdown, no explanation):\n\n"
            "[\n"
            "  {\n"
            '    "problem": "exact original problem title",\n'
            '    "attack_classification": {\n'
            '      "mitre_technique": "T1498 - Network Denial of Service (for DoS) OR T1110.001 - Password Guessing (for brute force)",\n'
            '      "mitre_tactic": "TA0040 - Impact (for DoS) OR TA0001 - Initial Access (for brute force)",\n'
            '      "threat_actor_profile": "Automated bot / Script kiddie / APT",\n'
            '      "attack_stage": "Initial Access / Persistence / Privilege Escalation / Impact"\n'
            '    },\n'
            '    "attack_progression": {\n'
            '      "stages_detected": [\n'
            '        {"stage": "Reconnaissance", "description": "Port scanning via VPC REJECT events (ports 22, 3306, 443)", "evidence": "215 REJECT events"},\n'
            '        {"stage": "Network Flood", "description": "High-frequency connection attempts", "evidence": "~500 connections in 2 minutes"},\n'
            '        {"stage": "Resource Exhaustion", "description": "Connection pool saturation", "evidence": "Pool 100/100"},\n'
            '        {"stage": "Service Degradation", "description": "Timeouts and errors", "evidence": "HTTP 500 errors, RDS timeout"}\n'
            '      ]\n'
            '    },\n'
            '    "summary": {\n'
            '      "severity": "Critical / High / Medium / Low",\n'
            '      "impact": "Brief description of blast radius and business impact",\n'
            '      "confidence": "Confirmed / Highly Likely / Possible"\n'
            '    },\n'
            '    "investigation": {\n'
            '      "evidence_from_logs": [\n'
            '        "Exact log entry 1 with timestamp",\n'
            '        "Exact log entry 2 with timestamp"\n'
            '      ],\n'
            '      "attack_timeline": {\n'
            '        "first_seen": "2024-01-15 10:23:45",\n'
            '        "peak_activity": "2024-01-15 10:25:00",\n'
            '        "last_seen": "2024-01-15 10:27:30",\n'
            '        "total_duration": "3 minutes 45 seconds"\n'
            '      },\n'
            '      "attack_metrics": {\n'
            '        "total_attempts": 53,\n'
            '        "attempts_per_minute": 14.5,\n'
            '        "success_rate": "0%",\n'
            '        "unique_targets": 3\n'
            '      },\n'
            '      "inference": [\n'
            '        "Deduction 1 based on evidence",\n'
            '        "Deduction 2 based on patterns"\n'
            '      ],\n'
            '      "why_not_other_causes": "Explanation ruling out false positives"\n'
            '    },\n'
            '    "root_cause_analysis": {\n'
            '      "root_cause": "TECHNICAL FAILURE from logs (e.g., Connection pool exhausted 100/100)",\n'
            '      "why_1": {\n'
            '        "question": "Why did the incident occur?",\n'
            '        "answer": "Because [specific symptom with evidence]",\n'
            '        "evidence": "Quote exact log entry showing the symptom"\n'
            '      },\n'
            '      "why_2": {\n'
            '        "question": "Why did [answer from why_1] happen?",\n'
            '        "answer": "Because [dig deeper with conservative wording]",\n'
            '        "evidence": "Use conservative language: ~500 connections observed, NOT 500 concurrent"\n'
            '      },\n'
            '      "why_3": {\n'
            '        "question": "Why did [answer from why_2] happen?",\n'
            '        "answer": "Because [keep digging]",\n'
            '        "evidence": "Conservative: No evidence of rate limiting in logs, NOT No rate limiting configured"\n'
            '      },\n'
            '      "why_4": {\n'
            '        "question": "Why did [answer from why_3] happen?",\n'
            '        "answer": "Because [almost there]",\n'
            '        "evidence": "Conservative: No evidence of WAF in logs, NOT No WAF configured"\n'
            '      },\n'
            '      "why_5": {\n'
            '        "question": "Why did [answer from why_4] happen?",\n'
            '        "answer": "⭐ PROCESS GAP: Missing security controls in deployment checklist (e.g., WAF, rate limiting)",\n'
            '        "evidence": "This is a PROCESS GAP, NOT root cause!"\n'
            '      },\n'
            '      "root_cause_summary": "One sentence: The TECHNICAL root cause (e.g., Connection pool exhausted due to high connection volume)"\n'
            '    },\n'
            '    "control_gaps": {\n'
            '      "critical": [\n'
            '        {\n'
            '          "control": "AWS WAF on ALB",\n'
            '          "expected": "WAF with rate limiting (100 req/min per IP)",\n'
            '          "actual": "No evidence of WAF or rate limiting observed in logs",\n'
            '          "impact": "Allows high-volume unfiltered connections, leading to resource exhaustion"\n'
            '        }\n'
            '      ],\n'
            '      "medium": [\n'
            '        {\n'
            '          "control": "Connection Pool Size",\n'
            '          "expected": "500 connections",\n'
            '          "actual": "100 connections (observed in logs)",\n'
            '          "impact": "Pool exhaustion under moderate load"\n'
            '        }\n'
            '      ]\n'
            '    },\n'
            '    "action_plan": {\n'
            '      "immediate_containment": [\n'
            '        "Enable rate limiting on ALB (strategic)",\n'
            '        "Scale up application instances (strategic)",\n'
            '        "Increase connection pool temporarily (strategic)",\n'
            '        "Block attacker IPs if identified (tactical)"\n'
            '      ],\n'
            '      "next_best_command": "aws elbv2 modify-load-balancer-attributes --load-balancer-arn <arn> --attributes Key=routing.http.drop_invalid_header_fields.enabled,Value=true",\n'
            '      "verification_commands": [\n'
            '        "aws logs tail /aws/ec2/applogs --since 5m | grep ERROR",\n'
            '        "aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime"\n'
            '      ]\n'
            '    }\n'
            "  }\n"
            "]\n\n"
            "REMEMBER: Output must be PURE JSON only. No markdown code blocks, no conversational text.\n"
        )
        
        return prompt
    
    def _call_bedrock(self, prompt: str, max_retries: int = 3) -> dict:
        """
        Call Bedrock API with retry mechanism and better error handling.
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            dict with 'text' and 'usage' keys
        """
        import time
        
        last_error = None
        for attempt in range(max_retries):
            try:
                # Prepare request body based on model
                if "claude" in self.model_id.lower():
                    # Claude format
                    body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 8192,  # Increased from 4096 to 8192 for deeper analysis
                        "temperature": 0.3,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                else:
                    # Nova format
                    body = {
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": prompt}]
                            }
                        ],
                        "inferenceConfig": {
                            "maxTokens": 8192,  # Increased from 4096 to 8192 for deeper analysis
                            "temperature": 0.3,
                            "topP": 0.9
                        }
                    }
                
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps(body)
                )
                
                response_body = json.loads(response['body'].read())
                
                # Extract text and usage based on model format
                if "claude" in self.model_id.lower():
                    text = response_body['content'][0]['text']
                    usage = {
                        'input_tokens': response_body['usage']['input_tokens'],
                        'output_tokens': response_body['usage']['output_tokens'],
                        'total_tokens': response_body['usage']['input_tokens'] + response_body['usage']['output_tokens']
                    }
                else:
                    # Nova format
                    text = response_body['output']['message']['content'][0]['text']
                    usage = {
                        'input_tokens': response_body['usage']['inputTokens'],
                        'output_tokens': response_body['usage']['outputTokens'],
                        'total_tokens': response_body['usage']['inputTokens'] + response_body['usage']['outputTokens']
                    }
                
                # Validate response
                if not text or len(text) < 10:
                    raise ValueError(f"Bedrock returned empty or too short response: {text}")
                
                print(f"[Bedrock API] Success on attempt {attempt + 1}")
                return {
                    'text': text,
                    'usage': usage
                }
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Check if it's a throttling error
                if 'ThrottlingException' in error_msg or 'TooManyRequestsException' in error_msg:
                    wait_time = (2 ** attempt) * 4  # Exponential backoff: 4s, 8s, 16s
                    print(f"[Bedrock API] Throttled on attempt {attempt + 1}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Check if it's a model not found error
                if 'ResourceNotFoundException' in error_msg or 'ValidationException' in error_msg:
                    print(f"[Bedrock API] Model error: {error_msg}")
                    raise  # Don't retry for model errors
                
                # For other errors, retry with backoff
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Linear backoff: 2s, 4s
                    print(f"[Bedrock API] Error on attempt {attempt + 1}: {error_msg}")
                    print(f"[Bedrock API] Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"[Bedrock API] Failed after {max_retries} attempts")
                    raise
        
        # If we get here, all retries failed
        raise Exception(f"Bedrock API failed after {max_retries} attempts. Last error: {last_error}")
    
    def _parse_response(self, original_solutions: List[Solution], response: dict) -> List[Solution]:
        """
        Parse Bedrock response and create enhanced solutions with attack classification.
        Handles truncated JSON from max_tokens cutoff.
        """
        text = response['text']
        
        # Log raw response for debugging (first 500 chars)
        print(f"[Bedrock Response Preview] {text[:500]}")
        
        try:
            # 1. Look for markdown code blocks first
            json_text = ""
            code_block_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
            if code_block_match:
                json_text = code_block_match.group(1)
                print("[Bedrock Parse] Found JSON in markdown code block")
            else:
                # 2. Use regex to find the start of a JSON array: [{
                match = re.search(r'\[\s*\{', text, re.DOTALL)
                if match:
                    json_start = match.start()
                    json_end = text.rfind(']') + 1
                    if json_end > json_start:
                        json_text = text[json_start:json_end]
                else:
                    # 3. Fallback to simple find
                    json_start = text.find('[')
                    json_end = text.rfind(']') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_text = text[json_start:json_end]

            if json_text:
                enhanced_data = self._safe_json_loads(json_text)
                
                if enhanced_data is not None:
                    enhanced_solutions = []
                    for i, solution in enumerate(original_solutions):
                        if i < len(enhanced_data):
                            raw_val = enhanced_data[i]
                            # Check if we have the new enhanced format with attack_classification
                            if isinstance(raw_val, dict) and ("summary" in raw_val or "attack_classification" in raw_val):
                                # New structured format
                                enhanced_text = "See Details"
                                structured_data = raw_val
                                
                                # Validate RCA quality
                                validation = self._validate_rca_quality(structured_data)
                                print(f"[RCA Quality Check] Issue {i+1}: Grade {validation['grade']} (Score: {validation['quality_score']}/100)")
                                for fb in validation['feedback']:
                                    print(f"  {fb}")
                                
                                if not validation['is_acceptable']:
                                    print(f"[RCA Quality Warning] Issue {i+1} has low quality RCA (score < 70)")
                                
                                # Validate required fields
                                if "summary" not in structured_data:
                                    print(f"[Bedrock Parse Warning] Missing 'summary' in response for issue {i+1}")
                                if "investigation" not in structured_data:
                                    print(f"[Bedrock Parse Warning] Missing 'investigation' in response for issue {i+1}")
                                if "action_plan" not in structured_data:
                                    print(f"[Bedrock Parse Warning] Missing 'action_plan' in response for issue {i+1}")
                            else:
                                # Legacy format
                                enhanced_text = str(raw_val.get('enhanced_solution', solution.solution))
                                structured_data = None
                        else:
                            enhanced_text = solution.solution
                            structured_data = None
                        
                        # Calculate per-solution cost
                        total_tokens = response.get('usage', {}).get('total_tokens', 0)
                        tokens_per_solution = total_tokens // len(original_solutions)
                        
                        usage = response.get('usage', {})
                        input_tokens = usage.get('input_tokens')
                        output_tokens = usage.get('output_tokens')
                        
                        if input_tokens and output_tokens:
                            cost_per_solution = self._calculate_cost(
                                tokens_per_solution,
                                input_tokens // len(original_solutions),
                                output_tokens // len(original_solutions)
                            )
                        else:
                            cost_per_solution = self._calculate_cost(tokens_per_solution)
                        
                        enhanced_solution = Solution(
                            problem=solution.problem,
                            solution=enhanced_text,
                            issue_type=solution.issue_type,
                            affected_components=solution.affected_components,
                            ai_enhanced=True,
                            tokens_used=tokens_per_solution,
                            estimated_cost=cost_per_solution,
                            structured_solution=structured_data
                        )
                        enhanced_solutions.append(enhanced_solution)
                    
                    print(f"[Bedrock Parse] Successfully parsed {len(enhanced_solutions)} enhanced solutions")
                    return enhanced_solutions
                else:
                    print(f"[Bedrock Parse Warning] Could not parse JSON even after repair. Text: {json_text[:500]}")
                    return original_solutions
            else:
                # No JSON array found at all
                print(f"[Bedrock Parse Warning] No JSON array found in response. Full text: {text[:1000]}")
                return original_solutions
        
        except Exception as e:
            print(f"[Bedrock Parse Error] Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return original_solutions
    
    def _fix_json_newlines(self, text: str) -> str:
        """
        Escape literal newlines/tabs inside JSON string values.
        
        When AI writes multi-line text directly inside a JSON string (without \\n),
        the result is invalid JSON. This method walks through char-by-char,
        tracking whether we are inside a string, and escapes bare newlines.
        """
        result = []
        in_string = False
        escape_next = False

        for ch in text:
            if escape_next:
                result.append(ch)
                escape_next = False
                continue

            if ch == '\\' and in_string:
                result.append(ch)
                escape_next = True
                continue

            if ch == '"':
                in_string = not in_string
                result.append(ch)
                continue

            if in_string:
                if ch == '\n':
                    result.append('\\n')
                    continue
                if ch == '\r':
                    result.append('\\r')
                    continue
                if ch == '\t':
                    result.append('\\t')
                    continue

            result.append(ch)

        return ''.join(result)

    def _safe_json_loads(self, text: str):
        """
        Try to parse JSON robustly.
        Step 1: Fix literal newlines inside string values (most common AI mistake).
        Step 2: Direct parse.
        Step 3: If truncated, find last complete object and close the array.
        """
        # Step 1: Fix literal newlines inside JSON strings
        fixed = self._fix_json_newlines(text)

        # Step 2: Direct parse on fixed text
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        # Step 3: Response might be truncated — find last complete } and close ]
        repaired = fixed.rstrip()
        last_brace = repaired.rfind('}')
        if last_brace > 0:
            repaired = repaired[:last_brace + 1]
            if not repaired.rstrip().endswith(']'):
                repaired = repaired.rstrip().rstrip(',') + ']'
            try:
                result = json.loads(repaired)
                print(f"[Bedrock Parse] Repaired truncated JSON ({len(result)} items salvaged)")
                return result
            except json.JSONDecodeError:
                pass

        print(f"[Bedrock Parse] All repair attempts failed. Raw snippet: {text[:300]}")
        return None

    def _validate_rca_quality(self, parsed_response: dict) -> dict:
        """
        Validate if RCA is deep enough with evidence.
        Returns quality score and feedback.
        """
        quality_score = 0
        feedback = []
        
        # Check 1: Has root_cause_analysis section?
        if 'root_cause_analysis' in parsed_response:
            rca = parsed_response['root_cause_analysis']
            
            # Check for 5 Why questions
            why_count = sum(1 for k in rca.keys() if k.startswith('why_'))
            if why_count >= 5:
                quality_score += 40
                feedback.append(f"✅ Complete 5 Why analysis ({why_count} questions)")
            elif why_count >= 3:
                quality_score += 20
                feedback.append(f"⚠️ Partial 5 Why analysis ({why_count}/5 questions)")
            else:
                feedback.append(f"❌ Incomplete 5 Why analysis ({why_count}/5 questions)")
            
            # Check for evidence in Why answers
            evidence_count = 0
            for i in range(1, 6):
                why_key = f"why_{i}"
                if why_key in rca:
                    why_item = rca[why_key]
                    if isinstance(why_item, dict) and 'evidence' in why_item and len(why_item.get('evidence', '')) > 10:
                        evidence_count += 1
            
            if evidence_count >= 4:
                quality_score += 20
                feedback.append(f"✅ Evidence provided for {evidence_count}/5 Why answers")
            elif evidence_count >= 2:
                quality_score += 10
                feedback.append(f"⚠️ Evidence provided for only {evidence_count}/5 Why answers")
            else:
                feedback.append(f"❌ Insufficient evidence ({evidence_count}/5 Why answers)")
            
            # Check for root_cause_summary
            if 'root_cause_summary' in rca and len(rca['root_cause_summary']) > 20:
                quality_score += 10
                feedback.append("✅ Root cause summary present")
            else:
                feedback.append("❌ Missing or too short root cause summary")
        else:
            feedback.append("❌ Missing root_cause_analysis section entirely")
        
        # Check 2: Root cause is SPECIFIC (not generic)
        root_cause_summary = parsed_response.get('root_cause_analysis', {}).get('root_cause_summary', '').lower()
        
        # Generic keywords (BAD)
        generic_keywords = ['process', 'operations', 'comprehensive', 'robust', 'adequate', 'proper']
        # Specific keywords (GOOD)
        specific_keywords = ['waf', 'rate limiting', 'connection pool', 'security group', 'alb', 'firewall', 'max_connections']
        
        has_generic = any(kw in root_cause_summary for kw in generic_keywords)
        has_specific = any(kw in root_cause_summary for kw in specific_keywords)
        
        if has_specific:
            quality_score += 30
            feedback.append("✅ Root cause is SPECIFIC (mentions concrete controls/configs)")
        elif has_generic and not has_specific:
            quality_score += 5
            feedback.append("⚠️ Root cause is too GENERIC (lacks specific control names)")
        else:
            feedback.append("❌ Root cause lacks specificity")
        
        return {
            'quality_score': quality_score,
            'feedback': feedback,
            'is_acceptable': quality_score >= 70,
            'grade': 'A' if quality_score >= 90 else 'B' if quality_score >= 70 else 'C' if quality_score >= 50 else 'D'
        }


    
    def _calculate_cost(self, tokens: int, input_tokens: int = None, output_tokens: int = None) -> float:
        """
        Calculate estimated cost based on tokens with accurate input/output split.
        
        Args:
            tokens: Total tokens (used if input/output not provided)
            input_tokens: Actual input tokens (if available)
            output_tokens: Actual output tokens (if available)
            
        Returns:
            Estimated cost in USD
        """
        # If we have actual input/output split, use it
        if input_tokens is not None and output_tokens is not None:
            if "nova-micro" in self.model_id.lower():
                input_cost_per_1m = 0.035
                output_cost_per_1m = 0.14
            elif "haiku" in self.model_id.lower():
                input_cost_per_1m = 0.25
                output_cost_per_1m = 1.25
            elif "sonnet" in self.model_id.lower():
                input_cost_per_1m = 3.0
                output_cost_per_1m = 15.0
            else:
                # Default to Nova Micro
                input_cost_per_1m = 0.035
                output_cost_per_1m = 0.14
            
            input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
            output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
            return input_cost + output_cost
        
        # Fallback: assume 50/50 split if actual split not available
        if "nova-micro" in self.model_id.lower():
            input_cost_per_1m = 0.035
            output_cost_per_1m = 0.14
            avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
        elif "haiku" in self.model_id.lower():
            input_cost_per_1m = 0.25
            output_cost_per_1m = 1.25
            avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
        elif "sonnet" in self.model_id.lower():
            input_cost_per_1m = 3.0
            output_cost_per_1m = 15.0
            avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
        else:
            # Default to Nova Micro pricing
            avg_cost_per_1m = 0.0875
        
        return (tokens / 1_000_000) * avg_cost_per_1m

    # ================================================================
    # Global RCA — ONE call, FULL picture
    # ================================================================

    def generate_global_rca(self, unified_context: dict) -> tuple:
        """
        Send ONE comprehensive API call with full cross-source context.
        Returns (GlobalRCA, usage_stats).
        """
        from models import GlobalRCA
        
        if not self.is_available():
            return GlobalRCA(), {"ai_enhancement_used": False, "error": "Bedrock not available"}
        
        prompt = self._build_global_rca_prompt(unified_context)
        
        try:
            response = self._call_bedrock(prompt)
            text = response.get('text', '')
            usage = response.get('usage', {})
            
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            cost = self._calculate_cost(total_tokens, input_tokens, output_tokens)
            
            print(f"[Global RCA] Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost:.4f}")
            
            # Parse JSON response
            parsed = self._extract_json_object(text)
            
            if parsed:
                rca = GlobalRCA(
                    incident_story=parsed.get('incident_story', []),
                    threat_assessment=parsed.get('threat_assessment', {}),
                    attack_narrative=parsed.get('attack_narrative', ''),
                    affected_components=parsed.get('affected_components', []),
                    root_cause=parsed.get('root_cause', ''),
                    mitre_mapping=parsed.get('mitre_mapping', {}),
                    immediate_actions=parsed.get('immediate_actions', []),
                    remediation_plan=parsed.get('remediation_plan', {}),
                    raw_ai_response=parsed,
                    tokens_used=total_tokens,
                    cost=cost,
                )
            else:
                rca = GlobalRCA(
                    attack_narrative=text[:500],
                    raw_ai_response={'raw_text': text[:1000]},
                    tokens_used=total_tokens,
                    cost=cost,
                )
            
            stats = {
                "ai_enhancement_used": True,
                "bedrock_model_used": self.model_id,
                "total_tokens_used": total_tokens,
                "estimated_total_cost": cost,
                "api_calls_made": 1,
            }
            return rca, stats
            
        except Exception as e:
            print(f"[Global RCA] Error: {e}")
            return GlobalRCA(), {"ai_enhancement_used": False, "error": str(e)}

    def _build_global_rca_prompt(self, ctx: dict) -> str:
        """Build the prompt for Global RCA using unified context with event signals."""
        import json as _json
        
        prompt = (
            "You are an expert AWS Security Operations Center (SOC) analyst.\n"
            "You are performing a GLOBAL Root Cause Analysis across multiple AWS log sources.\n\n"
        )
        
        # --- Overview ---
        prompt += (
            "# ENVIRONMENT OVERVIEW\n"
            f"Sources analyzed: {ctx.get('source_count', 0)}\n"
            f"Total log entries: {ctx.get('total_logs', 0)}\n"
            f"Time range: {ctx.get('time_range', 'N/A')}\n"
            f"Correlated attack patterns detected: {ctx.get('correlation_count', 0)}\n\n"
        )
        
        # --- Per-source summaries ---
        prompt += "# PER-SOURCE HEALTH SUMMARY\n"
        for source, summary in ctx.get('source_summaries', {}).items():
            prompt += (
                f"## {source}\n"
                f"  Entries: {summary.get('total_entries', 0)} | "
                f"Errors: {summary.get('error_count', 0)} ({summary.get('error_rate', '0%')})\n"
                f"  Severity: {_json.dumps(summary.get('severity_distribution', {}))}\n"
            )
            if summary.get('top_ips'):
                ips_str = ', '.join(f"{ip['ip']}({ip['count']}x)" for ip in summary['top_ips'][:3])
                prompt += f"  Top IPs: {ips_str}\n"
            prompt += "\n"
        
        # --- Event signals (core intelligence) ---
        prompt += "# DETECTED EVENT SIGNALS (Abstracted from raw logs)\n"
        for i, sig in enumerate(ctx.get('signals', [])[:20], 1):
            prompt += (
                f"{i}. [{sig.get('severity', 'UNKNOWN')}] {sig.get('event_type', 'unknown')} "
                f"(source: {sig.get('source', '?')}, count: {sig.get('count', 0)}, "
                f"anomaly: {sig.get('anomaly_score', 0)})\n"
                f"   {sig.get('description', '')[:150]}\n"
            )
            if sig.get('actors'):
                prompt += f"   Actors: {', '.join(sig['actors'][:3])}\n"
            if sig.get('time_window'):
                prompt += f"   Window: {sig.get('time_window')}\n"
            if sig.get('indicators'):
                prompt += f"   Indicators: {_json.dumps(sig['indicators'])[:200]}\n"
        prompt += "\n"
        
        # --- Correlated incident timeline ---
        if ctx.get('incident_timeline'):
            prompt += "# CORRELATED INCIDENT TIMELINE (Cross-source, chronological)\n"
            for evt in ctx['incident_timeline'][:15]:
                prompt += (
                    f"  [{evt.get('time', '?')}] {evt.get('source', '?')}: "
                    f"{evt.get('event', '?')} by {evt.get('actor', '?')} "
                    f"- {evt.get('message', '')[:80]}\n"
                )
            prompt += "\n"
        
        # --- Suspicious IPs ---
        if ctx.get('suspicious_ips'):
            prompt += "# SUSPICIOUS IP ADDRESSES\n"
            for ip_info in ctx['suspicious_ips']:
                ext_label = "EXTERNAL" if ip_info.get('is_external') else "INTERNAL"
                prompt += f"  {ip_info['ip']} - {ip_info['count']} occurrences [{ext_label}]\n"
            prompt += "\n"
        
        # --- Critical raw samples (tiny selection) ---
        if ctx.get('critical_samples'):
            prompt += "# CRITICAL RAW LOG SAMPLES (Top 5 most severe)\n"
            for sample in ctx['critical_samples'][:5]:
                prompt += f"  {sample}\n"
            prompt += "\n"
        
        # --- Output format ---
        prompt += (
            "# YOUR TASK\n"
            "Produce a comprehensive Global Root Cause Analysis as a single JSON object.\n\n"
            "# CRITICAL RULES\n"
            "- Use ONLY data from the signals and logs above. NEVER invent IPs, timestamps, or events.\n"
            "- NEVER block internal/destination IPs (10.x, 172.x, 192.168.x). Block EXTERNAL SOURCE IPs only.\n"
            "- MITRE technique MUST match actual attack type:\n"
            "  • DoS/DDoS → TA0040 Impact + T1498 Network Denial of Service (NOT T1190!)\n"
            "  • Port 3306 attacks → T1190 Exploit or T1078 Valid Accounts (NOT RDP!)\n"
            "  • Brute Force → TA0001 Initial Access + T1110 Brute Force\n"
            "- Confidence MUST be a float between 0.0 and 1.0 with reasoning.\n"
            "- Keep text fields concise (1-2 sentences max).\n"
            "- MANDATORY: Perform 5 Why analysis with EVIDENCE from logs.\n"
            "- MANDATORY: Each Why answer MUST include specific metrics/values from logs.\n"
            "- MANDATORY: Root cause MUST be the DIRECT technical failure (e.g., 'Connection pool exhausted', 'Memory OOM').\n"
            "- MANDATORY: WHY #5 is a PROCESS GAP (NOT root cause!) - missing controls in deployment/operations.\n"
            "- MANDATORY: Control Gaps are SEPARATE from Root Cause (missing protections like WAF, rate limiting).\n"
            "- MANDATORY: Use CONSERVATIVE language for inferred data:\n"
            "  • 'High volume of connections (~500 observed)' NOT '500 concurrent connections'\n"
            "  • 'No evidence of WAF in logs' NOT 'No WAF configured'\n\n"
            "# ROOT CAUSE vs CONTROL GAP (CRITICAL DISTINCTION)\n"
            "❗ ROOT CAUSE = What DIRECTLY killed the system (technical failure)\n"
            "   Examples: 'Connection pool exhausted (100/100)', 'Memory OOM (99% heap)', 'CPU 100%'\n"
            "   Evidence: MUST quote exact log entries showing the failure\n\n"
            "❗ CONTROL GAP = What SHOULD HAVE prevented it (missing protection)\n"
            "   Examples: 'No WAF', 'No rate limiting', 'Connection pool too small (100)'\n"
            "   Evidence: Can infer from absence (e.g., 'No WAF logs found')\n\n"
            "BAD Example (WRONG):\n"
            "Root Cause: 'No AWS WAF on ALB' ❌ (This is a Control Gap, not Root Cause!)\n\n"
            "GOOD Example (CORRECT):\n"
            "Root Cause: 'Connection pool exhausted (100/100) causing request timeouts' ✅\n"
            "Control Gap: 'No WAF to filter malicious traffic' ✅\n\n"
            "# EVIDENCE RULES (CRITICAL)\n"
            "❗ NEVER fabricate evidence not in logs\n"
            "❗ If you don't see ALB config in logs, DON'T claim 'ALB config shows...'\n"
            "❗ If you don't see WAF logs, DON'T claim 'WAF rules show...'\n"
            "❗ Only quote ACTUAL log entries provided in the context\n\n"
            "ALLOWED Evidence:\n"
            "✅ Direct quotes from logs: '[ERROR] ConnectionPool: active=100/100'\n"
            "✅ Metrics from logs: '215 REJECT events, 153 errors'\n"
            "✅ Absence inference: 'No WAF logs found in provided log sources'\n\n"
            "FORBIDDEN Evidence:\n"
            "❌ 'ALB config shows...' (if no ALB config in logs)\n"
            "❌ 'Security group rules indicate...' (if no SG logs)\n"
            "❌ 'WAF configuration reveals...' (if no WAF logs)\n\n"
            "# 5 WHY EVIDENCE REQUIREMENTS\n"
            "Each Why answer MUST follow this format:\n"
            "- WHY #1-2: Quote EXACT log entries showing DIRECT technical failure\n"
            "  Example: 'Connection pool exhausted' with evidence '[ERROR] ConnectionPool: active=100/100 idle=0'\n"
            "- WHY #3-4: Explain HOW the failure cascaded (use conservative language)\n"
            "  Example: 'Pool exhausted because high volume of connections (~500 observed)' with evidence 'VPC Flow: ~500 ACCEPT events in 2 minutes'\n"
            "- WHY #5: Identify the PROCESS GAP (NOT root cause!)\n"
            "  Example: '⭐ PROCESS GAP: Missing security controls in deployment checklist (e.g., WAF, rate limiting)' with evidence 'No rate limiting logs found'\n\n"
            "# CONTROL GAPS REQUIREMENTS\n"
            "After 5 Why analysis, identify ALL security control gaps:\n"
            "- CRITICAL: Missing controls that directly enabled the attack (e.g., No WAF, No rate limiting)\n"
            "- MEDIUM: Insufficient controls that amplified impact (e.g., Small connection pool, No auto-scaling)\n"
            "- LOW: Missing monitoring/alerting that delayed detection (e.g., No CloudWatch alarms)\n\n"
            "For each gap, provide:\n"
            "- Control name (e.g., 'AWS WAF on ALB')\n"
            "- Expected state (e.g., 'WAF with rate limiting 100 req/min')\n"
            "- Actual state (e.g., 'No evidence of WAF or rate limiting observed in logs')\n"
            "- Impact (e.g., 'Allows high-volume unfiltered connections')\n"
            "- Fix command (for critical gaps only)\n\n"
            "BAD Example (DO NOT DO THIS):\n"
            "WHY #1: Because system was overwhelmed ❌ (No evidence!)\n"
            "WHY #5: Because lack of security process ❌ (Too generic!)\n\n"
            "GOOD Example (DO THIS):\n"
            "WHY #1: Why did service become unavailable?\n"
            "        → Because connection pool exhausted (Evidence: '[ERROR] ConnectionPool: active=100/100 idle=0 waiting=150') ✅\n"
            "WHY #3: Why did pool exhaust?\n"
            "        → Because high volume of connections (~500 observed in short time window) (Evidence: 'VPC Flow: ~500 ACCEPT events in 2 minutes') ✅\n"
            "WHY #5: Why did high-volume connections succeed?\n"
            "        → ⭐ PROCESS GAP: Missing security controls in deployment checklist (e.g., WAF, rate limiting) (Evidence: 'No rate limiting logs found') ✅\n\n"
            "ROOT CAUSE: Connection pool exhausted (100/100) due to high connection volume, causing request timeouts and service unavailability ✅\n\n"
            "CONTROL GAPS:\n"
            "🔴 Critical: No evidence of WAF or rate limiting observed in logs\n"
            "🔴 Critical: No rate limiting (should be 100 req/min per IP)\n"
            "🟡 Medium: Connection pool too small (100, should be 500)\n\n"
            "# OUTPUT FORMAT (Return ONLY valid JSON, no markdown)\n"
            "{\n"
            '  "incident_story": [\n'
            '    "[HH:MM:SS] Brief description with SPECIFIC values (e.g., connection pool 100/100)"\n'
            '  ],\n'
            '  "threat_assessment": {\n'
            '    "severity": "Critical/High/Medium/Low",\n'
            '    "confidence": 0.87,\n'
            '    "reasoning": "Why this confidence level (cite specific evidence)",\n'
            '    "scope": "Which systems/components affected with evidence"\n'
            '  },\n'
            '  "attack_narrative": "2-3 sentence summary with METRICS (e.g., 500 connections, 95% CPU)",\n'
            '  "affected_components": [\n'
            '    {"component": "/aws/vpc/flowlogs", "impact_level": "High", "evidence": "215 REJECT events from 5 attacker IPs"}\n'
            '  ],\n'
            '  "root_cause": "DIRECT technical failure that killed the system (e.g., Connection pool exhausted 100/100, Memory OOM 99%)",\n'
            '  "root_cause_analysis": {\n'
            '    "why_1": {\n'
            '      "question": "Why did the incident occur?",\n'
            '      "answer": "Because [SPECIFIC symptom with EXACT log quote or metric]",\n'
            '      "evidence": "Quote exact log entry or metric value"\n'
            '    },\n'
            '    "why_2": {\n'
            '      "question": "Why did [answer from why_1] happen?",\n'
            '      "answer": "Because [dig deeper with SPECIFIC value]",\n'
            '      "evidence": "Quote exact log entry or metric value"\n'
            '    },\n'
            '    "why_3": {\n'
            '      "question": "Why did [answer from why_2] happen?",\n'
            '      "answer": "Because [SPECIFIC missing control with conservative language]",\n'
            '      "evidence": "What control is missing (e.g., No evidence of WAF in logs, No rate limiting observed)"\n'
            '    },\n'
            '    "why_4": {\n'
            '      "question": "Why did [answer from why_3] happen?",\n'
            '      "answer": "Because [SPECIFIC configuration gap]",\n'
            '      "evidence": "What configuration is wrong (e.g., ALB deployed without WAF)"\n'
            '    },\n'
            '    "why_5": {\n'
            '      "question": "Why did [answer from why_4] happen?",\n'
            '      "answer": "⭐ PROCESS GAP: Missing security controls in deployment checklist (e.g., WAF, rate limiting)",\n'
            '      "evidence": "This is a PROCESS GAP, NOT root cause! (e.g., Deployment checklist missing DDoS protection step)"\n'
            '    },\n'
            '    "root_cause_summary": "One sentence describing DIRECT technical failure (e.g., Connection pool exhausted 100/100 due to high connection volume)"\n'
            '  },\n'
            '  "control_gaps": {\n'
            '    "critical": [\n'
            '      {\n'
            '        "control": "AWS WAF on ALB",\n'
            '        "expected": "WAF with rate limiting (100 req/min per IP)",\n'
            '        "actual": "No evidence of WAF or rate limiting observed in logs",\n'
            '        "impact": "Allows high-volume unfiltered connections, leading to resource exhaustion",\n'
            '        "fix": "aws wafv2 associate-web-acl --web-acl-arn arn:aws:wafv2:... --resource-arn arn:aws:elasticloadbalancing:..."\n'
            '      }\n'
            '    ],\n'
            '    "medium": [\n'
            '      {\n'
            '        "control": "Connection Pool Size",\n'
            '        "expected": "500 connections",\n'
            '        "actual": "100 connections",\n'
            '        "impact": "Pool exhaustion under moderate load"\n'
            '      }\n'
            '    ],\n'
            '    "low": [\n'
            '      {\n'
            '        "control": "CloudWatch Alarms",\n'
            '        "expected": "Alarm for >80% connection pool usage",\n'
            '        "actual": "No alarms configured"\n'
            '      }\n'
            '    ]\n'
            '  },\n'
            '  "mitre_mapping": {\n'
            '    "tactics": ["TA0040 Impact (for DoS) OR TA0001 Initial Access (for brute force)"],\n'
            '    "techniques": ["T1498 Network Denial of Service (for DoS) OR T1110 Brute Force (for brute force) OR T1190 Exploit Public-Facing Application"]\n'
            '  },\n'
            '  "immediate_actions": [\n'
            '    {"action": "Enable rate limiting on ALB (strategic)", "command": "aws elbv2 modify-load-balancer-attributes --load-balancer-arn <arn> --attributes Key=routing.http.drop_invalid_header_fields.enabled,Value=true", "priority": "P1"},\n'
            '    {"action": "Scale up application instances (strategic)", "command": "aws autoscaling set-desired-capacity --auto-scaling-group-name <asg> --desired-capacity 5", "priority": "P1"},\n'
            '    {"action": "Block attacker IP 203.0.113.42 (tactical)", "command": "aws ec2 revoke-security-group-ingress --group-id sg-xxx --cidr 203.0.113.42/32", "priority": "P2"}\n'
            '  ]\n'
            "}\n"
        )
        
        return prompt

    def _extract_json_object(self, text: str) -> dict:
        """Extract a JSON object (not array) from text."""
        # Try direct parse
        try:
            return json.loads(text)
        except Exception:
            pass
        
        # Find { ... } block
        match = re.search(r'\{', text)
        if match:
            start = match.start()
            end = text.rfind('}') + 1
            if end > start:
                try:
                    return json.loads(text[start:end])
                except Exception:
                    # Try repair
                    repaired = self._safe_json_loads(f"[{text[start:end]}]")
                    if repaired and len(repaired) > 0:
                        return repaired[0] if isinstance(repaired[0], dict) else None
        return None

    # ================================================================
    # Deep Dive — ONE call per source, enriched with Global RCA
    # ================================================================

    def generate_deep_dive(self, deep_dive_context: dict) -> tuple:
        """
        Analyze a single log group in depth, enriched with Global RCA context.
        Returns (DeepDiveResult, usage_stats).
        """
        from models import DeepDiveResult
        
        if not self.is_available():
            return DeepDiveResult(log_group=deep_dive_context.get('log_group', '')), {
                "ai_enhancement_used": False, "error": "Bedrock not available"
            }
        
        prompt = self._build_deep_dive_prompt(deep_dive_context)
        
        try:
            response = self._call_bedrock(prompt)
            text = response.get('text', '')
            usage = response.get('usage', {})
            
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            cost = self._calculate_cost(total_tokens, input_tokens, output_tokens)
            
            log_group = deep_dive_context.get('log_group', '')
            print(f"[Deep Dive: {log_group}] Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost:.4f}")
            
            parsed = self._extract_json_object(text)
            
            if parsed:
                result = DeepDiveResult(
                    log_group=log_group,
                    component_summary=parsed.get('component_summary', ''),
                    specific_findings=parsed.get('specific_findings', []),
                    recommendations=parsed.get('recommendations', []),
                    component_metrics=deep_dive_context.get('component_metrics', {}),
                    anomalies=deep_dive_context.get('anomalies', []),
                    global_rca_reference=deep_dive_context.get('global_rca_summary', ''),
                    raw_ai_response=parsed,
                    tokens_used=total_tokens,
                    cost=cost,
                )
            else:
                result = DeepDiveResult(
                    log_group=log_group,
                    component_summary=text[:500],
                    raw_ai_response={'raw_text': text[:1000]},
                    tokens_used=total_tokens,
                    cost=cost,
                )
            
            stats = {
                "ai_enhancement_used": True,
                "bedrock_model_used": self.model_id,
                "total_tokens_used": total_tokens,
                "estimated_total_cost": cost,
                "api_calls_made": 1,
            }
            return result, stats
            
        except Exception as e:
            print(f"[Deep Dive] Error: {e}")
            return DeepDiveResult(log_group=deep_dive_context.get('log_group', '')), {
                "ai_enhancement_used": False, "error": str(e)
            }

    def _build_deep_dive_prompt(self, ctx: dict) -> str:
        """Build prompt for Deep Dive into a single log group."""
        import json as _json
        
        log_group = ctx.get('log_group', 'unknown')
        source_type = ctx.get('source_type', 'unknown')
        
        prompt = (
            f"You are an expert AWS engineer performing a DEEP DIVE analysis on: {log_group}\n"
            f"Source type: {source_type}\n\n"
        )
        
        # --- Global RCA context (so AI knows the big picture) ---
        if ctx.get('global_rca_summary'):
            prompt += (
                "# GLOBAL CONTEXT (from prior Root Cause Analysis)\n"
                f"{ctx['global_rca_summary']}\n\n"
                "Use this context to EXPLAIN findings in this component. "
                "You already know the attack story — now provide DEPTH, not breadth.\n\n"
            )
        
        # --- Component metrics ---
        metrics = ctx.get('component_metrics', {})
        prompt += (
            "# COMPONENT METRICS\n"
            f"Total entries: {metrics.get('total_entries', 0)}\n"
            f"Error count: {metrics.get('error_count', 0)} ({metrics.get('error_rate', '0%')})\n"
            f"Severity distribution: {_json.dumps(metrics.get('severity_distribution', {}))}\n\n"
        )
        
        # --- Anomalies ---
        if ctx.get('anomalies'):
            prompt += "# DETECTED ANOMALIES\n"
            for i, anom in enumerate(ctx['anomalies'][:10], 1):
                sec_flag = " [SECURITY]" if anom.get('is_security_relevant') else ""
                prompt += (
                    f"{i}. {anom.get('pattern', '?')} "
                    f"(count: {anom.get('count', 0)}, anomaly: {anom.get('anomaly_score', 0)}){sec_flag}\n"
                )
            prompt += "\n"
        
        # --- Top IPs ---
        if ctx.get('top_ips'):
            prompt += "# TOP IP ADDRESSES\n"
            for ip_info in ctx['top_ips'][:5]:
                prompt += f"  {ip_info['ip']} - {ip_info['count']} occurrences\n"
            prompt += "\n"
        
        # --- Raw samples ---
        if ctx.get('raw_samples'):
            prompt += "# RAW LOG SAMPLES (Most relevant)\n"
            for i, sample in enumerate(ctx['raw_samples'][:8], 1):
                prompt += f"{i}. {sample}\n"
            prompt += "\n"
        
        # --- Output format ---
        prompt += (
            "# YOUR TASK\n"
            "Provide a DEEP analysis of this specific component.\n"
            "Use the Global Context to explain HOW this component fits into the larger incident.\n\n"
            "# RULES\n"
            "- Use ONLY data from the logs/metrics above\n"
            "- Reference the Global RCA context to connect findings\n"
            "- Provide specific, actionable recommendations\n\n"
            "# OUTPUT FORMAT (Return ONLY valid JSON, no markdown)\n"
            "{\n"
            '  "component_summary": "2-3 sentence summary of this component\'s role in the incident",\n'
            '  "specific_findings": [\n'
            '    {"finding": "description", "severity": "High", "evidence": "log reference", "anomaly_score": 0.9}\n'
            '  ],\n'
            '  "recommendations": [\n'
            '    "Specific actionable recommendation with command if applicable"\n'
            '  ]\n'
            "}\n"
        )
        
        return prompt
