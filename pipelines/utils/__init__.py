# Legacy utils module
# This module contains legacy utilities that are still in use
# during the transition to the modern src/pipelines structure

import sys
from pathlib import Path

# Direct import approach using sys.modules and importlib
import importlib.util

# Get the current directory
pipelines_utils_path = Path(__file__).parent

def load_module_from_file(module_name, file_path):
    """Load a module from a specific file path"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except Exception as e:
        print(f"Warning: Could not load {module_name} from {file_path}: {e}")
    return None

try:
    # Load db_helper module
    db_helper_path = pipelines_utils_path / "db_helper.py"
    db_helper_module = load_module_from_file("db_helper", db_helper_path)
    
    # Load logger_helper module
    logger_helper_path = pipelines_utils_path / "logger_helper.py"
    logger_helper_module = load_module_from_file("logger_helper", logger_helper_path)
    
    if db_helper_module and logger_helper_module:
        # Create a db object that has the functions as attributes for backward compatibility
        class DbWrapper:
            def __init__(self):
                self.get_connection = db_helper_module.get_connection
                self.run_query = db_helper_module.run_query
                self.execute = db_helper_module.execute

        db = DbWrapper()
        
        # Create logger wrapper
        class LoggerWrapper:
            def __init__(self):
                self.get_logger = logger_helper_module.get_logger
        
        logger = LoggerWrapper()
        
    else:
        raise ImportError("Could not load helper modules")
        
except Exception as e:
    print(f"Warning: Could not import from pipelines/utils helpers: {e}")
    
    # Create minimal fallback wrappers
    class DbWrapper:
        def get_connection(self, *args, **kwargs):
            raise NotImplementedError("Database connection not available")
        def run_query(self, *args, **kwargs):
            raise NotImplementedError("Database query not available")
        def execute(self, *args, **kwargs):
            raise NotImplementedError("Database execute not available")
    
    class LoggerWrapper:
        def get_logger(self, name):
            import logging
            return logging.getLogger(name)
    
    db = DbWrapper()
    logger = LoggerWrapper()

# Add config helper for monday_sync compatibility
try:
    config_helper_path = pipelines_utils_path / "config_helper.py"
    config_helper_module = load_module_from_file("config_helper", config_helper_path)
    
    if config_helper_module:
        class ConfigWrapper:
            def __init__(self):
                self.get_config = config_helper_module.get_config
        
        config = ConfigWrapper()
    else:
        raise ImportError("Could not load config_helper")
        
except Exception:
    # Create minimal config compatibility if config_helper doesn't exist
    class ConfigWrapper:
        @staticmethod
        def get_config(*args, **kwargs):
            return {}
    config = ConfigWrapper()
