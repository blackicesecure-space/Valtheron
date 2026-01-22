"""
Code Analyzer Tool Implementation.
Analyzes code for complexity, security issues, and performance concerns.
"""
import ast
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ToolStatus(Enum):
    """Execution status for tool operations."""
    SUCCESS = "success"
    ERROR = "error"
    INVALID_INPUT = "invalid_input"


@dataclass
class ToolResult:
    """Result container for tool execution."""
    status: ToolStatus
    data: Optional[Any] = None
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == ToolStatus.SUCCESS


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    severity: str
    category: str
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "line": self.line,
            "suggestion": self.suggestion
        }


class ComplexityAnalyzer:
    """Analyzes code complexity metrics."""

    def __init__(self, code: str, language: str):
        self.code = code
        self.language = language
        self.lines = code.split('\n')

    def calculate_cyclomatic_complexity(self) -> int:
        """Calculate cyclomatic complexity for Python code."""
        if self.language != "python":
            return self._estimate_complexity()

        try:
            tree = ast.parse(self.code)
            complexity = 1

            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            return complexity
        except SyntaxError:
            return self._estimate_complexity()

    def _estimate_complexity(self) -> int:
        """Estimate complexity for non-Python languages."""
        patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\bcatch\b', r'\bexcept\b', r'\bcase\b', r'\b\?\s*:', r'\&\&', r'\|\|'
        ]
        complexity = 1
        for pattern in patterns:
            complexity += len(re.findall(pattern, self.code))
        return complexity

    def calculate_loc_metrics(self) -> Dict[str, int]:
        """Calculate lines of code metrics."""
        total_lines = len(self.lines)
        blank_lines = sum(1 for line in self.lines if not line.strip())
        comment_lines = sum(1 for line in self.lines if line.strip().startswith(('#', '//', '/*', '*')))
        code_lines = total_lines - blank_lines - comment_lines

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "comment_ratio": round(comment_lines / max(code_lines, 1) * 100, 2)
        }

    def find_long_functions(self, threshold: int = 50) -> List[CodeIssue]:
        """Find functions that exceed the line threshold."""
        issues = []
        if self.language != "python":
            return issues

        try:
            tree = ast.parse(self.code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > threshold:
                            issues.append(CodeIssue(
                                severity="medium",
                                category="complexity",
                                message=f"Function '{node.name}' is {func_lines} lines (threshold: {threshold})",
                                line=node.lineno,
                                suggestion="Consider breaking this function into smaller, focused functions"
                            ))
        except SyntaxError:
            pass

        return issues


class SecurityAnalyzer:
    """Analyzes code for security vulnerabilities."""

    SECURITY_PATTERNS = {
        "python": [
            (r'eval\s*\(', "high", "Use of eval() can execute arbitrary code", "Use ast.literal_eval() for safe evaluation"),
            (r'exec\s*\(', "high", "Use of exec() can execute arbitrary code", "Avoid exec() or use restricted execution"),
            (r'__import__\s*\(', "medium", "Dynamic imports can be a security risk", "Use explicit imports"),
            (r'pickle\.loads?\s*\(', "high", "Pickle can execute arbitrary code during deserialization", "Use JSON or other safe formats"),
            (r'subprocess\..*shell\s*=\s*True', "high", "Shell=True can lead to command injection", "Use shell=False with explicit arguments"),
            (r'os\.system\s*\(', "high", "os.system() is vulnerable to command injection", "Use subprocess with shell=False"),
            (r'password\s*=\s*["\'][^"\']+["\']', "critical", "Hardcoded password detected", "Use environment variables or secure vaults"),
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "critical", "Hardcoded API key detected", "Use environment variables"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "critical", "Hardcoded secret detected", "Use environment variables or secure vaults"),
        ],
        "javascript": [
            (r'eval\s*\(', "high", "Use of eval() can execute arbitrary code", "Avoid eval() entirely"),
            (r'innerHTML\s*=', "medium", "innerHTML can lead to XSS", "Use textContent or sanitize input"),
            (r'document\.write\s*\(', "medium", "document.write can overwrite page content", "Use DOM manipulation methods"),
            (r'password\s*[:=]\s*["\'][^"\']+["\']', "critical", "Hardcoded password detected", "Use environment variables"),
        ]
    }

    def __init__(self, code: str, language: str):
        self.code = code
        self.language = language
        self.lines = code.split('\n')

    def analyze(self) -> List[CodeIssue]:
        """Run security analysis on the code."""
        issues = []
        patterns = self.SECURITY_PATTERNS.get(self.language, [])

        for pattern, severity, message, suggestion in patterns:
            for i, line in enumerate(self.lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=severity,
                        category="security",
                        message=message,
                        line=i,
                        suggestion=suggestion
                    ))

        return issues


