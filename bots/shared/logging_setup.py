"""
Centralized logging configuration for all bots.
"""

import logging
from typing import Optional


def setup_logging(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup and return a logger with consistent formatting.

    Args:
        name: Logger name. If None, uses the root logger.
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)


# Default logger instance
logger = setup_logging(__name__)
