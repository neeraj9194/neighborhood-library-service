"""Structured logging configuration for the library service."""
import logging
import sys
from datetime import datetime, timezone

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """Format log lines as: timestamp | level | logger | message"""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return (
            f"{timestamp} | {record.levelname:<8} | {record.name} | {record.getMessage()}"
        )


def setup_logging() -> None:
    """Configure root logger with structured output to stderr."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(StructuredFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers on repeated calls (e.g. tests)
    root.handlers.clear()
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("tortoise").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
