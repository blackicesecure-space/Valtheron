"""
Bash execution tool for the agentic workspace.
Provides secure command execution with timeout and output capture.
"""
import subprocess
import shlex
import os
import signal
from pathlib import Path
from typing import List, Optional, Dict, Any

from .base import BaseTool, ToolParameter, ToolResult, register_tool


class BashTool(BaseTool):
    """Execute bash commands with security controls."""
    
    # Commands that are blocked by default
    BLOCKED_COMMANDS = {
        "rm -rf /",
        "rm -rf /*",
        "mkfs",
        "dd if=/dev/zero",
        ":(){:|:&};:",  # Fork bomb
        "chmod -R 777 /",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
    }
    
    # Dangerous patterns to check
    DANGEROUS_PATTERNS = [
        r">\s*/dev/sd[a-z]",  # Writing to disk devices
        r">\s*/dev/null\s*2>&1\s*&",  # Background with no output (suspicious)
        r"\|\s*bash",  # Piping to bash
        r"curl.*\|\s*sh",  # Curl piping to shell
        r"wget.*\|\s*sh",  # Wget piping to shell
    ]
    
    @property
    def name(self) -> str:
        return "bash"
    
    @property
    def description(self) -> str:
        return "Execute bash commands in a controlled environment"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="command",
                param_type="string",
                description="The bash command to execute"
            ),
            ToolParameter(
                name="working_directory",
                param_type="string",
                description="Working directory for command execution",
                required=False,
                default="."
            ),
            ToolParameter(
                name="timeout_seconds",
                param_type="integer",
                description="Maximum execution time in seconds",
                required=False,
                default=60
            ),
            ToolParameter(
                name="env_vars",
                param_type="object",
                description="Additional environment variables",
                required=False
            ),
            ToolParameter(
                name="capture_stderr",
                param_type="boolean",
                description="Capture stderr separately (vs merging with stdout)",
                required=False,
                default=True
            )
        ]
    
    def _is_command_safe(self, command: str) -> Optional[str]:
        """
        Check if a command is safe to execute.
        
        Returns:
            Error message if unsafe, None if safe
        """
        import re
        
        # Check against blocked commands
        normalized = " ".join(command.lower().split())
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in normalized:
                return f"Blocked command pattern: {blocked}"
        
        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                return f"Dangerous pattern detected: {pattern}"
        
        return None
    
    def execute(self, command: str, working_directory: str = ".",
                timeout_seconds: int = 60, env_vars: Optional[Dict[str, str]] = None,
                capture_stderr: bool = True) -> ToolResult:
        
        # Security check
        safety_error = self._is_command_safe(command)
        if safety_error:
            return ToolResult.failure(safety_error, "SecurityError")
        
        # Validate working directory
        cwd = Path(working_directory)
        if not cwd.exists():
            return ToolResult.failure(
                f"Working directory not found: {working_directory}",
                "FileNotFoundError"
            )
        
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        
        # Configure stderr handling
        stderr_config = subprocess.PIPE if capture_stderr else subprocess.STDOUT
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            return ToolResult.success(
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr if capture_stderr else None,
                    "return_code": result.returncode,
                    "success": result.returncode == 0
                },
                metadata={
                    "command": command,
                    "working_directory": str(cwd.absolute()),
                    "timeout_seconds": timeout_seconds
                }
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult.failure(
                f"Command timed out after {timeout_seconds} seconds",
                "TimeoutError"
            )
        except Exception as e:
            return ToolResult.failure(str(e), type(e).__name__)


