# Config Directory

This directory contains global configuration files for the agentic workspace.

## Configuration Files

### workspace.json
Main workspace configuration including:
- Workspace metadata
- Directory paths
- Default settings
- Logging configuration
- Execution parameters
- Security settings
- Monitoring options

### models.json
AI model configurations:
- Available model providers (Anthropic, OpenAI, etc.)
- Model specifications and pricing
- Rate limits
- Model preferences and fallbacks
- Auto-selection criteria

### secrets.json (not in repo)
Sensitive credentials and API keys:
- API keys for model providers
- Database credentials
- Service tokens
- **Important**: Never commit this file to version control

## Environment Variables

Use `.env` file in the workspace root for environment-specific configuration:

```bash
cp ../.env.example ../.env
# Edit .env with your actual values
```

## Configuration Loading

Configurations are loaded in this order (later overrides earlier):
1. Default values in configuration files
2. Environment variables
3. Command-line arguments (if applicable)

## Using Configurations

### Python
```python
from utils.config_loader import ConfigLoader

# Load workspace config
workspace_config = ConfigLoader.load_json("config/workspace.json")

# Load model config
model_config = ConfigLoader.load_json("config/models.json")

# Access settings
log_level = workspace_config["logging"]["level"]
default_model = model_config["preferences"]["default_model"]
```

### JavaScript
```javascript
const fs = require('fs');
const path = require('path');

// Load workspace config
const workspaceConfig = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'workspace.json'), 'utf8')
);

// Access settings
const logLevel = workspaceConfig.logging.level;
```

## Configuration Sections

### Workspace Settings
- **name**: Workspace identifier
- **version**: Workspace version
- **paths**: Directory locations
- **defaults**: Default agent/tool settings

### Logging
- **level**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **format**: text, json
- **output**: console, file, both
- **rotation**: Log file rotation settings

### Execution
- **parallel_max_workers**: Max concurrent tasks
- **enable_caching**: Enable result caching
- **cache_ttl_seconds**: Cache time-to-live
- **auto_cleanup**: Automatic cleanup of temp files

### Security
- **validate_inputs**: Input validation
- **sanitize_outputs**: Output sanitization
- **require_agent_auth**: Agent authentication
- **allowed_tools**: Tool access control

### Monitoring
- **enabled**: Enable monitoring
- **metrics**: Tracked metrics
- **alerts**: Alert configuration

## Best Practices

1. **Version Control**
   - Commit configuration templates
   - Never commit secrets
   - Use .env for local overrides

2. **Documentation**
   - Document all configuration options
   - Provide example values
   - Explain impact of changes

3. **Validation**
   - Validate configs on load
   - Use schemas where possible
   - Fail fast on invalid config

4. **Security**
   - Store secrets securely
   - Use environment variables for sensitive data
   - Rotate credentials regularly

5. **Maintainability**
   - Keep configs organized
   - Use clear naming
   - Group related settings

## Environment-Specific Configs

For multiple environments:

```
config/
├── workspace.json (default)
├── workspace.development.json
├── workspace.staging.json
└── workspace.production.json
```

Load based on environment:
```python
env = os.getenv("WORKSPACE_ENV", "development")
config_file = f"config/workspace.{env}.json"
```

## Configuration Validation

Validate configurations before use:

```python
from utils.config_loader import ConfigLoader

config = ConfigLoader.load_json("config/workspace.json")
required_fields = ["workspace", "paths", "defaults"]
ConfigLoader.validate_config(config, required_fields)
```

## Troubleshooting

**Config not found**
- Check file path is correct
- Ensure file exists in config directory

**Invalid JSON**
- Validate JSON syntax
- Check for trailing commas
- Use JSON linter

**Missing values**
- Check all required fields are present
- Verify environment variables are set
- Review .env.example for required variables

## Updates and Migration

When updating configurations:
1. Document changes
2. Update example files
3. Notify team members
4. Provide migration guide if needed
5. Test thoroughly
