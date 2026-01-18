# Workflows Directory

This directory contains workflow definitions that orchestrate multiple agents to accomplish complex tasks.

## Structure

- `workflow-schema.json` - JSON schema for workflow definitions
- `example-*.json` - Example workflow implementations
- Custom workflows should follow the schema

## Workflow Components

### Steps
Individual actions performed by agents in sequence or parallel.

### Dependencies
Define which steps must complete before others can start.

### Error Handling
Configure how the workflow responds to failures:
- `fail-fast`: Stop on first error
- `continue`: Continue despite errors
- `partial-success`: Complete what's possible

### Parallel Execution
Steps without dependencies can run concurrently for better performance.

## Example Workflows

### Automated Code Review
**File**: `example-code-review.json`

Performs comprehensive code review including:
- Finding changed files
- Analyzing code quality
- Running tests
- Generating review summary

**Usage:**
```json
{
  "repository_path": "./my-project",
  "files": ["src/main.py", "src/utils.py"]
}
```

### Data Processing Pipeline
**File**: `example-data-pipeline.json`

End-to-end data processing:
- Input validation
- Data cleaning
- Transformation
- Pattern analysis
- Report generation

**Usage:**
```json
{
  "input_file": "./data/raw_data.csv",
  "output_dir": "./data/processed"
}
```

## Creating a Workflow

1. **Define the purpose**: What problem does this workflow solve?
2. **Identify steps**: Break down into discrete actions
3. **Assign agents**: Choose appropriate agents for each step
4. **Set dependencies**: Define execution order
5. **Configure error handling**: Decide failure behavior
6. **Test thoroughly**: Validate with various inputs

## Workflow Definition Template

```json
{
  "name": "workflow-name",
  "version": "1.0.0",
  "description": "What this workflow does",
  "inputs": {
    "param1": {
      "type": "string",
      "description": "Parameter description"
    }
  },
  "outputs": {
    "result": {
      "type": "object",
      "description": "Output description"
    }
  },
  "steps": [
    {
      "name": "step-1",
      "agent": "agent-name",
      "action": "action-name",
      "params": {
        "key": "value"
      }
    }
  ],
  "error_handling": {
    "strategy": "fail-fast"
  }
}
```

## Variable Interpolation

Reference outputs from previous steps:
- `${inputs.param_name}` - Workflow input
- `${steps.step-name.output}` - Step output
- `${steps.step-name.output.field}` - Specific field

## Best Practices

1. **Modularity**: Keep steps focused and reusable
2. **Error handling**: Always define failure behavior
3. **Logging**: Ensure adequate logging for debugging
4. **Testing**: Test each step independently first
5. **Documentation**: Document workflow purpose and usage
6. **Versioning**: Use semantic versioning for workflows
7. **Idempotency**: Design steps to be safely retryable

## Workflow Execution

Workflows can be executed by:
- Workflow coordinator agent
- CLI tools
- API endpoints
- Scheduled jobs

## Monitoring

Track workflow execution:
- Step completion status
- Execution time per step
- Error rates
- Resource usage
- Output quality

## Common Patterns

### Sequential Processing
Steps execute one after another in order.

### Parallel Fanout
Multiple independent steps execute simultaneously.

### Conditional Execution
Steps execute based on previous results.

### Retry with Backoff
Failed steps retry with increasing delays.

### Partial Success
Continue workflow even if some steps fail.
