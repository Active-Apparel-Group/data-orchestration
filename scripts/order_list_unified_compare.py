"""
ORDER_LIST vs vORDERS_UNIFIED Comparison Script
Purpose: Compare table and view data excluding UUIDs, using ORDER_LIST schema groups
Uses: Professional column matching based on Group 1 (Order Details) + Group 2 (Garment Sizes)
"""
import sys
from pathlib import Path
import pyodbc
import pandas as pd
import hashlib
from typing import List, Dict, Set

# Standard import pattern - use this in ALL scripts
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import from utils/ - PRODUCTION PATTERN
import db_helper as db
import logger_helper

def get_order_list_group1_group2_columns() -> List[str]:
    """
    Extract Group 1 (Order Details) and Group 2 (Garment Sizes) columns 
    from ORDER_LIST schema definition
    
    Returns:
        List of column names for comparison (excludes UUIDs, IDs)
    """
    
    # GROUP 1: ORDER DETAILS (56 columns) - Key business columns
    group1_columns = [
        'AAG ORDER NUMBER'
    ]

    group2_core_sizes = [
        # Standard apparel sizes
        'TOTAL QTY'
    ]

    groupone_columns = [
        'AAG ORDER NUMBER', 'CUSTOMER NAME', 'ORDER DATE PO RECEIVED', 
        'PO NUMBER', 'CUSTOMER ALT PO', 'AAG SEASON', 'CUSTOMER SEASON',
        'DROP', 'MONTH', 'RANGE / COLLECTION', 
        'PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)', 'CATEGORY', 'PATTERN ID',
        'PLANNER', 'MAKE OR BUY', 'ORIGINAL ALIAS/RELATED ITEM',
        'PRICING ALIAS/RELATED ITEM', 'ALIAS/RELATED ITEM', 'CUSTOMER STYLE',
        'STYLE DESCRIPTION', 'CUSTOMER\'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS',
        'CUSTOMER COLOUR DESCRIPTION', 'INFOR WAREHOUSE CODE', 'BULK AGREEMENT NUMBER',
        'INFOR FACILITY CODE', 'INFOR BUSINESS UNIT AREA', 'BULK AGREEMENT DESCRIPTION',
        'CO NUMBER - INITIAL DISTRO', 'INFOR CUSTOMER CODE', 'CO NUMBER - ALLOCATION DISTRO',
        'CO NUMBER (INITIAL DISTRO)', 'CO NUMBER (ALLOCATION DISTRO)', 'INFOR ORDER TYPE',
        'INFOR SEASON CODE', 'ITEM TYPE CODE', 'PRODUCT GROUP CODE', 'ITEM GROUP CODE',
        'PLANNER2', 'GENDER GROUP CODE', 'FABRIC TYPE CODE', 'INFOR MAKE/BUY CODE',
        'INFOR ITEM TYPE CODE', 'INFOR PRODUCT GROUP CODE', 'INFOR ITEM GROUP CODE',
        'INFOR GENDER GROUP CODE', 'INFOR FABRIC TYPE CODE', 'LONGSON ALIAS',
        'INFOR COLOUR CODE', 'FACILITY CODE', 'CUSTOMER CODE', 'Column2', 'Column1',
        'AAG SEASON CODE', 'MAKE OR BUY FLAG', 'MAKE/BUY CODE', 'UNIT OF MEASURE'
    ]
    
    # GROUP 2: GARMENT SIZES (251 columns) - All INT columns for quantities
    # Sample of key size columns (most common across customers)
    grouptwo_core_sizes = [
        # Standard apparel sizes
        'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', '2XL', '3XL', '4XL',
        'XXS', 'S/M', 'M/L', 'L/XL', 'XS/S', 'XL/XXL',
        # Numeric sizes
        '0', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20', '22', '24',
        # Extended numeric
        '26', '28', '30', '32', '34', '36', '38', '40', '42', '44', '46', '48',
        # One size
        'ONE SIZE', 'OS', 'One Size', 'One Sz', 'O/S',
        # Children sizes
        '2T', '3T', '4T', '5T', '6T', '1Y', '2Y', '3Y', '4Y',
        # Special sizes  
        '1X', '2X', '3X', '4X', 'S+', 'M+', 'L+',
        # Waist/inseam combinations
        '30/30', '32/32', '34/34', '36/36', '30x30', '32x32', '34x32',
        # Plus sizes
        '0w', '2w', '4w', '6w', '8w', '10w', '12w', '14w', '16w', '18w', '20w',
        # Bra sizes
        '32C', '32D', '32DD', '34C', '34D', '34DD', '36C', '36D', '36DD', '38C', '38D', '38DD'
    ]
    
    # Combine both groups
    comparison_columns = group1_columns + group2_core_sizes
    
    return comparison_columns

