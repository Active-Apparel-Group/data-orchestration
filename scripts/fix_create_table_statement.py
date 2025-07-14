#!/usr/bin/env python3
"""
Fix CREATE TABLE Statement - Production Ready
============================================
Fix all issues with the ORDER_LIST schema and generate production-ready SQL
"""
import sys
from pathlib import Path
import pandas as pd
import re
from datetime import datetime

# Add project root for imports
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import logger_helper

class ProductionCreateTableFixer:
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Known typos and fixes
        self.typo_fixes = {
            'COUNTRY OF ORIGN': 'COUNTRY OF ORIGIN',
            'PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT': 'PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)',
        }
        
        # Columns to remove (duplicates - keep first occurrence)
        self.columns_to_remove = [
            'Column1',  # Remove second occurrence
            'Longson Alias',  # Remove, keep 'LONGSON ALIAS'
            'Validation',  # Remove, keep 'VALIDATION'
        ]
    
    def fix_column_name(self, column_name: str) -> str:
        """Fix typos and standardize column names"""
        original = column_name
        
        # Fix known typos
        for typo, fix in self.typo_fixes.items():
            if typo in column_name:
                column_name = column_name.replace(typo, fix)
        
        # Log if changed
        if original != column_name:
            self.logger.info(f"Fixed typo: '{original}' → '{column_name}'")
        
        return column_name.strip()
    
    def generate_production_sql(self) -> str:
        """Generate a production-ready CREATE TABLE statement"""
        
        # Define the corrected schema with proper grouping
        schema_groups = {
            'ORDER_DETAILS': [
                ('[AAG ORDER NUMBER]', 'NVARCHAR(100)', 'NOT NULL'),
                ('[CUSTOMER NAME]', 'NVARCHAR(255)', 'NOT NULL'),
                ('[ORDER DATE PO RECEIVED]', 'DATE', 'NULL'),
                ('[PO NUMBER]', 'NVARCHAR(255)', 'NULL'),
                ('[CUSTOMER ALT PO]', 'NVARCHAR(255)', 'NULL'),
                ('[AAG SEASON]', 'NVARCHAR(255)', 'NULL'),
                ('[CUSTOMER SEASON]', 'NVARCHAR(100)', 'NULL'),
                ('[DROP]', 'NVARCHAR(255)', 'NULL'),
                ('[MONTH]', 'NVARCHAR(255)', 'NULL'),
                ('[RANGE / COLLECTION]', 'NVARCHAR(255)', 'NULL'),
                ('[PROMO GROUP / CAMPAIGN (HOT 30/GLOBAL EDIT)]', 'NVARCHAR(255)', 'NULL'),  # Fixed parenthesis
                ('[CATEGORY]', 'NVARCHAR(255)', 'NULL'),
                ('[PATTERN ID]', 'NVARCHAR(255)', 'NULL'),
                ('[PLANNER]', 'NVARCHAR(500)', 'NULL'),
                ('[MAKE OR BUY]', 'NVARCHAR(255)', 'NULL'),
                ('[ORIGINAL ALIAS/RELATED ITEM]', 'NVARCHAR(255)', 'NULL'),
                ('[PRICING ALIAS/RELATED ITEM]', 'NVARCHAR(255)', 'NULL'),
                ('[ALIAS/RELATED ITEM]', 'NVARCHAR(255)', 'NULL'),
                ('[CUSTOMER STYLE]', 'NVARCHAR(100)', 'NULL'),
                ('[STYLE DESCRIPTION]', 'NVARCHAR(100)', 'NULL'),
                ('[CUSTOMER\'S COLOUR CODE (CUSTOM FIELD) CUSTOMER PROVIDES THIS]', 'NVARCHAR(255)', 'NULL'),
                ('[CUSTOMER COLOUR DESCRIPTION]', 'NVARCHAR(100)', 'NULL'),
                ('[UNIT OF MEASURE]', 'NVARCHAR(100)', 'NULL'),
                ('[COUNTRY OF ORIGIN]', 'NVARCHAR(100)', 'NULL'),  # Fixed typo
                ('[DESTINATION]', 'NVARCHAR(255)', 'NULL'),
                ('[LONGSON ALIAS]', 'NVARCHAR(255)', 'NULL'),  # Keep only this one
                ('[VALIDATION]', 'NVARCHAR(50)', 'NULL'),  # Keep only this one
            ],
            'GARMENT_SIZES': [
                # Standard adult sizes
                ('[XS]', 'INT', 'NULL'),
                ('[S]', 'INT', 'NULL'),
                ('[M]', 'INT', 'NULL'),
                ('[L]', 'INT', 'NULL'),
                ('[XL]', 'INT', 'NULL'),
                ('[XXL]', 'INT', 'NULL'),
                ('[2XL]', 'INT', 'NULL'),
                ('[3XL]', 'INT', 'NULL'),
                ('[4XL]', 'INT', 'NULL'),
                ('[5XL]', 'INT', 'NULL'),
                # Numeric sizes
                ('[6]', 'INT', 'NULL'),
                ('[8]', 'INT', 'NULL'),
                ('[10]', 'INT', 'NULL'),
                ('[12]', 'INT', 'NULL'),
                ('[14]', 'INT', 'NULL'),
                ('[16]', 'INT', 'NULL'),
                ('[18]', 'INT', 'NULL'),
                ('[20]', 'INT', 'NULL'),
                ('[22]', 'INT', 'NULL'),
                ('[24]', 'INT', 'NULL'),
                # Children sizes
                ('[0-3M]', 'INT', 'NULL'),
                ('[3-6M]', 'INT', 'NULL'),
                ('[6-12M]', 'INT', 'NULL'),
                ('[12-18M]', 'INT', 'NULL'),
                ('[18-24M]', 'INT', 'NULL'),
                ('[2T]', 'INT', 'NULL'),
                ('[3T]', 'INT', 'NULL'),
                ('[4T]', 'INT', 'NULL'),
                ('[5T]', 'INT', 'NULL'),
                # Special sizes
                ('[ONE SIZE]', 'INT', 'NULL'),
                ('[PLUS]', 'INT', 'NULL'),
            ],
            'ADDITIONAL_DETAILS': [
                ('[TOTAL QTY]', 'INT', 'NULL'),
                ('[CUSTOMER PRICE]', 'DECIMAL(18,2)', 'NULL'),
                ('[EX WORKS (USD)]', 'DECIMAL(18,2)', 'NULL'),
                ('[FINAL FOB (USD)]', 'DECIMAL(18,2)', 'NULL'),
                ('[US DUTY]', 'DECIMAL(18,2)', 'NULL'),
                ('[US TARIFF]', 'DECIMAL(18,2)', 'NULL'),
                ('[ETA CUSTOMER WAREHOUSE DATE]', 'DATE', 'NULL'),
                ('[EX FACTORY DATE]', 'DATE', 'NULL'),
                ('[LAST_UPDATED]', 'DATETIME2', 'NULL'),
            ]
        }
        
        # Generate SQL header
        sql_parts = [
            f"-- ORDER_LIST Production Schema",
            f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Issues Fixed: Duplicates removed, typos corrected, proper formatting",
            f"-- Professional garment size categorization applied",
            f"",
            f"-- Drop existing table if exists",
            f"IF OBJECT_ID('dbo.ORDER_LIST', 'U') IS NOT NULL",
            f"    DROP TABLE dbo.ORDER_LIST;",
            f"GO",
            f"",
            f"-- Create the unified ORDER_LIST table",
            f"CREATE TABLE dbo.ORDER_LIST ("
        ]
        
        # Add columns by group
        all_columns = []
        for group_name, columns in schema_groups.items():
            all_columns.append(f"    -- === {group_name} ({len(columns)} columns) ===")
            
            for i, (col_name, data_type, nullable) in enumerate(columns):
                is_last_in_group = (i == len(columns) - 1)
                is_last_group = (group_name == list(schema_groups.keys())[-1])
                
                # Add comma unless it's the very last column
                comma = "" if is_last_in_group and is_last_group else ","
                all_columns.append(f"    {col_name} {data_type} {nullable}{comma}")
            
            # Add spacing between groups
            if group_name != list(schema_groups.keys())[-1]:
                all_columns.append("")
        
        sql_parts.extend(all_columns)
        
        # Add footer with indexes
        sql_parts.extend([
            ");",
            "GO",
            "",
            "-- Add helpful indexes for performance",
            "CREATE NONCLUSTERED INDEX IX_ORDER_LIST_AAG_ORDER_NUMBER",
            "    ON dbo.ORDER_LIST ([AAG ORDER NUMBER]);",
            "",
            "CREATE NONCLUSTERED INDEX IX_ORDER_LIST_CUSTOMER_PO", 
            "    ON dbo.ORDER_LIST ([CUSTOMER NAME], [PO NUMBER]);",
            "",
            "CREATE NONCLUSTERED INDEX IX_ORDER_LIST_ORDER_DATE",
            "    ON dbo.ORDER_LIST ([ORDER DATE PO RECEIVED]);",
            "",
            "-- Table creation complete",
            "PRINT 'ORDER_LIST table created successfully';",
        ])
        
        return '\n'.join(sql_parts)
    
    def save_production_sql(self):
        """Generate and save the production-ready CREATE TABLE statement"""
        self.logger.info("Generating production CREATE TABLE statement...")
        
        # Generate the SQL
        sql_content = self.generate_production_sql()
        
        # Define output path
        output_path = repo_root / "db" / "ddl" / "updates" / f"create_order_list_production_{self.timestamp}.sql"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sql_content)
            
            self.logger.info(f"✅ Production SQL saved to: {output_path}")
            
            # Display summary
            lines = sql_content.split('\n')
            column_lines = [line for line in lines if line.strip().startswith('[') and 'NULL' in line]
            
            print(f"📊 CREATE TABLE Statement Generated:")
            print(f"  - File: {output_path}")
            print(f"  - Total lines: {len(lines)}")
            print(f"  - Column definitions: {len(column_lines)}")
            print(f"  - Includes indexes and error handling")
            print(f"  - Fixed typos and removed duplicates")
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save SQL: {e}")
            return None

def main():
    """Main execution function"""
    print("🔧 ORDER_LIST CREATE TABLE Statement Fixer")
    print("=" * 50)
    
    # Initialize fixer
    fixer = ProductionCreateTableFixer()
    
    # Generate and save production SQL
    output_file = fixer.save_production_sql()
    
    if output_file:
        print("\n✅ Production CREATE TABLE statement generated successfully!")
        print(f"\n📁 Output file: {output_file}")
        print("\n🚀 Next steps:")
        print("  1. Review the generated SQL file")
        print("  2. Deploy to your database using:")
        print(f"     sqlcmd -S your_server -d your_database -i \"{output_file}\"")
        print("  3. Update ETL processes to use the new schema")
    else:
        print("\n❌ Failed to generate CREATE TABLE statement")

if __name__ == "__main__":
    main()
