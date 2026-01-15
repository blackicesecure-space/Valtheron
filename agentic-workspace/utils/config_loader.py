"""
Configuration loader utility for agentic workspace
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigLoader:
    """Load and validate configuration files for agents and workflows"""

    @staticmethod
    def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a JSON configuration file

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

        with open(path, 'r') as f:
            return json.load(f)

    @staticmethod
    def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load a YAML configuration file

        Args:
            file_path: Path to the YAML file

        Returns:
            Dictionary containing the configuration

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration file (auto-detect format)

        Args:
            file_path: Path to the configuration file

        Returns:
            Dictionary containing the configuration
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == '.json':
            return ConfigLoader.load_json(path)
        elif suffix in ['.yaml', '.yml']:
            return ConfigLoader.load_yaml(path)
        else:
            raise ValueError(f"Unsupported configuration format: {suffix}")

    @staticmethod
    def load_agent_config(agent_name: str, config_dir: str = "./agents") -> Dict[str, Any]:
        """
        Load an agent configuration by name

        Args:
            agent_name: Name of the agent
            config_dir: Directory containing agent configurations

        Returns:
            Agent configuration dictionary
        """
        config_path = Path(config_dir) / f"{agent_name}.json"
        if not config_path.exists():
            config_path = Path(config_dir) / f"{agent_name}.yaml"

        return ConfigLoader.load_config(config_path)

    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: list) -> bool:
        """
        Validate that configuration has required fields

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
        Merge two configuration dictionaries (override takes precedence)

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
