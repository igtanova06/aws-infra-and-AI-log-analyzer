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
        """Enhance a batch of solutions"""
        
        # Build prompt — prefer structured AIContext over flat examples
        prompt = self._build_prompt(solutions, log_examples=log_examples, ai_context=ai_context)
        
        # Call Bedrock API
        response = self._call_bedrock(prompt)
        
        # Parse response
        enhanced_solutions = self._parse_response(solutions, response)
        
        # Calculate tokens and cost
        tokens = response.get('usage', {}).get('total_tokens', 0)
        cost = self._calculate_cost(tokens)
        
        return enhanced_solutions, tokens, cost
    
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
        """
        # Source type label for the AI
        source_labels = {
            'vpc_flow': 'AWS VPC Flow Logs (network traffic records)',
            'cloudtrail': 'AWS CloudTrail (API audit logs)',
            'app': 'Application Logs (server/service logs)',
        }
        source_label = source_labels.get(ctx.source_type, 'Log data')
        
        prompt = (
            "You are an expert AWS security and log analysis engineer.\n"
            f"You are analyzing: {source_label}\n"
            f"Log group: {ctx.log_group_name}\n"
            f"Total logs retrieved: {ctx.total_logs_pulled} | "
            f"High-relevance logs: {ctx.total_logs_after_scoring}\n\n"
        )
        
        # Severity summary
        if ctx.severity_summary:
            prompt += "Severity distribution:\n"
            for sev, count in sorted(ctx.severity_summary.items(), key=lambda x: x[1], reverse=True):
                prompt += f"  {sev}: {count}\n"
            prompt += "\n"
        
        # Top error patterns
        if ctx.top_patterns:
            prompt += "Top error patterns (most frequent):\n"
            for i, p in enumerate(ctx.top_patterns, 1):
                prompt += f"  {i}. [{p['component']}] {p['pattern']} (count: {p['count']})\n"
            prompt += "\n"
        
        # Suspicious actors
        if ctx.suspicious_ips:
            prompt += "Suspicious IP addresses:\n"
            for item in ctx.suspicious_ips:
                prompt += f"  - {item['ip']} (seen {item['count']} times)\n"
            prompt += "\n"
        
        if ctx.suspicious_users:
            prompt += "Suspicious users/identities:\n"
            for item in ctx.suspicious_users:
                prompt += f"  - {item['user']} (seen {item['count']} times)\n"
            prompt += "\n"
        
        if ctx.suspicious_apis:
            prompt += "API actions observed:\n"
            for item in ctx.suspicious_apis:
                prompt += f"  - {item['api']} (count: {item['count']})\n"
            prompt += "\n"
        
        # Within-source hints
        if ctx.within_source_hints:
            prompt += "Correlation hints (within this log source):\n"
            for hint in ctx.within_source_hints:
                prompt += f"  - {hint}\n"
            prompt += "\n"
        
        # Representative samples
        if ctx.representative_samples:
            prompt += "Representative log samples (highest relevance):\n"
            for i, sample in enumerate(ctx.representative_samples, 1):
                prompt += f"  {i}. {sample}\n"
            prompt += "\n"
        
        # Detected issues to enhance
        prompt += "Detected issues to analyze:\n\n"
        for i, solution in enumerate(solutions, 1):
            prompt += f"{i}. Problem: {solution.problem}\n"
            prompt += f"   Current basic solution: {solution.solution}\n"
            prompt += f"   Affected components: {', '.join(solution.affected_components)}\n\n"
        
        # Demo specific context
        demo_mode_hint = ""
        if ctx.source_type == 'vpc_flow':
            demo_mode_hint = "Focus on network attacks: Port scanning, brute force attempts, unauthorized lateral movement."
        elif ctx.source_type == 'cloudtrail':
            demo_mode_hint = "Focus on IAM misuse: Privilege escalation, unauthorized resource deletion, stolen credentials."
        else:
            demo_mode_hint = "Focus on application failures: Resource exhaustion, crashes, failed authentications (e.g. JWT errors)."

        prompt += (
            "Based ONLY on the actual log data, patterns, IPs, users, APIs, and error messages provided above, "
            "write a COMPREHENSIVE and SPECIFIC analysis for each issue.\n\n"
            "Rules:\n"
            "- Do NOT give generic advice. Every recommendation must reference actual values from the data above.\n"
            "- If you saw IP 203.15.7.12 in the data, use that IP in your commands — not a placeholder.\n"
            "- If you saw a specific user ARN, use that ARN in your commands.\n"
            "- Adapt the commands to what the logs actually show — not what you assume the environment looks like.\n"
            "- SEPARATE factual evidence from your own inference explicitly.\n"
            f"- Scenario Strategy: {demo_mode_hint}\n\n"
            "IMPORTANT: Return ONLY a raw JSON array. No markdown code blocks, no conversational text. Output MUST strictly match this JSON schema:\n"
            "[\n"
            "  {\n"
            '    "problem": "exact original problem title",\n'
            '    "summary": {\n'
            '      "severity": "High / Medium / Low",\n'
            '      "impact": "Brief description of components and business impact"\n'
            '    },\n'
            '    "investigation": {\n'
            '      "evidence_from_logs": ["Specific log entry 1", "Specific log entry 2"],\n'
            '      "inference": ["Deduction 1", "Deduction 2"],\n'
            '      "why_not_other_causes": "Explanation of why alternatives were ruled out",\n'
            '      "confidence": "Confirmed by logs | Strongly suggested | Possible but unconfirmed"\n'
            '    },\n'
            '    "action_plan": {\n'
            '      "immediate_containment": "One key action to block damage immediately",\n'
            '      "next_best_command": "The exact CLI command to run right now to verify",\n'
            '      "verification_commands": ["cmd1", "cmd2"],\n'
            '      "fix_steps": ["step 1", "step 2"],\n'
            '      "prevention": "Architectural or policy change to prevent recurrence"\n'
            '    }\n'
            "  }\n"
            "]\n"
        )
        
        return prompt
    
    def _call_bedrock(self, prompt: str) -> dict:
        """Call Bedrock API"""
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
                    "temperature": 0.3
                }
            }
        
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        
        # Extract text based on model format
        if "claude" in self.model_id.lower():
            text = response_body['content'][0]['text']
            usage = {
                'total_tokens': response_body['usage']['input_tokens'] + response_body['usage']['output_tokens']
            }
        else:
            # Nova format
            text = response_body['output']['message']['content'][0]['text']
            usage = {
                'total_tokens': response_body['usage']['inputTokens'] + response_body['usage']['outputTokens']
            }
        
        return {
            'text': text,
            'usage': usage
        }
    
    def _parse_response(self, original_solutions: List[Solution], response: dict) -> List[Solution]:
        """Parse Bedrock response and create enhanced solutions.
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
                            # Store the structured dict nicely, and keep a backup string version for legacy
                            if isinstance(raw_val, dict) and "summary" in raw_val:
                                enhanced_text = "See Details"
                                structured_data = raw_val
                            else:
                                enhanced_text = str(raw_val.get('enhanced_solution', solution.solution))
                                structured_data = None
                        else:
                            enhanced_text = solution.solution
                            structured_data = None
                        
                        enhanced_solution = Solution(
                            problem=solution.problem,
                            solution=enhanced_text,
                            issue_type=solution.issue_type,
                            affected_components=solution.affected_components,
                            ai_enhanced=True,
                            tokens_used=response.get('usage', {}).get('total_tokens', 0) // len(original_solutions),
                            estimated_cost=self._calculate_cost(response.get('usage', {}).get('total_tokens', 0)) / len(original_solutions),
                            structured_solution=structured_data
                        )
                        enhanced_solutions.append(enhanced_solution)
                    
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

    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate estimated cost based on tokens"""
        # Nova Micro pricing: $0.035 per 1M input tokens, $0.14 per 1M output tokens
        # Assume 50/50 split for simplicity
        if "nova-micro" in self.model_id.lower():
            input_cost_per_1m = 0.035
            output_cost_per_1m = 0.14
            avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
        # Claude Haiku pricing: $0.25 per 1M input tokens, $1.25 per 1M output tokens
        elif "haiku" in self.model_id.lower():
            input_cost_per_1m = 0.25
            output_cost_per_1m = 1.25
            avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
        # Claude Sonnet pricing: $3 per 1M input tokens, $15 per 1M output tokens
        elif "sonnet" in self.model_id.lower():
            input_cost_per_1m = 3.0
            output_cost_per_1m = 15.0
            avg_cost_per_1m = (input_cost_per_1m + output_cost_per_1m) / 2
        else:
            # Default to Nova Micro pricing
            avg_cost_per_1m = 0.0875
        
        return (tokens / 1_000_000) * avg_cost_per_1m
