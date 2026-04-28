"""
Rule-based detector - Detect issues using predefined rules
Enhanced with context-aware detection and severity scoring
"""
from typing import List
from models import AnalysisData, Solution, IssueType


class RuleBasedDetector:
    """Detect issues using predefined rules with context awareness"""
    
    def __init__(self):
        # Positive keywords (true issues)
        self.connection_keywords = {
            'positive': ['timeout', 'refused', 'unreachable', 'failed to connect', 'connection reset'],
            'negative': ['connected', 'successful', 'established', 'connection ok']
        }
        self.permission_keywords = {
            'positive': ['denied', 'forbidden', 'unauthorized', 'access denied', 'permission denied'],
            'negative': ['granted', 'authorized', 'allowed', 'permission ok']
        }
        self.resource_keywords = {
            'positive': ['out of memory', 'cpu limit', 'disk full', 'capacity exceeded', 'quota exceeded'],
            'negative': ['available', 'freed', 'released']
        }
        self.database_keywords = {
            'positive': ['deadlock', 'lock timeout', 'connection pool exhausted', 'too many connections', 'query timeout'],
            'negative': ['query ok', 'connected', 'transaction committed']
        }
        self.security_keywords = {
            'positive': ['injection', 'brute force', 'authentication failed', 'invalid token', 'exploit'],
            'negative': ['authenticated', 'authorized', 'token valid']
        }
    
    def detect_issues(self, analysis: AnalysisData) -> List[dict]:
        """
        Detect issues from analysis data with context awareness.
        Returns empty list if no significant issues found (normal operations).
        """
        issues = []
        
        # Check for connection issues
        conn_result = self._detect_with_context(analysis, self.connection_keywords, IssueType.CONNECTION)
        if conn_result:
            issues.append(conn_result)
        
        # Check for permission issues
        perm_result = self._detect_with_context(analysis, self.permission_keywords, IssueType.PERMISSION)
        if perm_result:
            issues.append(perm_result)
        
        # Check for resource issues
        res_result = self._detect_with_context(analysis, self.resource_keywords, IssueType.RESOURCE)
        if res_result:
            issues.append(res_result)
        
        # Check for database issues
        db_result = self._detect_with_context(analysis, self.database_keywords, IssueType.DATABASE)
        if db_result:
            issues.append(db_result)
        
        # Check for security issues
        sec_result = self._detect_with_context(analysis, self.security_keywords, IssueType.SECURITY)
        if sec_result:
            issues.append(sec_result)
        
        # CRITICAL: Only flag general issues if error count is ABNORMALLY HIGH
        # Low error counts (<10) are normal operational noise
        if not issues and analysis.total_entries > 0:
            severity_dist = analysis.severity_distribution
            error_count = severity_dist.get('ERROR', 0) + severity_dist.get('CRITICAL', 0) + severity_dist.get('FATAL', 0)
            
            # THRESHOLD: Only flag if 10+ errors (not just 1-2 errors)
            if error_count >= 10:
                components = analysis.components
                most_common_component = max(components.items(), key=lambda x: x[1])[0] if components else 'unknown'
                
                # Calculate severity for general issues
                severity = self._calculate_severity(error_count)
                
                issues.append({
                    'type': IssueType.GENERAL,
                    'problem': f'Multiple errors in {most_common_component} component',
                    'components': [most_common_component],
                    'severity': severity,
                    'count': error_count
                })
            else:
                # Low error count = normal operations, not an issue
                print(f"[Rule Detector] {error_count} errors detected - below threshold (10), considered normal operations")
        
        return issues
    
    def _detect_with_context(self, analysis: AnalysisData, keywords: dict, issue_type: IssueType) -> dict:
        """
        Context-aware detection: check for positive keywords while excluding false positives.
        Returns issue dict or None.
        """
        positive_kw = keywords['positive']
        negative_kw = keywords['negative']
        
        matched_patterns = []
        total_count = 0
        affected_components = set()
        
        for pattern in analysis.error_patterns:
            pattern_lower = pattern.pattern.lower()
            
            # Check if pattern contains positive keywords
            has_positive = any(kw in pattern_lower for kw in positive_kw)
            
            # Check if pattern contains negative keywords (false positive)
            has_negative = any(kw in pattern_lower for kw in negative_kw)
            
            # Only count if positive match and no negative match
            if has_positive and not has_negative:
                matched_patterns.append(pattern)
                total_count += pattern.count
                affected_components.add(pattern.component)
        
        if not matched_patterns:
            return None
        
        # Calculate severity based on count
        severity = self._calculate_severity(total_count)
        
        # Build problem description
        issue_name = issue_type.value.replace('_', ' ').title()
        problem = f'{issue_name} detected ({total_count} occurrences)'
        
        return {
            'type': issue_type,
            'problem': problem,
            'components': list(affected_components),
            'severity': severity,
            'count': total_count,
            'patterns': matched_patterns[:3]  # Top 3 patterns for reference
        }
    
    def _calculate_severity(self, count: int) -> str:
        """Calculate severity level based on occurrence count"""
        if count >= 100:
            return 'CRITICAL'
        elif count >= 50:
            return 'HIGH'
        elif count >= 10:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_basic_solutions(self, issues: List[dict]) -> List[Solution]:
        """Generate basic solutions for detected issues with severity context"""
        solutions = []
        
        for issue in issues:
            issue_type = issue['type']
            problem = issue['problem']
            components = issue['components']
            severity = issue.get('severity', 'MEDIUM')
            count = issue.get('count', 0)
            
            # Add severity and count context to problem description
            problem_with_context = f"[{severity}] {problem}"
            
            if issue_type == IssueType.CONNECTION:
                solution_text = (
                    f"**Severity: {severity}** ({count} occurrences)\n\n"
                    "**Immediate Actions:**\n"
                    "1. Check network connectivity between services\n"
                    "2. Verify that all dependent services are running\n"
                    "3. Review firewall rules and security groups\n\n"
                    "**Investigation:**\n"
                    "- Check DNS resolution\n"
                    "- Verify service endpoints are correct\n"
                    "- Review recent network changes\n\n"
                    "**AWS Commands:**\n"
                    "```bash\n"
                    "# Check security group rules\n"
                    "aws ec2 describe-security-groups --group-ids <sg-id>\n"
                    "# Check VPC flow logs\n"
                    "aws logs filter-log-events --log-group-name /aws/vpc/flowlogs\n"
                    "```"
                )
            elif issue_type == IssueType.PERMISSION:
                solution_text = (
                    f"**Severity: {severity}** ({count} occurrences)\n\n"
                    "**Immediate Actions:**\n"
                    "1. Verify IAM role/user permissions\n"
                    "2. Check resource-based policies\n"
                    "3. Review recent permission changes in CloudTrail\n\n"
                    "**Investigation:**\n"
                    "- Identify the principal (user/role) being denied\n"
                    "- Check if MFA or IP restrictions apply\n"
                    "- Verify resource ARNs are correct\n\n"
                    "**AWS Commands:**\n"
                    "```bash\n"
                    "# Check IAM policy\n"
                    "aws iam get-role-policy --role-name <role> --policy-name <policy>\n"
                    "# Simulate policy\n"
                    "aws iam simulate-principal-policy --policy-source-arn <arn> --action-names <action>\n"
                    "```"
                )
            elif issue_type == IssueType.RESOURCE:
                solution_text = (
                    f"**Severity: {severity}** ({count} occurrences)\n\n"
                    "**Immediate Actions:**\n"
                    "1. Check system resources (memory, CPU, disk space)\n"
                    "2. Scale up infrastructure if needed\n"
                    "3. Identify resource-intensive processes\n\n"
                    "**Investigation:**\n"
                    "- Review CloudWatch metrics for resource utilization\n"
                    "- Check for memory leaks or runaway processes\n"
                    "- Analyze disk usage patterns\n\n"
                    "**AWS Commands:**\n"
                    "```bash\n"
                    "# Check EC2 metrics\n"
                    "aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization\n"
                    "# Check disk usage via SSM\n"
                    "aws ssm send-command --document-name AWS-RunShellScript --parameters 'commands=[\"df -h\"]'\n"
                    "```"
                )
            elif issue_type == IssueType.DATABASE:
                solution_text = (
                    f"**Severity: {severity}** ({count} occurrences)\n\n"
                    "**Immediate Actions:**\n"
                    "1. Check database connectivity and connection pool\n"
                    "2. Review slow query logs\n"
                    "3. Verify database indices are optimized\n\n"
                    "**Investigation:**\n"
                    "- Check for long-running queries or deadlocks\n"
                    "- Review connection pool settings\n"
                    "- Analyze query execution plans\n\n"
                    "**AWS Commands:**\n"
                    "```bash\n"
                    "# Check RDS metrics\n"
                    "aws cloudwatch get-metric-statistics --namespace AWS/RDS --metric-name DatabaseConnections\n"
                    "# Download slow query log\n"
                    "aws rds download-db-log-file-portion --db-instance-identifier <id> --log-file-name slowquery/mysql-slowquery.log\n"
                    "```"
                )
            elif issue_type == IssueType.SECURITY:
                solution_text = (
                    f"**Severity: {severity}** ({count} occurrences) 🚨\n\n"
                    "**URGENT - Immediate Actions:**\n"
                    "1. Block suspicious IPs in WAF/Security Groups\n"
                    "2. Review authentication logs for compromised accounts\n"
                    "3. Enable MFA if not already enabled\n\n"
                    "**Investigation:**\n"
                    "- Identify attack patterns (SQL injection, brute force, etc.)\n"
                    "- Check for successful authentication after failed attempts\n"
                    "- Review CloudTrail for unusual API activity\n\n"
                    "**AWS Commands:**\n"
                    "```bash\n"
                    "# Block IP in WAF\n"
                    "aws wafv2 update-ip-set --name BlockList --scope REGIONAL --addresses <ip>/32\n"
                    "# Check GuardDuty findings\n"
                    "aws guardduty list-findings --detector-id <id>\n"
                    "# Review CloudTrail for root activity\n"
                    "aws cloudtrail lookup-events --lookup-attributes AttributeKey=Username,AttributeValue=root\n"
                    "```"
                )
            else:
                solution_text = (
                    f"**Severity: {severity}** ({count} occurrences)\n\n"
                    f"Review the {components[0] if components else 'affected'} component logs in detail "
                    "and check recent code changes or configuration updates.\n\n"
                    "**Investigation Steps:**\n"
                    "1. Check recent deployments or configuration changes\n"
                    "2. Review application logs for stack traces\n"
                    "3. Compare with previous working state\n\n"
                    "**AWS Commands:**\n"
                    "```bash\n"
                    "# Get recent log events\n"
                    "aws logs tail /aws/ec2/app-tier/application --follow\n"
                    "```"
                )
            
            solutions.append(Solution(
                problem=problem_with_context,
                solution=solution_text,
                issue_type=issue_type,
                affected_components=components,
                ai_enhanced=False
            ))
        
        return solutions
