"""
Agentic Workspace Utilities.

This package provides the core infrastructure for the agentic workspace:
- Configuration loading and validation
- Structured logging with metrics
- Workflow engine with dependency management
- Agent orchestration and coordination
"""
from .config_loader import ConfigLoader
from .logger import AgenticLogger, get_logger, MetricsCollector
from .workflow_engine import (
    WorkflowEngine,
    WorkflowResult,
    WorkflowStatus,
    StepResult,
    StepStatus,
    VariableResolver,
    DependencyResolver,
    load_workflow,
)
from .agent_orchestrator import (
    AgentOrchestrator,
    BaseAgent,
    TaskExecutorAgent,
    ResearcherAgent,
    AgentFactory,
    AgentConfig,
    AgentState,
    TaskContext,
    TaskResult,
)

__all__ = [
    # Config
    "ConfigLoader",
    
    # Logging
    "AgenticLogger",
    "get_logger",
    "MetricsCollector",
    
    # Workflow
    "WorkflowEngine",
    "WorkflowResult",
    "WorkflowStatus",
    "StepResult",
    "StepStatus",
    "VariableResolver",
    "DependencyResolver",
    "load_workflow",
    
    # Agents
    "AgentOrchestrator",
    "BaseAgent",
    "TaskExecutorAgent",
    "ResearcherAgent",
    "AgentFactory",
    "AgentConfig",
    "AgentState",
    "TaskContext",
    "TaskResult",
]


def create_workspace(workspace_dir: str = ".") -> dict:
    """
    Initialize and return a complete workspace setup.
    
    Args:
        workspace_dir: Root directory of the workspace
        
    Returns:
        Dictionary containing initialized components
    """
    from pathlib import Path
    import sys
    
    # Add tools to path
    tools_path = Path(workspace_dir) / "tools" / "implementations"
    if str(tools_path) not in sys.path:
        sys.path.insert(0, str(tools_path))
    
    # Load configuration
    config = ConfigLoader.load_workspace_config(workspace_dir)
    
    # Initialize logger
    log_dir = Path(workspace_dir) / config.get("paths", {}).get("logs", "./logs")
    logger = get_logger(str(log_dir))
    
    # Import and get tool registry
    try:
        from tools.implementations import get_registry
        tool_registry = get_registry()
    except ImportError:
        tool_registry = None
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        max_concurrent_tasks=config.get("execution", {}).get("parallel_max_workers", 4)
    )
    
    if tool_registry:
        orchestrator.set_tool_registry(tool_registry)
    
    # Initialize workflow engine
    def agent_executor(agent_name: str, action: str, params: dict):
        result = orchestrator.execute_task(agent_name, action, params)
        if result.status == "success":
            return result.output
        raise RuntimeError(result.error or "Task execution failed")
    
    workflow_engine = WorkflowEngine(
        agent_executor=agent_executor,
        max_workers=config.get("execution", {}).get("parallel_max_workers", 4)
    )
    
    return {
        "config": config,
        "logger": logger,
        "tool_registry": tool_registry,
        "orchestrator": orchestrator,
        "workflow_engine": workflow_engine,
    }
