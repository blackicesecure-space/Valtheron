"""
Comprehensive example demonstrating the full agentic workspace.
Shows how agents, tools, workflows, and orchestration work together.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import ConfigLoader
from utils.logger import AgenticLogger
from utils.workflow_engine import WorkflowEngine, WorkflowStatus
from utils.agent_orchestrator import (
    AgentOrchestrator,
    AgentConfig,
    TaskPriority
)


def demo_tool_usage():
    """Demonstrate direct tool usage."""
    print("\n" + "="*60)
    print("1. DIRECT TOOL USAGE")
    print("="*60)
    
    try:
        from tools.implementations import CodeAnalyzerTool, FileReadTool
        
        # Analyze some Python code
        analyzer = CodeAnalyzerTool()
        
        sample_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        if item.price > 0:
            if item.quantity > 0:
                if item.discount:
                    total += item.price * item.quantity * (1 - item.discount)
                else:
                    total += item.price * item.quantity
    return total

password = "secret123"  # This should be flagged
'''
        
        result = analyzer(code=sample_code, language="python", analysis_type="all")
        
        print(f"\nCode Analysis Result:")
        print(f"  Status: {result.status.value}")
        print(f"  Quality Score: {result.data['metrics']['quality_score']}")
        print(f"  Cyclomatic Complexity: {result.data['metrics']['cyclomatic_complexity']}")
        print(f"  Issues Found: {len(result.data['issues'])}")
        
        for issue in result.data['issues'][:3]:
            print(f"    - [{issue['severity'].upper()}] {issue['message']}")
        
        if result.data['recommendations']:
            print(f"\n  Recommendations:")
            for rec in result.data['recommendations']:
                print(f"    • {rec}")
                
    except ImportError as e:
        print(f"  (Tools not available for demo: {e})")
        print("  In production, tools would analyze actual code.")


def demo_agent_orchestration():
    """Demonstrate agent orchestration."""
    print("\n" + "="*60)
    print("2. AGENT ORCHESTRATION")
    print("="*60)
    
    # Initialize logger
    logger = AgenticLogger(log_dir="../logs")
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        agents_dir="../agents",
        tools={},  # Tools would be loaded in production
        logger=logger
    )
    
    # Register agents from example configs
    task_executor_config = AgentConfig(
        name="task-executor-001",
        agent_type="task-executor",
        version="1.0.0",
        description="General purpose task executor",
        capabilities=["code-execution", "file-management"],
        tools=["bash", "read", "write", "edit"]
    )
    
    researcher_config = AgentConfig(
        name="researcher-001",
        agent_type="researcher",
        version="1.0.0",
        description="Research and analysis agent",
        capabilities=["codebase-analysis", "information-gathering"],
        tools=["read", "glob", "grep", "code_analyzer"]
    )
    
    planner_config = AgentConfig(
        name="planner-001",
        agent_type="planner",
        version="1.0.0",
        description="Task planning agent",
        capabilities=["task-decomposition", "planning"],
        tools=[]
    )
    
    orchestrator.register_agent(task_executor_config)
    orchestrator.register_agent(researcher_config)
    orchestrator.register_agent(planner_config)
    
    print(f"\nRegistered Agents:")
    for agent_info in orchestrator.list_agents():
        print(f"  • {agent_info['name']} ({agent_info['type']}) - {agent_info['status']}")
    
    # Execute a task
    print(f"\nExecuting Task: 'analyze_project'")
    task = orchestrator.execute_task(
        name="analyze_project",
        action="codebase-analysis",
        params={"path": "./src", "depth": "full"},
        agent_name="researcher-001"
    )
    
    print(f"  Task ID: {task.id}")
    print(f"  Status: {task.status}")
    print(f"  Assigned to: {task.assigned_agent}")
    
    # Use planner for high-level delegation
    print(f"\nDelegating Goal: 'Implement user authentication'")
    plan = orchestrator.delegate(
        goal="Implement user authentication",
        context={"constraints": ["Must use OAuth2", "Support MFA"]}
    )
    
    print(f"  Planning Status: {plan['status']}")
    if plan.get('plan'):
        print(f"  Generated Steps:")
        for step in plan['plan'].get('steps', [])[:3]:
            print(f"    {step['order']}. {step['action']}")


def demo_workflow_execution():
    """Demonstrate workflow execution."""
    print("\n" + "="*60)
    print("3. WORKFLOW EXECUTION")
    print("="*60)
    
    # Initialize
    logger = AgenticLogger(log_dir="../logs")
    engine = WorkflowEngine(
        agents={},
        tools={},
        max_workers=4,
        logger=logger
    )
    
    # Define a sample workflow
    workflow = {
        "name": "code-review-demo",
        "version": "1.0.0",
        "description": "Automated code review workflow",
        "steps": [
            {
                "name": "find-files",
                "agent": "task-executor-001",
                "action": "find_files",
                "params": {
                    "pattern": "${inputs.file_pattern}",
                    "directory": "${inputs.repository}"
                }
            },
            {
                "name": "analyze-code",
                "agent": "researcher-001",
                "action": "analyze_code",
                "params": {
                    "files": "${steps.find-files.output}"
                },
                "depends_on": ["find-files"]
            },
            {
                "name": "run-tests",
                "agent": "task-executor-001",
                "action": "run_tests",
                "params": {
                    "test_path": "${inputs.test_path}"
                },
                "depends_on": ["find-files"],
                "on_failure": "continue"
            },
            {
                "name": "generate-report",
                "agent": "researcher-001",
                "action": "generate_report",
                "params": {
                    "analysis": "${steps.analyze-code.output}",
                    "test_results": "${steps.run-tests.output}"
                },
                "depends_on": ["analyze-code", "run-tests"]
            }
        ],
        "error_handling": {
            "strategy": "partial-success"
        },
        "parallel": True
    }
    
    # Validate workflow
    errors = engine.validate_workflow(workflow)
    print(f"\nWorkflow Validation: {'✓ Valid' if not errors else '✗ Invalid'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # Execute workflow
    print(f"\nExecuting Workflow: '{workflow['name']}'")
    result = engine.execute(
        workflow=workflow,
        inputs={
            "repository": "./src",
            "file_pattern": "**/*.py",
            "test_path": "./tests"
        },
        parallel=True
    )
    
    print(f"\nWorkflow Result:")
    print(f"  Status: {result.status.value}")
    print(f"  Duration: {result.duration_ms:.2f}ms")
    print(f"  Success Rate: {result.success_rate:.1f}%")
    
    print(f"\n  Step Results:")
    for step_name, step_result in result.steps.items():
        status_icon = "✓" if step_result.status == WorkflowStatus.COMPLETED else "✗"
        print(f"    {status_icon} {step_name}: {step_result.status.value}")


def demo_full_pipeline():
    """Demonstrate a complete pipeline from configuration to execution."""
    print("\n" + "="*60)
    print("4. FULL PIPELINE DEMO")
    print("="*60)
    
    # Load workspace configuration
    try:
        workspace_config = ConfigLoader.load_json("../config/workspace.json")
        models_config = ConfigLoader.load_json("../config/models.json")
        
        print(f"\nWorkspace: {workspace_config['workspace']['name']} v{workspace_config['workspace']['version']}")
        print(f"Default Model: {models_config['preferences']['default_model']}")
        
        # Show model aliases
        print(f"\nAvailable Model Aliases:")
        for alias, model in models_config.get('model_aliases', {}).items():
            print(f"  • {alias} → {model}")
            
    except FileNotFoundError:
        print("\n  (Configuration files would be loaded in production)")
    
    print(f"\nPipeline Summary:")
    print(f"  1. Configuration loaded from JSON/YAML files")
    print(f"  2. Agents registered based on their type and capabilities")
    print(f"  3. Tools instantiated and made available to agents")
    print(f"  4. Workflows orchestrate multi-step processes")
    print(f"  5. Results aggregated and logged for monitoring")


def main():
    """Run all demonstrations."""
    print("="*60)
    print("AGENTIC WORKSPACE - COMPREHENSIVE DEMO")
    print("="*60)
    print("\nThis demo shows the key components of the agentic workspace")
    print("working together: tools, agents, workflows, and orchestration.")
    
    demo_tool_usage()
    demo_agent_orchestration()
    demo_workflow_execution()
    demo_full_pipeline()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("  • Tools provide atomic operations (file I/O, analysis, testing)")
    print("  • Agents combine tools with intelligence for specific roles")
    print("  • Workflows coordinate multiple agents across steps")
    print("  • The orchestrator manages the full lifecycle")
    print("\nSee the documentation in docs/ for more details.")
    
    return 0


if __name__ == "__main__":
    exit(main())
