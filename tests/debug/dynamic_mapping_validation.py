"""
Dynamic Mapping Validation Tool
Purpose: Compare ORDERS_UNIFIED columns vs STG_ table columns vs Comprehensive Mapping
Created: Dynamic validation using actual DDL and mapping files
"""
import sys
from pathlib import Path
import yaml
import pandas as pd
import re
import pyodbc

# Standard import pattern
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

import db_helper as db
import logger_helper

class DynamicMappingValidator:
    """
    Validates mappings between ORDERS_UNIFIED, STG tables, and comprehensive mapping YAML
    """
    
    def __init__(self):
        self.repo_root = find_repo_root()
        self.logger = logger_helper.get_logger(__name__)
        
        # File paths
        self.mapping_file = self.repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
        self.stg_ddl_file = self.repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule.sql"
        
        # Data containers
        self.orders_unified_columns = []
        self.stg_table_columns = []
        self.mapping_columns = []
        self.validation_df = None
        
    def get_orders_unified_schema(self) -> list:
        """Get actual column names from ORDERS_UNIFIED table"""
        self.logger.info("Fetching ORDERS_UNIFIED schema from database...")
        
        try:
            with db.get_connection('orders') as conn:
                # Get table schema
                schema_query = """
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'ORDERS_UNIFIED'
                ORDER BY ORDINAL_POSITION
                """
                
                df = pd.read_sql(schema_query, conn)
                self.orders_unified_columns = df['COLUMN_NAME'].tolist()
                
                self.logger.info(f"Found {len(self.orders_unified_columns)} columns in ORDERS_UNIFIED")
                return self.orders_unified_columns
                
        except Exception as e:
            self.logger.error(f"Error fetching ORDERS_UNIFIED schema: {e}")
            return []
    
    def parse_stg_ddl_columns(self) -> list:
        """Parse STG table DDL file to extract column names"""
        self.logger.info(f"Parsing STG DDL file: {self.stg_ddl_file}")
        
        try:
            with open(self.stg_ddl_file, 'r') as f:
                ddl_content = f.read()
            
            # Extract column definitions using regex
            # Look for lines like [COLUMN_NAME] TYPE constraints,
            column_pattern = r'\[([^\]]+)\]\s+(?:NVARCHAR|VARCHAR|BIGINT|INT|FLOAT|DATE|DATETIME2)'
            
            matches = re.findall(column_pattern, ddl_content)
            
            # Filter out staging-specific columns (start with stg_)
            business_columns = [col for col in matches if not col.lower().startswith('stg_')]
            
            self.stg_table_columns = business_columns
            self.logger.info(f"Found {len(self.stg_table_columns)} business columns in STG DDL")
            
            return self.stg_table_columns
            
        except Exception as e:
            self.logger.error(f"Error parsing STG DDL: {e}")
            return []
    
    def parse_comprehensive_mapping(self) -> list:
        """Parse comprehensive mapping YAML to extract source fields"""
        self.logger.info(f"Parsing comprehensive mapping: {self.mapping_file}")
        
        try:
            with open(self.mapping_file, 'r') as f:
                mapping_data = yaml.safe_load(f)
            
            mapping_columns = []
            
            # Extract from exact_matches
            if 'exact_matches' in mapping_data:
                for mapping in mapping_data['exact_matches']:
                    if 'source_field' in mapping:
                        mapping_columns.append(mapping['source_field'])
            
            # Extract from field_mappings if it exists
            if 'field_mappings' in mapping_data:
                for mapping in mapping_data['field_mappings']:
                    if 'source_field' in mapping:
                        mapping_columns.append(mapping['source_field'])
            
            # Extract from any other mapping sections
            for key, value in mapping_data.items():
                if isinstance(value, list) and key not in ['exact_matches', 'field_mappings']:
                    for item in value:
                        if isinstance(item, dict) and 'source_field' in item:
                            mapping_columns.append(item['source_field'])
            
            self.mapping_columns = list(set(mapping_columns))  # Remove duplicates
            self.logger.info(f"Found {len(self.mapping_columns)} unique source fields in mapping")
            
            return self.mapping_columns
            
        except Exception as e:
            self.logger.error(f"Error parsing comprehensive mapping: {e}")
            return []
    
    def create_validation_dataframe(self) -> pd.DataFrame:
        """Create comprehensive validation DataFrame"""
        self.logger.info("Creating validation DataFrame...")
        
        # Get all unique column names from all sources
        all_columns = set()
        all_columns.update(self.orders_unified_columns)
        all_columns.update(self.stg_table_columns)
        all_columns.update(self.mapping_columns)
        
        all_columns = sorted(list(all_columns))
        
        # Create validation data
        validation_data = []
        
        for column in all_columns:
            row = {
                'column_name': column,
                'in_orders_unified': column in self.orders_unified_columns,
                'in_stg_table': column in self.stg_table_columns,
                'in_mapping_yaml': column in self.mapping_columns,
                'all_three_match': (
                    column in self.orders_unified_columns and 
                    column in self.stg_table_columns and 
                    column in self.mapping_columns
                ),
                'orders_unified_only': (
                    column in self.orders_unified_columns and 
                    column not in self.stg_table_columns and 
                    column not in self.mapping_columns
                ),
                'stg_table_only': (
                    column not in self.orders_unified_columns and 
                    column in self.stg_table_columns and 
                    column not in self.mapping_columns
                ),
                'mapping_only': (
                    column not in self.orders_unified_columns and 
                    column not in self.stg_table_columns and 
                    column in self.mapping_columns
                )
            }
            validation_data.append(row)
        
        self.validation_df = pd.DataFrame(validation_data)
        
        return self.validation_df
    
    def print_summary_report(self):
        """Print comprehensive summary report"""
        if self.validation_df is None:
            self.logger.error("No validation DataFrame available")
            return
        
        print("\n" + "="*80)
        print("DYNAMIC MAPPING VALIDATION REPORT")
        print("="*80)
        
        print(f"\nSOURCE COUNTS:")
        print(f"  ORDERS_UNIFIED columns: {len(self.orders_unified_columns)}")
        print(f"  STG table columns: {len(self.stg_table_columns)}")
        print(f"  Mapping YAML columns: {len(self.mapping_columns)}")
        print(f"  Total unique columns: {len(self.validation_df)}")
        
        print(f"\nMATCH ANALYSIS:")
        all_three = self.validation_df['all_three_match'].sum()
        orders_only = self.validation_df['orders_unified_only'].sum()
        stg_only = self.validation_df['stg_table_only'].sum()
        mapping_only = self.validation_df['mapping_only'].sum()
        
        print(f"  ✅ All three match: {all_three}")
        print(f"  🔶 ORDERS_UNIFIED only: {orders_only}")
        print(f"  🔶 STG table only: {stg_only}")
        print(f"  🔶 Mapping YAML only: {mapping_only}")
        
        # Show problematic columns
        if orders_only > 0:
            print(f"\n📋 COLUMNS IN ORDERS_UNIFIED BUT NOT MAPPED ({orders_only}):")
            unmapped = self.validation_df[self.validation_df['orders_unified_only']]['column_name'].tolist()
            for i, col in enumerate(unmapped[:10]):  # Show first 10
                print(f"  {i+1:2d}. {col}")
            if len(unmapped) > 10:
                print(f"  ... and {len(unmapped) - 10} more")
        
        if stg_only > 0:
            print(f"\n📋 COLUMNS IN STG TABLE BUT NOT IN SOURCE ({stg_only}):")
            stg_orphans = self.validation_df[self.validation_df['stg_table_only']]['column_name'].tolist()
            for i, col in enumerate(stg_orphans[:10]):
                print(f"  {i+1:2d}. {col}")
            if len(stg_orphans) > 10:
                print(f"  ... and {len(stg_orphans) - 10} more")
        
        if mapping_only > 0:
            print(f"\n📋 COLUMNS IN MAPPING BUT NOT IN SOURCE ({mapping_only}):")
            mapping_orphans = self.validation_df[self.validation_df['mapping_only']]['column_name'].tolist()
            for i, col in enumerate(mapping_orphans[:10]):
                print(f"  {i+1:2d}. {col}")
            if len(mapping_orphans) > 10:
                print(f"  ... and {len(mapping_orphans) - 10} more")
        
        print(f"\n✅ PERFECT MATCHES (sample):")
        perfect_matches = self.validation_df[self.validation_df['all_three_match']]['column_name'].tolist()
        for i, col in enumerate(perfect_matches[:10]):
            print(f"  {i+1:2d}. {col}")
        if len(perfect_matches) > 10:
            print(f"  ... and {len(perfect_matches) - 10} more")
    
    def save_detailed_report(self, filename: str = None):
        """Save detailed CSV report"""
        if filename is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mapping_validation_report_{timestamp}.csv"
        
        output_path = self.repo_root / "test_results" / filename
        output_path.parent.mkdir(exist_ok=True)
        
        self.validation_df.to_csv(output_path, index=False)
        self.logger.info(f"Detailed report saved to: {output_path}")
        print(f"\n📄 Detailed report saved to: {output_path}")
    
    def run_full_validation(self):
        """Run complete validation process"""
        self.logger.info("Starting dynamic mapping validation...")
        
        # Step 1: Get ORDERS_UNIFIED schema
        self.get_orders_unified_schema()
        
        # Step 2: Parse STG DDL
        self.parse_stg_ddl_columns()
        
        # Step 3: Parse comprehensive mapping
        self.parse_comprehensive_mapping()
        
        # Step 4: Create validation DataFrame
        self.create_validation_dataframe()
        
        # Step 5: Print summary
        self.print_summary_report()
        
        # Step 6: Save detailed report
        self.save_detailed_report()
        
        return self.validation_df

def main():
    """Main execution function"""
    print("🔍 Dynamic Mapping Validation Tool")
    print("Comparing ORDERS_UNIFIED vs STG tables vs Comprehensive Mapping YAML")
    print("-" * 70)
    
    validator = DynamicMappingValidator()
    validation_df = validator.run_full_validation()
    
    print(f"\n🎯 Validation complete! Found {len(validation_df)} total columns to analyze.")
    
    return validation_df

if __name__ == "__main__":
    result = main()