def get_common_columns(table_columns: List[str], view_columns: List[str], 
                      target_columns: List[str]) -> List[str]:
    """
    Find columns that exist in both table and view AND are in our target list
    
    Args:
        table_columns: Columns from the table
        view_columns: Columns from the view  
        target_columns: Columns we want to compare (from ORDER_LIST schema)
        
    Returns:
        List of columns safe to compare
    """
    
    # Convert to sets for efficient intersection
    table_set = set(table_columns)
    view_set = set(view_columns)
    target_set = set(target_columns)
    
    # Find intersection of all three sets
    common_columns = table_set & view_set & target_set
    
    # Convert back to sorted list for consistent ordering
    return sorted(list(common_columns))

def hash_row_selective(row: pd.Series, columns: List[str]) -> str:
    """
    Hash only selected columns from a row, excluding UUIDs
    
    Args:
        row: DataFrame row
        columns: Column names to include in hash
        
    Returns:
        SHA256 hash of concatenated column values
    """
    
    # Build string from only specified columns
    values = []
    for col in columns:
        if col in row.index:
            val = row[col]
            # Convert to string, handle None/NaN
            val_str = str(val) if val is not None and pd.notna(val) else ''
            values.append(val_str)
        else:
            values.append('')  # Column missing, use empty string
    
    # Create hash from concatenated values
    row_str = '|'.join(values)
    return hashlib.sha256(row_str.encode('utf-8')).hexdigest()

