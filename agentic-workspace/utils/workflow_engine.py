"""
Workflow Engine for the Agentic Workspace.
Orchestrates multi-step processes coordinating agents and tools.
"""
import asyncio
import re
import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class WorkflowStatus(Enum):
    """Status of workflow or step execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class ErrorStrategy(Enum):
    """How to handle errors in workflow execution."""
    FAIL_FAST = "fail-fast"
    CONTINUE = "continue"
    PARTIAL_SUCCESS = "partial-success"


@dataclass
class StepResult:
    """Result of a workflow step execution."""
    step_name: str
    status: WorkflowStatus
    output: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retries: int = 0

    @property
    def duration_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries": self.retries
        }


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution."""
    workflow_name: str
    status: WorkflowStatus
    steps: Dict[str, StepResult] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def duration_ms(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0

    @property
    def success_rate(self) -> float:
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps.values() if s.status == WorkflowStatus.COMPLETED)
        return completed / len(self.steps) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "success_rate": self.success_rate,
            "steps": {name: step.to_dict() for name, step in self.steps.items()},
            "outputs": self.outputs,
            "error": self.error
        }


class VariableResolver:
    """Resolves variable references in workflow parameters."""

    VARIABLE_PATTERN = re.compile(r'\$\{([^}]+)\}')

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def resolve(self, value: Any) -> Any:
        """Resolve variables in a value recursively."""
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self.resolve(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self.resolve(item) for item in value]
        return value

    def _resolve_string(self, text: str) -> Any:
        """Resolve variable references in a string."""
        # Check if entire string is a variable reference
        match = self.VARIABLE_PATTERN.fullmatch(text)
        if match:
            return self._get_value(match.group(1))

        # Replace embedded references
        def replacer(m):
            val = self._get_value(m.group(1))
            return str(val) if val is not None else m.group(0)

        return self.VARIABLE_PATTERN.sub(replacer, text)

    def _get_value(self, path: str) -> Any:
        """Get value from context using dot notation path."""
        parts = path.split('.')
        value = self.context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value


class StepExecutor:
    """Executes individual workflow steps."""

    def __init__(self, agents: Dict[str, Any], tools: Dict[str, Callable]):
        self.agents = agents
        self.tools = tools

    def execute(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any],
        retry_config: Optional[Dict[str, Any]] = None
    ) -> StepResult:
        """Execute a workflow step."""
        step_name = step.get("name", "unknown")
        result = StepResult(step_name=step_name, status=WorkflowStatus.RUNNING)
        result.start_time = datetime.now()

        retry_config = retry_config or step.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 1)
        backoff = retry_config.get("backoff", "linear")

        # Resolve variables in parameters
        resolver = VariableResolver(context)
        params = resolver.resolve(step.get("params", {}))

        last_error = None
        for attempt in range(max_attempts):
            result.retries = attempt

            try:
                # Get agent and action
                agent_name = step.get("agent")
                action = step.get("action")

                # Execute the step
                output = self._execute_action(agent_name, action, params)
                
                result.status = WorkflowStatus.COMPLETED
                result.output = output
                result.end_time = datetime.now()
                return result

            except Exception as e:
                last_error = str(e)
                if attempt < max_attempts - 1:
                    # Calculate backoff delay
                    if backoff == "exponential":
                        delay = 2 ** attempt
                    else:
                        delay = attempt + 1
                    time.sleep(delay)

        result.status = WorkflowStatus.FAILED
        result.error = last_error
        result.end_time = datetime.now()
        return result

    def _execute_action(self, agent_name: str, action: str, params: Dict[str, Any]) -> Any:
        """Execute an action using an agent or tool."""
        # Try to find a tool with this action name
        if action in self.tools:
            tool = self.tools[action]
            result = tool(**params)
            if hasattr(result, 'data'):
                return result.data
            return result

        # Try to find agent with this action
        agent = self.agents.get(agent_name)
        if agent and hasattr(agent, action):
            method = getattr(agent, action)
            return method(**params)

        # Fallback: simulate execution for demonstration
        return {"simulated": True, "agent": agent_name, "action": action, "params": params}


