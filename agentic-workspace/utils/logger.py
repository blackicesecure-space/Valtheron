"""
Logging utility for agentic workspace operations.

Provides structured logging with JSON output, metrics tracking,
and comprehensive agent/workflow monitoring.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import threading


@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates metrics for monitoring."""
    
    def __init__(self):
        self._metrics: Dict[str, List[MetricPoint]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        with self._lock:
            point = MetricPoint(name=name, value=value, tags=tags or {})
            self._metrics[name].append(point)
    
    def get_metrics(self, name: str) -> List[MetricPoint]:
        """Get all recorded values for a metric."""
        with self._lock:
            return self._metrics.get(name, []).copy()
    
    def get_summary(self, name: str) -> Dict[str, float]:
        """Get statistical summary for a metric."""
        points = self.get_metrics(name)
        if not points:
            return {}
        
        values = [p.value for p in points]
        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }
    
    def clear(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self._metrics.clear()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "agent"):
            log_data["agent"] = record.agent
        if hasattr(record, "action"):
            log_data["action"] = record.action
        if hasattr(record, "details"):
            log_data["details"] = record.details
        if hasattr(record, "workflow"):
            log_data["workflow"] = record.workflow
        if hasattr(record, "step"):
            log_data["step"] = record.step
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class AgenticLogger:
    """
    Logger for tracking agent operations and workflows.
    
    Provides structured logging with JSON output, metric collection,
    and comprehensive event tracking.
    """

    def __init__(self, 
                 log_dir: str = "./logs", 
                 level: int = logging.INFO,
                 json_format: bool = True,
                 console_output: bool = True):
        """
        Initialize the logger.

        Args:
            log_dir: Directory to store log files
            level: Logging level
            json_format: Use JSON format for logs
            console_output: Also output to console
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = MetricsCollector()

        # Set up logging
        self.logger = logging.getLogger("agentic-workspace")
        self.logger.setLevel(level)
        self.logger.handlers.clear()  # Clear existing handlers
        
        # Formatter
        if json_format:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # File handler
        log_file = self.log_dir / f"agentic_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def log_agent_action(
        self,
        agent_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> None:
        """
        Log an agent action.

        Args:
            agent_name: Name of the agent
            action: Action being performed
            details: Additional details about the action
            level: Log level (info, warning, error, debug)
        """
        extra = {
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }
        
        message = f"[{agent_name}] {action}"
        record = self.logger.makeRecord(
            self.logger.name,
            getattr(logging, level.upper()),
            "",
            0,
            message,
            (),
            None
        )
        
        for key, value in extra.items():
            setattr(record, key, value)
        
        self.logger.handle(record)
        
        # Record metric
        self.metrics.record(
            "agent_action",
            1,
            {"agent": agent_name, "action": action}
        )

    def log_workflow_start(self, workflow_name: str, params: Dict[str, Any]) -> None:
        """Log the start of a workflow."""
        extra = {
            "workflow": workflow_name,
            "action": "workflow_start",
            "details": {"parameters": params}
        }
        
        message = f"[Workflow] Starting: {workflow_name}"
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "",
            0,
            message,
            (),
            None
        )
        
        for key, value in extra.items():
            setattr(record, key, value)
        
        self.logger.handle(record)

    def log_workflow_step(
        self,
        workflow_name: str,
        step_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a workflow step execution."""
        extra = {
            "workflow": workflow_name,
            "step": step_name,
            "action": f"step_{status}",
            "details": details or {}
        }
        
        message = f"[Workflow:{workflow_name}] Step '{step_name}': {status}"
        
        level = logging.ERROR if status == "failed" else logging.INFO
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            message,
            (),
            None
        )
        
        for key, value in extra.items():
            setattr(record, key, value)
        
        self.logger.handle(record)

    def log_workflow_end(
        self,
        workflow_name: str,
        status: str,
        results: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log the end of a workflow."""
        extra = {
            "workflow": workflow_name,
            "action": "workflow_end",
            "details": {"status": status, "results": results}
        }
        
        message = f"[Workflow] Completed: {workflow_name} ({status})"
        
        level = logging.ERROR if status == "failed" else logging.INFO
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            message,
            (),
            None
        )
        
        for key, value in extra.items():
            setattr(record, key, value)
        
        self.logger.handle(record)

    def log_error(
        self, 
        agent_name: str, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Log an error with context."""
        extra = {
            "agent": agent_name,
            "action": "error",
            "details": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context
            }
        }
        
        message = f"[{agent_name}] Error: {type(error).__name__}: {error}"
        
        self.logger.error(message, exc_info=True, extra=extra)
        
        # Record error metric
        self.metrics.record(
            "error",
            1,
            {"agent": agent_name, "error_type": type(error).__name__}
        )

    def log_tool_execution(
        self,
        tool_name: str,
        agent_name: str,
        execution_time_ms: float,
        success: bool,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log tool execution with timing metrics."""
        status = "success" if success else "failure"
        
        self.log_agent_action(
            agent_name,
            f"tool_execute:{tool_name}",
            {
                "tool": tool_name,
                "execution_time_ms": execution_time_ms,
                "status": status,
                **(details or {})
            }
        )
        
        # Record timing metric
        self.metrics.record(
            "tool_execution_time",
            execution_time_ms,
            {"tool": tool_name, "agent": agent_name, "status": status}
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all collected metrics."""
        return {
            "agent_actions": self.metrics.get_summary("agent_action"),
            "errors": self.metrics.get_summary("error"),
            "tool_execution_time": self.metrics.get_summary("tool_execution_time")
        }


# Global logger instance
_global_logger: Optional[AgenticLogger] = None


def get_logger(log_dir: str = "./logs") -> AgenticLogger:
    """Get or create the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AgenticLogger(log_dir=log_dir)
    return _global_logger
