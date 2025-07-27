#!/usr/bin/env python3
"""
DEBUG: Comprehensive Table Schema and Data Validation Check
==========================================================
Purpose: Complete schema validation for enhanced merge orchestrator testing
- Verify table existence and column schemas
- Check GREYSON test data availability and quality
- Validate source/target table column mappings
- Enhanced data validation for item_name, group_name, group_id values
"""

import sys
from pathlib import Path
import pandas as pd

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def validate_source_data_quality(config, cursor):
    """Enhanced validation for GREYSON test data and source table quality"""
    print(f"\n🧪 Enhanced Source Data Quality Validation:")
    
    # Check what GREYSON data actually exists
    greyson_query = f"""
    SELECT 
        [CUSTOMER NAME],
        [PO NUMBER],
        COUNT(*) as record_count
    FROM {config.source_table}
    WHERE [CUSTOMER NAME] LIKE '%GREYSON%'
    GROUP BY [CUSTOMER NAME], [PO NUMBER]
    ORDER BY record_count DESC
    """
    
    try:
        df = pd.read_sql(greyson_query, cursor.connection)
        print(f"   📊 GREYSON data found:")
        
        if not df.empty:
            for idx, row in df.head(10).iterrows():
                customer = row['CUSTOMER NAME']
                po = row['PO NUMBER']
                count = row['record_count']
                print(f"      • {customer} PO {po}: {count} records")
        else:
            print(f"      ⚠️ No GREYSON data found in {config.source_table}")
            
        return df
        
    except Exception as e:
        print(f"      ❌ Error checking GREYSON data: {e}")
        return pd.DataFrame()

