"""
Agent Orchestration System for the agentic workspace.

Provides agent lifecycle management, capability-based routing,
multi-agent coordination, and intelligent task delegation.
"""
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Lifecycle state of an agent."""
    UNINITIALIZED = "uninitialized"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentCapability(Enum):
    """Standard agent capabilities."""
    CODE_EXECUTION = "code-execution"
    FILE_MANAGEMENT = "file-management"
    COMMAND_EXECUTION = "command-execution"
    TEXT_PROCESSING = "text-processing"
    CODEBASE_ANALYSIS = "codebase-analysis"
    DOCUMENTATION_RESEARCH = "documentation-research"
    INFORMATION_GATHERING = "information-gathering"
    PATTERN_RECOGNITION = "pattern-recognition"
    TASK_PLANNING = "task-planning"
    CODE_REVIEW = "code-review"
    SECURITY_ANALYSIS = "security-analysis"
    WORKFLOW_COORDINATION = "workflow-coordination"


@dataclass
class AgentConfig:
    """Configuration for an agent instance."""
    name: str
    agent_type: str
    version: str
    description: str = ""
    model_provider: str = "anthropic"
    model_name: str = "claude-sonnet-4-5-20250929"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create config from dictionary."""
        model = data.get("model", {})
        return cls(
            name=data["name"],
            agent_type=data["type"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            model_provider=model.get("provider", "anthropic"),
            model_name=model.get("name", "claude-sonnet-4-5-20250929"),
            temperature=model.get("temperature", 0.7),
            max_tokens=model.get("max_tokens", 4096),
            tools=data.get("tools", []),
            capabilities=data.get("capabilities", []),
            dependencies=data.get("dependencies", []),
            config=data.get("config", {})
        )
    
    @classmethod
    def from_file(cls, path: str) -> "AgentConfig":
        """Load config from JSON file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


@dataclass
class TaskContext:
    """Context information passed to agent during task execution."""
    task_id: str
    workflow_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TaskResult:
    """Result from an agent task execution."""
    task_id: str
    agent_name: str
    status: str  # "success", "failure", "timeout", "cancelled"
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time_ms": self.execution_time_ms,
            "tool_calls": self.tool_calls
        }


class BaseAgent:
    """
    Base class for all agents.
    
    Agents are autonomous units that can execute tasks using configured tools
    and capabilities. This class provides the foundation for agent lifecycle
    management and task execution.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.UNINITIALIZED
        self._lock = threading.Lock()
        self._current_task: Optional[TaskContext] = None
        self._tool_registry = None
        self._execution_history: List[TaskResult] = []
    
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def capabilities(self) -> List[str]:
        return self.config.capabilities
    
    @property
    def tools(self) -> List[str]:
        return self.config.tools
    
    def initialize(self, tool_registry=None) -> bool:
        """
        Initialize the agent and prepare for task execution.
        
        Returns:
            True if initialization successful
        """
        with self._lock:
            if self.state != AgentState.UNINITIALIZED:
                logger.warning(f"Agent {self.name} already initialized")
                return True
            
            try:
                self._tool_registry = tool_registry
                self._validate_tools()
                self.state = AgentState.READY
                logger.info(f"Agent {self.name} initialized successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize agent {self.name}: {e}")
                self.state = AgentState.ERROR
                return False
    
    def _validate_tools(self) -> None:
        """Validate that all required tools are available."""
        if self._tool_registry is None:
            return
        
        available_tools = set(self._tool_registry.list_tools())
        required_tools = set(self.config.tools)
        missing = required_tools - available_tools
        
        if missing:
            raise ValueError(f"Missing required tools: {missing}")
    
    def execute(self, action: str, context: TaskContext) -> TaskResult:
        """
        Execute a task with the given action and context.
        
        Args:
            action: The action to perform
            context: Task context with inputs and metadata
            
        Returns:
            TaskResult with execution outcome
        """
        with self._lock:
            if self.state != AgentState.READY:
                return TaskResult(
                    task_id=context.task_id,
                    agent_name=self.name,
                    status="failure",
                    error=f"Agent not ready (state: {self.state.value})"
                )
            
            self.state = AgentState.BUSY
            self._current_task = context
        
        result = TaskResult(
            task_id=context.task_id,
            agent_name=self.name,
            status="success",
            started_at=datetime.utcnow().isoformat()
        )
        
        start_time = time.time()
        
        try:
            output = self._perform_action(action, context)
            result.output = output
            result.status = "success"
        except TimeoutError as e:
            result.status = "timeout"
            result.error = str(e)
        except Exception as e:
            logger.exception(f"Agent {self.name} failed executing {action}")
            result.status = "failure"
            result.error = str(e)
        finally:
            result.completed_at = datetime.utcnow().isoformat()
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            with self._lock:
                self.state = AgentState.READY
                self._current_task = None
                self._execution_history.append(result)
        
        return result
    
    def _perform_action(self, action: str, context: TaskContext) -> Any:
        """
        Perform the actual action. Override in subclasses for specific behavior.
        
        Default implementation routes to tool execution.
        """
        # Default behavior: try to find and execute a matching tool
        if self._tool_registry:
            tool = self._tool_registry.get(action)
            if tool:
                result = tool.run(**context.inputs)
                if result.is_success():
                    return result.data
                else:
                    raise RuntimeError(result.error)
        
        raise NotImplementedError(f"Action '{action}' not implemented")
    
    def terminate(self) -> None:
        """Terminate the agent and clean up resources."""
        with self._lock:
            self.state = AgentState.TERMINATED
            self._current_task = None
            logger.info(f"Agent {self.name} terminated")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        successful = sum(1 for r in self._execution_history if r.status == "success")
        failed = sum(1 for r in self._execution_history if r.status == "failure")
        total_time = sum(r.execution_time_ms for r in self._execution_history)
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_tasks": len(self._execution_history),
            "successful_tasks": successful,
            "failed_tasks": failed,
            "success_rate": successful / len(self._execution_history) if self._execution_history else 0,
            "total_execution_time_ms": total_time,
            "average_execution_time_ms": total_time / len(self._execution_history) if self._execution_history else 0
        }


