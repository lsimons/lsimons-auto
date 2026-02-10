#!/usr/bin/env python3
"""
logging_utils.py - Centralized logging configuration for lsimons-auto

Provides consistent logging setup across all actions and modules.
"""

import logging
import sys


def setup_logging(
    name: str = "lsimons_auto", level: int = logging.INFO, log_file: str | None = None
) -> logging.Logger:
    """
    Set up logging configuration with consistent formatting.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional file path for file logging

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is provided
    if log_file:
        try:
            from pathlib import Path

            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, ImportError) as e:
            logger.warning(f"Could not set up file logging to {log_file}: {e}")

    return logger


def get_logger(name: str = "lsimons_auto") -> logging.Logger:
    """
    Get or create a logger with the standard configuration.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    # Check if logger already exists and has handlers
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    return setup_logging(name)


# Module-level logger for convenience
logger = get_logger()
