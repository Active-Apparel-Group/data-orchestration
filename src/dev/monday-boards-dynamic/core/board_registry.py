#!/usr/bin/env python3
"""
Board Registry - Manage Monday.com board configurations and deployment tracking

This module manages the registry of configured Monday.com boards, their metadata,
and deployment status. It provides CRUD operations for board configurations
and tracks the lifecycle of board deployments.

Key Features:
- Board configuration management (create, read, update, delete)
- Deployment status tracking
- Schema version management
- Validation and error handling
- JSON-based persistence with backup capabilities
- Board discovery and listing

Usage:
    from core.board_registry import BoardRegistry
    
    registry = BoardRegistry()
    
    # Register a new board
    board_config = {
        "board_id": 12345,
        "board_name": "Customer Orders",
        "table_name": "MON_CustomerOrders",
        "database": "orders"
    }
    registry.register_board(board_config)
    
    # Get board configuration
    config = registry.get_board_config(12345)
    
    # List all boards
    boards = registry.list_all_boards()
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
from dataclasses import dataclass, asdict

# Repository root discovery (using the same pattern as existing scripts)
def find_repo_root():
    """Find the repository root by looking for utils folder"""
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:  # Not at filesystem root
        utils_path = current_path / "utils"
        if utils_path.exists() and (utils_path / "db_helper.py").exists():
            return current_path
        current_path = current_path.parent
    raise RuntimeError("Could not find repository root with utils folder")

# Add utils to path
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

try:
    import db_helper as db
    import mapping_helper as mapping
except ImportError as e:
    raise ImportError(f"Failed to import utilities: {e}. Ensure utils directory is accessible.")

# Import BoardSchema from the schema generator
sys.path.insert(0, str(Path(__file__).parent))
from board_schema_generator import BoardSchema, ColumnDefinition

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DeploymentStatus:
    """Track deployment status of a board"""
    ddl_deployed: bool = False
    script_generated: bool = False
    workflow_created: bool = False
    last_successful_run: Optional[datetime] = None
    last_deployment: Optional[datetime] = None
    deployment_errors: List[str] = None
    
    def __post_init__(self):
        if self.deployment_errors is None:
            self.deployment_errors = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        if self.last_successful_run:
            result['last_successful_run'] = self.last_successful_run.isoformat()
        if self.last_deployment:
            result['last_deployment'] = self.last_deployment.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DeploymentStatus':
        """Create from dictionary"""
        if 'last_successful_run' in data and data['last_successful_run']:
            data['last_successful_run'] = datetime.fromisoformat(data['last_successful_run'])
        if 'last_deployment' in data and data['last_deployment']:
            data['last_deployment'] = datetime.fromisoformat(data['last_deployment'])
        return cls(**data)


@dataclass
class BoardConfig:
    """Complete board configuration"""
    board_id: int
    board_name: str
    table_name: str
    database: str
    created_at: datetime
    updated_at: datetime
    schema_version: str = "1.0"
    deployment_status: DeploymentStatus = None
    metadata_path: Optional[str] = None
    script_path: Optional[str] = None
    workflow_path: Optional[str] = None
    configuration: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.deployment_status is None:
            self.deployment_status = DeploymentStatus()
        if self.configuration is None:
            self.configuration = {}
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        result['updated_at'] = self.updated_at.isoformat()
        result['deployment_status'] = self.deployment_status.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BoardConfig':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['deployment_status'] = DeploymentStatus.from_dict(data['deployment_status'])
        return cls(**data)


class BoardRegistryError(Exception):
    """Raised when board registry operations fail"""
    pass


class BoardValidationError(Exception):
    """Raised when board validation fails"""
    pass


class BoardRegistry:
    """
    Manages Monday.com board configurations and deployment tracking
    """
    
    def __init__(self, registry_dir: str = None):
        """
        Initialize the board registry
        
        Args:
            registry_dir: Directory containing registry files
        """
        if registry_dir is None:
            registry_dir = Path(__file__).parent.parent / "metadata"
        
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        
        self.registry_file = self.registry_dir / "board_registry.json"
        self.boards_dir = self.registry_dir / "boards"
        self.boards_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry
        self._registry = self._load_registry()
        
        logger.info(f"Initialized BoardRegistry with {len(self._registry)} boards")
    
    def _load_registry(self) -> Dict[int, BoardConfig]:
        """Load board registry from JSON file"""
        if not self.registry_file.exists():
            logger.info("Creating new board registry")
            return {}
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            registry = {}
            for board_id_str, config_data in data.items():
                board_id = int(board_id_str)
                registry[board_id] = BoardConfig.from_dict(config_data)
            
            logger.info(f"Loaded registry with {len(registry)} boards")
            return registry
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            # Create backup of corrupted file
            backup_path = self.registry_file.with_suffix('.json.backup')
            if self.registry_file.exists():
                self.registry_file.rename(backup_path)
                logger.warning(f"Corrupted registry backed up to {backup_path}")
            return {}
    
    def _save_registry(self) -> None:
        """Save board registry to JSON file"""
        try:
            # Convert to serializable format
            data = {}
            for board_id, config in self._registry.items():
                data[str(board_id)] = config.to_dict()
            
            # Write to temporary file first
            temp_file = self.registry_file.with_suffix('.json.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.registry_file)
            logger.debug(f"Saved registry with {len(self._registry)} boards")
            
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
            raise BoardRegistryError(f"Failed to save registry: {e}")
    
    def register_board(
        self, 
        board_schema: Union[BoardSchema, Dict[str, Any]], 
        force: bool = False
    ) -> BoardConfig:
        """
        Register a new board in the registry
        
        Args:
            board_schema: BoardSchema object or dictionary with board configuration
            force: Overwrite existing board if it exists
            
        Returns:
            BoardConfig object
        """
        # Handle both BoardSchema objects and dictionaries
        if isinstance(board_schema, BoardSchema):
            board_id = board_schema.board_id
            board_name = board_schema.board_name
            table_name = board_schema.table_name
            database = board_schema.database
        else:
            # Dictionary input
            board_id = board_schema["board_id"]
            board_name = board_schema["board_name"]
            table_name = board_schema["table_name"]
            database = board_schema.get("database", "orders")
        
        # Validation
        self._validate_board_config(board_id, board_name, table_name, database)
        
        # Check if board already exists
        if board_id in self._registry and not force:
            raise BoardRegistryError(f"Board {board_id} already registered. Use force=True to overwrite.")
        
        # Create board configuration
        now = datetime.now()
        board_config = BoardConfig(
            board_id=board_id,
            board_name=board_name,
            table_name=table_name,
            database=database,
            created_at=now if board_id not in self._registry else self._registry[board_id].created_at,
            updated_at=now,
            deployment_status=DeploymentStatus()
        )
        
        # Store in registry
        self._registry[board_id] = board_config
        self._save_registry()
        
        logger.info(f"Registered board {board_id}: '{board_name}' → {table_name}")
        return board_config
    
    def _validate_board_config(self, board_id: int, board_name: str, table_name: str, database: str):
        """Validate board configuration parameters"""
        if not isinstance(board_id, int) or board_id <= 0:
            raise BoardValidationError(f"Invalid board_id: {board_id}")
        
        if not board_name or not isinstance(board_name, str):
            raise BoardValidationError(f"Invalid board_name: {board_name}")
        
        if not table_name or not isinstance(table_name, str):
            raise BoardValidationError(f"Invalid table_name: {table_name}")
        
        if not database or not isinstance(database, str):
            raise BoardValidationError(f"Invalid database: {database}")
        
        # Check table name format
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', table_name):
            raise BoardValidationError(f"Invalid table name format: {table_name}")
    
    def get_board_config(self, board_id: int) -> Optional[BoardConfig]:
        """
        Get board configuration by ID
        
        Args:
            board_id: Monday.com board ID
            
        Returns:
            BoardConfig object or None if not found
        """
        return self._registry.get(board_id)
    
    def list_all_boards(self) -> List[BoardConfig]:
        """
        List all registered boards
        
        Returns:
            List of BoardConfig objects
        """
        return list(self._registry.values())
    
    def update_board_status(
        self, 
        board_id: int, 
        status_updates: Dict[str, Any]
    ) -> bool:
        """
        Update deployment status for a board
        
        Args:
            board_id: Monday.com board ID
            status_updates: Dictionary of status updates
            
        Returns:
            True if successful
        """
        if board_id not in self._registry:
            raise BoardRegistryError(f"Board {board_id} not found in registry")
        
        board_config = self._registry[board_id]
        
        # Update deployment status
        for key, value in status_updates.items():
            if hasattr(board_config.deployment_status, key):
                setattr(board_config.deployment_status, key, value)
            else:
                logger.warning(f"Unknown status field: {key}")
        
        # Update modified timestamp
        board_config.updated_at = datetime.now()
        
        self._save_registry()
        logger.info(f"Updated status for board {board_id}: {status_updates}")
        return True
    
    def remove_board(self, board_id: int) -> bool:
        """
        Remove board from registry
        
        Args:
            board_id: Monday.com board ID
            
        Returns:
            True if successful
        """
        if board_id not in self._registry:
            raise BoardRegistryError(f"Board {board_id} not found in registry")
        
        board_config = self._registry[board_id]
        board_name = board_config.board_name
        
        # Remove from registry
        del self._registry[board_id]
        self._save_registry()
        
        logger.info(f"Removed board {board_id}: '{board_name}' from registry")
        return True
    
    def get_boards_by_status(self, **status_filters) -> List[BoardConfig]:
        """
        Get boards by deployment status
        
        Args:
            **status_filters: Status filters (e.g., ddl_deployed=True)
            
        Returns:
            List of matching BoardConfig objects
        """
        matching_boards = []
        
        for board_config in self._registry.values():
            match = True
            for key, value in status_filters.items():
                if hasattr(board_config.deployment_status, key):
                    if getattr(board_config.deployment_status, key) != value:
                        match = False
                        break
                else:
                    match = False
                    break
            
            if match:
                matching_boards.append(board_config)
        
        return matching_boards
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """
        Get summary of deployment status across all boards
        
        Returns:
            Dictionary with deployment statistics
        """
        total_boards = len(self._registry)
        
        if total_boards == 0:
            return {"total_boards": 0}
        
        ddl_deployed = sum(1 for bc in self._registry.values() if bc.deployment_status.ddl_deployed)
        script_generated = sum(1 for bc in self._registry.values() if bc.deployment_status.script_generated)
        workflow_created = sum(1 for bc in self._registry.values() if bc.deployment_status.workflow_created)
        
        fully_deployed = sum(1 for bc in self._registry.values() 
                           if all([bc.deployment_status.ddl_deployed,
                                  bc.deployment_status.script_generated,
                                  bc.deployment_status.workflow_created]))
        
        return {
            "total_boards": total_boards,
            "ddl_deployed": ddl_deployed,
            "script_generated": script_generated,
            "workflow_created": workflow_created,
            "fully_deployed": fully_deployed,
            "deployment_percentage": (fully_deployed / total_boards) * 100
        }
    
    def export_registry(self, output_path: str = None) -> str:
        """
        Export registry to JSON file
        
        Args:
            output_path: Output file path (optional)
            
        Returns:
            Path to exported file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.registry_dir / f"board_registry_export_{timestamp}.json"
        
        output_path = Path(output_path)
        
        # Export with additional metadata
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_boards": len(self._registry),
            "registry": {str(k): v.to_dict() for k, v in self._registry.items()}
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported registry to {output_path}")
        return str(output_path)


