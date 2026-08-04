"""
Logging configuration for the service

This module sets up structured logging with JSON format for production
and human readable format for development
"""

import logging
import os
from pythonjsonlogger import jsonlogger
from typing import Optional
from datetime import datetime, timezone


class ServiceContextFilter(logging.Filter):
    """
    Adds service metadata to the log entry

    This filter injects service name, environment, and version into
    every log message automatically
    """

    def __init__(self, service_name: str, environment: str, version: str):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.version = version

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add service metadata to the log entry

        Args:
            record: The log record to modify
        
        Returns:
            True (always pass the record through)
        """
        record.service = self.service_name
        record.environment = self.environment
        record.version = self.version
        return True


class CorrelationIdFilter(logging.Filter):
    """
    Adds correlation id to the log entry

    This filter retrieves the correlation id from the request context
    and adds it to the log entry
    """

    def __init__(self, correlation_id: str):
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add correlation id to the log entry
        Imports here to avoid circular imports

        Args:
            record: The log record to modify
        
        Returns:
            True (always pass the record through)
        """
        from app.log_context import get_correlation_id

        # Get correlation id from request context (or None if not available/set)
        record.correlation_id = get_correlation_id() or None
        return True


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with ISO 8601 timestamps

    This formatter ensure all logs are in json format with
    consistent field names and timestamps format.
    """

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> dict:
        """
        Customize the JSON log output

        Args:
            log_record: The dictionary that will be output as JSON
            record: The original log record
            message_dict: Additional fields from the log call
        """
        super().add_fields(log_record, record, message_dict)

        # Add ISO 8601 timestamp
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Rename 'levelname' to 'level' for cleaner output
        log_record["level"] = record.levelname

        # Remove the redundant 'levelname' field
        if "levelname" in log_record:
            del log_record["levelname"]



class PrettyFormatter(logging.Formatter):
    """
    Human readable formatter for local development

    Outputs logs in a format that's easy to read in the terminal
    with colors and cleaner structure
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Bold Red
        "CRITICAL": "\033[35m", # Magenta
        "RESET": "\033[0m",     # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log message

        Args:
            record: The log record to format

        Returns:
            The formatted log message
        """

        # Add color codes to the log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]

        # Get correlation id from request context (or None if not available/set)
        correlation_id = getattr(record, "correlation_id", None)

        # Get the service name and environment from the log record
        service = getattr(record, "service", "unknown")

        # Build the log message
        log_line = (
            f"{timestamp} | "
            f"{color}{record.levelname:8}{reset} | "
            f"{service:20} | "
            f"{correlation_id:36} | "
            f"{record.getMessage()}"
        )

        # Add exception info if available
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        return log_line


def setup_logging(
        service_name: Optional[str] = None, 
        environment: Optional[str] = None, 
        level: Optional[str] = None,
        log_format: Optional[str] = None,
) -> None:
    """
    Configure logging for the service.

    This function should be called once at application startup
    It reads configuration from environment variables and configures
    the root logger with the appropriate formatters and filters

    Args:
        service_name: The name of the service (e.g., "product-service")
        environment: The environment the service is running in (e.g., "production", "development")
        level: The log level to use (e.g., "INFO", "DEBUG")
        log_format: The log format to use (e.g., "json", "pretty")
    
    Environment variables:
        SERVICE_NAME: The name of the service (e.g., "product-service")
        ENVIRONMENT: The environment the service is running in (e.g., "production", "development")
        LOG_LEVEL: The log level to use (e.g., "INFO", "DEBUG")
        LOG_FORMAT: The log format to use (e.g., "json", "pretty")
        SERVICE_VERSION: The version of the service (defaults to "1.0.0")
    """

    # Read the environment variables with fallbacks
    service_name = service_name or os.getenv("SERVICE_NAME", "unknown")
    environment = environment or os.getenv("ENVIRONMENT", "unknown")
    level = level or os.getenv("LOG_LEVEL", "INFO")
    log_format = log_format or os.getenv("LOG_FORMAT", "pretty")
    version = os.getenv("SERVICE_VERSION", "1.0.0")

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create console handler (logs to stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level.upper())

    # Choose formatter based on log format settings
    if log_format.lower() == "pretty":
        formatter = PrettyFormatter()
    else:
        formatter = CustomJsonFormatter(
            fmt='%(timestamp)s %(level)s %(service)s %(correlation_id)s %(message)s'
        )
    console_handler.setFormatter(formatter)

    # Add filters to inject metadata
    console_handler.addFilter(ServiceContextFilter(service_name, environment, version))
    console_handler.addFilter(CorrelationIdFilter())

    # Add the console handler to the root logger
    root_logger.addHandler(console_handler)

    # Log startup message
    root_logger.info(
        "Logging configured",
        extra={
            "event": "logging_initialized",
            "log_level": level,
            "log_format": log_format,
            "service": service_name,
            "environment": environment,
        }
    )