class TestRunnerTool(BaseTool):
    """Run tests using various test frameworks."""
    
    FRAMEWORK_COMMANDS = {
        "pytest": "pytest {path} {options}",
        "jest": "npx jest {path} {options}",
        "mocha": "npx mocha {path} {options}",
        "go-test": "go test {path} {options}",
        "unittest": "python -m unittest discover -s {path} {options}",
    }
    
    @property
    def name(self) -> str:
        return "test_runner"
    
    @property
    def description(self) -> str:
        return "Execute tests using various testing frameworks"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="test_path",
                param_type="string",
                description="Path to test file or directory"
            ),
            ToolParameter(
                name="framework",
                param_type="string",
                description="Testing framework to use",
                enum_values=["pytest", "jest", "mocha", "go-test", "unittest"]
            ),
            ToolParameter(
                name="verbose",
                param_type="boolean",
                description="Run with verbose output",
                required=False,
                default=False
            ),
            ToolParameter(
                name="coverage",
                param_type="boolean",
                description="Collect coverage data",
                required=False,
                default=False
            ),
            ToolParameter(
                name="parallel",
                param_type="boolean",
                description="Run tests in parallel",
                required=False,
                default=False
            ),
            ToolParameter(
                name="filter_pattern",
                param_type="string",
                description="Filter tests by name pattern",
                required=False
            ),
            ToolParameter(
                name="timeout_seconds",
                param_type="integer",
                description="Maximum execution time",
                required=False,
                default=300
            )
        ]
    
    def execute(self, test_path: str, framework: str, verbose: bool = False,
                coverage: bool = False, parallel: bool = False,
                filter_pattern: Optional[str] = None,
                timeout_seconds: int = 300) -> ToolResult:
        
        path = Path(test_path)
        if not path.exists():
            return ToolResult.failure(f"Test path not found: {test_path}", "FileNotFoundError")
        
        # Build command options
        options = []
        
        if framework == "pytest":
            if verbose:
                options.append("-v")
            if coverage:
                options.append("--cov=.")
            if parallel:
                options.append("-n auto")
            if filter_pattern:
                options.append(f"-k '{filter_pattern}'")
            options.append("--tb=short")
            options.append("-q")
        
        elif framework == "jest":
            if verbose:
                options.append("--verbose")
            if coverage:
                options.append("--coverage")
            if parallel:
                options.append("--maxWorkers=auto")
            if filter_pattern:
                options.append(f"--testNamePattern='{filter_pattern}'")
        
        elif framework == "mocha":
            if verbose:
                options.append("--reporter spec")
            if parallel:
                options.append("--parallel")
            if filter_pattern:
                options.append(f"--grep '{filter_pattern}'")
        
        # Build command
        options_str = " ".join(options)
        command_template = self.FRAMEWORK_COMMANDS.get(framework)
        command = command_template.format(path=test_path, options=options_str)
        
        # Execute tests
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            
            # Parse results (basic parsing)
            output = result.stdout + result.stderr
            
            # Try to extract test counts from output
            test_data = self._parse_test_output(output, framework)
            test_data["raw_output"] = output
            test_data["return_code"] = result.returncode
            test_data["success"] = result.returncode == 0
            
            return ToolResult.success(
                data=test_data,
                metadata={"framework": framework, "command": command}
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult.failure(
                f"Tests timed out after {timeout_seconds} seconds",
                "TimeoutError"
            )
    
    def _parse_test_output(self, output: str, framework: str) -> Dict[str, Any]:
        """Parse test output to extract metrics."""
        import re
        
        data = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage_percent": None,
            "failures": []
        }
        
        if framework == "pytest":
            # Match pytest summary line: "5 passed, 2 failed, 1 skipped"
            match = re.search(r'(\d+)\s+passed', output)
            if match:
                data["passed"] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+failed', output)
            if match:
                data["failed"] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+skipped', output)
            if match:
                data["skipped"] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+error', output)
            if match:
                data["errors"] = int(match.group(1))
            
            # Coverage
            match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
            if match:
                data["coverage_percent"] = int(match.group(1))
        
        elif framework == "jest":
            # Match Jest summary
            match = re.search(r'Tests:\s+(\d+)\s+passed', output)
            if match:
                data["passed"] = int(match.group(1))
            
            match = re.search(r'(\d+)\s+failed', output)
            if match:
                data["failed"] = int(match.group(1))
        
        data["total_tests"] = data["passed"] + data["failed"] + data["skipped"] + data["errors"]
        
        return data


# Register tools
register_tool(BashTool())
register_tool(TestRunnerTool())