def validate_source_columns(config, cursor):
    """Validate source table columns for transformation requirements"""
    print(f"\n📋 Source Table Column Validation:")
    
    # First check color columns
    color_columns = check_color_columns(config, cursor)
    
    # Check required columns for transformations
    required_columns = [
        'CUSTOMER NAME',
        'CUSTOMER SEASON', 
        'AAG SEASON',
        'CUSTOMER STYLE',
        'CUSTOMER COLOUR DESCRIPTION',
        'AAG ORDER NUMBER',
        'PO NUMBER'
    ]
    
    columns_query = f"""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = '{config.source_table}'
      AND COLUMN_NAME IN ('{'',''.join([f"'{col}'" for col in required_columns])})
    ORDER BY COLUMN_NAME
    """
    
    try:
        cursor.execute(columns_query)
        columns = cursor.fetchall()
        
        found_columns = [col[0] for col in columns]
        missing_columns = [col for col in required_columns if col not in found_columns]
        
        print(f"   ✅ Found columns in {config.source_table}:")
        for col in columns:
            col_name, data_type, nullable, max_length = col
            length_info = f"({max_length})" if max_length else ""
            print(f"      • {col_name}: {data_type}{length_info} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
        
        if missing_columns:
            print(f"   ⚠️ Missing required columns:")
            for col in missing_columns:
                print(f"      • {col}")
        
        return found_columns, missing_columns
        
    except Exception as e:
        print(f"   ❌ Error checking source columns: {e}")
        return [], required_columns

def check_color_columns(config, cursor):
    """Check what color-related columns exist in the source table"""
    print(f"\n🎨 Color Column Validation:")
    
    try:
        # Check for color-related columns
        color_query = f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{config.source_table}'
        AND (COLUMN_NAME LIKE '%COLOR%' OR COLUMN_NAME LIKE '%COLOUR%')
        ORDER BY COLUMN_NAME
        """
        
        cursor.execute(color_query)
        color_columns = [row[0] for row in cursor.fetchall()]
        
        print(f"   ✅ Color-related columns found:")
        for col in color_columns:
            print(f"      • {col}")
        
        if not color_columns:
            print(f"   ⚠️ No color-related columns found!")
        
        # Check specific columns mentioned in TOML
        specific_checks = ['CUSTOMER STYLE', 'CUSTOMER COLOUR DESCRIPTION', 'AAG ORDER NUMBER']
        print(f"\n   🔍 Checking TOML-configured columns:")
        
        for col in specific_checks:
            check_query = f"""
            SELECT COUNT(*) as exists_count
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{config.source_table}' AND COLUMN_NAME = '{col}'
            """
            cursor.execute(check_query)
            exists = cursor.fetchone()[0] > 0
            print(f"      {'✅' if exists else '❌'} {col}")
        
        return color_columns
        
    except Exception as e:
        print(f"   ❌ Error checking color columns: {e}")
        return []

def validate_target_data_integrity(config, cursor):
    """Enhanced validation for target table data integrity and cleanup needs"""
    print(f"\n🎯 Target Table Data Integrity Check:")
    
    try:
        # Check existing data patterns
        integrity_query = f"""
        SELECT 
            group_name,
            item_name,
            group_id,
            sync_state,
            action_type,
            COUNT(*) as record_count
        FROM {config.target_table}
        WHERE group_name IS NOT NULL 
           OR item_name IS NOT NULL 
           OR group_id IS NOT NULL
        GROUP BY group_name, item_name, group_id, sync_state, action_type
        ORDER BY record_count DESC
        """
        
        df = pd.read_sql(integrity_query, cursor.connection)
        total_records = df['record_count'].sum() if not df.empty else 0
        
        print(f"   📊 Target table analysis ({config.target_table}):")
        print(f"      Total records with group/item data: {total_records}")
        
        if not df.empty:
            print(f"      Sample data patterns:")
            for idx, row in df.head(5).iterrows():
                group_name = row['group_name'] or 'NULL'
                item_name = row['item_name'] or 'NULL'
                group_id = row['group_id'] or 'NULL'
                sync_state = row['sync_state'] or 'NULL'
                count = row['record_count']
                print(f"        • Group: '{group_name}', Item: '{item_name[:30]}...', "
                      f"ID: '{group_id}', State: '{sync_state}', Count: {count}")
        
        # Check for potential conflicts
        conflicts = []
        if not df.empty:
            # Incomplete sync states
            incomplete = df[(df['sync_state'].isnull()) | 
                          (df['sync_state'].isin(['pending', 'failed']))]
            if not incomplete.empty:
                conflict_count = incomplete['record_count'].sum()
                conflicts.append(f"Incomplete sync states: {conflict_count} records")
            
            # GREYSON test data conflicts
            greyson_conflicts = df[
                (df['group_name'].str.contains('GREYSON', na=False)) |
                (df['item_name'].str.contains('GREYSON', na=False)) |
                (df['item_name'].str.contains('4755', na=False))
            ]
            if not greyson_conflicts.empty:
                greyson_count = greyson_conflicts['record_count'].sum()
                conflicts.append(f"Existing GREYSON test data: {greyson_count} records")
        
        if conflicts:
            print(f"   ⚠️ Potential data conflicts found:")
            for conflict in conflicts:
                print(f"      • {conflict}")
        else:
            print(f"   ✅ No data conflicts detected")
        
        return {
            'total_records': total_records,
            'conflicts': conflicts,
            'sample_data': df.head(5).to_dict('records') if not df.empty else []
        }
        
    except Exception as e:
        print(f"   ❌ Error checking target data integrity: {e}")
        return {'error': str(e)}

def main():
    print("🔍 COMPREHENSIVE DEBUG: Table Schema and Data Validation")
    print("=" * 70)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    print(f"📋 TOML Configuration:")
    print(f"   Source table: {config.source_table}")
    print(f"   Target table: {config.target_table}")
    print(f"   Lines table: {config.lines_table}")
    print(f"   Database: {config.db_key}")
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # 1. TABLE EXISTENCE CHECK
        print(f"\n🗂️ TABLE EXISTENCE VALIDATION:")
        tables_to_check = [
            config.source_table,
            config.target_table, 
            config.lines_table,
            "ORDER_LIST",        # Original table
            "ORDER_LIST_V2",     # Hardcoded table from code
            "swp_ORDER_LIST_SYNC",  # From TOML
            "FACT_ORDER_LIST"    # TOML target table
        ]
        
        existing_tables = []
        
        for table_name in tables_to_check:
            try:
                check_query = f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = '{table_name}'
                """
                cursor.execute(check_query)
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"   ✅ {table_name} - EXISTS")
                    existing_tables.append(table_name)
                else:
                    print(f"   ❌ {table_name} - NOT FOUND")
                    
            except Exception as e:
                print(f"   ❌ {table_name} - ERROR: {e}")
        
        # 2. SCHEMA COLUMN CHECK
        print(f"\n📊 SCHEMA COLUMN VALIDATION:")
        
        for table_name in existing_tables:
            try:
                columns_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{table_name}'
                  AND COLUMN_NAME IN ('group_name', 'item_name', 'sync_state', 'action_type')
                ORDER BY COLUMN_NAME
                """
                cursor.execute(columns_query)
                columns = cursor.fetchall()
                
                print(f"\n   📋 {table_name}:")
                if columns:
                    for col in columns:
                        col_name, data_type, nullable, max_length = col
                        length_info = f"({max_length})" if max_length else ""
                        print(f"      ✅ {col_name}: {data_type}{length_info} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
                else:
                    print(f"      ⚠️ No sync columns (group_name, item_name, sync_state, action_type) found")
                    
            except Exception as e:
                print(f"      ❌ Error checking columns: {e}")
        
        # 3. ENHANCED SOURCE DATA VALIDATION
        validate_source_data_quality(config, cursor)
        
        # 4. SOURCE COLUMN MAPPING VALIDATION  
        validate_source_columns(config, cursor)
        
        # 5. TARGET DATA INTEGRITY CHECK
        validate_target_data_integrity(config, cursor)
        
        # 6. SAMPLE DATA CHECK
        print(f"\n📈 SAMPLE DATA AVAILABILITY:")
        for table_name in existing_tables[:3]:  # Check first 3 tables only
            try:
                sample_query = f"SELECT TOP 1 * FROM [{table_name}]"
                cursor.execute(sample_query)
                result = cursor.fetchone()
                
                if result:
                    print(f"   ✅ {table_name} - Has data ({len(result)} columns)")
                else:
                    print(f"   📭 {table_name} - Empty table")
                    
            except Exception as e:
                print(f"   ❌ {table_name} - Error: {e}")
        
        cursor.close()
    
    print(f"\n" + "=" * 70)
    print(f"🏁 COMPREHENSIVE VALIDATION COMPLETE")
    print(f"=" * 70)

if __name__ == "__main__":
    main()
