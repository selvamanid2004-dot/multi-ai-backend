import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """
    Standardizes log output with structured format.
    """
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname
        name = record.name
        message = record.getMessage()
        
        # Extract optional extra attributes
        correlation_id = getattr(record, "correlation_id", "-")
        agent_name = getattr(record, "agent_name", "-")
        
        return f"[{timestamp}] [{level:<7}] [cid:{correlation_id}] [{name}] [{agent_name}] {message}"


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured structured logger.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