def main():
    """Main comparison function"""
    
    logger = logger_helper.get_logger(__name__)
    config = db.load_config()
    
    logger.info("🔄 Starting ORDER_LIST vs vORDERS_UNIFIED comparison")
    
    # === CONFIGURATION ===
    table_name = 'ORDERS_UNIFIED'  # Source table
    view_name = 'vORDERS_UNIFIED'   # Target view
    database_name = 'orders'        # From config.yaml
    
    try:
        # === GET COLUMN SCHEMAS ===
        logger.info("📋 Extracting column schemas...")
        
        with db.get_connection(database_name) as conn:
            # Get table columns
            table_schema_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? AND TABLE_SCHEMA = 'dbo'
            ORDER BY ORDINAL_POSITION
            """
            table_cols_df = pd.read_sql(table_schema_query, conn, params=[table_name])
            table_columns = table_cols_df['COLUMN_NAME'].tolist()
            
            # Get view columns  
            view_schema_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = ? AND TABLE_SCHEMA = 'dbo'
            ORDER BY ORDINAL_POSITION
            """
            view_cols_df = pd.read_sql(view_schema_query, conn, params=[view_name])
            view_columns = view_cols_df['COLUMN_NAME'].tolist()
        
        logger.info(f"📊 Table columns found: {len(table_columns)}")
        logger.info(f"📊 View columns found: {len(view_columns)}")
        
        # === GET TARGET COLUMNS FROM ORDER_LIST SCHEMA ===
        target_columns = get_order_list_group1_group2_columns()
        logger.info(f"🎯 Target columns (Group 1 + Group 2): {len(target_columns)}")
        
        # === FIND COMMON COLUMNS ===
        common_columns = get_common_columns(table_columns, view_columns, target_columns)
        logger.info(f"✅ Common columns for comparison: {len(common_columns)}")
        
        if len(common_columns) == 0:
            logger.error("❌ No common columns found for comparison!")
            return
        
        # Log sample of columns being compared
        logger.info(f"📝 Sample columns: {common_columns[:10]}...")
        
        # === EXCLUDE UUID AND ID COLUMNS ===
        excluded_patterns = ['uuid', 'id', 'ID', 'record_id', 'identity']
        filtered_columns = []
        excluded_count = 0
        
        for col in common_columns:
            should_exclude = False
            for pattern in excluded_patterns:
                if pattern.lower() in col.lower():
                    should_exclude = True
                    excluded_count += 1
                    break
            
            if not should_exclude:
                filtered_columns.append(col)
        
        logger.info(f"🚫 Excluded {excluded_count} UUID/ID columns")
        logger.info(f"✅ Final comparison columns: {len(filtered_columns)}")
        
        if len(filtered_columns) == 0:
            logger.error("❌ No valid columns remaining after filtering!")
            return
        
        # === LOAD DATA ===
        logger.info("📥 Loading data for comparison...")
        
        # Build dynamic SELECT statement for only common columns
        column_list = ', '.join(f'[{col}]' for col in filtered_columns)
        
        with db.get_connection(database_name) as conn:
            table_query = f"SELECT {column_list} FROM [{table_name}]"
            view_query = f"SELECT {column_list} FROM [{view_name}]"
            
            logger.info("📊 Loading table data...")
            df_table = pd.read_sql(table_query, conn)
            
            logger.info("📊 Loading view data...")
            df_view = pd.read_sql(view_query, conn)
        
        logger.info(f"✅ Table rows loaded: {len(df_table):,}")
        logger.info(f"✅ View rows loaded: {len(df_view):,}")
        
        # === HASH COMPARISON ===
        logger.info("🔐 Computing row hashes...")
        
        # Hash each row using only filtered columns
        df_table['row_hash'] = df_table.apply(
            lambda row: hash_row_selective(row, filtered_columns), axis=1
        )
        
        df_view['row_hash'] = df_view.apply(
            lambda row: hash_row_selective(row, filtered_columns), axis=1
        )
        
        # === COMPARE HASHES ===
        logger.info("⚖️ Comparing data...")
        
        table_hashes = set(df_table['row_hash'])
        view_hashes = set(df_view['row_hash'])
        
        matched = table_hashes & view_hashes
        missing_in_view = table_hashes - view_hashes
        missing_in_table = view_hashes - table_hashes
        
        # === RESULTS ===
        print("\n" + "="*60)
        print("📊 ORDER_LIST vs vORDERS_UNIFIED COMPARISON RESULTS")
        print("="*60)
        print(f"✅ Total rows in {table_name}: {len(df_table):,}")
        print(f"✅ Total rows in {view_name}: {len(df_view):,}")
        print(f"📋 Columns compared: {len(filtered_columns)}")
        print(f"✅ Matched rows: {len(matched):,}")
        print(f"❌ Rows in {table_name} but missing in {view_name}: {len(missing_in_view):,}")
        print(f"❌ Rows in {view_name} but missing in {table_name}: {len(missing_in_table):,}")
        
        # Calculate match percentage
        total_unique = len(table_hashes | view_hashes)
        if total_unique > 0:
            match_percentage = (len(matched) / total_unique) * 100
            print(f"📈 Data consistency: {match_percentage:.2f}%")
        
        # === DETAILED ANALYSIS ===
        if missing_in_view and len(missing_in_view) <= 10:
            print(f"\n🔍 Sample rows in {table_name} but missing in {view_name}:")
            sample_missing = df_table[df_table['row_hash'].isin(missing_in_view)].head()
            key_cols = [col for col in ['AAG ORDER NUMBER', 'CUSTOMER NAME', 'PO NUMBER'] 
                       if col in sample_missing.columns]
            if key_cols:
                for _, row in sample_missing.iterrows():
                    key_values = [f"{col}: {row[col]}" for col in key_cols]
                    print(f"   • {' | '.join(key_values)}")
        
        if missing_in_table and len(missing_in_table) <= 10:
            print(f"\n🔍 Sample rows in {view_name} but missing in {table_name}:")
            sample_missing = df_view[df_view['row_hash'].isin(missing_in_table)].head()
            key_cols = [col for col in ['AAG ORDER NUMBER', 'CUSTOMER NAME', 'PO NUMBER'] 
                       if col in sample_missing.columns]
            if key_cols:
                for _, row in sample_missing.iterrows():
                    key_values = [f"{col}: {row[col]}" for col in key_cols]
                    print(f"   • {' | '.join(key_values)}")
        
        print("="*60)
        
        logger.info("✅ Comparison completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Comparison failed: {e}")
        raise

if __name__ == "__main__":
    main()