class DependencyGraph:
    """Manages step dependencies and execution order."""

    def __init__(self, steps: List[Dict[str, Any]]):
        self.steps = {step["name"]: step for step in steps}
        self.dependencies = {}
        self.dependents = {}

        for step in steps:
            name = step["name"]
            deps = step.get("depends_on", [])
            self.dependencies[name] = set(deps)
            
            for dep in deps:
                if dep not in self.dependents:
                    self.dependents[dep] = set()
                self.dependents[dep].add(name)

    def get_ready_steps(self, completed: set) -> List[str]:
        """Get steps that are ready to execute."""
        ready = []
        for name, deps in self.dependencies.items():
            if name not in completed and deps.issubset(completed):
                ready.append(name)
        return ready

    def get_execution_order(self) -> List[List[str]]:
        """Get execution order as waves of parallelizable steps."""
        completed = set()
        waves = []

        while len(completed) < len(self.steps):
            wave = self.get_ready_steps(completed)
            if not wave:
                # Circular dependency or missing dependency
                remaining = set(self.steps.keys()) - completed
                raise ValueError(f"Cannot resolve dependencies for: {remaining}")
            waves.append(wave)
            completed.update(wave)

        return waves

    def validate(self) -> List[str]:
        """Validate the dependency graph."""
        errors = []

        # Check for missing dependencies
        all_names = set(self.steps.keys())
        for name, deps in self.dependencies.items():
            missing = deps - all_names
            if missing:
                errors.append(f"Step '{name}' has missing dependencies: {missing}")

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in self.dependencies.get(node, []):
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for name in self.steps:
            if name not in visited:
                if has_cycle(name):
                    errors.append(f"Circular dependency detected involving step: {name}")
                    break

        return errors


