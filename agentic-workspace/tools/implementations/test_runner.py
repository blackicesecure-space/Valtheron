"""
Test Runner Tool Implementation.
Executes tests using various frameworks and collects results.
"""
import subprocess
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .base_tool import (
    BaseTool, ToolResult, ToolStatus, ToolParameter, ToolRegistry
)


@dataclass
class TestCase:
    """Represents a single test case result."""
    name: str
    status: str  # passed, failed, skipped, error
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "file": self.file,
            "line": self.line
        }


@dataclass
class TestSuiteResult:
    """Aggregated test results."""
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    duration_ms: float = 0.0
    coverage: Optional[float] = None
    test_cases: List[TestCase] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.errors > 0:
            return "error"
        elif self.failed > 0:
            return "failed"
        elif self.total == 0:
            return "no_tests"
        return "passed"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "total_tests": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
            "coverage": self.coverage,
            "failures": [tc.to_dict() for tc in self.test_cases if tc.status in ("failed", "error")]
        }


class PytestRunner:
    """Runs Python tests using pytest."""

    def __init__(self, test_path: str, options: Dict[str, Any]):
        self.test_path = test_path
        self.verbose = options.get("verbose", False)
        self.coverage = options.get("coverage", False)
        self.parallel = options.get("parallel", False)
        self.markers = options.get("markers", [])
        self.timeout = options.get("timeout", 300)

    def run(self) -> TestSuiteResult:
        """Execute pytest and parse results."""
        result = TestSuiteResult()
        
        # Build command
        cmd = ["python", "-m", "pytest", self.test_path, "--json-report", "--json-report-file=-"]
        
        if self.verbose:
            cmd.append("-v")
        if self.coverage:
            cmd.extend(["--cov", "--cov-report=json"])
        if self.parallel:
            cmd.extend(["-n", "auto"])
        for marker in self.markers:
            cmd.extend(["-m", marker])

        start_time = time.time()
        
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=os.path.dirname(self.test_path) or "."
            )
            
            result.duration_ms = (time.time() - start_time) * 1000
            
            # Try to parse JSON report from stdout
            try:
                # Look for JSON in output
                json_match = re.search(r'\{.*"tests".*\}', proc.stdout, re.DOTALL)
                if json_match:
                    report = json.loads(json_match.group())
                    result = self._parse_json_report(report)
                else:
                    result = self._parse_text_output(proc.stdout, proc.stderr)
            except json.JSONDecodeError:
                result = self._parse_text_output(proc.stdout, proc.stderr)
                
            # Parse coverage if available
            if self.coverage:
                result.coverage = self._parse_coverage()
                
        except subprocess.TimeoutExpired:
            result.errors = 1
            result.test_cases.append(TestCase(
                name="timeout",
                status="error",
                error_message=f"Test execution timed out after {self.timeout}s"
            ))
        except FileNotFoundError:
            result.errors = 1
            result.test_cases.append(TestCase(
                name="setup",
                status="error",
                error_message="pytest not found. Install with: pip install pytest"
            ))
        except Exception as e:
            result.errors = 1
            result.test_cases.append(TestCase(
                name="execution",
                status="error",
                error_message=str(e)
            ))

        return result

    def _parse_json_report(self, report: Dict) -> TestSuiteResult:
        """Parse pytest JSON report."""
        result = TestSuiteResult()
        
        tests = report.get("tests", [])
        result.total = len(tests)
        result.duration_ms = report.get("duration", 0) * 1000
        
        for test in tests:
            outcome = test.get("outcome", "unknown")
            tc = TestCase(
                name=test.get("nodeid", "unknown"),
                status=outcome,
                duration_ms=test.get("duration", 0) * 1000
            )
            
            if outcome == "passed":
                result.passed += 1
            elif outcome == "failed":
                result.failed += 1
                tc.error_message = test.get("call", {}).get("longrepr", "")
            elif outcome == "skipped":
                result.skipped += 1
            else:
                result.errors += 1
                
            result.test_cases.append(tc)
            
        return result

    def _parse_text_output(self, stdout: str, stderr: str) -> TestSuiteResult:
        """Parse pytest text output as fallback."""
        result = TestSuiteResult()
        
        # Look for summary line like "5 passed, 2 failed in 1.23s"
        summary_match = re.search(
            r'(\d+)\s+passed.*?(?:(\d+)\s+failed)?.*?(?:(\d+)\s+skipped)?.*?(?:(\d+)\s+error)?.*?in\s+([\d.]+)s',
            stdout
        )
        
        if summary_match:
            result.passed = int(summary_match.group(1) or 0)
            result.failed = int(summary_match.group(2) or 0)
            result.skipped = int(summary_match.group(3) or 0)
            result.errors = int(summary_match.group(4) or 0)
            result.duration_ms = float(summary_match.group(5)) * 1000
            result.total = result.passed + result.failed + result.skipped + result.errors
        
        # Extract failed test details
        failure_pattern = re.compile(r'FAILED\s+(\S+)\s*-\s*(.+?)(?=\n(?:FAILED|PASSED|=====)|\Z)', re.DOTALL)
        for match in failure_pattern.finditer(stdout):
            result.test_cases.append(TestCase(
                name=match.group(1),
                status="failed",
                error_message=match.group(2).strip()[:500]  # Limit error message length
            ))
            
        return result

    def _parse_coverage(self) -> Optional[float]:
        """Parse coverage report if available."""
        try:
            coverage_file = Path("coverage.json")
            if coverage_file.exists():
                data = json.loads(coverage_file.read_text())
                return data.get("totals", {}).get("percent_covered", None)
        except Exception:
            pass
        return None


