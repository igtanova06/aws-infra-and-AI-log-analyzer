"""
Rule-based detector - Detect issues using predefined rules
"""
from typing import List
from models import AnalysisData, Solution, IssueType


class RuleBasedDetector:
    """Detect issues using predefined rules"""
    
    def __init__(self):
        self.connection_keywords = ['connection', 'timeout', 'connect', 'refused', 'unreachable']
        self.permission_keywords = ['permission', 'access', 'denied', 'forbidden', 'unauthorized']
        self.resource_keywords = ['memory', 'cpu', 'capacity', 'full', 'disk', 'space']
        self.database_keywords = ['database', 'db', 'sql', 'query', 'deadlock', 'transaction']
        self.security_keywords = ['security', 'auth', 'authentication', 'token', 'credential']
    
    def detect_issues(self, analysis: AnalysisData) -> List[dict]:
        """Detect issues from analysis data"""
        issues = []
        
        # Check for connection issues
        if self._has_pattern_with_keywords(analysis, self.connection_keywords):
            issues.append({
                'type': IssueType.CONNECTION,
                'problem': 'Connection issues detected',
                'components': self._get_affected_components(analysis, self.connection_keywords)
            })
        
        # Check for permission issues
        if self._has_pattern_with_keywords(analysis, self.permission_keywords):
            issues.append({
                'type': IssueType.PERMISSION,
                'problem': 'Permission issues detected',
                'components': self._get_affected_components(analysis, self.permission_keywords)
            })
        
        # Check for resource issues
        if self._has_pattern_with_keywords(analysis, self.resource_keywords):
            issues.append({
                'type': IssueType.RESOURCE,
                'problem': 'Resource constraint issues detected',
                'components': self._get_affected_components(analysis, self.resource_keywords)
            })
        
        # Check for database issues
        if self._has_pattern_with_keywords(analysis, self.database_keywords):
            issues.append({
                'type': IssueType.DATABASE,
                'problem': 'Database issues detected',
                'components': self._get_affected_components(analysis, self.database_keywords)
            })
        
        # Check for security issues
        if self._has_pattern_with_keywords(analysis, self.security_keywords):
            issues.append({
                'type': IssueType.SECURITY,
                'problem': 'Security issues detected',
                'components': self._get_affected_components(analysis, self.security_keywords)
            })
        
        # General issue if nothing specific found
        if not issues and analysis.total_entries > 0:
            severity_dist = analysis.severity_distribution
            error_count = severity_dist.get('ERROR', 0) + severity_dist.get('CRITICAL', 0) + severity_dist.get('FATAL', 0)
            
            if error_count > 0:
                components = analysis.components
                most_common_component = max(components.items(), key=lambda x: x[1])[0] if components else 'unknown'
                
                issues.append({
                    'type': IssueType.GENERAL,
                    'problem': f'Multiple errors in {most_common_component} component',
                    'components': [most_common_component]
                })
        
        return issues
    
    def generate_basic_solutions(self, issues: List[dict]) -> List[Solution]:
        """Generate basic solutions for detected issues"""
        solutions = []
        
        for issue in issues:
            issue_type = issue['type']
            problem = issue['problem']
            components = issue['components']
            
            if issue_type == IssueType.CONNECTION:
                solution_text = (
                    "Check network connectivity between services and verify that all dependent services are running. "
                    "Look for firewall or DNS issues."
                )
            elif issue_type == IssueType.PERMISSION:
                solution_text = (
                    "Verify file and resource permissions. "
                    "Check that service accounts have the necessary access rights."
                )
            elif issue_type == IssueType.RESOURCE:
                solution_text = (
                    "Check system resources (memory, CPU, disk space). "
                    "Consider scaling up infrastructure or optimizing resource usage."
                )
            elif issue_type == IssueType.DATABASE:
                solution_text = (
                    "Check database connectivity, query performance, and database logs. "
                    "Verify that database indices are properly set up."
                )
            elif issue_type == IssueType.SECURITY:
                solution_text = (
                    "Review authentication and authorization configurations. "
                    "Check for expired credentials or tokens."
                )
            else:
                solution_text = (
                    f"Review the {components[0] if components else 'affected'} component logs in detail "
                    "and check recent code changes or configuration updates."
                )
            
            solutions.append(Solution(
                problem=problem,
                solution=solution_text,
                issue_type=issue_type,
                affected_components=components,
                ai_enhanced=False
            ))
        
        return solutions
    
    def _has_pattern_with_keywords(self, analysis: AnalysisData, keywords: List[str]) -> bool:
        """Check if any error pattern contains the keywords"""
        for pattern in analysis.error_patterns:
            pattern_lower = pattern.pattern.lower()
            if any(keyword in pattern_lower for keyword in keywords):
                return True
        return False
    
    def _get_affected_components(self, analysis: AnalysisData, keywords: List[str]) -> List[str]:
        """Get components affected by issues with specific keywords"""
        components = set()
        for pattern in analysis.error_patterns:
            pattern_lower = pattern.pattern.lower()
            if any(keyword in pattern_lower for keyword in keywords):
                components.add(pattern.component)
        return list(components)
