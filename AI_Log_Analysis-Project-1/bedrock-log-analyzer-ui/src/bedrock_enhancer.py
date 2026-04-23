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
        
        # Enhanced analysis instructions
        prompt += (
            "# YOUR TASK: COMPREHENSIVE SECURITY ANALYSIS\n\n"
            "Analyze each issue using the MITRE ATT&CK framework and provide:\n\n"
            "1. **THREAT CLASSIFICATION**\n"
            "   - Attack technique (e.g., T1110 Brute Force, T1078 Valid Accounts)\n"
            "   - Threat actor profile (script kiddie, APT, insider)\n"
            "   - Attack stage (reconnaissance, initial access, persistence, etc.)\n\n"
            "2. **EVIDENCE-BASED ANALYSIS**\n"
            "   - Quote EXACT log entries that prove the attack\n"
            "   - Identify attack timeline (first seen, peak activity, last seen)\n"
            "   - Calculate attack metrics (attempts/minute, success rate)\n\n"
            "3. **IMPACT ASSESSMENT**\n"
            "   - Severity: Critical/High/Medium/Low with justification\n"
            "   - Blast radius: Which systems/data are at risk\n"
            "   - Business impact: Downtime, data loss, compliance violation\n\n"
            "4. **ROOT CAUSE ANALYSIS**\n"
            "   - Primary vulnerability exploited\n"
            "   - Why existing controls failed\n"
            "   - Alternative attack vectors ruled out\n\n"
            "5. **IMMEDIATE RESPONSE**\n"
            "   - Containment: Block attacker IP/user NOW\n"
            "   - Verification: Command to confirm attack stopped\n"
            "   - Evidence preservation: Logs to save for forensics\n\n"
            "6. **REMEDIATION STEPS**\n"
            "   - Short-term fixes (< 1 hour)\n"
            "   - Medium-term hardening (< 1 day)\n"
            "   - Long-term prevention (< 1 week)\n\n"
            "7. **PREVENTION STRATEGY**\n"
            "   - AWS security controls to enable (GuardDuty, WAF, etc.)\n"
            "   - Configuration changes (Security Groups, IAM policies)\n"
            "   - Monitoring improvements (CloudWatch Alarms, SNS alerts)\n\n"
        )
        
        # Critical rules
        prompt += (
            "# CRITICAL RULES\n"
            "✓ Use ACTUAL values from logs (IPs, usernames, timestamps)\n"
            "✓ Provide EXECUTABLE commands (not placeholders)\n"
            "✓ Reference SPECIFIC log entries as evidence\n"
            "✓ Calculate METRICS from the data (frequency, duration)\n"
            "✓ Explain WHY this is an attack (not just what happened)\n"
            "✗ NO generic advice without evidence\n"
            "✗ NO placeholder values like <instance-id>\n"
            "✗ NO assumptions not supported by logs\n\n"
        )
        
        # JSON schema
        prompt += (
            "# OUTPUT FORMAT\n"
            "Return ONLY a valid JSON array (no markdown, no explanation):\n\n"
            "[\n"
            "  {\n"
            '    "problem": "exact original problem title",\n'
            '    "attack_classification": {\n'
            '      "mitre_technique": "T1110.001 - Password Guessing",\n'
            '      "threat_actor_profile": "Automated bot / Script kiddie / APT",\n'
            '      "attack_stage": "Initial Access / Persistence / Privilege Escalation"\n'
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
            '    "action_plan": {\n'
            '      "immediate_containment": "Block IP 203.0.113.42 in Security Group sg-abc123",\n'
            '      "next_best_command": "aws ec2 revoke-security-group-ingress --group-id sg-abc123 --protocol tcp --port 22 --cidr 203.0.113.42/32",\n'
            '      "verification_commands": [\n'
            '        "aws logs tail /aws/ec2/applogs --since 5m | grep 203.0.113.42",\n'
            '        "aws ec2 describe-security-groups --group-ids sg-abc123"\n'
            '      ],\n'
            '      "fix_steps": [\n'
            '        "1. Verify attacker IP is blocked (run verification commands)",\n'
            '        "2. Review all SSH access logs for successful logins",\n'
            '        "3. Rotate SSH keys if any successful access detected",\n'
            '        "4. Enable fail2ban on all SSH-accessible instances"\n'
            '      ],\n'
            '      "prevention": {\n'
            '        "aws_services": ["Enable AWS GuardDuty", "Configure VPC Flow Logs alerts"],\n'
            '        "configuration": ["Disable password auth, use SSH keys only", "Implement rate limiting"],\n'
            '        "monitoring": ["CloudWatch Alarm for >10 failed SSH in 5min", "SNS notification to security team"]\n'
            '      }\n'
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
                        "max_tokens": 4096,
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
                            "maxTokens": 4096,
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
                    wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
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
