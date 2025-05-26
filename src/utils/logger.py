import logging
import os
import sys
import time
from typing import Optional

class Logger:
    """
    A custom logger for the blockchain gossip network.
    """
    
    def __init__(self, name: str, log_level: int = logging.INFO, log_file: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            name: The name of the logger
            log_level: The logging level (default: INFO)
            log_file: The path to the log file (default: None, logs to console only)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False
        
        # Clear any existing handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add console handler to logger
        self.logger.addHandler(console_handler)
        
        # Add file handler if log_file is provided
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """
        Log a debug message.
        
        Args:
            message: The message to log
        """
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """
        Log an info message.
        
        Args:
            message: The message to log
        """
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """
        Log a warning message.
        
        Args:
            message: The message to log
        """
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """
        Log an error message.
        
        Args:
            message: The message to log
        """
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """
        Log a critical message.
        
        Args:
            message: The message to log
        """
        self.logger.critical(message)


def get_logger(name: str, log_level: int = logging.INFO, log_file: Optional[str] = None) -> Logger:
    """
    Get a logger instance.
    
    Args:
        name: The name of the logger
        log_level: The logging level (default: INFO)
        log_file: The path to the log file (default: None, logs to console only)
        
    Returns:
        Logger: A logger instance
    """
    return Logger(name, log_level, log_file)