# Utils Directory

This directory contains utility modules that support agent operations and workflows.

## Available Utilities

### logger.py
Logger for tracking agent operations, workflows, and errors.

**Features:**
- Structured logging with JSON output
- Agent action tracking
- Workflow lifecycle logging
- Error logging with context
- File and console output

**Usage:**
```python
from utils.logger import AgenticLogger

logger = AgenticLogger(log_dir="./logs")
logger.log_agent_action("agent-001", "file_read", {"file": "data.txt"})
logger.log_workflow_start("data-processing", {"input": "raw_data"})
```

### config_loader.py
Configuration file loader with support for JSON and YAML formats.

**Features:**
- Load JSON and YAML configurations
- Auto-detect file format
- Configuration validation
- Configuration merging
- Agent-specific config loading

**Usage:**
```python
from utils.config_loader import ConfigLoader

config = ConfigLoader.load_config("config.json")
agent_config = ConfigLoader.load_agent_config("task-executor-001")
ConfigLoader.validate_config(config, ["name", "version"])
```

## Creating New Utilities

When creating new utilities:

1. **Single responsibility**: Each utility should have a clear, focused purpose
2. **Documentation**: Include docstrings for all functions and classes
3. **Type hints**: Use type hints for better code clarity
4. **Error handling**: Implement proper error handling and validation
5. **Testing**: Create corresponding tests in the tests/ directory
6. **Examples**: Provide usage examples in the README

## Common Utility Patterns

### Data Processing
- Data validation
- Format conversion
- Data transformation
- Serialization/deserialization

### File Operations
- File finding and filtering
- Batch file operations
- Path manipulation
- Content parsing

### API Helpers
- HTTP request wrappers
- Authentication handling
- Response parsing
- Rate limiting

### Workflow Support
- State management
- Result caching
- Retry mechanisms
- Progress tracking