class TaskExecutorAgent(BaseAgent):
    """Agent specialized for executing code, commands, and file operations."""
    
    def _perform_action(self, action: str, context: TaskContext) -> Any:
        """Execute task-oriented actions."""
        action_map = {
            "read_file": "read",
            "write_file": "write",
            "edit_file": "edit",
            "find_files": "glob",
            "search_files": "grep",
            "run_command": "bash",
            "run_tests": "test_runner",
        }
        
        tool_name = action_map.get(action, action)
        
        if self._tool_registry:
            tool = self._tool_registry.get(tool_name)
            if tool:
                result = tool.run(**context.inputs)
                if result.is_success():
                    return result.data
                else:
                    raise RuntimeError(f"Tool execution failed: {result.error}")
        
        return super()._perform_action(action, context)


class ResearcherAgent(BaseAgent):
    """Agent specialized for information gathering and analysis."""
    
    def _perform_action(self, action: str, context: TaskContext) -> Any:
        """Execute research-oriented actions."""
        if action == "analyze_code":
            return self._analyze_code(context.inputs)
        elif action == "gather_information":
            return self._gather_information(context.inputs)
        elif action == "generate_review_summary":
            return self._generate_summary(context.inputs)
        
        return super()._perform_action(action, context)
    
    def _analyze_code(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code files for patterns and issues."""
        if self._tool_registry:
            analyzer = self._tool_registry.get("code_analyzer")
            if analyzer:
                files = inputs.get("files", [])
                results = []
                for file_path in files:
                    result = analyzer.run(file_path=file_path, analysis_type="all")
                    if result.is_success():
                        results.append(result.data)
                return {"analyses": results, "files_analyzed": len(results)}
        
        return {"error": "Code analyzer not available"}
    
    def _gather_information(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Gather information from various sources."""
        # Placeholder for information gathering logic
        return {"gathered": True, "sources": inputs.get("sources", [])}
    
    def _generate_summary(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary from analysis results."""
        analysis = inputs.get("analysis_results", {})
        test_results = inputs.get("test_results", {})
        
        return {
            "summary": "Analysis complete",
            "issues_found": len(analysis.get("analyses", [])),
            "tests_passed": test_results.get("passed", 0)
        }


class AgentFactory:
    """Factory for creating agent instances."""
    
    _agent_types: Dict[str, Type[BaseAgent]] = {
        "task-executor": TaskExecutorAgent,
        "researcher": ResearcherAgent,
        "planner": BaseAgent,
        "reviewer": BaseAgent,
        "coordinator": BaseAgent,
    }
    
    @classmethod
    def register_type(cls, type_name: str, agent_class: Type[BaseAgent]) -> None:
        """Register a custom agent type."""
        cls._agent_types[type_name] = agent_class
    
    @classmethod
    def create(cls, config: AgentConfig) -> BaseAgent:
        """Create an agent instance from configuration."""
        agent_class = cls._agent_types.get(config.agent_type, BaseAgent)
        return agent_class(config)
    
    @classmethod
    def create_from_file(cls, path: str) -> BaseAgent:
        """Create an agent from a configuration file."""
        config = AgentConfig.from_file(path)
        return cls.create(config)


class AgentOrchestrator:
    """
    Central orchestrator for managing and coordinating multiple agents.
    
    Provides:
    - Agent lifecycle management
    - Capability-based task routing
    - Multi-agent coordination
    - Load balancing
    - Health monitoring
    """
    
    def __init__(self, max_concurrent_tasks: int = 4):
        self._agents: Dict[str, BaseAgent] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> agent names
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        self._tool_registry = None
    
    def set_tool_registry(self, registry) -> None:
        """Set the tool registry for agent initialization."""
        self._tool_registry = registry
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: The agent to register
            
        Returns:
            True if registration successful
        """
        with self._lock:
            if agent.name in self._agents:
                logger.warning(f"Agent {agent.name} already registered, replacing")
            
            # Initialize agent
            if not agent.initialize(self._tool_registry):
                return False
            
            self._agents[agent.name] = agent
            
            # Index capabilities
            for capability in agent.capabilities:
                if capability not in self._capability_index:
                    self._capability_index[capability] = set()
                self._capability_index[capability].add(agent.name)
            
            logger.info(f"Registered agent: {agent.name}")
            return True
    
    def register_from_config(self, config: AgentConfig) -> bool:
        """Register an agent from configuration."""
        agent = AgentFactory.create(config)
        return self.register_agent(agent)
    
    def register_from_file(self, path: str) -> bool:
        """Register an agent from a configuration file."""
        config = AgentConfig.from_file(path)
        return self.register_from_config(config)
    
    def register_from_directory(self, directory: str, pattern: str = "*.json") -> int:
        """
        Register all agents from configuration files in a directory.
        
        Returns:
            Number of agents successfully registered
        """
        dir_path = Path(directory)
        count = 0
        
        for config_file in dir_path.glob(pattern):
            if config_file.name.startswith("example-") or config_file.name.endswith(".schema.json"):
                continue
            
            try:
                if self.register_from_file(str(config_file)):
                    count += 1
            except Exception as e:
                logger.error(f"Failed to register agent from {config_file}: {e}")
        
        return count
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def find_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Find all agents that have a specific capability."""
        agent_names = self._capability_index.get(capability, set())
        return [self._agents[name] for name in agent_names if name in self._agents]
    
    def select_agent(self, 
                     required_capabilities: Optional[List[str]] = None,
                     preferred_agent: Optional[str] = None) -> Optional[BaseAgent]:
        """
        Select the best available agent for a task.
        
        Args:
            required_capabilities: Capabilities the agent must have
            preferred_agent: Name of preferred agent
            
        Returns:
            Selected agent or None if no suitable agent found
        """
        # Try preferred agent first
        if preferred_agent and preferred_agent in self._agents:
            agent = self._agents[preferred_agent]
            if agent.state == AgentState.READY:
                if not required_capabilities or all(
                    cap in agent.capabilities for cap in required_capabilities
                ):
                    return agent
        
        # Find agents with required capabilities
        candidates = list(self._agents.values())
        
        if required_capabilities:
            candidates = [
                a for a in candidates
                if all(cap in a.capabilities for cap in required_capabilities)
            ]
        
        # Filter by ready state
        ready_candidates = [a for a in candidates if a.state == AgentState.READY]
        
        if not ready_candidates:
            return None
        
        # Select agent with best success rate
        return max(ready_candidates, key=lambda a: a.get_stats().get("success_rate", 0))
    
    def execute_task(self,
                     agent_name: str,
                     action: str,
                     inputs: Dict[str, Any],
                     task_id: Optional[str] = None,
                     timeout_seconds: int = 300) -> TaskResult:
        """
        Execute a task on a specific agent.
        
        Args:
            agent_name: Name of the agent to use
            action: Action to perform
            inputs: Input parameters
            task_id: Optional task identifier
            timeout_seconds: Maximum execution time
            
        Returns:
            TaskResult with execution outcome
        """
        agent = self.get_agent(agent_name)
        
        if not agent:
            return TaskResult(
                task_id=task_id or f"task-{time.time()}",
                agent_name=agent_name,
                status="failure",
                error=f"Agent not found: {agent_name}"
            )
        
        context = TaskContext(
            task_id=task_id or f"task-{time.time()}",
            inputs=inputs,
            timeout_seconds=timeout_seconds
        )
        
        return agent.execute(action, context)
    
    def delegate_task(self,
                      action: str,
                      inputs: Dict[str, Any],
                      required_capabilities: Optional[List[str]] = None,
                      task_id: Optional[str] = None) -> TaskResult:
        """
        Delegate a task to the best available agent.
        
        Args:
            action: Action to perform
            inputs: Input parameters
            required_capabilities: Required agent capabilities
            task_id: Optional task identifier
            
        Returns:
            TaskResult with execution outcome
        """
        agent = self.select_agent(required_capabilities=required_capabilities)
        
        if not agent:
            return TaskResult(
                task_id=task_id or f"task-{time.time()}",
                agent_name="none",
                status="failure",
                error=f"No suitable agent found for capabilities: {required_capabilities}"
            )
        
        return self.execute_task(agent.name, action, inputs, task_id)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        return {
            "agents": {name: agent.get_stats() for name, agent in self._agents.items()},
            "total_agents": len(self._agents),
            "ready_agents": sum(1 for a in self._agents.values() if a.state == AgentState.READY),
            "capabilities": {cap: list(agents) for cap, agents in self._capability_index.items()}
        }
    
    def shutdown(self) -> None:
        """Shutdown all agents and the orchestrator."""
        logger.info("Shutting down orchestrator")
        
        for agent in self._agents.values():
            agent.terminate()
        
        self._executor.shutdown(wait=True)
        logger.info("Orchestrator shutdown complete")
