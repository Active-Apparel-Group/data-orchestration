# Utils Module Development Standards - Data Orchestration Project

## 🎯 Purpose & Organization

### **What Goes in utils/**
- **Python modules only** (.py files with classes/functions)
- **Reusable utilities** that can be imported by scripts/, tests/, dev/
- **Shared functionality** used across multiple pipeline components
- **Configuration files** (config.yaml, reference mappings that modules need)

### **What Does NOT Go in utils/**
- ❌ Executable scripts (those go in scripts/)
- ❌ SQL files (those go in sql/)
- ❌ Documentation (those go in docs/)
- ❌ Test files (those go in tests/)

## 🔧 Standard Module Template

### **1. Module Header Pattern**
```python
"""
[Module Name] - [Brief Description]
Purpose: [What this module provides]
Location: utils/[module_name].py
"""
import sys
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# Standard repo root resolution
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
```

### **2. Class Design Pattern**
```python
class UtilityClass:
    """
    Brief class description
    
    Key Features:
    - Feature 1
    - Feature 2
    - Feature 3
    
    Usage:
        utility = UtilityClass(config_param="value")
        result = utility.transform_data(data)
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the utility class"""
        self.logger = logging.getLogger(__name__)
        self._load_configuration(config_file)
        
    def _load_configuration(self, config_file: Optional[str] = None):
        """Load configuration from YAML file"""
        # Implementation here
        pass
```

### **3. Factory Function Pattern**
```python
# Always provide a simple factory function for easy usage
def create_utility(**kwargs) -> UtilityClass:
    """
    Factory function for easy utility creation
    
    Args:
        **kwargs: Configuration parameters
        
    Returns:
        UtilityClass: Configured utility instance
    """
    return UtilityClass(**kwargs)
```

## 📋 Configuration Loading Standards

### **Standard Pattern for Loading YAML Config**
```python
def _load_configuration(self, config_file: Optional[str] = None):
    """Load configuration from YAML file with robust path resolution"""
    
    # Use standard path resolution pattern
    if config_file is None:
        # Check multiple possible locations
        utils_path = repo_root / "utils" / "config.yaml"
        sql_path = repo_root / "sql" / "mappings" / "canonical-references.yaml"
        
        if utils_path.exists():
            config_file = str(utils_path)
        elif sql_path.exists():
            config_file = str(sql_path)
        else:
            raise FileNotFoundError("Could not find configuration file")
    
    self.config_file = Path(config_file)
    
    try:
        with open(self.config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.logger.info(f"Configuration loaded from {self.config_file}")
    except Exception as e:
        self.logger.error(f"Failed to load configuration: {str(e)}")
        raise
```

## 🚨 Critical Import Standards

### **Module Imports**
```python
# ✅ CORRECT - Import other utils modules
import db_helper as db
import logger_helper
from utils.simple_mapper import SimpleOrdersMapper

# ❌ WRONG - Never import from sql/, docs/, or scripts/
from sql.mappings.something import Something  # BAD
```

### **Path Resolution**
```python
# ✅ ALWAYS use robust path resolution
repo_root = find_repo_root()
config_path = repo_root / "utils" / "config.yaml"

# ❌ NEVER use relative paths
config_path = "../utils/config.yaml"  # BAD
```

### **Loading Files from sql/mappings/**
```python
# ✅ CORRECT - Load files from sql/mappings/ as text/data, not imports
mapping_path = repo_root / "sql" / "mappings" / "canonical-references.yaml"
with open(mapping_path, 'r') as f:
    mapping_data = yaml.safe_load(f)

# ❌ WRONG - Never try to import from sql/
from sql.mappings.canonical_references import data  # BAD
```

## 🎯 Data Processing Standards

### **DataFrame Transformation Pattern**
```python
def transform_dataframe(self, df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """
    Transform DataFrame with canonical transformations
    
    Args:
        df: Input DataFrame
        **kwargs: Transformation parameters
        
    Returns:
        pd.DataFrame: Transformed DataFrame
    """
    if df.empty:
        self.logger.warning("Empty DataFrame provided for transformation")
        return df
        
    original_shape = df.shape
    
    try:
        # Apply transformations
        transformed_df = df.copy()
        
        # Track transformations for audit
        self._track_transformation("transform_dataframe", original_shape, transformed_df.shape)
        
        return transformed_df
        
    except Exception as e:
        self.logger.error(f"DataFrame transformation failed: {str(e)}")
        raise
```

