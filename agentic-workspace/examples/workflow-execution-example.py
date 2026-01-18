"""
Example of loading and executing a workflow
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import ConfigLoader
from utils.logger import AgenticLogger


class SimpleWorkflowExecutor:
    """Simple workflow executor for demonstration"""

    def __init__(self, workflow_config: Dict[str, Any]):
        self.config = workflow_config
        self.logger = AgenticLogger(log_dir="../logs")
        self.results = {}

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the workflow"""
        workflow_name = self.config['name']

        self.logger.log_workflow_start(workflow_name, inputs)

        print(f"\n{'='*60}")
        print(f"Executing Workflow: {workflow_name}")
        print(f"Version: {self.config['version']}")
        print(f"Description: {self.config['description']}")
        print(f"{'='*60}\n")

        try:
            # Execute each step
            for step in self.config['steps']:
                self._execute_step(step, inputs)

            print(f"\n{'='*60}")
            print(f"Workflow completed successfully!")
            print(f"{'='*60}\n")

            self.logger.log_workflow_end(workflow_name, "success", self.results)
            return self.results

        except Exception as e:
            print(f"\nWorkflow failed: {e}")
            self.logger.log_workflow_end(workflow_name, "failed", {"error": str(e)})
            raise

    def _execute_step(self, step: Dict[str, Any], inputs: Dict[str, Any]):
        """Execute a single workflow step"""
        step_name = step['name']
        agent = step['agent']
        action = step['action']

        print(f"Step: {step_name}")
        print(f"  Agent: {agent}")
        print(f"  Action: {action}")

        # Check dependencies
        if 'depends_on' in step:
            print(f"  Dependencies: {', '.join(step['depends_on'])}")
            for dep in step['depends_on']:
                if dep not in self.results:
                    raise Exception(f"Dependency not met: {dep}")

        # Log step start
        self.logger.log_agent_action(
            agent,
            f"step_start: {step_name}",
            {"action": action}
        )

        # Simulate step execution
        # In a real implementation, this would invoke the actual agent
        print(f"  Status: Executing...")

        # Store mock result
        self.results[step_name] = {
            "status": "completed",
            "output": f"Result from {step_name}"
        }

        print(f"  Status: Completed ✓\n")

        # Log step completion
        self.logger.log_agent_action(
            agent,
            f"step_complete: {step_name}",
            {"status": "success"}
        )


def main():
    """Demonstrate workflow execution"""

    # Load workflow configuration
    workflow_path = "../workflows/example-data-pipeline.json"

    try:
        config = ConfigLoader.load_json(workflow_path)

        # Create executor
        executor = SimpleWorkflowExecutor(config)

        # Define workflow inputs
        inputs = {
            "input_file": "./data/sample_data.csv",
            "output_dir": "./data/processed"
        }

        # Execute workflow
        results = executor.execute(inputs)

        print("Final Results:")
        for step_name, result in results.items():
            print(f"  {step_name}: {result['status']}")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
