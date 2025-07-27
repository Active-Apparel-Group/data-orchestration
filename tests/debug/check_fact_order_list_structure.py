#!/usr/bin/env python3
"""
Quick check of FACT_ORDER_LIST table structure to understand current columns
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 Analyzing FACT_ORDER_LIST table structure...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Check table structure
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'FACT_ORDER_LIST'
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(query)
        columns = cursor.fetchall()
        
        print(f"\n📋 FACT_ORDER_LIST Table Structure ({len(columns)} columns):")
        print("="*80)
        print(f"{'Column Name':<30} {'Data Type':<15} {'Max Length':<12} {'Nullable':<10}")
        print("="*80)
        
        api_related_columns = []
        for column_name, data_type, max_length, is_nullable in columns:
            max_len_str = str(max_length) if max_length else "N/A"
            print(f"{column_name:<30} {data_type:<15} {max_len_str:<12} {is_nullable:<10}")
            
            # Identify API-related columns
            if any(keyword in column_name.lower() for keyword in ['monday', 'sync', 'api', 'payload', 'request', 'response']):
                api_related_columns.append(column_name)
        
        print("="*80)
        
        if api_related_columns:
            print(f"\n🔗 Existing API-related columns: {', '.join(api_related_columns)}")
        else:
            print(f"\n❗ No existing API-related columns found")
        
        # Check if we need to add new columns
        print(f"\n💡 Recommended columns for Monday.com API logging:")
        suggested_columns = [
            "api_request_payload NVARCHAR(MAX)",
            "api_response_payload NVARCHAR(MAX)", 
            "api_request_timestamp DATETIME2",
            "api_response_timestamp DATETIME2",
            "api_operation_type NVARCHAR(50)",
            "api_status NVARCHAR(20)"
        ]
        
        for suggestion in suggested_columns:
            print(f"  - {suggestion}")
        
        cursor.close()

if __name__ == "__main__":
    main()
