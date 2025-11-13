"""
Initializes and exports a pre-configured logger.

Log format:
%(asctime)s %(levelname)s %(message)s

Usage:
    from logger import logger
    logger.info("Message")

The logger is configured via configure_logger().
"""

import logging as logger
from config import config

from .configure_logger import configure_logger

logger = configure_logger(logger_mode=config.Logger.logger_mode, file_name=config.Logger.logger_file)

__all__ = [
    "logger"
]
