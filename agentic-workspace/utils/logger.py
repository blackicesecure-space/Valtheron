"""
Logging utility for agentic workspace operations
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class AgenticLogger:
    """Logger for tracking agent operations and workflows"""

    def __init__(self, log_dir: str = "./logs", level: int = logging.INFO):
        """
        Initialize the logger

        Args:
            log_dir: Directory to store log files
            level: Logging level
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Set up logging
        self.logger = logging.getLogger("agentic-workspace")
        self.logger.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler
        log_file = self.log_dir / f"agentic_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ):
        """
        Log an agent action

        Args:
            agent_name: Name of the agent
            action: Action being performed
            details: Additional details about the action
            level: Log level (info, warning, error, debug)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }

        log_message = json.dumps(log_entry)

        if level == "debug":
            self.logger.debug(log_message)
        elif level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)

    def log_workflow_start(self, workflow_name: str, params: Dict[str, Any]):
        """Log the start of a workflow"""
        self.log_agent_action(
            "workflow-coordinator",
            f"workflow_start: {workflow_name}",
            {"parameters": params}
        )

    def log_workflow_end(
        self,
        workflow_name: str,
        status: str,
        results: Optional[Dict[str, Any]] = None
    ):
        """Log the end of a workflow"""
        self.log_agent_action(
            "workflow-coordinator",
            f"workflow_end: {workflow_name}",
            {"status": status, "results": results}
        )

    def log_error(self, agent_name: str, error: Exception, context: Dict[str, Any]):
        """Log an error with context"""
        self.log_agent_action(
            agent_name,
            "error",
            {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            },
            level="error"
        )
