"""
Agent Orchestrator for the Agentic Workspace.
Coordinates multiple agents to work together on complex tasks.
"""
import json
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import threading
from queue import Queue, Empty
import uuid


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentCapability:
    """Represents a capability an agent provides."""
    name: str
    description: str
    tools_required: List[str] = field(default_factory=list)


@dataclass
class AgentTask:
    """A task to be executed by an agent."""
    id: str
    name: str
    action: str
    params: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout_seconds: int = 300
    created_at: datetime = field(default_factory=datetime.now)
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "priority": self.priority.value,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "assigned_agent": self.assigned_agent,
            "status": self.status,
            "result": self.result,
            "error": self.error
        }


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    name: str
    agent_type: str
    version: str
    description: str = ""
    model: Dict[str, Any] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str) -> "AgentConfig":
        """Load agent configuration from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        return cls(
            name=data["name"],
            agent_type=data["type"],
            version=data["version"],
            description=data.get("description", ""),
            model=data.get("model", {}),
            tools=data.get("tools", []),
            capabilities=data.get("capabilities", []),
            config=data.get("config", {})
        )


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    Provides common functionality and interface for agent implementations.
    """

    def __init__(self, config: AgentConfig, tools: Dict[str, Callable] = None):
        self.config = config
        self.tools = tools or {}
        self.status = AgentStatus.IDLE
        self._current_task: Optional[AgentTask] = None
        self._task_history: List[AgentTask] = []
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def agent_type(self) -> str:
        return self.config.agent_type

    @property
    def capabilities(self) -> List[str]:
        return self.config.capabilities

    @abstractmethod
    def execute(self, task: AgentTask) -> Any:
        """Execute a task. Must be implemented by subclasses."""
        pass

    def can_handle(self, action: str) -> bool:
        """Check if this agent can handle a specific action."""
        return action in self.capabilities or action in self.tools

    def run_task(self, task: AgentTask) -> AgentTask:
        """Run a task with status tracking and error handling."""
        with self._lock:
            self.status = AgentStatus.BUSY
            self._current_task = task
            task.assigned_agent = self.name
            task.status = "running"

        try:
            result = self.execute(task)
            task.result = result
            task.status = "completed"
        except Exception as e:
            task.error = str(e)
            task.status = "failed"
            self.status = AgentStatus.ERROR
        finally:
            with self._lock:
                self._current_task = None
                self._task_history.append(task)
                if self.status != AgentStatus.ERROR:
                    self.status = AgentStatus.IDLE

        return task

    def invoke_tool(self, tool_name: str, **kwargs) -> Any:
        """Invoke a tool by name."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool not available: {tool_name}")
        
        tool = self.tools[tool_name]
        return tool(**kwargs)

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        completed = sum(1 for t in self._task_history if t.status == "completed")
        failed = sum(1 for t in self._task_history if t.status == "failed")
        
        return {
            "name": self.name,
            "type": self.agent_type,
            "status": self.status.value,
            "tasks_completed": completed,
            "tasks_failed": failed,
            "success_rate": completed / max(len(self._task_history), 1) * 100
        }


class TaskExecutorAgent(BaseAgent):
    """Agent specialized in executing code and commands."""

    def execute(self, task: AgentTask) -> Any:
        action = task.action
        params = task.params

        if action == "read_file" and "read" in self.tools:
            return self.invoke_tool("read", file_path=params.get("file_path"))

        elif action == "write_file" and "write" in self.tools:
            return self.invoke_tool(
                "write",
                file_path=params.get("file_path"),
                content=params.get("content")
            )

        elif action == "run_command" and "bash" in self.tools:
            return self.invoke_tool("bash", command=params.get("command"))

        elif action == "search_files" and "glob" in self.tools:
            return self.invoke_tool(
                "glob",
                pattern=params.get("pattern"),
                directory=params.get("directory", ".")
            )

        elif action in self.tools:
            return self.invoke_tool(action, **params)

        return {"simulated": True, "action": action, "params": params}


class ResearcherAgent(BaseAgent):
    """Agent specialized in gathering and analyzing information."""

    def execute(self, task: AgentTask) -> Any:
        action = task.action
        params = task.params

        if action == "analyze_code" and "code_analyzer" in self.tools:
            return self.invoke_tool(
                "code_analyzer",
                file_path=params.get("file_path"),
                language=params.get("language", "python"),
                analysis_type=params.get("analysis_type", "all")
            )

        elif action == "search_content" and "grep" in self.tools:
            return self.invoke_tool(
                "grep",
                pattern=params.get("pattern"),
                path=params.get("path")
            )

        elif action == "find_files" and "glob" in self.tools:
            return self.invoke_tool(
                "glob",
                pattern=params.get("pattern"),
                directory=params.get("directory", ".")
            )

        elif action in self.tools:
            return self.invoke_tool(action, **params)

        return {"simulated": True, "action": action, "params": params}


class PlannerAgent(BaseAgent):
    """Agent specialized in breaking down complex tasks."""

    def execute(self, task: AgentTask) -> Any:
        action = task.action
        params = task.params

        if action == "decompose_task":
            return self._decompose_task(params.get("task_description", ""))

        elif action == "create_plan":
            return self._create_plan(
                params.get("goal", ""),
                params.get("constraints", [])
            )

        return {"simulated": True, "action": action, "params": params}

    def _decompose_task(self, description: str) -> Dict[str, Any]:
        """Decompose a complex task into subtasks."""
        return {
            "original_task": description,
            "subtasks": [
                {"name": "analyze", "description": "Analyze requirements"},
                {"name": "design", "description": "Design solution"},
                {"name": "implement", "description": "Implement solution"},
                {"name": "test", "description": "Test implementation"},
                {"name": "review", "description": "Review and refine"}
            ],
            "estimated_steps": 5
        }

    def _create_plan(self, goal: str, constraints: List[str]) -> Dict[str, Any]:
        """Create an execution plan for a goal."""
        return {
            "goal": goal,
            "constraints": constraints,
            "steps": [
                {"order": 1, "action": "gather_requirements"},
                {"order": 2, "action": "analyze_scope"},
                {"order": 3, "action": "design_solution"},
                {"order": 4, "action": "execute_plan"},
                {"order": 5, "action": "validate_results"}
            ]
        }


class ReviewerAgent(BaseAgent):
    """Agent specialized in reviewing code and outputs."""

    def execute(self, task: AgentTask) -> Any:
        action = task.action
        params = task.params

        if action == "review_code" and "code_analyzer" in self.tools:
            analysis = self.invoke_tool(
                "code_analyzer",
                file_path=params.get("file_path"),
                language=params.get("language", "python"),
                analysis_type="all"
            )
            return self._format_review(analysis)

        elif action == "run_tests" and "test_runner" in self.tools:
            return self.invoke_tool(
                "test_runner",
                test_path=params.get("test_path"),
                framework=params.get("framework", "pytest")
            )

        return {"simulated": True, "action": action, "params": params}

    def _format_review(self, analysis: Any) -> Dict[str, Any]:
        """Format analysis results as a code review."""
        if hasattr(analysis, 'data'):
            data = analysis.data
        else:
            data = analysis

        return {
            "review_type": "automated",
            "quality_score": data.get("metrics", {}).get("quality_score", 0),
            "issues_found": len(data.get("issues", [])),
            "issues": data.get("issues", []),
            "recommendations": data.get("recommendations", []),
            "approved": data.get("metrics", {}).get("quality_score", 0) >= 70
        }


class AgentRegistry:
    """Registry for managing agent types."""

    _agents: Dict[str, Type[BaseAgent]] = {
        "task-executor": TaskExecutorAgent,
        "researcher": ResearcherAgent,
        "planner": PlannerAgent,
        "reviewer": ReviewerAgent,
    }

    @classmethod
    def register(cls, agent_type: str, agent_class: Type[BaseAgent]):
        """Register a new agent type."""
        cls._agents[agent_type] = agent_class

    @classmethod
    def get(cls, agent_type: str) -> Optional[Type[BaseAgent]]:
        """Get an agent class by type."""
        return cls._agents.get(agent_type)

    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered agent types."""
        return list(cls._agents.keys())


