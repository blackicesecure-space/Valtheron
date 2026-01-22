"""
Agentic Workspace Utilities Package.
Provides core utilities for agent operations, workflows, and orchestration.
"""
from .config_loader import ConfigLoader
from .logger import AgenticLogger
from .workflow_engine import (
    WorkflowEngine,
    WorkflowResult,
    WorkflowStatus,
    StepResult,
    ErrorStrategy,
    VariableResolver,
    DependencyGraph,
    execute_workflow_async
)
from .agent_orchestrator import (
    AgentOrchestrator,
    BaseAgent,
    TaskExecutorAgent,
    ResearcherAgent,
    PlannerAgent,
    ReviewerAgent,
    AgentRegistry,
    AgentConfig,
    AgentTask,
    AgentStatus,
    TaskPriority,
    AgentCapability
)

__all__ = [
    # Config and logging
    "ConfigLoader",
    "AgenticLogger",
    
    # Workflow engine
    "WorkflowEngine",
    "WorkflowResult",
    "WorkflowStatus",
    "StepResult",
    "ErrorStrategy",
    "VariableResolver",
    "DependencyGraph",
    "execute_workflow_async",
    
    # Agent orchestration
    "AgentOrchestrator",
    "BaseAgent",
    "TaskExecutorAgent",
    "ResearcherAgent",
    "PlannerAgent",
    "ReviewerAgent",
    "AgentRegistry",
    "AgentConfig",
    "AgentTask",
    "AgentStatus",
    "TaskPriority",
    "AgentCapability",
]


def create_workspace(
    agents_dir: str = "./agents",
    tools_dir: str = "./tools",
    config_path: str = "./config/workspace.json"
) -> "AgentOrchestrator":
    """
    Create a fully configured workspace with agents and tools.
    
    Args:
        agents_dir: Path to agent configurations
        tools_dir: Path to tool definitions
        config_path: Path to workspace configuration
        
    Returns:
        Configured AgentOrchestrator instance
    """
    from pathlib import Path
    
    # Load workspace config
    config = ConfigLoader.load_json(config_path)
    
    # Initialize logger
    log_dir = config.get("paths", {}).get("logs", "./logs")
    logger = AgenticLogger(log_dir=log_dir)
    
    # Load tools
    tools = _load_tools(tools_dir)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        agents_dir=agents_dir,
        tools=tools,
        logger=logger,
        max_concurrent_tasks=config.get("execution", {}).get("parallel_max_workers", 4)
    )
    
    # Load agents
    orchestrator.load_agents()
    
    return orchestrator


def _load_tools(tools_dir: str) -> dict:
    """Load tool implementations."""
    tools = {}
    
    try:
        from tools.implementations import (
            CodeAnalyzerTool,
            TestRunnerTool,
            FileReadTool,
            FileWriteTool,
            FileSearchTool,
            GrepTool,
            FileEditTool
        )
        
        # Instantiate tools
        tool_instances = [
            CodeAnalyzerTool(),
            TestRunnerTool(),
            FileReadTool(),
            FileWriteTool(),
            FileSearchTool(),
            GrepTool(),
            FileEditTool()
        ]
        
        for tool in tool_instances:
            tools[tool.name] = tool
            
    except ImportError:
        pass
    
    return tools
