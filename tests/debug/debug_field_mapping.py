"""
Debug Field Mapping Issue
Analyze why only 1 field is being mapped instead of 37+ fields
"""
import sys
from pathlib import Path
import yaml

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

import db_helper as db
import logger_helper
import pandas as pd

def debug_field_mapping():
    """Debug field mapping process"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Starting field mapping debug analysis")
    
    # 1. Load the YAML mapping
    mapping_path = repo_root / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
    logger.info(f"Loading mapping from: {mapping_path}")
    
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping_data = yaml.safe_load(f)
    
    logger.info("📊 YAML MAPPING ANALYSIS")
    logger.info(f"   Exact matches: {len(mapping_data.get('exact_matches', []))}")
    logger.info(f"   Mapped fields: {len(mapping_data.get('mapped_fields', []))}")
    logger.info(f"   Computed fields: {len(mapping_data.get('computed_fields', []))}")
    
    # 2. Get sample data from staging
    logger.info("\n📊 SAMPLE STAGING DATA")
    with db.get_connection('dms') as conn:
        sql = """
        SELECT TOP 1 *
        FROM [dbo].[STG_MON_CustMasterSchedule]
        WHERE [CUSTOMER] = 'GREYSON'
        ORDER BY [stg_created_date] DESC
        """
        sample_data = pd.read_sql(sql, conn)
    
    if len(sample_data) > 0:
        sample_record = sample_data.iloc[0]
        logger.info(f"   Available columns in staging: {len(sample_record)}")
        logger.info(f"   Sample columns: {list(sample_record.index)[:10]}...")
        
        # 3. Test exact matches
        logger.info("\n🔍 TESTING EXACT MATCHES")
        exact_matches = mapping_data.get('exact_matches', [])
        
        for i, field_mapping in enumerate(exact_matches[:5]):  # Test first 5
            source_field = field_mapping.get('source_field')
            target_column_id = field_mapping.get('target_column_id')
            
            logger.info(f"   [{i+1}] {source_field} -> {target_column_id}")
            
            if source_field in sample_record:
                value = sample_record.get(source_field)
                logger.info(f"       ✅ Found: {value} (type: {type(value)})")
                
                # Test if value would pass _extract_clean_value logic
                if value and str(value).strip() and str(value).strip() != 'nan':
                    logger.info(f"       ✅ Would be included in mapping")
                else:
                    logger.info(f"       ❌ Would be filtered out (empty/nan)")
            else:
                logger.info(f"       ❌ Source field not found in data")
        
        # 4. Test mapped fields
        logger.info("\n🔍 TESTING MAPPED FIELDS")
        mapped_fields = mapping_data.get('mapped_fields', [])
        
        for i, field_mapping in enumerate(mapped_fields):
            source_field = field_mapping.get('source_field')
            target_field = field_mapping.get('target_field')
            transformation = field_mapping.get('transformation')
            
            logger.info(f"   [{i+1}] {source_field} -> {target_field} ({transformation})")
            
            if source_field in sample_record:
                value = sample_record.get(source_field)
                logger.info(f"       ✅ Found: {value}")
            else:
                logger.info(f"       ❌ Source field not found")
        
        # 5. Test computed fields
        logger.info("\n🔍 TESTING COMPUTED FIELDS")
        computed_fields = mapping_data.get('computed_fields', [])
        
        for computed_field in computed_fields:
            target_field = computed_field.get('target_field')
            source_fields = computed_field.get('source_fields', [])
            transformation = computed_field.get('transformation')
            
            logger.info(f"   {target_field} ({transformation})")
            logger.info(f"       Source fields: {source_fields}")
            
            for sf in source_fields:
                if sf in sample_record:
                    value = sample_record.get(sf)
                    logger.info(f"       ✅ {sf}: {value}")
                else:
                    logger.info(f"       ❌ {sf}: NOT FOUND")
    
    else:
        logger.warning("No staging data found for GREYSON")

if __name__ == "__main__":
    debug_field_mapping()