class AgentOrchestrator:
    """
    Orchestrates multiple agents to accomplish complex tasks.
    Handles agent lifecycle, task distribution, and coordination.
    """

    def __init__(
        self,
        agents_dir: str = "./agents",
        tools: Optional[Dict[str, Callable]] = None,
        logger: Optional[Any] = None,
        max_concurrent_tasks: int = 4
    ):
        self.agents_dir = Path(agents_dir)
        self.tools = tools or {}
        self.logger = logger
        self.max_concurrent_tasks = max_concurrent_tasks
        
        self._agents: Dict[str, BaseAgent] = {}
        self._task_queue: Queue = Queue()
        self._results: Dict[str, AgentTask] = {}
        self._lock = threading.Lock()
        self._running = False
        self._workers: List[threading.Thread] = []

    def load_agents(self) -> int:
        """Load all agent configurations from the agents directory."""
        loaded = 0
        
        for config_file in self.agents_dir.glob("*.json"):
            if config_file.name.startswith("example-") or config_file.name.endswith("-schema.json"):
                try:
                    config = AgentConfig.from_file(str(config_file))
                    self.register_agent(config)
                    loaded += 1
                except Exception as e:
                    if self.logger:
                        self.logger.log_error("orchestrator", e, {"file": str(config_file)})

        return loaded

    def register_agent(self, config: AgentConfig) -> BaseAgent:
        """Register an agent from configuration."""
        agent_class = AgentRegistry.get(config.agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {config.agent_type}")

        # Filter tools for this agent
        agent_tools = {name: tool for name, tool in self.tools.items() if name in config.tools}
        
        agent = agent_class(config, agent_tools)
        self._agents[config.name] = agent
        
        if self.logger:
            self.logger.log_agent_action(
                config.name,
                "registered",
                {"type": config.agent_type, "capabilities": config.capabilities}
            )
        
        return agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their status."""
        return [agent.get_stats() for agent in self._agents.values()]

    def find_agent_for_task(self, action: str) -> Optional[BaseAgent]:
        """Find an available agent that can handle a specific action."""
        for agent in self._agents.values():
            if agent.status == AgentStatus.IDLE and agent.can_handle(action):
                return agent
        return None

    def submit_task(
        self,
        name: str,
        action: str,
        params: Dict[str, Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        agent_name: Optional[str] = None,
        timeout_seconds: int = 300
    ) -> str:
        """Submit a task for execution."""
        task = AgentTask(
            id=str(uuid.uuid4()),
            name=name,
            action=action,
            params=params,
            priority=priority,
            timeout_seconds=timeout_seconds,
            assigned_agent=agent_name
        )
        
        self._task_queue.put((priority.value, task))
        
        if self.logger:
            self.logger.log_agent_action(
                "orchestrator",
                "task_submitted",
                {"task_id": task.id, "action": action}
            )
        
        return task.id

    def execute_task(
        self,
        name: str,
        action: str,
        params: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> AgentTask:
        """Execute a task synchronously."""
        task = AgentTask(
            id=str(uuid.uuid4()),
            name=name,
            action=action,
            params=params,
            assigned_agent=agent_name
        )

        # Find or use specified agent
        if agent_name:
            agent = self.get_agent(agent_name)
            if not agent:
                task.status = "failed"
                task.error = f"Agent not found: {agent_name}"
                return task
        else:
            agent = self.find_agent_for_task(action)
            if not agent:
                task.status = "failed"
                task.error = f"No available agent for action: {action}"
                return task

        # Execute task
        return agent.run_task(task)

    def start(self):
        """Start the orchestrator's background workers."""
        if self._running:
            return

        self._running = True
        
        for i in range(self.max_concurrent_tasks):
            worker = threading.Thread(target=self._worker_loop, name=f"worker-{i}")
            worker.daemon = True
            worker.start()
            self._workers.append(worker)

    def stop(self):
        """Stop the orchestrator's background workers."""
        self._running = False
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=5)
        
        self._workers.clear()

    def _worker_loop(self):
        """Background worker loop for processing tasks."""
        while self._running:
            try:
                _, task = self._task_queue.get(timeout=1)
            except Empty:
                continue

            # Find agent
            if task.assigned_agent:
                agent = self.get_agent(task.assigned_agent)
            else:
                agent = self.find_agent_for_task(task.action)

            if agent:
                try:
                    agent.run_task(task)
                except Exception as e:
                    task.status = "failed"
                    task.error = str(e)
            else:
                task.status = "failed"
                task.error = f"No agent available for: {task.action}"

            with self._lock:
                self._results[task.id] = task

    def get_result(self, task_id: str) -> Optional[AgentTask]:
        """Get the result of a submitted task."""
        with self._lock:
            return self._results.get(task_id)

    def delegate(
        self,
        goal: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        High-level delegation: orchestrator decides how to accomplish a goal.
        This is a simplified implementation showing the pattern.
        """
        context = context or {}
        
        # Use planner agent if available
        planner = None
        for agent in self._agents.values():
            if agent.agent_type == "planner":
                planner = agent
                break

        if planner:
            # Get plan from planner
            plan_task = AgentTask(
                id=str(uuid.uuid4()),
                name="create_plan",
                action="create_plan",
                params={"goal": goal, "constraints": context.get("constraints", [])}
            )
            plan_result = planner.run_task(plan_task)
            
            if plan_result.status == "completed":
                return {
                    "goal": goal,
                    "plan": plan_result.result,
                    "status": "planned"
                }

        return {
            "goal": goal,
            "error": "Could not create execution plan",
            "status": "failed"
        }

    def coordinate_workflow(
        self,
        workflow: Dict[str, Any],
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordinate a workflow by assigning steps to appropriate agents.
        """
        from .workflow_engine import WorkflowEngine
        
        engine = WorkflowEngine(
            agents=self._agents,
            tools=self.tools,
            logger=self.logger
        )
        
        result = engine.execute(workflow, inputs)
        return result.to_dict()
