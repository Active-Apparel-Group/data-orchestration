#!/usr/bin/env python3
"""
Logger Helper for Monday.com Data Integration
Provides unified logging interface for both VS Code/local development and Kestra orchestration
"""

import os
import sys
from pathlib import Path

def get_logger(name="monday_integration"):
    """
    Get appropriate logger based on environment (Kestra vs local development)
    
    Returns:
        logger: Either Kestra.logger() if running in Kestra, or standard Python logger for local dev
    """
      # Option 1: Try to use Kestra logger if available (running in Kestra environment)
    try:
        from kestra import Kestra
        logger = Kestra.logger()
        logger.info(f"Using Kestra logger for {name}")
        return KestralLoggerWrapper(logger)
    except ImportError:
        # Option 2: Fall back to standard Python logging for local development
        import logging
        
        logger = logging.getLogger(name)
        
        # Only configure if not already configured (avoid duplicate handlers)
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # Try to add file handler (fallback to console if fails)
            try:
                # Find repository root for log file
                current_path = Path(__file__).resolve()
                while current_path.parent != current_path:
                    if (current_path / "utils").exists():
                        repo_root = current_path
                        break
                    current_path = current_path.parent
                else:
                    repo_root = Path.cwd()
                
                log_file = repo_root / 'monday_integration.log'
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (PermissionError, OSError):
                pass  # File handler failed, will use console only
            
            # Always add console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        logger.info(f"Using standard Python logger for {name}")
        return StandardLoggerWrapper(logger)

class LoggerWrapper:
    """Base wrapper class to provide consistent interface"""
    def __init__(self, logger):
        self._logger = logger
    
    def info(self, msg, *args, **kwargs):
        """Log info message"""
        if args:
            msg = msg % args
        self._logger.info(msg)
    
    def debug(self, msg, *args, **kwargs):
        """Log debug message"""
        if args:
            msg = msg % args
        self._logger.debug(msg)
    
    def warning(self, msg, *args, **kwargs):
        """Log warning message"""
        if args:
            msg = msg % args
        self._logger.warning(msg)
    
    def error(self, msg, *args, **kwargs):
        """Log error message"""
        if args:
            msg = msg % args
        self._logger.error(msg)
    
    def critical(self, msg, *args, **kwargs):
        """Log critical message"""
        if args:
            msg = msg % args
        self._logger.critical(msg)

class KestralLoggerWrapper(LoggerWrapper):
    """Wrapper for Kestra logger"""
    pass

class StandardLoggerWrapper(LoggerWrapper):
    """Wrapper for standard Python logger"""
    pass

# Convenience functions for direct import
_default_logger = None

def get_default_logger():
    """Get the default logger instance"""
    global _default_logger
    if _default_logger is None:
        _default_logger = get_logger()
    return _default_logger

def info(msg, *args, **kwargs):
    """Log info message using default logger"""
    get_default_logger().info(msg, *args, **kwargs)

def debug(msg, *args, **kwargs):
    """Log debug message using default logger"""
    get_default_logger().debug(msg, *args, **kwargs)

def warning(msg, *args, **kwargs):
    """Log warning message using default logger"""
    get_default_logger().warning(msg, *args, **kwargs)

def error(msg, *args, **kwargs):
    """Log error message using default logger"""
    get_default_logger().error(msg, *args, **kwargs)

def critical(msg, *args, **kwargs):
    """Log critical message using default logger"""
    get_default_logger().critical(msg, *args, **kwargs)

# Environment detection helpers
def is_kestra_environment():
    """Check if running in Kestra environment"""
    try:
        from kestra import Kestra
        return True
    except ImportError:
        return False

def is_vscode_environment():
    """Check if running in VS Code environment"""
    return os.getenv('VSCODE_PID') is not None or 'code' in sys.executable.lower()

def get_environment_info():
    """Get information about current execution environment"""
    env_info = {
        'is_kestra': is_kestra_environment(),
        'is_vscode': is_vscode_environment(),
        'python_executable': sys.executable,
        'working_directory': os.getcwd()
    }
    return env_info
