"""
Logging Configuration for Baby Timeline
Centralized logging setup for the application.
"""

import logging
import sys


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger for a module.

    Args:
        name: Logger name (typically __name__ from the calling module)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance

    Usage:
        from src.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("Application started")
        logger.error("An error occurred", exc_info=True)
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured (prevents duplicate handlers)
    if not logger.handlers:
        logger.setLevel(level)

        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Format: timestamp - module - level - message
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger
