"""
File-based logging system for MT5 Automation
Creates timestamped log files and manages log formatting
"""
import os
import logging
from datetime import datetime
from pathlib import Path
import config

# Use log directory from config if available, otherwise use default
try:
    LOG_DIRECTORY = config.LOG_DIRECTORY
except AttributeError:
    LOG_DIRECTORY = os.path.join(os.path.dirname(__file__), "logs")

# Ensure log directory exists
os.makedirs(LOG_DIRECTORY, exist_ok=True)


def setup_logger(log_file_name=None):
    """
    Set up a file-based logger with timestamped filename
    
    Args:
        log_file_name: Optional custom filename. If not provided, uses timestamp.
        
    Returns:
        Logger instance
    """
    # Create log filename with timestamp if not provided
    if log_file_name is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file_name = f"automation_{timestamp}.log"
    
    log_file_path = os.path.join(LOG_DIRECTORY, log_file_name)
    
    # Create logger
    logger = logging.getLogger('MT5Automation')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create file handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter - simple format for file logging
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    # Also add console handler for real-time monitoring
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file_path


def get_logger():
    """
    Get the current logger instance (creates one if doesn't exist)
    """
    logger = logging.getLogger('MT5Automation')
    if not logger.handlers:
        # Initialize with default settings if not already set up
        setup_logger()
    return logger

