"""
DistriStore — Centralized Logging
Provides a configured logger for all modules.
"""

import logging
import sys
from pathlib import Path


_initialized = False


def setup_logging(level: str = "DEBUG", log_file: str = None) -> None:
    """
    Configure the root 'distristore' logger.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    log_level = getattr(logging, level.upper(), logging.DEBUG)

    # Root logger for the entire distristore package
    logger = logging.getLogger("distristore")
    logger.setLevel(log_level)
    logger.propagate = False

    # Console handler — colored output
    console_fmt = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)-28s │ %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_fmt = logging.Formatter(
            fmt="%(asctime)s │ %(levelname)-8s │ %(name)-28s │ %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(str(file_path))
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger under the 'distristore' namespace.

    Usage:
        logger = get_logger("network.discovery")
        logger.info("Broadcasting presence...")
    """
    return logging.getLogger(f"distristore.{name}")
