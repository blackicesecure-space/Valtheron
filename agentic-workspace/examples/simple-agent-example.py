"""
Simple example of loading and using an agent configuration
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import ConfigLoader
from utils.logger import AgenticLogger


def main():
    """Demonstrate basic agent usage"""

    # Initialize logger
    logger = AgenticLogger(log_dir="../logs")
    logger.log_agent_action("example", "initialization", {"status": "started"})

    # Load agent configuration
    agent_config_path = "../agents/example-task-executor.json"

    try:
        config = ConfigLoader.load_json(agent_config_path)
        print(f"Loaded agent: {config['name']}")
        print(f"Type: {config['type']}")
        print(f"Version: {config['version']}")
        print(f"Description: {config['description']}")
        print(f"\nCapabilities:")
        for capability in config['capabilities']:
            print(f"  - {capability}")

        print(f"\nTools:")
        for tool in config['tools']:
            print(f"  - {tool}")

        print(f"\nModel Configuration:")
        print(f"  Provider: {config['model']['provider']}")
        print(f"  Model: {config['model']['name']}")
        print(f"  Temperature: {config['model']['temperature']}")

        logger.log_agent_action(
            config['name'],
            "configuration_loaded",
            {"tools_count": len(config['tools'])}
        )

        # Simulate agent performing a task
        print("\n--- Simulating Task Execution ---")
        logger.log_agent_action(config['name'], "task_start", {"task": "example_task"})

        # Your agent logic would go here
        print("Task: Read a file and analyze its contents")
        print("Status: In Progress...")
        print("Status: Completed")

        logger.log_agent_action(
            config['name'],
            "task_complete",
            {"task": "example_task", "status": "success"}
        )

    except Exception as e:
        logger.log_error("example", e, {"config_path": agent_config_path})
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