class JestRunner:
    """Runs JavaScript/TypeScript tests using Jest."""

    def __init__(self, test_path: str, options: Dict[str, Any]):
        self.test_path = test_path
        self.verbose = options.get("verbose", False)
        self.coverage = options.get("coverage", False)
        self.timeout = options.get("timeout", 300)

    def run(self) -> TestSuiteResult:
        """Execute Jest and parse results."""
        result = TestSuiteResult()
        
        cmd = ["npx", "jest", self.test_path, "--json"]
        
        if self.verbose:
            cmd.append("--verbose")
        if self.coverage:
            cmd.append("--coverage")

        start_time = time.time()
        
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            result.duration_ms = (time.time() - start_time) * 1000
            
            try:
                report = json.loads(proc.stdout)
                result = self._parse_json_report(report)
            except json.JSONDecodeError:
                result = self._parse_text_output(proc.stdout, proc.stderr)
                
        except subprocess.TimeoutExpired:
            result.errors = 1
            result.test_cases.append(TestCase(
                name="timeout",
                status="error",
                error_message=f"Test execution timed out after {self.timeout}s"
            ))
        except FileNotFoundError:
            result.errors = 1
            result.test_cases.append(TestCase(
                name="setup",
                status="error",
                error_message="Jest not found. Install with: npm install jest"
            ))

        return result

    def _parse_json_report(self, report: Dict) -> TestSuiteResult:
        """Parse Jest JSON output."""
        result = TestSuiteResult()
        
        result.total = report.get("numTotalTests", 0)
        result.passed = report.get("numPassedTests", 0)
        result.failed = report.get("numFailedTests", 0)
        result.skipped = report.get("numPendingTests", 0)
        
        for test_result in report.get("testResults", []):
            for assertion in test_result.get("assertionResults", []):
                if assertion.get("status") == "failed":
                    result.test_cases.append(TestCase(
                        name=assertion.get("fullName", "unknown"),
                        status="failed",
                        file=test_result.get("name"),
                        error_message="\n".join(assertion.get("failureMessages", []))[:500]
                    ))
        
        # Parse coverage if available
        coverage_map = report.get("coverageMap", {})
        if coverage_map:
            total_statements = 0
            covered_statements = 0
            for file_coverage in coverage_map.values():
                s = file_coverage.get("s", {})
                total_statements += len(s)
                covered_statements += sum(1 for v in s.values() if v > 0)
            if total_statements > 0:
                result.coverage = round(covered_statements / total_statements * 100, 2)
        
        return result

    def _parse_text_output(self, stdout: str, stderr: str) -> TestSuiteResult:
        """Parse Jest text output as fallback."""
        result = TestSuiteResult()
        
        # Look for summary
        match = re.search(r'Tests:\s+(\d+)\s+passed.*?(\d+)\s+total', stdout)
        if match:
            result.passed = int(match.group(1))
            result.total = int(match.group(2))
            result.failed = result.total - result.passed
            
        return result


@ToolRegistry.register
class TestRunnerTool(BaseTool):
    """
    Executes tests using various testing frameworks.
    Supports pytest for Python and Jest for JavaScript/TypeScript.
    """

    @property
    def name(self) -> str:
        return "test_runner"

    @property
    def description(self) -> str:
        return "Executes tests for a project and returns comprehensive results"

    @classmethod
    def get_parameters(cls) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="test_path",
                param_type="string",
                description="Path to test file or directory",
                required=True
            ),
            ToolParameter(
                name="framework",
                param_type="string",
                description="Testing framework to use",
                required=True,
                enum_values=["pytest", "jest", "mocha", "junit", "go-test"]
            ),
            ToolParameter(
                name="options",
                param_type="object",
                description="Framework-specific options",
                required=False,
                default={}
            )
        ]

    def execute(self, **kwargs) -> ToolResult:
        test_path = kwargs.get("test_path")
        framework = kwargs.get("framework")
        options = kwargs.get("options", {})

        # Validate test path exists
        path = Path(test_path)
        if not path.exists():
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Test path not found: {test_path}"
            )

        # Select and run the appropriate test runner
        runners = {
            "pytest": PytestRunner,
            "jest": JestRunner,
        }

        runner_class = runners.get(framework)
        if not runner_class:
            return ToolResult(
                status=ToolStatus.ERROR,
                error=f"Unsupported framework: {framework}. Supported: {list(runners.keys())}"
            )

        runner = runner_class(test_path, options)
        suite_result = runner.run()

        return ToolResult(
            status=ToolStatus.SUCCESS if suite_result.status in ("passed", "no_tests") else ToolStatus.ERROR,
            data=suite_result.to_dict(),
            metadata={
                "framework": framework,
                "test_path": test_path,
                "total_tests": suite_result.total,
                "pass_rate": round(suite_result.passed / max(suite_result.total, 1) * 100, 2)
            }
        )
