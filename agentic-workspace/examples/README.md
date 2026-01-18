# Examples Directory

This directory contains example implementations demonstrating how to use the agentic workspace.

## Available Examples

### simple-agent-example.py
Demonstrates basic agent configuration loading and usage.

**Features:**
- Loading agent configuration from JSON
- Using the logger utility
- Simulating basic task execution
- Error handling

**Run:**
```bash
cd examples
python simple-agent-example.py
```

### workflow-execution-example.py
Shows how to load and execute a workflow.

**Features:**
- Loading workflow configuration
- Step-by-step execution
- Dependency management
- Result tracking
- Workflow logging

**Run:**
```bash
cd examples
python workflow-execution-example.py
```

## Example Structure

Each example follows this pattern:
1. Import necessary utilities
2. Load configuration
3. Initialize logger
4. Execute operations
5. Handle errors
6. Report results

## Creating Your Own Examples

When creating new examples:

1. **Clear purpose**: Focus on one concept
2. **Complete code**: Should run without modifications
3. **Documentation**: Explain what the example demonstrates
4. **Error handling**: Show proper error handling
5. **Comments**: Add helpful comments
6. **Dependencies**: Document any requirements

## Common Patterns

### Loading Configuration
```python
from utils.config_loader import ConfigLoader

config = ConfigLoader.load_json("path/to/config.json")
```

### Using the Logger
```python
from utils.logger import AgenticLogger

logger = AgenticLogger(log_dir="./logs")
logger.log_agent_action("agent-name", "action", {"key": "value"})
```

### Agent Initialization
```python
agent_config = ConfigLoader.load_agent_config("agent-name", "./agents")
# Use agent_config to initialize your agent
```

### Workflow Execution
```python
workflow_config = ConfigLoader.load_json("./workflows/my-workflow.json")
# Execute workflow steps
```

## Testing Examples

Before adding examples to the repository:
1. Test in a clean environment
2. Verify all imports work
3. Check error handling
4. Update documentation
5. Add helpful comments

## Integration Examples

For more complex integration examples:
- Multi-agent coordination
- External API integration
- Database connectivity
- Real-time processing
- Production deployment

## Learning Path

Suggested order for learning:
1. Start with `simple-agent-example.py`
2. Move to `workflow-execution-example.py`
3. Review agent and workflow configurations
4. Experiment with custom agents
5. Build your own workflows

## Resources

- Agent configuration schema: `../agents/agent-config.schema.json`
- Workflow schema: `../workflows/workflow-schema.json`
- Tool definitions: `../tools/tool-definition.schema.json`
- Task schema: `../tasks/task-schema.json`

## Troubleshooting

Common issues:
- **Import errors**: Ensure parent directory is in Python path
- **Config not found**: Check file paths are correct
- **Logger errors**: Ensure logs directory exists or can be created
- **Missing dependencies**: Install required packages

## Contributing Examples

When contributing new examples:
1. Follow existing code style
2. Add comprehensive documentation
3. Include usage instructions
4. Test thoroughly
5. Update this README
