"""
Configuration loader utility for agentic workspace.

Provides comprehensive configuration loading, validation, merging,
and environment variable support.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ConfigLoader:
    """Load and validate configuration files for agents and workflows."""
    
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_enabled: bool = True

    @classmethod
    def enable_cache(cls, enabled: bool = True) -> None:
        """Enable or disable configuration caching."""
        cls._cache_enabled = enabled
        if not enabled:
            cls._cache.clear()

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the configuration cache."""
        cls._cache.clear()

    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON configuration file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Dictionary containing the configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a YAML configuration file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Dictionary containing the configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML support. Install with: pip install pyyaml")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    @classmethod
    def load_config(cls, file_path: Union[str, Path], use_cache: bool = True) -> Dict[str, Any]:
        """
        Load configuration file (auto-detect format).

        Args:
            file_path: Path to the configuration file
            use_cache: Whether to use cached configuration

        Returns:
            Dictionary containing the configuration
        """
        path = Path(file_path)
        cache_key = str(path.absolute())
        
        if use_cache and cls._cache_enabled and cache_key in cls._cache:
            return cls._cache[cache_key].copy()
        
        suffix = path.suffix.lower()

        if suffix == '.json':
            config = cls.load_json(path)
        elif suffix in ['.yaml', '.yml']:
            config = cls.load_yaml(path)
        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")
        
        if cls._cache_enabled:
            cls._cache[cache_key] = config.copy()
        
        return config

    @classmethod
    def load_agent_config(cls, agent_name: str, config_dir: str = "./agents") -> Dict[str, Any]:
        """
        Load an agent configuration by name.

        Args:
            agent_name: Name of the agent
            config_dir: Directory containing agent configurations

        Returns:
            Agent configuration dictionary
        """
        config_path = Path(config_dir) / f"{agent_name}.json"
        if not config_path.exists():
            config_path = Path(config_dir) / f"{agent_name}.yaml"
        
        if not config_path.exists():
            # Try with example- prefix
            config_path = Path(config_dir) / f"example-{agent_name}.json"

        return cls.load_config(config_path)

    @classmethod
    def load_workflow_config(cls, workflow_name: str, config_dir: str = "./workflows") -> Dict[str, Any]:
        """
        Load a workflow configuration by name.

        Args:
            workflow_name: Name of the workflow
            config_dir: Directory containing workflow configurations

        Returns:
            Workflow configuration dictionary
        """
        config_path = Path(config_dir) / f"{workflow_name}.json"
        if not config_path.exists():
            config_path = Path(config_dir) / f"{workflow_name}.yaml"
        
        if not config_path.exists():
            config_path = Path(config_dir) / f"example-{workflow_name}.json"

        return cls.load_config(config_path)

    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that configuration has required fields.

        Args:
            config: Configuration dictionary
            required_fields: List of required field names

        Returns:
            True if valid

        Raises:
            ValueError: If required fields are missing
        """
        missing = [field for field in required_fields if field not in config]
        if missing:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing)}")
        return True

    @staticmethod
    def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two configuration dictionaries (override takes precedence).

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Merged configuration
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigLoader.merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def resolve_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve environment variable references in configuration.
        
        Supports ${ENV_VAR} and ${ENV_VAR:default} syntax.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with resolved environment variables
        """
        import re
        
        def resolve_value(value: Any) -> Any:
            if isinstance(value, str):
                pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
                
                def replace(match):
                    var_name = match.group(1)
                    default = match.group(2)
                    return os.environ.get(var_name, default if default is not None else match.group(0))
                
                return re.sub(pattern, replace, value)
            elif isinstance(value, dict):
                return {k: resolve_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [resolve_value(item) for item in value]
            return value
        
        return resolve_value(config)

    @classmethod
    def load_workspace_config(cls, workspace_dir: str = ".") -> Dict[str, Any]:
        """
        Load the main workspace configuration with environment resolution.

        Args:
            workspace_dir: Root directory of the workspace

        Returns:
            Complete workspace configuration
        """
        config_path = Path(workspace_dir) / "config" / "workspace.json"
        
        if not config_path.exists():
            config_path = Path(workspace_dir) / "config" / "workspace.yaml"
        
        config = cls.load_config(config_path)
        return cls.resolve_env_vars(config)