### **Audit Trail Pattern**
```python
def get_transformation_audit(self) -> Dict[str, Any]:
    """
    Return audit trail of transformations applied
    
    Returns:
        Dict containing transformation statistics and metadata
    """
    return {
        'transformations_applied': self.transformations_applied,
        'total_records_processed': self.total_records_processed,
        'timestamp': self.last_transformation_time,
        'config_file': str(self.config_file)
    }

def _track_transformation(self, operation: str, input_shape: tuple, output_shape: tuple):
    """Track transformation for audit purposes"""
    if not hasattr(self, 'transformations_applied'):
        self.transformations_applied = []
        
    self.transformations_applied.append({
        'operation': operation,
        'input_shape': input_shape,
        'output_shape': output_shape,
        'timestamp': pd.Timestamp.now()
    })
```

## 🔄 Integration Patterns

### **Database Integration**
```python
# Always use table-aware database helpers
import db_helper as db

def query_data(self, table_name: str, filters: Dict = None) -> pd.DataFrame:
    """Query data using table-aware connection"""
    try:
        query = self._build_query(table_name, filters)
        return db.run_query_for_table(query, table_name)
    except Exception as e:
        self.logger.error(f"Query failed for table {table_name}: {str(e)}")
        raise
```

### **Configuration Hot-Reload Pattern**
```python
def reload_configuration(self):
    """Reload configuration if file has changed"""
    if self.config_file.stat().st_mtime > self.last_config_load_time:
        self.logger.info("Configuration file changed, reloading...")
        self._load_configuration()
        self.last_config_load_time = self.config_file.stat().st_mtime
        self.logger.info("Configuration reloaded due to file changes")
```

## 📝 Documentation Standards

### **Docstring Requirements**
- **Class docstrings**: Purpose, key features, usage examples
- **Method docstrings**: Args, Returns, Raises with clear descriptions
- **Type hints**: Use typing module for all function signatures
- **Examples**: Include usage examples in docstrings

### **Error Handling**
```python
def method_with_error_handling(self, param: str) -> str:
    """
    Method with proper error handling
    
    Args:
        param: Input parameter
        
    Returns:
        str: Processed result
        
    Raises:
        ValueError: If param is invalid
        FileNotFoundError: If required files not found
    """
    try:
        # Method implementation
        result = self._process_param(param)
        return result
        
    except ValueError as e:
        self.logger.error(f"Invalid parameter {param}: {str(e)}")
        raise
    except Exception as e:
        self.logger.error(f"Unexpected error in method: {str(e)}")
        raise
```

## 🎯 Testing Standards

### **Test Integration**
```python
def _validate_input(self, data: Any) -> bool:
    """Validate input data for testing and production"""
    # Add validation logic
    return True

def _create_test_data(self) -> pd.DataFrame:
    """Create test data for development and testing"""
    # Only include in development builds
    return pd.DataFrame()
```

## 📋 Module Checklist

When creating a new utils module, ensure:

- [ ] **File placement**: Located in utils/ directory
- [ ] **Import pattern**: Uses standard repo root resolution
- [ ] **Configuration**: Robust YAML loading with error handling
- [ ] **Logging**: Uses proper logging patterns
- [ ] **Type hints**: All methods have type annotations
- [ ] **Docstrings**: Comprehensive documentation
- [ ] **Error handling**: Try/catch with meaningful error messages
- [ ] **Factory function**: Simple creation function provided
- [ ] **Audit trail**: Transformation tracking if applicable
- [ ] **Testing hooks**: Validation and test data methods
- [ ] **Integration**: Works with existing db_helper patterns

## 🚨 Common Mistakes to Avoid

- ❌ **Importing from sql/**: Never import Python modules from sql/ folder
- ❌ **Hardcoded paths**: Always use repo root resolution
- ❌ **Missing error handling**: Always wrap file operations in try/catch
- ❌ **No logging**: Every utility should use proper logging
- ❌ **No type hints**: All public methods need type annotations
- ❌ **No factory function**: Always provide easy creation pattern
