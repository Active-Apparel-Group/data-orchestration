"""
Comprehensive Mapping Validation Tool
Purpose: Dynamically validate all mappings between ORDERS_UNIFIED, staging tables, and Monday.com
Uses: Actual DDL files, comprehensive mapping YAML, and live database schema
"""
import sys
from pathlib import Path
import pandas as pd
import yaml
import re

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

class ComprehensiveMappingValidator:
    def __init__(self):
        self.repo_root = repo_root
        self.mapping_path = self.repo_root / "sql" / "mappings" / "orders-unified-comprehensive-mapping.yaml"
        self.ddl_master_path = self.repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule.sql"
        self.ddl_subitem_path = self.repo_root / "sql" / "ddl" / "tables" / "orders" / "staging" / "stg_mon_custmasterschedule_subitems.sql"
        
    def load_comprehensive_mapping(self):
        """Load the comprehensive mapping YAML"""
        print(f"Loading mapping from: {self.mapping_path}")
        with open(self.mapping_path, 'r') as f:
            mapping = yaml.safe_load(f)
        return mapping
    
    def extract_ddl_columns(self, ddl_path):
        """Extract column names from DDL file"""
        print(f"Extracting columns from DDL: {ddl_path}")
        with open(ddl_path, 'r') as f:
            ddl_content = f.read()
        
        # Find CREATE TABLE statement
        create_match = re.search(r'CREATE TABLE.*?\((.*?)\);', ddl_content, re.DOTALL | re.IGNORECASE)
        if not create_match:
            print(f"Warning: Could not find CREATE TABLE in {ddl_path}")
            return []
        
        table_definition = create_match.group(1)
        
        # Extract column definitions (simple regex for column names)
        column_pattern = r'^\s*\[?(\w+)\]?\s+(?:NVARCHAR|VARCHAR|INT|BIGINT|DECIMAL|DATETIME|UNIQUEIDENTIFIER|BIT)'
        columns = []
        
        for line in table_definition.split('\n'):
            match = re.match(column_pattern, line.strip(), re.IGNORECASE)
            if match:
                columns.append(match.group(1))
        
        return columns
    
    def get_orders_unified_schema(self):
        """Get actual ORDERS_UNIFIED table schema from database"""
        print("Querying ORDERS_UNIFIED schema from database...")
        
        schema_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'ORDERS_UNIFIED'
        ORDER BY ORDINAL_POSITION
        """
        
        try:
            with db.get_connection('orders') as conn:
                schema_df = pd.read_sql(schema_query, conn)
                return schema_df['COLUMN_NAME'].tolist()
        except Exception as e:
            print(f"Error querying ORDERS_UNIFIED schema: {e}")
            return []
    
    def create_validation_dataframe(self):
        """Create comprehensive validation DataFrame"""
        print("\n" + "="*80)
        print("COMPREHENSIVE MAPPING VALIDATION")
        print("="*80)
        
        print(f"\nData Sources Loaded:")
        mapping = self.load_comprehensive_mapping()
        master_ddl_columns = self.extract_ddl_columns(self.ddl_master_path)
        subitem_ddl_columns = self.extract_ddl_columns(self.ddl_subitem_path)
        orders_unified_columns = self.get_orders_unified_schema()
        
        # Process exact_matches mappings (correct structure)
        exact_matches = mapping.get('exact_matches', [])
        business_logic_mappings = mapping.get('business_logic_mappings', {})
        subitem_mappings = mapping.get('subitem_mappings', {})
        
        print(f"  - Exact matches: {len(exact_matches)} mappings")
        print(f"  - Business logic mappings: {len(business_logic_mappings)} mappings")
        print(f"  - Subitem mappings: {len(subitem_mappings)} mappings")
        print(f"  - Master DDL columns: {len(master_ddl_columns)} columns")
        print(f"  - Subitem DDL columns: {len(subitem_ddl_columns)} columns")
        print(f"  - ORDERS_UNIFIED columns: {len(orders_unified_columns)} columns")
        
        # Create validation data
        validation_data = []
        
        # Track all mapped staging columns
        all_mapped_staging = set()
        
        # Process exact matches
        for match in exact_matches:
            source_field = match.get('source_field', '')
            target_field = match.get('target_field', '')
            target_column_id = match.get('target_column_id', '')
            mapping_source = match.get('mapping_source', '')
            
            # Use target_field as staging column name
            staging_column = target_field
            all_mapped_staging.add(staging_column)
            
            # Check if columns exist in various places
            in_master_ddl = staging_column in master_ddl_columns
            in_subitem_ddl = staging_column in subitem_ddl_columns
            in_orders_unified = source_field in orders_unified_columns
            
            validation_data.append({
                'staging_column': staging_column,
                'source_column': source_field,
                'description': f'{mapping_source} - {target_column_id}',
                'in_master_ddl': in_master_ddl,
                'in_subitem_ddl': in_subitem_ddl,
                'in_orders_unified': in_orders_unified,
                'mapping_valid': in_orders_unified and (in_master_ddl or in_subitem_ddl),
                'table_target': 'master' if in_master_ddl else ('subitem' if in_subitem_ddl else 'missing'),
                'monday_column_id': target_column_id
            })
        
        # Process business logic mappings
        for staging_column, mapping_info in business_logic_mappings.items():
            if isinstance(mapping_info, dict):
                source_column = mapping_info.get('source_column', mapping_info.get('derived_from', ''))
                description = mapping_info.get('description', 'Business logic mapping')
                all_mapped_staging.add(staging_column)
                
                # Check if columns exist in various places
                in_master_ddl = staging_column in master_ddl_columns
                in_subitem_ddl = staging_column in subitem_ddl_columns
                in_orders_unified = source_column in orders_unified_columns if source_column else False
                
                validation_data.append({
                    'staging_column': staging_column,
                    'source_column': source_column,
                    'description': description,
                    'in_master_ddl': in_master_ddl,
                    'in_subitem_ddl': in_subitem_ddl,
                    'in_orders_unified': in_orders_unified,
                    'mapping_valid': (not source_column or in_orders_unified) and (in_master_ddl or in_subitem_ddl),
                    'table_target': 'master' if in_master_ddl else ('subitem' if in_subitem_ddl else 'missing'),
                    'monday_column_id': ''
                })
        
        # Process subitem mappings  
        for staging_column, mapping_info in subitem_mappings.items():
            if isinstance(mapping_info, dict):
                source_column = mapping_info.get('source_column', mapping_info.get('derived_from', ''))
                description = mapping_info.get('description', 'Subitem mapping')
                all_mapped_staging.add(staging_column)
                
                # Check if columns exist in various places
                in_master_ddl = staging_column in master_ddl_columns
                in_subitem_ddl = staging_column in subitem_ddl_columns
                in_orders_unified = source_column in orders_unified_columns if source_column else False
                
                validation_data.append({
                    'staging_column': staging_column,
                    'source_column': source_column,
                    'description': description,
                    'in_master_ddl': in_master_ddl,
                    'in_subitem_ddl': in_subitem_ddl,
                    'in_orders_unified': in_orders_unified,
                    'mapping_valid': (not source_column or in_orders_unified) and (in_master_ddl or in_subitem_ddl),
                    'table_target': 'master' if in_master_ddl else ('subitem' if in_subitem_ddl else 'missing'),
                    'monday_column_id': ''
                })
        
        # Add unmapped DDL columns
        
        for col in master_ddl_columns:
            if col not in all_mapped_staging:
                validation_data.append({
                    'staging_column': col,
                    'source_column': '',
                    'description': 'UNMAPPED DDL COLUMN',
                    'in_master_ddl': True,
                    'in_subitem_ddl': False,
                    'in_orders_unified': False,
                    'mapping_valid': False,
                    'table_target': 'master',
                    'monday_column_id': ''
                })
        
        for col in subitem_ddl_columns:
            if col not in all_mapped_staging:
                validation_data.append({
                    'staging_column': col,
                    'source_column': '',
                    'description': 'UNMAPPED DDL COLUMN',
                    'in_master_ddl': False,
                    'in_subitem_ddl': True,
                    'in_orders_unified': False,
                    'mapping_valid': False,
                    'table_target': 'subitem',
                    'monday_column_id': ''
                })
        
        return pd.DataFrame(validation_data)
    
    def analyze_validation_results(self, df):
        """Analyze and report validation results"""
        print("\n" + "="*80)
        print("VALIDATION ANALYSIS")
        print("="*80)
        
        total_mappings = len(df)
        valid_mappings = len(df[df['mapping_valid'] == True])
        invalid_mappings = total_mappings - valid_mappings
        
        print(f"\nOverall Statistics:")
        print(f"  Total mappings analyzed: {total_mappings}")
        print(f"  Valid mappings: {valid_mappings} ({valid_mappings/total_mappings*100:.1f}%)")
        print(f"  Invalid mappings: {invalid_mappings} ({invalid_mappings/total_mappings*100:.1f}%)")
        
        # Breakdown by table
        master_count = len(df[df['table_target'] == 'master'])
        subitem_count = len(df[df['table_target'] == 'subitem'])
        missing_count = len(df[df['table_target'] == 'missing'])
        
        print(f"\nBreakdown by target table:")
        print(f"  Master table mappings: {master_count}")
        print(f"  Subitem table mappings: {subitem_count}")
        print(f"  Missing/unmapped: {missing_count}")
        
        # Show invalid mappings
        invalid = df[df['mapping_valid'] == False]
        if len(invalid) > 0:
            print(f"\n❌ INVALID MAPPINGS ({len(invalid)} found):")
            for idx, row in invalid.head(10).iterrows():
                status = []
                if not row['in_orders_unified'] and row['source_column']:
                    status.append("source column missing")
                if not row['in_master_ddl'] and not row['in_subitem_ddl']:
                    status.append("staging column missing")
                if not row['source_column']:
                    status.append("unmapped DDL column")
                
                print(f"  - {row['staging_column']} -> {row['source_column']} ({', '.join(status)})")
            
            if len(invalid) > 10:
                print(f"  ... and {len(invalid) - 10} more invalid mappings")
        
        # Show valid mappings
        valid = df[df['mapping_valid'] == True]
        if len(valid) > 0:
            print(f"\n✅ VALID MAPPINGS (showing first 10 of {len(valid)}):")
            for idx, row in valid.head(10).iterrows():
                target = row['table_target']
                print(f"  - {row['staging_column']} -> {row['source_column']} ({target})")
        
        return df
    
    def save_detailed_report(self, df):
        """Save detailed CSV report"""
        report_path = self.repo_root / "mapping_validation_detailed_report.csv"
        df.to_csv(report_path, index=False)
        print(f"\n📊 Detailed report saved to: {report_path}")
        
        return report_path
    
    def run_validation(self):
        """Run complete validation process"""
        try:
            # Create validation DataFrame
            df = self.create_validation_dataframe()
            
            # Analyze results
            df = self.analyze_validation_results(df)
            
            # Save report
            report_path = self.save_detailed_report(df)
            
            print(f"\n🎯 VALIDATION COMPLETE!")
            print(f"📄 Full report: {report_path}")
            
            return df
            
        except Exception as e:
            print(f"❌ ERROR during validation: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Main execution function"""
    validator = ComprehensiveMappingValidator()
    results = validator.run_validation()
    
    if results is not None:
        print(f"\n✅ Validation completed successfully!")
        print(f"📊 {len(results)} total mappings analyzed")
    else:
        print(f"❌ Validation failed!")

if __name__ == "__main__":
    main()
