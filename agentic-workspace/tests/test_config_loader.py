"""
Unit tests for config_loader utility
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader utility"""

    def test_load_json_success(self):
        """Test loading a valid JSON file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"key": "value", "number": 42}
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = ConfigLoader.load_json(temp_path)
            assert result == test_data
        finally:
            os.unlink(temp_path)

    def test_load_json_file_not_found(self):
        """Test loading a non-existent JSON file"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_json("/path/that/does/not/exist.json")

    def test_load_json_invalid_json(self):
        """Test loading invalid JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json content}")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                ConfigLoader.load_json(temp_path)
        finally:
            os.unlink(temp_path)

    def test_validate_config_success(self):
        """Test successful config validation"""
        config = {
            "name": "test-agent",
            "type": "task-executor",
            "version": "1.0.0"
        }
        required = ["name", "type", "version"]

        assert ConfigLoader.validate_config(config, required) is True

    def test_validate_config_missing_fields(self):
        """Test config validation with missing fields"""
        config = {
            "name": "test-agent",
            "type": "task-executor"
        }
        required = ["name", "type", "version"]

        with pytest.raises(ValueError) as exc_info:
            ConfigLoader.validate_config(config, required)

        assert "version" in str(exc_info.value)

    def test_merge_configs(self):
        """Test merging two configurations"""
        base = {
            "name": "agent",
            "config": {
                "timeout": 300,
                "retries": 3
            }
        }
        override = {
            "name": "new-agent",
            "config": {
                "timeout": 600
            }
        }

        result = ConfigLoader.merge_configs(base, override)

        assert result["name"] == "new-agent"
        assert result["config"]["timeout"] == 600
        assert result["config"]["retries"] == 3

    def test_merge_configs_nested(self):
        """Test merging nested configurations"""
        base = {
            "model": {
                "provider": "anthropic",
                "name": "claude-sonnet",
                "temperature": 0.7
            }
        }
        override = {
            "model": {
                "temperature": 0.9
            }
        }

        result = ConfigLoader.merge_configs(base, override)

        assert result["model"]["provider"] == "anthropic"
        assert result["model"]["name"] == "claude-sonnet"
        assert result["model"]["temperature"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
