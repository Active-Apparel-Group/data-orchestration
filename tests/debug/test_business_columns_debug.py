#!/usr/bin/env python3
"""
Debug Business Columns - Verify transformation columns inclusion
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def main():
    """Debug business columns to verify transformation columns inclusion"""
    try:
        logger.info("🔍 Debug Business Columns - Checking transformation columns...")
        
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Get business columns from config parser
        business_columns = config.get_business_columns()
        logger.info(f"📊 Business columns count: {len(business_columns)}")
        
        # Check for transformation columns
        transformation_columns = ['group_name', 'group_id', 'item_name']
        logger.info(f"🔍 Checking for transformation columns: {transformation_columns}")
        
        for col in transformation_columns:
            is_present = col in business_columns
            logger.info(f"   {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
        
        # Show first 10 business columns for context
        logger.info(f"📋 First 10 business columns: {business_columns[:10]}")
        
        # Check essential columns from TOML
        essential_columns = config._config.get('database', {}).get('essential_columns', [])
        logger.info(f"🗃️ Essential columns from TOML: {len(essential_columns)} columns")
        logger.info(f"📋 Essential columns: {essential_columns}")
        
        # Check Monday.com mappings
        monday_headers = (config._config.get('monday', {})
                         .get('column_mapping', {})
                         .get(config._environment, {})
                         .get('headers', {}))
        logger.info(f"🗺️ Monday.com headers count: {len(monday_headers)}")
        
        # Template engine context
        template_engine = SQLTemplateEngine(config)
        context = template_engine.get_template_context()
        template_business_columns = context.get('business_columns', [])
        logger.info(f"🎨 Template engine business columns: {len(template_business_columns)}")
        
        # Check if transformation columns are in template context
        for col in transformation_columns:
            is_present = col in template_business_columns
            logger.info(f"   Template {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
        
        # Determine if fix is working
        all_transformation_present = all(col in business_columns for col in transformation_columns)
        
        if all_transformation_present:
            logger.info("✅ SUCCESS: All transformation columns found in business_columns")
        else:
            logger.error("❌ ISSUE: Transformation columns missing from business_columns")
            logger.error("🔧 SOLUTION NEEDED: Transformation columns must be added to business_columns list")
        
        return all_transformation_present
        
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"🏁 Debug completed: {'SUCCESS' if success else 'NEEDS FIX'}")
    sys.exit(0 if success else 1)
