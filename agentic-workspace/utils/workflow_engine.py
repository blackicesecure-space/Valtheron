"""
Workflow Engine for the agentic workspace.

Orchestrates multi-step workflows with dependency management,
parallel execution, and comprehensive error handling.
"""
import asyncio
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class StepStatus(Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class StepResult:
    """Result of a single workflow step."""
    step_name: str
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_ms: float = 0.0
    retries: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time_ms": self.execution_time_ms,
            "retries": self.retries
        }


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    workflow_name: str
    status: WorkflowStatus
    steps: Dict[str, StepResult] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    total_execution_time_ms: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "outputs": self.outputs,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_execution_time_ms": self.total_execution_time_ms,
            "error": self.error
        }


class VariableResolver:
    """
    Resolves variable references in workflow parameters.
    
    Supports:
    - ${inputs.param_name} - Workflow input parameters
    - ${steps.step_name.output} - Output from a previous step
    - ${steps.step_name.output.field} - Specific field from step output
    - ${env.VAR_NAME} - Environment variable
    """
    
    def __init__(self, inputs: Dict[str, Any], step_results: Dict[str, StepResult]):
        self.inputs = inputs
        self.step_results = step_results
        self._pattern = re.compile(r'\$\{([^}]+)\}')
    
    def resolve(self, value: Any) -> Any:
        """Resolve variables in a value (recursively for dicts/lists)."""
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value
    
    def _resolve_string(self, value: str) -> Any:
        """Resolve variable references in a string."""
        # Check if the entire string is a variable reference
        match = self._pattern.fullmatch(value)
        if match:
            return self._get_value(match.group(1))
        
        # Otherwise, perform string interpolation
        def replace(m):
            result = self._get_value(m.group(1))
            return str(result) if result is not None else ""
        
        return self._pattern.sub(replace, value)
    
    def _get_value(self, path: str) -> Any:
        """Get a value from the context using a dot-notation path."""
        import os
        
        parts = path.split(".")
        
        if parts[0] == "inputs":
            return self._navigate(self.inputs, parts[1:])
        elif parts[0] == "steps":
            if len(parts) < 2:
                return None
            step_name = parts[1]
            if step_name not in self.step_results:
                return None
            step_result = self.step_results[step_name]
            if len(parts) == 2:
                return step_result.output
            if parts[2] == "output":
                return self._navigate(step_result.output, parts[3:])
            return None
        elif parts[0] == "env":
            if len(parts) >= 2:
                return os.environ.get(parts[1])
            return None
        
        return None
    
    def _navigate(self, obj: Any, path: List[str]) -> Any:
        """Navigate through nested dicts/lists using a path."""
        for key in path:
            if obj is None:
                return None
            if isinstance(obj, dict):
                obj = obj.get(key)
            elif isinstance(obj, list) and key.isdigit():
                idx = int(key)
                obj = obj[idx] if 0 <= idx < len(obj) else None
            else:
                return None
        return obj


