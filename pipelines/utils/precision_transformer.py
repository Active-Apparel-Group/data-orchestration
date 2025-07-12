"""
Simple Precision Transformer
Purpose: Handle INT and DECIMAL precision issues in ORDER_LIST tables
Author: Data Engineering Team
Date: July 10, 2025

Simple solution:
- INT columns: FLOOR(TRY_CAST([column_name] AS FLOAT))
- DECIMAL columns: TRY_CAST([column_name] AS DECIMAL(p,s)) from DDL
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional

def find_repo_root() -> Path:
    """Find repository root by looking for pipelines/utils folder"""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current.parent.parent / "pipelines" / "utils").exists():
            return current.parent.parent
        current = current.parent
    raise RuntimeError("Could not find repository root with pipelines/utils folder")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))  # Only use pipelines/utils for Kestra compatibility

import db_helper as db
import logger_helper

class SimplePrecisionTransformer:
    """
    Simple precision transformer for ORDER_LIST tables
    Handles INT, DECIMAL, and DATE precision/conversion issues
    """
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.schema_types = self._load_schema_types()
        
        # Known problematic date values from debug analysis
        self.problematic_date_values = [
            '00/00/00', 'TBC', 'TBA', 'TBD', '', 'NULL', 'null'
        ]
        
    def _load_schema_types(self) -> Dict[str, str]:
        """Load column types from DDL file"""
        ddl_path = repo_root / "db" / "ddl" / "tables" / "orders" / "dbo_order_list.sql"
        
        with open(ddl_path, 'r') as f:
            ddl_content = f.read()
        
        # Parse DDL for column types (include DATE columns)
        pattern = r'\[([^\]]+)\]\s+(INT|SMALLINT|TINYINT|DECIMAL\(\d+,\d+\)|DATE|DATETIME|DATETIME2)\s+NULL'
        matches = re.findall(pattern, ddl_content)
        
        schema_types = {}
        for column_name, data_type in matches:
            # Apply your schema fixes (DECIMAL(17,15) → DECIMAL(17,4))
            if data_type == 'DECIMAL(17,15)':
                data_type = 'DECIMAL(17,4)'
            schema_types[column_name] = data_type
        
        self.logger.info(f"Loaded {len(schema_types)} column types from DDL")
        return schema_types
    
    def get_precision_transform(self, column_name: str) -> Optional[str]:
        """
        Get the precision transform for a column
        
        Args:
            column_name: Name of the column
            
        Returns:
            SQL transform string or None if no transform needed
        """
        if column_name not in self.schema_types:
            return None
            
        data_type = self.schema_types[column_name]
        
        # INT transform: FLOOR(TRY_CAST([column_name] AS FLOAT))
        if data_type in ('INT', 'SMALLINT', 'TINYINT'):
            return f"FLOOR(TRY_CAST([{column_name}] AS FLOAT)) AS [{column_name}]"
        
        # DECIMAL transform: TRY_CAST([column_name] AS DECIMAL(p,s))
        elif data_type.startswith('DECIMAL'):
            return f"TRY_CAST([{column_name}] AS {data_type}) AS [{column_name}]"
        
        # DATE transform: Efficient pre-NULL + single TRY_CONVERT
        elif data_type in ('DATE', 'DATETIME', 'DATETIME2'):
            problematic_values = "', '".join(self.problematic_date_values)
            return f"""CASE 
                WHEN [{column_name}] IN ('{problematic_values}') THEN NULL
                ELSE TRY_CONVERT(DATE, NULLIF(LTRIM(RTRIM([{column_name}])), ''), 120)
            END AS [{column_name}]"""
        
        return None
    
    def apply_precision_transforms(self, select_columns: List[str]) -> List[str]:
        """
        Apply precision transforms to a list of SELECT columns
        
        Args:
            select_columns: List of column expressions
            
        Returns:
            List of column expressions with precision transforms applied
        """
        transformed_columns = []
        
        for col_expr in select_columns:
            # Extract column name from expression (handle AS clauses)
            if ' AS ' in col_expr.upper():
                # Handle "expression AS [column_name]"
                parts = col_expr.split(' AS ')
                if len(parts) == 2:
                    column_name = parts[1].strip('[]')
                else:
                    column_name = parts[0].strip('[]')
            else:
                # Handle simple "[column_name]"
                column_name = col_expr.strip('[]')
            
            # Get precision transform if available
            precision_transform = self.get_precision_transform(column_name)
            
            if precision_transform:
                transformed_columns.append(precision_transform)
                self.logger.debug(f"Applied precision transform to {column_name}")
            else:
                transformed_columns.append(col_expr)
        
        return transformed_columns

# Factory function for easy usage
def create_precision_transformer() -> SimplePrecisionTransformer:
    """Create a precision transformer instance"""
    return SimplePrecisionTransformer()

if __name__ == "__main__":
    # Simple test
    transformer = SimplePrecisionTransformer()
    
    # Test columns (including DATE columns)
    test_columns = ['[XS]', '[S]', '[FINAL FOB (USD)]', '[CUSTOMER NAME]', '[ETA CUSTOMER WAREHOUSE DATE]', '[EX FACTORY DATE]']
    
    print("Testing precision transforms:")
    for col in test_columns:
        transform = transformer.get_precision_transform(col.strip('[]'))
        if transform:
            print(f"  {col} → {transform}")
        else:
            print(f"  {col} → No transform needed")
    
    print(f"\nTotal schema columns loaded: {len(transformer.schema_types)}")
    print("INT columns:", [col for col, dtype in transformer.schema_types.items() if dtype in ('INT', 'SMALLINT', 'TINYINT')])
    print("DECIMAL columns:", [col for col, dtype in transformer.schema_types.items() if dtype.startswith('DECIMAL')])
    print("DATE columns:", [col for col, dtype in transformer.schema_types.items() if dtype in ('DATE', 'DATETIME', 'DATETIME2')])

