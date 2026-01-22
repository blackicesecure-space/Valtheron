"""
Code analysis tools for the agentic workspace.
Provides complexity analysis, security scanning, and code quality metrics.
"""
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .base import BaseTool, ToolParameter, ToolResult, register_tool


@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    parameters: int
    returns_count: int
    has_docstring: bool


@dataclass
class FileMetrics:
    """Metrics for a single file."""
    path: str
    language: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: int = 0
    imports: int = 0
    average_complexity: float = 0.0


class PythonAnalyzer:
    """Static analyzer for Python code."""
    
    @staticmethod
    def calculate_cyclomatic_complexity(node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity of an AST node.
        
        Complexity increases for each decision point:
        - if, elif, for, while, except, with, assert
        - boolean operators (and, or)
        - comprehensions
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += len(child.ifs)
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
        
        return complexity
    
    @staticmethod
    def calculate_cognitive_complexity(node: ast.AST, nesting: int = 0) -> int:
        """
        Calculate cognitive complexity (how hard code is to understand).
        
        Adds to complexity for:
        - Nesting depth
        - Breaking linear flow
        - Recursion
        """
        complexity = 0
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1 + nesting
                complexity += PythonAnalyzer.calculate_cognitive_complexity(child, nesting + 1)
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1 + nesting
                complexity += PythonAnalyzer.calculate_cognitive_complexity(child, nesting + 1)
            elif isinstance(child, ast.BoolOp):
                complexity += 1
            elif isinstance(child, (ast.Break, ast.Continue)):
                complexity += 1
            else:
                complexity += PythonAnalyzer.calculate_cognitive_complexity(child, nesting)
        
        return complexity
    
    @classmethod
    def analyze_function(cls, node: ast.FunctionDef, source_lines: List[str]) -> FunctionMetrics:
        """Analyze a single function."""
        line_start = node.lineno
        line_end = node.end_lineno or line_start
        
        # Count parameters
        args = node.args
        param_count = (
            len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs) +
            (1 if args.vararg else 0) + (1 if args.kwarg else 0)
        )
        
        # Count return statements
        returns = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
        
        # Check for docstring
        has_docstring = (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )
        
        # Lines of code (excluding blanks and comments)
        func_lines = source_lines[line_start - 1:line_end]
        loc = sum(1 for line in func_lines if line.strip() and not line.strip().startswith('#'))
        
        return FunctionMetrics(
            name=node.name,
            line_start=line_start,
            line_end=line_end,
            cyclomatic_complexity=cls.calculate_cyclomatic_complexity(node),
            cognitive_complexity=cls.calculate_cognitive_complexity(node),
            lines_of_code=loc,
            parameters=param_count,
            returns_count=returns,
            has_docstring=has_docstring
        )
    
    @classmethod
    def analyze_file(cls, content: str, file_path: str) -> FileMetrics:
        """Analyze a Python file."""
        lines = content.splitlines()
        
        # Count line types
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        code_lines = total_lines - blank_lines - comment_lines
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return FileMetrics(
                path=file_path,
                language="python",
                total_lines=total_lines,
                code_lines=code_lines,
                comment_lines=comment_lines,
                blank_lines=blank_lines
            )
        
        functions = []
        classes = 0
        imports = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip nested functions and methods (they're counted separately)
                functions.append(cls.analyze_function(node, lines))
            elif isinstance(node, ast.ClassDef):
                classes += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports += 1
        
        avg_complexity = (
            sum(f.cyclomatic_complexity for f in functions) / len(functions)
            if functions else 0
        )
        
        return FileMetrics(
            path=file_path,
            language="python",
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            functions=functions,
            classes=classes,
            imports=imports,
            average_complexity=round(avg_complexity, 2)
        )


class SecurityScanner:
    """Basic security scanner for code."""
    
    PATTERNS = {
        "hardcoded_secret": [
            (r'(?i)(password|passwd|pwd|secret|api_key|apikey|token|auth)\s*=\s*["\'][^"\']+["\']', "Possible hardcoded secret"),
            (r'(?i)(password|secret|key)\s*:\s*["\'][^"\']+["\']', "Possible hardcoded secret in dict/config"),
        ],
        "sql_injection": [
            (r'execute\s*\(\s*["\'].*%s', "Possible SQL injection via string formatting"),
            (r'execute\s*\(\s*f["\']', "Possible SQL injection via f-string"),
            (r'cursor\.execute\s*\([^,]+\+', "Possible SQL injection via concatenation"),
        ],
        "command_injection": [
            (r'os\.system\s*\(', "Use of os.system (prefer subprocess with shell=False)"),
            (r'subprocess.*shell\s*=\s*True', "subprocess with shell=True"),
            (r'eval\s*\(', "Use of eval() - potential code injection"),
            (r'exec\s*\(', "Use of exec() - potential code injection"),
        ],
        "path_traversal": [
            (r'open\s*\([^)]*\+', "Possible path traversal via concatenation"),
        ],
        "insecure_random": [
            (r'import\s+random(?!\s+#.*cryptographic)', "random module (not cryptographically secure)"),
        ],
        "debug_code": [
            (r'import\s+pdb', "Debug import (pdb)"),
            (r'breakpoint\s*\(', "Debug breakpoint"),
            (r'print\s*\([^)]*password', "Possible password in print statement"),
        ],
    }
    
    @classmethod
    def scan(cls, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Scan content for security issues."""
        issues = []
        lines = content.splitlines()
        
        for category, patterns in cls.PATTERNS.items():
            for pattern, description in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issues.append({
                            "category": category,
                            "severity": cls._get_severity(category),
                            "description": description,
                            "file": file_path,
                            "line": line_num,
                            "content": line.strip()[:100]
                        })
        
        return issues
    
    @staticmethod
    def _get_severity(category: str) -> str:
        severity_map = {
            "hardcoded_secret": "high",
            "sql_injection": "critical",
            "command_injection": "critical",
            "path_traversal": "high",
            "insecure_random": "medium",
            "debug_code": "low",
        }
        return severity_map.get(category, "medium")


class CodeAnalyzerTool(BaseTool):
    """Analyze code for complexity, maintainability, and security."""
    
    @property
    def name(self) -> str:
        return "code_analyzer"
    
    @property
    def description(self) -> str:
        return "Analyze code for complexity, maintainability, and potential security issues"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="file_path",
                param_type="string",
                description="Path to the file to analyze"
            ),
            ToolParameter(
                name="language",
                param_type="string",
                description="Programming language",
                required=False,
                default="auto",
                enum_values=["auto", "python", "javascript", "typescript"]
            ),
            ToolParameter(
                name="analysis_type",
                param_type="string",
                description="Type of analysis to perform",
                required=False,
                default="all",
                enum_values=["complexity", "security", "all"]
            )
        ]
    
    def execute(self, file_path: str, language: str = "auto",
                analysis_type: str = "all") -> ToolResult:
        path = Path(file_path)
        
        if not path.exists():
            return ToolResult.failure(f"File not found: {file_path}", "FileNotFoundError")
        
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult.failure("Unable to read file as text", "UnicodeDecodeError")
        
        # Detect language
        if language == "auto":
            suffix = path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "javascript",
                ".tsx": "typescript",
            }
            language = language_map.get(suffix, "unknown")
        
        result_data = {
            "file": str(path),
            "language": language,
            "metrics": None,
            "security_issues": [],
            "recommendations": []
        }
        
        # Complexity analysis (Python only for now)
        if analysis_type in ("complexity", "all") and language == "python":
            metrics = PythonAnalyzer.analyze_file(content, file_path)
            result_data["metrics"] = {
                "total_lines": metrics.total_lines,
                "code_lines": metrics.code_lines,
                "comment_lines": metrics.comment_lines,
                "blank_lines": metrics.blank_lines,
                "classes": metrics.classes,
                "imports": metrics.imports,
                "average_complexity": metrics.average_complexity,
                "functions": [
                    {
                        "name": f.name,
                        "line_start": f.line_start,
                        "cyclomatic_complexity": f.cyclomatic_complexity,
                        "cognitive_complexity": f.cognitive_complexity,
                        "lines_of_code": f.lines_of_code,
                        "has_docstring": f.has_docstring
                    }
                    for f in metrics.functions
                ]
            }
            
            # Generate recommendations
            for func in metrics.functions:
                if func.cyclomatic_complexity > 10:
                    result_data["recommendations"].append({
                        "type": "complexity",
                        "severity": "high" if func.cyclomatic_complexity > 15 else "medium",
                        "message": f"Function '{func.name}' has high complexity ({func.cyclomatic_complexity}). Consider refactoring.",
                        "line": func.line_start
                    })
                if not func.has_docstring:
                    result_data["recommendations"].append({
                        "type": "documentation",
                        "severity": "low",
                        "message": f"Function '{func.name}' lacks a docstring.",
                        "line": func.line_start
                    })
                if func.parameters > 5:
                    result_data["recommendations"].append({
                        "type": "design",
                        "severity": "medium",
                        "message": f"Function '{func.name}' has many parameters ({func.parameters}). Consider using a configuration object.",
                        "line": func.line_start
                    })
        
        # Security analysis
        if analysis_type in ("security", "all"):
            result_data["security_issues"] = SecurityScanner.scan(content, file_path)
        
        return ToolResult.success(
            data=result_data,
            metadata={"analysis_type": analysis_type, "language": language}
        )


# Register the tool
register_tool(CodeAnalyzerTool())