class DependencyResolver:
    """Resolves step dependencies and determines execution order."""
    
    @staticmethod
    def build_dependency_graph(steps: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """Build a dependency graph from step definitions."""
        graph = {}
        for step in steps:
            name = step["name"]
            deps = set(step.get("depends_on", []))
            graph[name] = deps
        return graph
    
    @staticmethod
    def topological_sort(graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Perform topological sort to determine execution order.
        
        Returns:
            List of execution levels, where steps in each level can run in parallel
        """
        in_degree = {node: 0 for node in graph}
        for deps in graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] = in_degree.get(dep, 0)
        
        for node, deps in graph.items():
            for dep in deps:
                if dep not in graph:
                    raise ValueError(f"Unknown dependency: {dep}")
        
        for deps in graph.values():
            for dep in deps:
                if dep in in_degree:
                    in_degree[dep] += 0  # Already counted
        
        # Kahn's algorithm with level tracking
        # Recalculate in-degrees
        in_degree = {node: 0 for node in graph}
        for node, deps in graph.items():
            in_degree[node] = len(deps)
        
        levels = []
        remaining = set(graph.keys())
        
        while remaining:
            # Find all nodes with no remaining dependencies
            ready = [n for n in remaining if in_degree[n] == 0]
            
            if not ready:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected among: {remaining}")
            
            levels.append(ready)
            
            for node in ready:
                remaining.remove(node)
                # Decrease in-degree for dependent nodes
                for other, deps in graph.items():
                    if node in deps:
                        in_degree[other] -= 1
        
        return levels
    
    @staticmethod
    def get_ready_steps(graph: Dict[str, Set[str]], 
                        completed: Set[str]) -> List[str]:
        """Get steps that are ready to execute (all dependencies satisfied)."""
        ready = []
        for step, deps in graph.items():
            if step not in completed and deps.issubset(completed):
                ready.append(step)
        return ready


class WorkflowEngine:
    """
    Executes workflows with full orchestration capabilities.
    
    Features:
    - Dependency-based execution ordering
    - Parallel execution of independent steps
    - Variable resolution between steps
    - Retry logic with backoff
    - Comprehensive error handling
    - Execution logging and metrics
    """
    
    def __init__(self, 
                 agent_executor: Optional[Callable] = None,
                 max_workers: int = 4):
        """
        Initialize the workflow engine.
        
        Args:
            agent_executor: Callable that executes agent actions
                           Signature: (agent_name, action, params) -> result
            max_workers: Maximum parallel workers for concurrent execution
        """
        self.agent_executor = agent_executor or self._default_executor
        self.max_workers = max_workers
        self._running = False
    
    def _default_executor(self, agent: str, action: str, params: Dict) -> Any:
        """Default executor that simulates agent execution."""
        logger.info(f"Executing {action} on {agent} with params: {params}")
        return {"status": "simulated", "agent": agent, "action": action}
    
    def execute(self, 
                workflow_config: Dict[str, Any],
                inputs: Optional[Dict[str, Any]] = None,
                parallel: bool = True) -> WorkflowResult:
        """
        Execute a workflow synchronously.
        
        Args:
            workflow_config: Workflow configuration dictionary
            inputs: Input parameters for the workflow
            parallel: Whether to execute independent steps in parallel
            
        Returns:
            WorkflowResult with execution details
        """
        workflow_name = workflow_config.get("name", "unnamed")
        inputs = inputs or {}
        
        result = WorkflowResult(
            workflow_name=workflow_name,
            status=WorkflowStatus.PENDING,
            started_at=datetime.utcnow().isoformat()
        )
        
        start_time = time.time()
        
        try:
            # Validate inputs
            self._validate_inputs(workflow_config, inputs)
            
            # Build dependency graph
            steps = workflow_config.get("steps", [])
            step_map = {s["name"]: s for s in steps}
            dep_graph = DependencyResolver.build_dependency_graph(steps)
            
            # Get execution order
            execution_levels = DependencyResolver.topological_sort(dep_graph)
            
            result.status = WorkflowStatus.RUNNING
            step_results: Dict[str, StepResult] = {}
            failed_steps: Set[str] = set()
            
            # Execute each level
            for level in execution_levels:
                if parallel and len(level) > 1:
                    level_results = self._execute_level_parallel(
                        level, step_map, inputs, step_results, failed_steps,
                        workflow_config.get("error_handling", {})
                    )
                else:
                    level_results = self._execute_level_sequential(
                        level, step_map, inputs, step_results, failed_steps,
                        workflow_config.get("error_handling", {})
                    )
                
                step_results.update(level_results)
                
                # Check for failures
                for step_name, step_result in level_results.items():
                    if step_result.status == StepStatus.FAILED:
                        failed_steps.add(step_name)
                        
                        # Check error handling strategy
                        strategy = workflow_config.get("error_handling", {}).get("strategy", "fail-fast")
                        if strategy == "fail-fast":
                            result.status = WorkflowStatus.FAILED
                            result.error = f"Step '{step_name}' failed: {step_result.error}"
                            break
                
                if result.status == WorkflowStatus.FAILED:
                    break
            
            # Determine final status
            if result.status != WorkflowStatus.FAILED:
                if failed_steps:
                    result.status = WorkflowStatus.PARTIAL_SUCCESS
                else:
                    result.status = WorkflowStatus.COMPLETED
            
            result.steps = step_results
            
            # Extract outputs
            output_config = workflow_config.get("outputs", {})
            resolver = VariableResolver(inputs, step_results)
            for output_name, output_def in output_config.items():
                if isinstance(output_def, dict) and "from" in output_def:
                    result.outputs[output_name] = resolver.resolve(f"${{{output_def['from']}}}")
                else:
                    result.outputs[output_name] = resolver.resolve(output_def)
            
        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            result.status = WorkflowStatus.FAILED
            result.error = str(e)
        
        result.completed_at = datetime.utcnow().isoformat()
        result.total_execution_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _validate_inputs(self, workflow_config: Dict, inputs: Dict) -> None:
        """Validate workflow inputs against schema."""
        input_schema = workflow_config.get("inputs", {})
        
        for param_name, param_def in input_schema.items():
            required = param_def.get("required", True) if isinstance(param_def, dict) else True
            if required and param_name not in inputs:
                raise ValueError(f"Missing required input: {param_name}")
    
    def _execute_level_sequential(self,
                                   level: List[str],
                                   step_map: Dict[str, Dict],
                                   inputs: Dict,
                                   step_results: Dict[str, StepResult],
                                   failed_steps: Set[str],
                                   error_handling: Dict) -> Dict[str, StepResult]:
        """Execute a level of steps sequentially."""
        results = {}
        for step_name in level:
            result = self._execute_step(
                step_map[step_name], inputs, step_results, failed_steps, error_handling
            )
            results[step_name] = result
            step_results[step_name] = result  # Update for subsequent steps
        return results
    
    def _execute_level_parallel(self,
                                 level: List[str],
                                 step_map: Dict[str, Dict],
                                 inputs: Dict,
                                 step_results: Dict[str, StepResult],
                                 failed_steps: Set[str],
                                 error_handling: Dict) -> Dict[str, StepResult]:
        """Execute a level of steps in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(level))) as executor:
            futures = {
                executor.submit(
                    self._execute_step,
                    step_map[step_name], inputs, step_results.copy(), failed_steps, error_handling
                ): step_name
                for step_name in level
            }
            
            for future in as_completed(futures):
                step_name = futures[future]
                try:
                    results[step_name] = future.result()
                except Exception as e:
                    results[step_name] = StepResult(
                        step_name=step_name,
                        status=StepStatus.FAILED,
                        error=str(e)
                    )
        
        return results
    
    def _execute_step(self,
                      step_config: Dict,
                      inputs: Dict,
                      step_results: Dict[str, StepResult],
                      failed_steps: Set[str],
                      error_handling: Dict) -> StepResult:
        """Execute a single workflow step."""
        step_name = step_config["name"]
        agent = step_config["agent"]
        action = step_config["action"]
        
        result = StepResult(
            step_name=step_name,
            status=StepStatus.PENDING,
            started_at=datetime.utcnow().isoformat()
        )
        
        # Check if dependencies failed
        deps = set(step_config.get("depends_on", []))
        failed_deps = deps.intersection(failed_steps)
        if failed_deps:
            on_failure = step_config.get("on_failure", error_handling.get("default_on_failure", "stop"))
            if on_failure != "continue":
                result.status = StepStatus.BLOCKED
                result.error = f"Blocked by failed dependencies: {failed_deps}"
                result.completed_at = datetime.utcnow().isoformat()
                return result
        
        start_time = time.time()
        result.status = StepStatus.RUNNING
        
        # Resolve parameters
        resolver = VariableResolver(inputs, step_results)
        params = resolver.resolve(step_config.get("params", {}))
        
        # Get retry configuration
        retry_config = step_config.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 1)
        backoff = retry_config.get("backoff", "linear")
        
        last_error = None
        for attempt in range(max_attempts):
            try:
                output = self.agent_executor(agent, action, params)
                result.status = StepStatus.COMPLETED
                result.output = output
                result.retries = attempt
                break
            except Exception as e:
                last_error = e
                result.retries = attempt + 1
                
                if attempt < max_attempts - 1:
                    # Calculate delay
                    if backoff == "exponential":
                        delay = 2 ** attempt
                    else:  # linear
                        delay = attempt + 1
                    time.sleep(delay)
        else:
            # All retries exhausted
            result.status = StepStatus.FAILED
            result.error = str(last_error)
        
        result.completed_at = datetime.utcnow().isoformat()
        result.execution_time_ms = (time.time() - start_time) * 1000
        
        return result


def load_workflow(path: str) -> Dict[str, Any]:
    """Load a workflow configuration from a JSON or YAML file."""
    file_path = Path(path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Workflow file not found: {path}")
    
    with open(file_path, "r") as f:
        if file_path.suffix in (".yaml", ".yml"):
            import yaml
            return yaml.safe_load(f)
        else:
            return json.load(f)
