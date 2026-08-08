"""
SentinelAI Structured Logging

Correlation IDs: event_id, alert_id, user_id, notification_id
Per PRD Section 69-70.
"""

import logging
import json
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """JSON-structured log formatter with correlation IDs."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add correlation IDs if present
        for key in ("event_id", "alert_id", "user_id", "notification_id", "conversation_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])

        return json.dumps(log_entry)


def setup_logging():
    """Configure structured logging for the application."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger("sentinel")
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger under the sentinel namespace."""
    return logging.getLogger(f"sentinel.{name}")
