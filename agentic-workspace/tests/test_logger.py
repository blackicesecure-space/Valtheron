"""
Unit tests for logger utility
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import AgenticLogger


class TestAgenticLogger:
    """Test cases for AgenticLogger utility"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = AgenticLogger(log_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_logger_initialization(self):
        """Test logger initializes correctly"""
        assert self.logger is not None
        assert Path(self.temp_dir).exists()

    def test_log_agent_action_info(self):
        """Test logging agent action at info level"""
        # Should not raise exception
        self.logger.log_agent_action(
            "test-agent",
            "test_action",
            {"key": "value"},
            level="info"
        )

    def test_log_agent_action_warning(self):
        """Test logging agent action at warning level"""
        self.logger.log_agent_action(
            "test-agent",
            "test_action",
            {"key": "value"},
            level="warning"
        )

    def test_log_agent_action_error(self):
        """Test logging agent action at error level"""
        self.logger.log_agent_action(
            "test-agent",
            "test_action",
            {"error": "something went wrong"},
            level="error"
        )

    def test_log_workflow_start(self):
        """Test logging workflow start"""
        self.logger.log_workflow_start(
            "test-workflow",
            {"param1": "value1"}
        )

    def test_log_workflow_end_success(self):
        """Test logging workflow end with success"""
        self.logger.log_workflow_end(
            "test-workflow",
            "success",
            {"output": "result"}
        )

    def test_log_workflow_end_failure(self):
        """Test logging workflow end with failure"""
        self.logger.log_workflow_end(
            "test-workflow",
            "failed",
            {"error": "test error"}
        )

    def test_log_error(self):
        """Test logging an error with context"""
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.logger.log_error(
                "test-agent",
                e,
                {"context": "test context"}
            )

    def test_log_files_created(self):
        """Test that log files are created"""
        self.logger.log_agent_action("test-agent", "test", {})

        log_files = list(Path(self.temp_dir).glob("*.log"))
        assert len(log_files) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
