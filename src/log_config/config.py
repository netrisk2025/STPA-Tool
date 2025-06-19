"""
Logging configuration for STPA Tool
Provides centralized logging setup and management.
"""

import logging
import os
from pathlib import Path
from typing import Optional

# Import handlers separately to avoid import issues
try:
    from logging.handlers import RotatingFileHandler
except ImportError:
    # Fallback for environments where handlers might not be available
    RotatingFileHandler = None


class LoggingConfig:
    """
    Centralized logging configuration for the STPA Tool.
    """
    
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    DEFAULT_LEVEL = logging.INFO
    
    @classmethod
    def setup_logging(
        cls,
        log_level: int = DEFAULT_LEVEL,
        log_file: Optional[str] = None,
        log_format: str = DEFAULT_FORMAT,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ) -> None:
        """
        Set up application-wide logging configuration.
        
        Args:
            log_level: Logging level (default: INFO)
            log_file: Path to log file (optional)
            log_format: Log message format
            max_bytes: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        # Create formatter
        formatter = logging.Formatter(log_format)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
        
        # File handler (if log file specified)
        if log_file and RotatingFileHandler:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
        elif log_file:
            # Fallback to basic FileHandler if RotatingFileHandler not available
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for the specified module.
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Logger instance
        """
        return logging.getLogger(name)
    
    @classmethod
    def set_level(cls, level: int) -> None:
        """
        Set the logging level for all handlers.
        
        Args:
            level: New logging level
        """
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        for handler in root_logger.handlers:
            handler.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return LoggingConfig.get_logger(name)