class PerformanceAnalyzer:
    """Analyzes code for performance concerns."""

    def __init__(self, code: str, language: str):
        self.code = code
        self.language = language
        self.lines = code.split('\n')

    def analyze(self) -> List[CodeIssue]:
        """Run performance analysis on the code."""
        issues = []

        if self.language == "python":
            issues.extend(self._analyze_python())
        elif self.language in ["javascript", "typescript"]:
            issues.extend(self._analyze_javascript())

        return issues

    def _analyze_python(self) -> List[CodeIssue]:
        """Analyze Python-specific performance issues."""
        issues = []

        patterns = [
            (r'for\s+.*\s+in\s+range\(len\(', "Using range(len()) is often unnecessary", "Iterate directly or use enumerate()"),
            (r'import\s+\*', "Wildcard imports affect performance and readability", "Import specific names"),
            (r'global\s+\w+', "Global variables can impact performance", "Consider passing as parameters"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, message, suggestion in patterns:
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        severity="low",
                        category="performance",
                        message=message,
                        line=i,
                        suggestion=suggestion
                    ))

        return issues

    def _analyze_javascript(self) -> List[CodeIssue]:
        """Analyze JavaScript-specific performance issues."""
        issues = []

        patterns = [
            (r'\.innerHTML\s*\+=', "innerHTML concatenation is slow", "Build string then assign once"),
            (r'JSON\.parse\(JSON\.stringify', "Deep clone via JSON is slow", "Use structuredClone() or a library"),
        ]

        for i, line in enumerate(self.lines, 1):
            for pattern, message, suggestion in patterns:
                if re.search(pattern, line):
                    issues.append(CodeIssue(
                        severity="low",
                        category="performance",
                        message=message,
                        line=i,
                        suggestion=suggestion
                    ))

        return issues


class CodeAnalyzerTool:
    """
    Analyzes code for complexity, security, and performance issues.
    """

    def __call__(self, file_path: str = None, code: str = None, 
                 language: str = "python", analysis_type: str = "all") -> ToolResult:
        """Execute the analysis."""
        
        # Get code from file or direct input
        if file_path:
            path = Path(file_path)
            if not path.exists():
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"File not found: {file_path}"
                )
            try:
                code = path.read_text(encoding='utf-8')
            except Exception as e:
                return ToolResult(
                    status=ToolStatus.ERROR,
                    error=f"Error reading file: {e}"
                )
        elif not code:
            return ToolResult(
                status=ToolStatus.INVALID_INPUT,
                error="Either file_path or code must be provided"
            )

        # Run analysis
        results = {
            "file": file_path,
            "language": language,
            "analysis_type": analysis_type,
            "issues": [],
            "metrics": {},
            "recommendations": []
        }

        all_issues = []

        # Complexity analysis
        if analysis_type in ["complexity", "all"]:
            complexity_analyzer = ComplexityAnalyzer(code, language)
            results["metrics"]["cyclomatic_complexity"] = complexity_analyzer.calculate_cyclomatic_complexity()
            results["metrics"]["loc"] = complexity_analyzer.calculate_loc_metrics()
            all_issues.extend(complexity_analyzer.find_long_functions())

            cc = results["metrics"]["cyclomatic_complexity"]
            if cc > 20:
                all_issues.append(CodeIssue(
                    severity="high",
                    category="complexity",
                    message=f"Very high cyclomatic complexity: {cc}",
                    suggestion="Consider refactoring to reduce complexity below 20"
                ))
            elif cc > 10:
                all_issues.append(CodeIssue(
                    severity="medium",
                    category="complexity",
                    message=f"High cyclomatic complexity: {cc}",
                    suggestion="Consider refactoring to reduce complexity"
                ))

        # Security analysis
        if analysis_type in ["security", "all"]:
            security_analyzer = SecurityAnalyzer(code, language)
            all_issues.extend(security_analyzer.analyze())

        # Performance analysis
        if analysis_type in ["performance", "all"]:
            performance_analyzer = PerformanceAnalyzer(code, language)
            all_issues.extend(performance_analyzer.analyze())

        # Convert issues to dict and calculate score
        results["issues"] = [issue.to_dict() for issue in all_issues]

        # Calculate overall score (0-100)
        severity_weights = {"critical": 25, "high": 15, "medium": 5, "low": 2}
        penalty = sum(severity_weights.get(issue.severity, 0) for issue in all_issues)
        results["metrics"]["quality_score"] = max(0, 100 - penalty)

        # Generate recommendations
        severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in all_issues:
            severity_count[issue.severity] = severity_count.get(issue.severity, 0) + 1

        if severity_count["critical"] > 0:
            results["recommendations"].append(
                f"Address {severity_count['critical']} critical issue(s) immediately"
            )
        if severity_count["high"] > 0:
            results["recommendations"].append(
                f"Review and fix {severity_count['high']} high-severity issue(s)"
            )
        if results["metrics"].get("cyclomatic_complexity", 0) > 15:
            results["recommendations"].append(
                "Consider breaking down complex functions"
            )
        if results["metrics"].get("loc", {}).get("comment_ratio", 0) < 10:
            results["recommendations"].append(
                "Consider adding more documentation comments"
            )

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=results
        )
