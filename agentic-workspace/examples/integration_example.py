#!/usr/bin/env python3
"""
Valtheron Agentic Workspace - Integration Example

This script demonstrates the complete integration of all components:
- Tool registry and execution
- Agent orchestration
- Workflow engine
- Logging and metrics

Run from the agentic-workspace directory:
    python examples/integration_example.py
"""
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    ConfigLoader,
    AgenticLogger,
    WorkflowEngine,
    AgentOrchestrator,
    AgentConfig,
    AgentFactory,
)


def main():
    """Demonstrate full workspace integration."""
    print("=" * 60)
    print("Valtheron Agentic Workspace - Integration Demo")
    print("=" * 60)
    print()
    
    # 1. Initialize logging
    print("[1] Initializing logger...")
    logger = AgenticLogger(log_dir="../logs", json_format=False)
    logger.log_agent_action("system", "initialization", {"status": "starting"})
    print("    ✓ Logger initialized")
    print()
    
    # 2. Load configuration
    print("[2] Loading workspace configuration...")
    try:
        config = ConfigLoader.load_workspace_config("..")
        print(f"    ✓ Workspace: {config['workspace']['name']}")
        print(f"    ✓ Version: {config['workspace']['version']}")
    except FileNotFoundError:
        print("    ! Configuration not found, using defaults")
        config = {"workspace": {"name": "demo", "version": "1.0.0"}}
    print()
    
    # 3. Initialize tool registry
    print("[3] Loading tool registry...")
    try:
        from tools.implementations import get_registry, list_available_tools
        registry = get_registry()
        tools = list_available_tools()
        print(f"    ✓ Registered tools: {', '.join(tools)}")
    except ImportError as e:
        print(f"    ! Could not load tools: {e}")
        registry = None
    print()
    
    # 4. Initialize agent orchestrator
    print("[4] Initializing agent orchestrator...")
    orchestrator = AgentOrchestrator(max_concurrent_tasks=4)
    
    if registry:
        orchestrator.set_tool_registry(registry)
    
    # Register example agents
    agent_configs = [
        AgentConfig(
            name="demo-executor",
            agent_type="task-executor",
            version="1.0.0",
            description="Demo task executor",
            tools=["read", "write", "bash"],
            capabilities=["code-execution", "file-management"]
        ),
        AgentConfig(
            name="demo-researcher",
            agent_type="researcher",
            version="1.0.0",
            description="Demo researcher",
            tools=["read", "grep", "glob", "code_analyzer"],
            capabilities=["codebase-analysis", "pattern-recognition"]
        )
    ]
    
    for agent_config in agent_configs:
        if orchestrator.register_from_config(agent_config):
            print(f"    ✓ Registered agent: {agent_config.name}")
    print()
    
    # 5. Demo tool execution
    print("[5] Demonstrating tool execution...")
    if registry:
        # Test the glob tool
        result = registry.execute("glob", pattern="*.py", base_path=".")
        if result.is_success():
            print(f"    ✓ Found {result.data['count']} Python files")
        else:
            print(f"    ! Tool error: {result.error}")
    print()
    
    # 6. Demo agent task execution
    print("[6] Demonstrating agent task execution...")
    task_result = orchestrator.execute_task(
        agent_name="demo-executor",
        action="read",
        inputs={"file_path": "../README.md"},
        task_id="demo-task-001"
    )
    
    if task_result.status == "success":
        content = task_result.output.get("content", "") if task_result.output else ""
        print(f"    ✓ Read file: {len(content)} characters")
    else:
        print(f"    ! Task failed: {task_result.error}")
    print()
    
    # 7. Initialize workflow engine
    print("[7] Initializing workflow engine...")
    
    def agent_executor(agent: str, action: str, params: dict):
        result = orchestrator.execute_task(agent, action, params)
        if result.status == "success":
            return result.output
        raise RuntimeError(result.error or "Execution failed")
    
    workflow_engine = WorkflowEngine(
        agent_executor=agent_executor,
        max_workers=4
    )
    print("    ✓ Workflow engine ready")
    print()
    
    # 8. Demo workflow execution
    print("[8] Executing demo workflow...")
    demo_workflow = {
        "name": "demo-workflow",
        "version": "1.0.0",
        "description": "Demonstration workflow",
        "inputs": {
            "target_path": {"type": "string", "required": False}
        },
        "steps": [
            {
                "name": "find-files",
                "agent": "demo-executor",
                "action": "glob",
                "params": {
                    "pattern": "*.md",
                    "base_path": ".."
                }
            },
            {
                "name": "report",
                "agent": "demo-researcher",
                "action": "gather_information",
                "params": {
                    "sources": ["${steps.find-files.output}"]
                },
                "depends_on": ["find-files"]
            }
        ]
    }
    
    workflow_result = workflow_engine.execute(demo_workflow, inputs={})
    
    print(f"    Status: {workflow_result.status.value}")
    for step_name, step_result in workflow_result.steps.items():
        status_icon = "✓" if step_result.status.value == "completed" else "✗"
        print(f"    {status_icon} Step '{step_name}': {step_result.status.value}")
    print(f"    Total time: {workflow_result.total_execution_time_ms:.2f}ms")
    print()
    
    # 9. Show metrics
    print("[9] Metrics summary:")
    metrics = logger.get_metrics_summary()
    for metric_name, summary in metrics.items():
        if summary:
            print(f"    {metric_name}: {summary.get('count', 0)} events")
    print()
    
    # 10. Cleanup
    print("[10] Cleanup...")
    orchestrator.shutdown()
    print("    ✓ Orchestrator shutdown complete")
    print()
    
    print("=" * 60)
    print("Integration demo completed successfully!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