# Convenience functions
def register_board_from_schema(board_schema: BoardSchema, force: bool = False) -> BoardConfig:
    """
    Convenience function to register a board from a BoardSchema object
    
    Args:
        board_schema: BoardSchema object
        force: Overwrite existing board if it exists
        
    Returns:
        BoardConfig object
    """
    registry = BoardRegistry()
    return registry.register_board(board_schema, force)


def get_board_by_id(board_id: int) -> Optional[BoardConfig]:
    """
    Convenience function to get a board configuration by ID
    
    Args:
        board_id: Monday.com board ID
        
    Returns:
        BoardConfig object or None
    """
    registry = BoardRegistry()
    return registry.get_board_config(board_id)


if __name__ == "__main__":
    # Test board registry functionality
    logger.info("Testing Board Registry")
    
    try:
        registry = BoardRegistry()
        
        # Test with existing Planning board
        test_board_config = {
            "board_id": 8709134353,
            "board_name": "Planning",
            "table_name": "MON_Planning",
            "database": "orders"
        }
        
        # Register the board
        board_config = registry.register_board(test_board_config, force=True)
        print(f"✅ Registered board: {board_config.board_name}")
        
        # Update status
        status_updates = {
            "ddl_deployed": True,
            "script_generated": True,
            "last_deployment": datetime.now()
        }
        registry.update_board_status(8709134353, status_updates)
        print("✅ Updated board status")
        
        # List all boards
        boards = registry.list_all_boards()
        print(f"✅ Found {len(boards)} registered boards")
        
        # Get deployment summary
        summary = registry.get_deployment_summary()
        print(f"✅ Deployment summary: {summary}")
        
        # Export registry
        export_path = registry.export_registry()
        print(f"✅ Exported registry to: {export_path}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
