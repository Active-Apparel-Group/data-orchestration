#!/usr/bin/env python3
"""
Board Schema Generator - Monday.com Board Discovery and SQL DDL Generation

This module discovers Monday.com board structure via API and generates
corresponding SQL Server database schemas and DDL statements.

Key Features:
- Automatic board introspection via Monday.com GraphQL API
- Comprehensive field type mapping (Monday.com → SQL Server)
- DDL generation with proper constraints and indexing
- Metadata storage for future reference and schema evolution
- Integration with existing db_helper infrastructure

Usage:
    from core.board_schema_generator import BoardSchemaGenerator
    
    generator = BoardSchemaGenerator()
    schema = generator.discover_board_structure(board_id=12345)
    ddl = generator.generate_sql_schema(schema, table_name="MON_NewBoard")
    generator.execute_ddl(ddl, database="orders")
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging

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

# Add utils to path using repository root method
repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

try:
    import db_helper as db
    import mapping_helper as mapping
except ImportError as e:
    raise ImportError(f"Failed to import utilities: {e}. Ensure utils directory is accessible.")

# Load configuration
config = db.load_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ColumnDefinition:
    """Monday.com column definition with SQL mapping"""
    monday_id: str
    monday_title: str
    monday_type: str
    sql_column: str
    sql_type: str
    extraction_field: str = "text"  # Which field to extract from Monday.com API response
    nullable: bool = True
    is_system_field: bool = False
    conversion_logic: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class BoardSchema:
    """Complete board schema definition"""
    board_id: int
    board_name: str
    table_name: str
    database: str
    discovered_at: datetime
    columns: List[ColumnDefinition]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result['discovered_at'] = self.discovered_at.isoformat()
        return result


class BoardSchemaGeneratorError(Exception):
    """Raised when board schema generation fails"""
    pass


class BoardSchemaGenerator:
    """
    Discovers Monday.com board structure and generates SQL Server schemas
    Uses centralized data_mapping.yaml for consistent type mappings
    """
    
    def __init__(self):
        """Initialize the schema generator"""
        self.monday_token = os.getenv('MONDAY_API_KEY') or config.get('apis', {}).get('monday', {}).get('api_token')
        self.api_url = config.get('apis', {}).get('monday', {}).get('api_url', "https://api.monday.com/v2")
        self.api_version = "2025-04"
        
        if not self.monday_token or self.monday_token == "YOUR_MONDAY_API_TOKEN_HERE":
            raise BoardSchemaGeneratorError(
                "Monday.com API token not configured. Please set MONDAY_API_KEY environment variable or update utils/config.yaml"
            )
        
        self.headers = {
            "Authorization": f"Bearer {self.monday_token}",
            "API-Version": self.api_version,
            "Content-Type": "application/json"
        }
          # Load type mappings from centralized data_mapping.yaml
        self.type_mappings = self._load_type_mappings()
        
        logger.info(f"Initialized BoardSchemaGenerator with API version {self.api_version}")
    
    def _load_type_mappings(self) -> Dict[str, Tuple[str, str, bool]]:
        """
        Load Monday.com to SQL type mappings from centralized data_mapping.yaml
        Uses the proven extraction logic from get_board_planning.py
        
        Returns:
            Dict mapping monday_type -> (sql_type, extraction_method, nullable)
        """
        try:
            # Load the centralized mapping from data_mapping.yaml
            monday_to_sql = mapping.get_all_type_mappings('monday_to_sql')
            
            # Combine SQL types with extraction logic from get_board_planning.py
            # This matches the proven working extraction logic
            type_mappings = {
                # Text Types - use 'text' field
                "text": (monday_to_sql.get("text", "NVARCHAR(MAX)"), "text", True),
                "long_text": (monday_to_sql.get("long_text", "NVARCHAR(MAX)"), "text", True),
                "email": (monday_to_sql.get("email", "NVARCHAR(255)"), "text", True),
                "phone": (monday_to_sql.get("phone", "NVARCHAR(50)"), "text", True),
                "link": (monday_to_sql.get("link", "NVARCHAR(500)"), "text", True),
                
                # Numeric Types - use 'number' field
                "numbers": (monday_to_sql.get("numbers", "BIGINT"), "number", True),
                "rating": (monday_to_sql.get("rating", "INT"), "number", True),
                "numeric": (monday_to_sql.get("numeric", "DECIMAL(18,2)"), "number", True),
                
                # Date/Time Types - use 'text' field (formatted dates)
                "date": (monday_to_sql.get("date", "DATE"), "text", True),
                "datetime": (monday_to_sql.get("datetime", "DATETIME2"), "text", True),
                "timeline": (monday_to_sql.get("timeline", "NVARCHAR(MAX)"), "text", True),
                
                # Choice Types - use specific field for each type
                "status": (monday_to_sql.get("status", "NVARCHAR(100)"), "label", True),  # Use 'label' for status
                "dropdown": (monday_to_sql.get("dropdown", "NVARCHAR(100)"), "text", True),
                "checkbox": (monday_to_sql.get("checkbox", "BIT"), "text", True),
                "color_picker": (monday_to_sql.get("color", "NVARCHAR(100)"), "text", True),
                
                # Relationship Types - use 'display_value' field
                "people": (monday_to_sql.get("people", "NVARCHAR(MAX)"), "text", True),
                "dependency": (monday_to_sql.get("dependency", "NVARCHAR(MAX)"), "display_value", True),
                "board_relation": (monday_to_sql.get("board_relation", "NVARCHAR(MAX)"), "display_value", True),
                "mirror": (monday_to_sql.get("mirror", "NVARCHAR(MAX)"), "display_value", True),
                "formula": (monday_to_sql.get("formula", "NVARCHAR(MAX)"), "display_value", True),
                
                # File and Special Types
                "file": (monday_to_sql.get("file", "NVARCHAR(MAX)"), "text", True),
                "tags": (monday_to_sql.get("tags", "NVARCHAR(MAX)"), "text", True),
                
                # Special case: item_id uses 'item_id' field
                "item_id": (monday_to_sql.get("item_id", "BIGINT"), "item_id", True),
                
                # System Fields (always present in Monday.com)
                "_item_id": (monday_to_sql.get("item_id", "BIGINT"), "item_id", False),
                "_item_name": (monday_to_sql.get("item_name", "NVARCHAR(500)"), "text", True),
                "_group_title": (monday_to_sql.get("group_title", "NVARCHAR(200)"), "text", True),
                "_updated_at": (monday_to_sql.get("updated_at", "DATETIME2"), "text", True),
                "_created_at": (monday_to_sql.get("created_at", "DATETIME2"), "text", True)
            }
            
            logger.info(f"Loaded {len(type_mappings)} type mappings from data_mapping.yaml")
            return type_mappings
            
        except Exception as e:
            logger.warning(f"Failed to load type mappings from data_mapping.yaml: {e}")
            logger.warning("Using fallback type mappings")
            
            # Fallback mappings if centralized mapping fails
            return {
                "text": ("NVARCHAR(MAX)", "text", True),
                "numbers": ("BIGINT", "number", True),
                "date": ("DATE", "text", True),
                "status": ("NVARCHAR(100)", "label", True),
                "dropdown": ("NVARCHAR(100)", "text", True),
                "item_id": ("BIGINT", "item_id", True),
                "_item_id": ("BIGINT", "item_id", False),
                "_item_name": ("NVARCHAR(500)", "text", True),
                "_group_title": ("NVARCHAR(200)", "text", True),
                "_updated_at": ("DATETIME2", "text", True),
                "_created_at": ("DATETIME2", "text", True)
            }
    
    @staticmethod
    def extract_value_from_monday(column_value: Dict[str, Any]) -> Any:
        """
        Extract the correct value from Monday.com column based on type.
        
        This uses the EXACT same logic as get_board_planning.py extract_value() function
        to ensure consistency with the proven working implementation.
        
        Args:
            column_value: Monday.com column_value object from GraphQL response
            
        Returns:
            Extracted value appropriate for the column type
        """
        cv = column_value
        column_type = cv["column"]["type"]
        
        # Handle different column types with proper value extraction
        # This is the EXACT logic from get_board_planning.py
        if column_type == "date":
            # For date columns, prefer the text value which is already formatted
            if cv.get("text") and cv.get("text").strip():
                return cv["text"]
            elif cv.get("value") and cv.get("value") != "None":
                return cv["value"]
            else:
                return None
        elif column_type == "dropdown" and cv.get("text"):
            return cv["text"]
        elif column_type == "status" and cv.get("label"):
            return cv["label"]
        elif column_type == "numbers" and cv.get("number") is not None:
            return cv["number"]
        elif column_type == "item_id" and cv.get("item_id"):
            return cv["item_id"]
        elif cv.get("display_value") and cv.get("display_value") != "":
            return cv["display_value"]
        elif cv.get("text"):
            return cv["text"]
        elif cv.get("value"):
            return cv["value"]
        
        return None
    
    def _execute_graphql_query(self, query: str) -> Dict[str, Any]:
        """Execute GraphQL query against Monday.com API"""
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"query": query},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                raise BoardSchemaGeneratorError(f"GraphQL errors: {result['errors']}")
            
            return result["data"]
            
        except requests.RequestException as e:
            raise BoardSchemaGeneratorError(f"API request failed: {e}")
        except json.JSONDecodeError as e:
            raise BoardSchemaGeneratorError(f"Failed to parse API response: {e}")
    
    def discover_board_structure(self, board_id: int) -> BoardSchema:
        """
        Discover the complete structure of a Monday.com board
        
        Args:
            board_id: Monday.com board identifier
            
        Returns:
            BoardSchema object with complete board structure
        """
        logger.info(f"Discovering structure for board {board_id}")
        
        # GraphQL query to get board metadata and columns
        query = f'''
        query GetBoardStructure {{
          boards(ids: {board_id}) {{
            id
            name
            description
            board_kind
            columns {{
              id
              title
              type
              description
              settings_str
            }}
            groups {{
              id
              title
              color
            }}
            items_page(limit: 1) {{
              items {{
                id
                name
                updated_at
                created_at
                column_values {{
                  column {{
                    id
                    title
                    type
                  }}
                  value
                  text
                }}
              }}
            }}
          }}
        }}
        '''
        
        try:
            data = self._execute_graphql_query(query)
            boards = data.get("boards", [])
            
            if not boards:
                raise BoardSchemaGeneratorError(f"Board {board_id} not found or not accessible")
            
            board = boards[0]
            board_name = board["name"]
            
            logger.info(f"Found board: '{board_name}' (ID: {board_id})")
            
            # Process columns to create column definitions
            columns = self._process_board_columns(board["columns"])
            
            # Add system fields that are always present
            system_columns = self._get_system_columns()
            columns.extend(system_columns)
            
            # Create board schema
            schema = BoardSchema(
                board_id=board_id,
                board_name=board_name,
                table_name=f"MON_{self._sanitize_name(board_name)}",
                database="orders",  # Default database
                discovered_at=datetime.now(),
                columns=columns,
                metadata={
                    "description": board.get("description"),
                    "board_kind": board.get("board_kind"),
                    "groups": board.get("groups", []),
                    "total_columns": len(columns),
                    "discovery_version": "1.0"
                }
            )
            
            logger.info(f"Discovered {len(columns)} columns for board '{board_name}'")
            return schema
            
        except Exception as e:
            raise BoardSchemaGeneratorError(f"Failed to discover board structure: {e}")
    
    def _process_board_columns(self, columns: List[Dict]) -> List[ColumnDefinition]:
        """Process Monday.com columns into ColumnDefinition objects"""
        processed_columns = []
        
        for col in columns:
            monday_type = col["type"]
            monday_title = col["title"]
            monday_id = col["id"]
            
            # Generate SQL column name (sanitized)
            sql_column = self._sanitize_column_name(monday_title)            # Map to SQL type and extraction logic using centralized mappings
            type_info = self.type_mappings.get(monday_type, ("NVARCHAR(MAX)", "text", True))
            sql_type, extraction_field, nullable = type_info
            
            # Generate conversion logic for special types
            conversion_logic = self._generate_conversion_logic(monday_type, monday_title)
            column_def = ColumnDefinition(
                monday_id=monday_id,
                monday_title=monday_title,
                monday_type=monday_type,
                sql_column=sql_column,
                sql_type=sql_type,
                extraction_field=extraction_field,
                nullable=nullable,
                is_system_field=False,
                conversion_logic=conversion_logic
            )
            
            processed_columns.append(column_def)
            logger.debug(f"Processed column: {monday_title} ({monday_type}) → {sql_column} ({sql_type})")        
        return processed_columns
    
    def _get_system_columns(self) -> List[ColumnDefinition]:
        """Get standard system columns that are always present"""
        return [            ColumnDefinition(
                monday_id="__item_id",
                monday_title="Item ID", 
                monday_type="item_id",
                sql_column="Item ID",
                sql_type="BIGINT",
                extraction_field="item_id",
                nullable=False,
                is_system_field=True
            ),
            ColumnDefinition(
                monday_id="__item_name",
                monday_title="Item Name",
                monday_type="text",
                sql_column="Item Name", 
                sql_type="NVARCHAR(500)",
                extraction_field="text",
                nullable=True,
                is_system_field=True
            ),
            ColumnDefinition(
                monday_id="__group_title",
                monday_title="Group Title",
                monday_type="text", 
                sql_column="Group Title",
                sql_type="NVARCHAR(200)",
                extraction_field="text",
                nullable=True,
                is_system_field=True
            ),
            ColumnDefinition(
                monday_id="__updated_at",
                monday_title="Updated At",
                monday_type="datetime",
                sql_column="Updated At",
                sql_type="DATETIME2",
                extraction_field="text",
                nullable=True,
                is_system_field=True
            ),
            ColumnDefinition(                monday_id="__created_at", 
                monday_title="Created At",
                monday_type="datetime",
                sql_column="Created At",
                sql_type="DATETIME2",
                extraction_field="text",
                nullable=True,
                is_system_field=True
            )
        ]
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize board name for SQL table naming"""
        # Remove special characters, replace spaces with underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
        sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
        return sanitized[:50]  # Limit length
    
    def _sanitize_column_name(self, name: str) -> str:
        """Preserve Monday.com column names exactly with SQL brackets"""
        # Simply return the original name - we'll use brackets in SQL
        # This preserves the exact Monday.com column names
        return name.strip()
    
    def _generate_conversion_logic(self, monday_type: str, monday_title: str) -> Optional[str]:
        """Generate type-specific conversion logic"""
        if monday_type == "date":
            return "safe_date_convert(extract_value(cv))"
        elif monday_type in ["numbers", "rating"]:
            return "safe_numeric_convert(extract_value(cv))"
        elif monday_type == "checkbox":
            return "1 if extract_value(cv) and extract_value(cv).lower() == 'true' else 0"
        elif monday_type in ["people", "tags"]:
            return "', '.join(extract_value(cv)) if isinstance(extract_value(cv), list) else extract_value(cv)"
        else:
            return None
    
    def generate_sql_schema(self, schema: BoardSchema, table_name: str = None) -> str:
        """
        Generate SQL DDL CREATE TABLE statements for both production and staging tables
        
        Args:
            schema: BoardSchema object
            table_name: Override table name (optional)
            
        Returns:
            SQL DDL statement for both production and staging tables
        """
        table_name = table_name or schema.table_name
        staging_table_name = f"stg_{table_name}"
        
        logger.info(f"Generating SQL DDL for production table {table_name} and staging table {staging_table_name}")
        
        # Build column definitions
        column_definitions = []
        
        for col in schema.columns:
            null_constraint = "" if col.nullable else " NOT NULL"
            column_def = f"    [{col.sql_column}] {col.sql_type}{null_constraint}"
            column_definitions.append(column_def)
        
        columns_ddl = ','.join(column_definitions)
        
        # Check for common indexable columns
        has_updated_at = any(col.sql_column == "Updated At" for col in schema.columns)
        has_group_title = any(col.sql_column == "Group Title" for col in schema.columns)
        
        # Build index statements
        production_indexes = []
        staging_indexes = []
        
        if has_updated_at:
            production_indexes.append(f"CREATE INDEX [IX_{table_name}_UpdatedAt] ON [dbo].[{table_name}] ([Updated At]);")
            staging_indexes.append(f"CREATE INDEX [IX_{staging_table_name}_UpdatedAt] ON [dbo].[{staging_table_name}] ([Updated At]);")
        
        if has_group_title:
            production_indexes.append(f"CREATE INDEX [IX_{table_name}_GroupTitle] ON [dbo].[{table_name}] ([Group Title]);")
            staging_indexes.append(f"CREATE INDEX [IX_{staging_table_name}_GroupTitle] ON [dbo].[{staging_table_name}] ([Group Title]);")
        
        production_indexes_ddl = "\n".join(production_indexes) if production_indexes else "-- No additional indexes needed"
        staging_indexes_ddl = "\n".join(staging_indexes) if staging_indexes else "-- No additional indexes needed"
        
        # Create DDL statement for both production and staging tables
        ddl = f"""-- Generated DDL for Monday.com Board: {schema.board_name}
-- Board ID: {schema.board_id}
-- Generated: {schema.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}
-- Total Columns: {len(schema.columns)}

-- ===============================================
-- PRODUCTION TABLE: {table_name}
-- ===============================================

-- Drop production table if it exists (development-safe)
DROP TABLE IF EXISTS [dbo].[{table_name}];

CREATE TABLE [dbo].[{table_name}] (
{columns_ddl},
    
    -- Constraints
    CONSTRAINT [PK_{table_name}] PRIMARY KEY CLUSTERED ([Item ID] ASC)
);

-- Create indexes for performance on production table
{production_indexes_ddl}

-- Add table description for production table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Monday.com Board: {schema.board_name} (ID: {schema.board_id}). Generated: {schema.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'{table_name}';

-- ===============================================
-- STAGING TABLE: {staging_table_name}
-- ===============================================

-- Drop staging table if it exists (development-safe)
DROP TABLE IF EXISTS [dbo].[{staging_table_name}];

CREATE TABLE [dbo].[{staging_table_name}] (
{columns_ddl},
    
    -- Constraints (same structure as production)
    CONSTRAINT [PK_{staging_table_name}] PRIMARY KEY CLUSTERED ([Item ID] ASC)
);

-- Create indexes for performance on staging table
{staging_indexes_ddl}

-- Add table description for staging table
EXEC sys.sp_addextendedproperty 
    @name = N'MS_Description',
    @value = N'Monday.com Board STAGING: {schema.board_name} (ID: {schema.board_id}). Generated: {schema.discovered_at.strftime('%Y-%m-%d %H:%M:%S')}',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'{staging_table_name}';
"""
        
        logger.info(f"Generated DDL with {len(schema.columns)} columns for both production and staging tables")
        return ddl
    
    def save_board_metadata(self, schema: BoardSchema, metadata_dir: str = None) -> str:
        """
        Save board metadata to JSON file for future reference
        
        Args:
            schema: BoardSchema object
            metadata_dir: Directory to save metadata (optional)
            
        Returns:
            Path to saved metadata file
        """
        if metadata_dir is None:
            metadata_dir = Path(__file__).parent.parent / "metadata" / "boards"
        
        metadata_dir = Path(metadata_dir)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"board_{schema.board_id}_metadata.json"
        filepath = metadata_dir / filename
        
        # Convert schema to dictionary for JSON serialization
        metadata = schema.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved board metadata to {filepath}")
        return str(filepath)
    
    def execute_ddl(self, ddl: str, database: str = "orders") -> bool:
        """
        Execute DDL statement against target database
        
        Args:
            ddl: SQL DDL statement
            database: Target database name
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Executing DDL against database '{database}'")
            db.execute(ddl, database)
            logger.info("DDL executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute DDL: {e}")
            raise BoardSchemaGeneratorError(f"DDL execution failed: {e}")


# Convenience functions for direct usage
def discover_and_generate_schema(board_id: int, table_name: str = None, database: str = "orders") -> Tuple[BoardSchema, str]:
    """
    Convenience function to discover board and generate schema in one call
    
    Args:
        board_id: Monday.com board ID
        table_name: SQL table name (optional, will be generated)
        database: Target database
        
    Returns:
        Tuple of (BoardSchema, DDL string)
    """
    generator = BoardSchemaGenerator()
    schema = generator.discover_board_structure(board_id)
    
    if table_name:
        schema.table_name = table_name
    schema.database = database
    
    ddl = generator.generate_sql_schema(schema)
    return schema, ddl


if __name__ == "__main__":
    # Test with the existing board
    test_board_id = 8709134353  # COO Planning board
    
    try:
        logger.info("Testing Board Schema Generator")
        schema, ddl = discover_and_generate_schema(test_board_id)
        
        print(f"\nDiscovered Board: {schema.board_name}")
        print(f"Table Name: {schema.table_name}")
        print(f"Columns: {len(schema.columns)}")
        print(f"\nDDL Preview (first 500 chars):")
        print(ddl[:500] + "..." if len(ddl) > 500 else ddl)
        
        # Save metadata
        generator = BoardSchemaGenerator()
        metadata_path = generator.save_board_metadata(schema)
        print(f"\nMetadata saved to: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
