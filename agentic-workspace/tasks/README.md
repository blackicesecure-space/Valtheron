# Tasks Directory

This directory contains task definitions that represent discrete units of work that can be executed by agents.

## Structure

- `task-schema.json` - JSON schema for task definitions
- `example-*.json` - Example task definitions
- Custom tasks should follow the schema

## Task Components

### Inputs
Define what data or parameters the task needs to execute.

### Outputs
Specify what the task produces upon completion.

### Success Criteria
List conditions that must be met for the task to be considered successful.

### Validation
Define how task completion is validated (automated script, manual review, or hybrid).

### Dependencies
Specify other tasks that must complete before this task can start.

## Task Types

### Data Processing
- Data transformation
- Validation
- Cleaning
- Aggregation

### Code Generation
- Feature implementation
- Refactoring
- Code migration
- Template generation

### Analysis
- Code analysis
- Security audits
- Performance profiling
- Pattern detection

### Testing
- Unit test execution
- Integration testing
- Load testing
- Test generation

### Documentation
- Code documentation
- API documentation
- User guides
- Architecture docs

### Deployment
- Build processes
- Deployment automation
- Configuration management
- Environment setup

### Monitoring
- Log analysis
- Performance monitoring
- Error tracking
- Health checks

## Example Tasks

### Code Refactoring
**File**: `example-code-refactor.json`

Refactor legacy code to improve quality:
- Apply coding standards
- Add type hints
- Reduce complexity
- Update documentation

### Security Audit
**File**: `example-security-audit.json`

Comprehensive security scanning:
- Dependency vulnerabilities
- Static code analysis
- Secret detection
- Permission audits

## Creating a Task

1. **Define scope**: Clear, focused objective
2. **Specify inputs**: All required data and parameters
3. **Define outputs**: Expected results
4. **Set criteria**: Measurable success conditions
5. **Choose agent**: Select appropriate agent type
6. **List tools**: Required tool capabilities
7. **Add validation**: How to verify completion

## Task Definition Template

```json
{
  "name": "task-identifier",
  "type": "task-type",
  "description": "Detailed task description",
  "priority": "medium",
  "estimated_duration": "30m",
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
  "agent": "preferred-agent",
  "tools_required": ["tool1", "tool2"],
  "success_criteria": [
    "Criterion 1",
    "Criterion 2"
  ],
  "validation": {
    "method": "automated",
    "script": "./validate.py"
  },
  "tags": ["tag1", "tag2"]
}
```

## Task Execution

Tasks can be executed:
- Individually by agents
- As part of workflows
- Scheduled/triggered
- Via API or CLI

## Task States

- **Pending**: Waiting to start
- **In Progress**: Currently executing
- **Blocked**: Waiting for dependencies
- **Completed**: Successfully finished
- **Failed**: Execution failed
- **Cancelled**: Manually stopped

## Best Practices

1. **Single responsibility**: One clear objective per task
2. **Clear inputs/outputs**: Well-defined interfaces
3. **Measurable success**: Objective completion criteria
4. **Proper validation**: Automated where possible
5. **Good documentation**: Clear description and usage
6. **Appropriate sizing**: Not too large or too small
7. **Reusability**: Design for reuse across projects

## Task Composition

Tasks can be composed into workflows for complex operations:
- Sequential chains
- Parallel execution
- Conditional branching
- Loop iterations

## Monitoring and Logging

Track task execution:
- Start/end timestamps
- Duration
- Success/failure status
- Output artifacts
- Error messages
- Resource usage

## Common Task Patterns

### Validation Task
Verify data or code meets requirements.

### Transformation Task
Convert from one format/structure to another.

### Analysis Task
Extract insights from data or code.

### Generation Task
Create new artifacts (code, docs, reports).

### Integration Task
Connect or sync between systems.
