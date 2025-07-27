#!/usr/bin/env python3
"""
Test Template Engine Business Columns - Focused Test
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.sql_template_engine import SQLTemplateEngine

logger = logger.get_logger(__name__)

def main():
    """Test what the template engine actually gets for business columns"""
    try:
        logger.info("🎯 Testing Template Engine Business Columns...")
        
        # Config FIRST
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        config = DeltaSyncConfig.from_toml(config_path)
        
        # Create template engine
        template_engine = SQLTemplateEngine(config)
        
        logger.info("📊 TEST 1: Template engine with use_dynamic_merge_columns=False (Monday.com mode)")
        context_monday = template_engine.get_template_context(use_dynamic_merge_columns=False)
        business_cols_monday = context_monday.get('business_columns', [])
        logger.info(f"   Business columns count: {len(business_cols_monday)}")
        
        # Check for transformation columns
        transformation_columns = ['group_name', 'group_id', 'item_name']
        for col in transformation_columns:
            is_present = col in business_cols_monday
            logger.info(f"   {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
        
        logger.info("📊 TEST 2: Template engine with use_dynamic_merge_columns=True (Merge mode)")
        context_merge = template_engine.get_template_context(use_dynamic_merge_columns=True)
        business_cols_merge = context_merge.get('business_columns', [])
        logger.info(f"   Business columns count: {len(business_cols_merge)}")
        
        # Check for transformation columns in merge mode
        for col in transformation_columns:
            is_present = col in business_cols_merge
            logger.info(f"   {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
        
        logger.info("📊 TEST 3: Direct config method calls")
        
        # Test config methods directly
        logger.info("   Config get_business_columns(use_dynamic_detection=False):")
        static_cols = config.get_business_columns(use_dynamic_detection=False)
        logger.info(f"     Count: {len(static_cols)}")
        for col in transformation_columns:
            is_present = col in static_cols
            logger.info(f"     {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
        
        logger.info("   Config get_business_columns(use_dynamic_detection=True):")
        dynamic_cols = config.get_business_columns(use_dynamic_detection=True)
        logger.info(f"     Count: {len(dynamic_cols)}")
        for col in transformation_columns:
            is_present = col in dynamic_cols
            logger.info(f"     {col}: {'✅ FOUND' if is_present else '❌ MISSING'}")
        
        # Determine which mode is working
        monday_has_all = all(col in business_cols_monday for col in transformation_columns)
        merge_has_all = all(col in business_cols_merge for col in transformation_columns)
        
        logger.info("🎯 RESULTS SUMMARY:")
        logger.info(f"   Monday.com mode has all transformation columns: {'✅ YES' if monday_has_all else '❌ NO'}")
        logger.info(f"   Merge mode has all transformation columns: {'✅ YES' if merge_has_all else '❌ NO'}")
        
        if merge_has_all:
            logger.info("✅ SUCCESS: Merge mode working correctly")
            return True
        elif monday_has_all:
            logger.info("✅ SUCCESS: Monday.com mode enhancement working")
            return True
        else:
            logger.error("❌ ISSUE: Neither mode has transformation columns")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    logger.info(f"🏁 Template engine test: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
