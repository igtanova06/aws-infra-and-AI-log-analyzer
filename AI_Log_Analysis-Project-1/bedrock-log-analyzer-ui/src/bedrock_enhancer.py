"""
Bedrock enhancer - Enhance solutions using AWS Bedrock
"""
import boto3
import json
from typing import List, Tuple, Dict
from models import Solution


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
        max_batch_size: int = 5
    ) -> Tuple[List[Solution], Dict]:
        """
        Enhance solutions using AWS Bedrock
        
        Args:
            solutions: List of basic solutions
            log_examples: Sample log entries for context
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
                enhanced_batch, tokens, cost = self._enhance_batch(batch, log_examples)
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
        log_examples: List[str] = None
    ) -> Tuple[List[Solution], int, float]:
        """Enhance a batch of solutions"""
        
        # Build prompt
        prompt = self._build_prompt(solutions, log_examples)
        
        # Call Bedrock API
        response = self._call_bedrock(prompt)
        
        # Parse response
        enhanced_solutions = self._parse_response(solutions, response)
        
        # Calculate tokens and cost
        tokens = response.get('usage', {}).get('total_tokens', 0)
        cost = self._calculate_cost(tokens)
        
        return enhanced_solutions, tokens, cost
    
    def _build_prompt(self, solutions: List[Solution], log_examples: List[str] = None) -> str:
        """Build prompt for Bedrock"""
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
    
    def _call_bedrock(self, prompt: str) -> dict:
        """Call Bedrock API"""
        # Prepare request body based on model
        if "claude" in self.model_id.lower():
            # Claude format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
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
                    "maxTokens": 2000,
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
        """Parse Bedrock response and create enhanced solutions"""
        text = response['text']
        
        try:
            # Try to extract JSON from response
            json_start = text.find('[')
            json_end = text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = text[json_start:json_end]
                enhanced_data = json.loads(json_text)
                
                enhanced_solutions = []
                for i, solution in enumerate(original_solutions):
                    if i < len(enhanced_data):
                        enhanced_text = enhanced_data[i].get('enhanced_solution', solution.solution)
                    else:
                        enhanced_text = solution.solution
                    
                    enhanced_solution = Solution(
                        problem=solution.problem,
                        solution=enhanced_text,
                        issue_type=solution.issue_type,
                        affected_components=solution.affected_components,
                        ai_enhanced=True,
                        tokens_used=response.get('usage', {}).get('total_tokens', 0) // len(original_solutions),
                        estimated_cost=self._calculate_cost(response.get('usage', {}).get('total_tokens', 0)) / len(original_solutions)
                    )
                    enhanced_solutions.append(enhanced_solution)
                
                return enhanced_solutions
            else:
                # If no JSON found, use original solutions
                return original_solutions
        
        except Exception as e:
            print(f"Error parsing Bedrock response: {e}")
            return original_solutions
    
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
