import sys
import os
from loguru import logger

def setup_logger(log_file: str = "logs/kolimarii.log", level: str = "INFO"):
    """
    Sets up the loguru logger with console and file handlers.
    
    Args:
        log_file (str): Path to the log file.
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Remove default handler
    logger.remove()

    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Add console handler with custom formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # Add file handler with rotation and retention
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation="10 MB",
        retention="1 week",
        compression="zip",
    )

    logger.info("Kolimarii Logger initialized successfully.")

# Initialize a default logger instance for imports
# This will use the default log file name unless overridden
setup_logger()
