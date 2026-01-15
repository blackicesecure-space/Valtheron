# Getting Started with Agentic Workspace

This guide will help you set up and start using the agentic workspace.

## Prerequisites

- **Python**: Version 3.8 or higher
- **Node.js**: Version 18 or higher (optional, for JavaScript tools)
- **Git**: For version control
- **API Keys**: Anthropic or OpenAI API key (for AI models)

## Installation

### 1. Clone or Navigate to the Workspace

If setting up fresh:
```bash
git clone <repository-url>
cd agentic-workspace
```

If already in the repository:
```bash
cd agentic-workspace
```

### 2. Set Up Python Environment

Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 3. Set Up JavaScript Environment (Optional)

If using JavaScript tools:
```bash
npm install
```

### 4. Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```bash
ANTHROPIC_API_KEY=your_actual_key_here
# or
OPENAI_API_KEY=your_actual_key_here
```

## Quick Start

### Example 1: Run a Simple Agent

```bash
cd examples
python simple-agent-example.py
```

This demonstrates:
- Loading agent configuration
- Logging agent actions
- Simulating task execution

### Example 2: Execute a Workflow

```bash
cd examples
python workflow-execution-example.py
```

This demonstrates:
- Loading workflow configuration
- Executing multiple steps
- Managing dependencies
- Tracking results

## Understanding the Structure

### Directory Layout

```
agentic-workspace/
├── agents/          # Agent configurations
├── tools/           # Tool definitions
├── workflows/       # Workflow definitions
├── tasks/           # Task definitions
├── config/          # Global configuration
├── utils/           # Utility modules
├── data/            # Data storage
├── docs/            # Documentation
├── examples/        # Example code
└── tests/           # Test suites
```

### Key Files

- **agents/example-task-executor.json**: Example agent configuration
- **workflows/example-code-review.json**: Example workflow
- **config/workspace.json**: Main workspace settings
- **utils/logger.py**: Logging utility
- **utils/config_loader.py**: Configuration loader

## Creating Your First Agent

### 1. Create Agent Configuration

Create `agents/my-first-agent.json`:

```json
{
  "name": "my-first-agent",
  "type": "task-executor",
  "version": "1.0.0",
  "description": "My first custom agent",
  "model": {
    "provider": "anthropic",
    "name": "claude-sonnet-4-5",
    "temperature": 0.7,
    "max_tokens": 4096
  },
  "tools": ["bash", "read", "write"],
  "capabilities": ["file-operations", "code-execution"],
  "config": {
    "max_retries": 3,
    "timeout_seconds": 300
  }
}
```

### 2. Use the Agent

```python
from utils.config_loader import ConfigLoader
from utils.logger import AgenticLogger

# Load configuration
config = ConfigLoader.load_agent_config("my-first-agent", "./agents")

# Initialize logger
logger = AgenticLogger()

# Log agent action
logger.log_agent_action(
    config['name'],
    "task_start",
    {"task": "my_task"}
)

# Your agent logic here
print(f"Agent {config['name']} is running!")
```

## Creating Your First Workflow

### 1. Create Workflow Configuration

Create `workflows/my-first-workflow.json`:

```json
{
  "name": "my-first-workflow",
  "version": "1.0.0",
  "description": "My first custom workflow",
  "inputs": {
    "input_file": {
      "type": "string",
      "description": "File to process"
    }
  },
  "steps": [
    {
      "name": "read-file",
      "agent": "my-first-agent",
      "action": "read_file",
      "params": {
        "file_path": "${inputs.input_file}"
      }
    },
    {
      "name": "process-content",
      "agent": "my-first-agent",
      "action": "process",
      "params": {
        "content": "${steps.read-file.output}"
      },
      "depends_on": ["read-file"]
    }
  ]
}
```

## Common Tasks

### List Available Agents

```bash
ls -1 agents/*.json
```

### Validate Configuration

```python
from utils.config_loader import ConfigLoader

config = ConfigLoader.load_json("agents/my-first-agent.json")
required = ["name", "type", "version"]
ConfigLoader.validate_config(config, required)
print("Configuration is valid!")
```

### View Logs

```bash
# View latest log file
tail -f logs/agentic_$(date +%Y%m%d).log

# Or use any text editor
cat logs/agentic_$(date +%Y%m%d).log
```

## Next Steps

### Learn More

1. **Read Documentation**
   - [Architecture](./ARCHITECTURE.md) - System design
   - Agent configurations - `agents/README.md`
   - Workflow definitions - `workflows/README.md`
   - Tool development - `tools/README.md`

2. **Explore Examples**
   - Review example agents
   - Study example workflows
   - Run example scripts

3. **Customize**
   - Create custom agents
   - Build custom workflows
   - Develop custom tools

### Best Practices

1. **Start Simple**
   - Begin with basic agents
   - Create simple workflows
   - Test thoroughly

2. **Use Examples**
   - Copy and modify examples
   - Follow established patterns
   - Reference existing code

3. **Document Everything**
   - Add clear descriptions
   - Document parameters
   - Explain complex logic

4. **Test Incrementally**
   - Test agents individually
   - Test workflow steps separately
   - Test complete workflows

5. **Monitor and Log**
   - Use the logger utility
   - Track agent actions
   - Monitor for errors

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Make sure you're in the right directory
cd agentic-workspace

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
```

**API Key Errors**
```bash
# Check .env file exists
ls -la .env

# Verify key is set
grep ANTHROPIC_API_KEY .env
```

**Configuration Errors**
```python
# Validate JSON syntax
import json
with open('agents/my-agent.json') as f:
    json.load(f)  # Will raise error if invalid
```

### Getting Help

1. Check documentation in `docs/`
2. Review examples in `examples/`
3. Check logs for error messages
4. Validate configurations against schemas

## Additional Resources

- **Schemas**: JSON schemas in each directory
- **Examples**: Working examples in `examples/`
- **Documentation**: Detailed docs in `docs/`
- **README files**: Context-specific docs in each directory

## What's Next?

Now that you have the basics:

1. Experiment with example agents and workflows
2. Create your own custom agents
3. Build workflows for your use cases
4. Develop custom tools if needed
5. Integrate with your existing systems

Happy building with the agentic workspace!