class WorkflowEngine:
    """
    Main workflow execution engine.
    Coordinates multi-step processes with parallel execution support.
    """

    def __init__(
        self,
        agents: Optional[Dict[str, Any]] = None,
        tools: Optional[Dict[str, Callable]] = None,
        max_workers: int = 4,
        logger: Optional[Any] = None
    ):
        self.agents = agents or {}
        self.tools = tools or {}
        self.max_workers = max_workers
        self.logger = logger
        self.executor = StepExecutor(self.agents, self.tools)
        self._running_workflows: Dict[str, WorkflowResult] = {}
        self._lock = threading.Lock()

    def load_workflow(self, path: str) -> Dict[str, Any]:
        """Load a workflow definition from a file."""
        workflow_path = Path(path)
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {path}")

        with open(workflow_path) as f:
            if workflow_path.suffix in ['.yaml', '.yml']:
                import yaml
                return yaml.safe_load(f)
            return json.load(f)

    def validate_workflow(self, workflow: Dict[str, Any]) -> List[str]:
        """Validate a workflow definition."""
        errors = []

        # Required fields
        if "name" not in workflow:
            errors.append("Workflow missing required field: name")
        if "steps" not in workflow:
            errors.append("Workflow missing required field: steps")
        elif not workflow["steps"]:
            errors.append("Workflow must have at least one step")

        # Validate steps
        if "steps" in workflow:
            step_names = set()
            for i, step in enumerate(workflow["steps"]):
                if "name" not in step:
                    errors.append(f"Step {i} missing required field: name")
                else:
                    if step["name"] in step_names:
                        errors.append(f"Duplicate step name: {step['name']}")
                    step_names.add(step["name"])

                if "agent" not in step:
                    errors.append(f"Step {i} missing required field: agent")
                if "action" not in step:
                    errors.append(f"Step {i} missing required field: action")

            # Validate dependency graph
            graph = DependencyGraph(workflow["steps"])
            errors.extend(graph.validate())

        return errors

    def execute(
        self,
        workflow: Dict[str, Any],
        inputs: Dict[str, Any],
        parallel: Optional[bool] = None
    ) -> WorkflowResult:
        """
        Execute a workflow with the given inputs.
        
        Args:
            workflow: Workflow definition dictionary
            inputs: Input parameters for the workflow
            parallel: Whether to execute steps in parallel (overrides workflow setting)
            
        Returns:
            WorkflowResult containing execution details
        """
        workflow_name = workflow.get("name", "unnamed")
        result = WorkflowResult(
            workflow_name=workflow_name,
            status=WorkflowStatus.RUNNING,
            start_time=datetime.now()
        )

        # Validate workflow
        errors = self.validate_workflow(workflow)
        if errors:
            result.status = WorkflowStatus.FAILED
            result.error = f"Validation errors: {', '.join(errors)}"
            result.end_time = datetime.now()
            return result

        # Store running workflow
        with self._lock:
            self._running_workflows[workflow_name] = result

        try:
            # Build context
            context = {
                "inputs": inputs,
                "steps": {},
                "workflow": workflow
            }

            # Get execution configuration
            error_strategy = ErrorStrategy(
                workflow.get("error_handling", {}).get("strategy", "fail-fast")
            )
            use_parallel = parallel if parallel is not None else workflow.get("parallel", False)

            # Build dependency graph
            graph = DependencyGraph(workflow["steps"])

            # Execute steps
            if use_parallel:
                self._execute_parallel(workflow, graph, context, result, error_strategy)
            else:
                self._execute_sequential(workflow, graph, context, result, error_strategy)

            # Determine final status
            failed_steps = [s for s in result.steps.values() if s.status == WorkflowStatus.FAILED]
            
            if failed_steps:
                if error_strategy == ErrorStrategy.PARTIAL_SUCCESS:
                    completed = [s for s in result.steps.values() if s.status == WorkflowStatus.COMPLETED]
                    if completed:
                        result.status = WorkflowStatus.COMPLETED
                    else:
                        result.status = WorkflowStatus.FAILED
                else:
                    result.status = WorkflowStatus.FAILED
            else:
                result.status = WorkflowStatus.COMPLETED

            # Collect outputs
            for step_name, step_result in result.steps.items():
                if step_result.output is not None:
                    context["steps"][step_name] = {"output": step_result.output}

            result.outputs = context.get("steps", {})

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error = str(e)

        finally:
            result.end_time = datetime.now()
            with self._lock:
                self._running_workflows.pop(workflow_name, None)

            if self.logger:
                self.logger.log_workflow_end(
                    workflow_name,
                    result.status.value,
                    result.to_dict()
                )

        return result

    def _execute_sequential(
        self,
        workflow: Dict[str, Any],
        graph: DependencyGraph,
        context: Dict[str, Any],
        result: WorkflowResult,
        error_strategy: ErrorStrategy
    ):
        """Execute workflow steps sequentially."""
        execution_order = graph.get_execution_order()

        for wave in execution_order:
            for step_name in wave:
                step = graph.steps[step_name]
                
                # Check if we should skip due to previous failure
                if error_strategy == ErrorStrategy.FAIL_FAST:
                    if any(s.status == WorkflowStatus.FAILED for s in result.steps.values()):
                        step_result = StepResult(step_name=step_name, status=WorkflowStatus.SKIPPED)
                        result.steps[step_name] = step_result
                        continue

                # Execute step
                step_result = self.executor.execute(step, context)
                result.steps[step_name] = step_result

                # Update context with output
                if step_result.output is not None:
                    context["steps"][step_name] = {"output": step_result.output}

                # Handle failure
                if step_result.status == WorkflowStatus.FAILED:
                    on_failure = step.get("on_failure", "stop")
                    if on_failure == "stop" and error_strategy == ErrorStrategy.FAIL_FAST:
                        return

    def _execute_parallel(
        self,
        workflow: Dict[str, Any],
        graph: DependencyGraph,
        context: Dict[str, Any],
        result: WorkflowResult,
        error_strategy: ErrorStrategy
    ):
        """Execute workflow steps in parallel where possible."""
        execution_order = graph.get_execution_order()
        context_lock = threading.Lock()

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            for wave in execution_order:
                # Check for early termination
                if error_strategy == ErrorStrategy.FAIL_FAST:
                    if any(s.status == WorkflowStatus.FAILED for s in result.steps.values()):
                        for step_name in wave:
                            result.steps[step_name] = StepResult(
                                step_name=step_name, 
                                status=WorkflowStatus.SKIPPED
                            )
                        continue

                # Submit all steps in this wave
                futures = {}
                for step_name in wave:
                    step = graph.steps[step_name]
                    future = pool.submit(self.executor.execute, step, context.copy())
                    futures[future] = step_name

                # Collect results
                for future in as_completed(futures):
                    step_name = futures[future]
                    try:
                        step_result = future.result()
                    except Exception as e:
                        step_result = StepResult(
                            step_name=step_name,
                            status=WorkflowStatus.FAILED,
                            error=str(e)
                        )

                    result.steps[step_name] = step_result

                    # Update context with output (thread-safe)
                    if step_result.output is not None:
                        with context_lock:
                            context["steps"][step_name] = {"output": step_result.output}

    def cancel(self, workflow_name: str) -> bool:
        """Cancel a running workflow."""
        with self._lock:
            if workflow_name in self._running_workflows:
                self._running_workflows[workflow_name].status = WorkflowStatus.CANCELLED
                return True
        return False

    def get_status(self, workflow_name: str) -> Optional[WorkflowResult]:
        """Get the status of a running workflow."""
        with self._lock:
            return self._running_workflows.get(workflow_name)


async def execute_workflow_async(
    engine: WorkflowEngine,
    workflow: Dict[str, Any],
    inputs: Dict[str, Any]
) -> WorkflowResult:
    """Execute a workflow asynchronously."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: engine.execute(workflow, inputs, parallel=True)
    )
