"""
Centralised logger for the Meeting AI Platform.
Usage:
    from backend.app.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("hello")
"""

import logging
import sys


def get_logger(name: str = "meeting_ai") -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
