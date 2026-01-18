# Agents Directory

This directory contains agent configurations and definitions for the agentic workspace.

## Structure

- `agent-config.schema.json` - JSON schema defining the structure for agent configurations
- `example-*.json` - Example agent configurations demonstrating different agent types
- Custom agent configurations should follow the schema defined in `agent-config.schema.json`

## Agent Types

### Task Executor
- **Purpose**: Execute specific tasks, run code, manage files
- **Use cases**: Code generation, file operations, command execution
- **Example**: `example-task-executor.json`

### Researcher
- **Purpose**: Gather information, analyze codebases, synthesize findings
- **Use cases**: Code exploration, documentation lookup, pattern analysis
- **Example**: `example-researcher.json`

### Planner
- **Purpose**: Break down complex tasks into manageable steps
- **Use cases**: Project planning, task decomposition, architecture design

### Reviewer
- **Purpose**: Review code, documentation, and outputs for quality
- **Use cases**: Code review, security analysis, quality assurance

### Coordinator
- **Purpose**: Orchestrate multiple agents to work together
- **Use cases**: Multi-agent workflows, task delegation, result aggregation

## Creating a New Agent

1. Copy one of the example configurations
2. Modify the fields according to your needs
3. Ensure it validates against `agent-config.schema.json`
4. Document the agent's specific capabilities and use cases

## Configuration Fields

- **name**: Unique identifier for the agent
- **type**: Agent category (task-executor, researcher, planner, reviewer, coordinator)
- **version**: Semantic version (e.g., 1.0.0)
- **description**: Detailed explanation of what the agent does
- **model**: AI model configuration (provider, name, temperature, max_tokens)
- **tools**: List of tools the agent can access
- **capabilities**: List of capabilities the agent provides
- **dependencies**: Other agents this agent relies on
- **config**: Agent-specific configuration options
