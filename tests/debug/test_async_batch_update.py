"""
Test Script: Async Batch Update Validation - Production Type
Purpose: Test the new async batch update script with planning production type configuration
Location: tests/debug/test_async_batch_update.py
Author: CTO / Head Data Engineer
Date: 2025-07-15

Features:
- Test async batch update import validation
- Validate production type TOML configuration loading
- Test batch preparation logic with real Planning board mappings
- Simulate dry run with production type updates
"""

import sys
from pathlib import Path

# Standard import pattern for project
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "pipelines" / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "pipelines" / "utils"))

import db_helper as db
import logger_helper
import pandas as pd
import asyncio

def test_imports():
    """Test that all required imports work"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing async batch update imports...")
    
    try:
        # Test the new async batch updater import
        sys.path.insert(0, str(repo_root / "pipelines" / "scripts" / "update"))
        from update_boards_async_batch import AsyncBatchMondayUpdater
        
        logger.info("SUCCESS: AsyncBatchMondayUpdater import successful")
        return True
        
    except ImportError as e:
        logger.error(f"FAILED: Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"FAILED: Unexpected error during import: {e}")
        return False

def test_config_loading():
    """Test TOML configuration loading"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing TOML configuration loading...")
    
    try:
        config_path = repo_root / "configs" / "updates" / "planning_update_production_type.toml"
        
        from update_boards_async_batch import AsyncBatchMondayUpdater
        updater = AsyncBatchMondayUpdater(str(config_path))
        
        # Validate config structure
        assert 'metadata' in updater.update_config
        assert 'query_config' in updater.update_config
        assert 'column_mapping' in updater.update_config
        
        logger.info("SUCCESS: TOML configuration loading successful")
        logger.info(f"   Board ID: {updater.update_config['metadata']['board_id']}")
        logger.info(f"   Column mappings: {len(updater.update_config['column_mapping'])}")
        
        return True
        
    except Exception as e:
        logger.error(f"FAILED: Config loading failed: {e}")
        return False

def test_batch_preparation():
    """Test batch update preparation logic"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing batch preparation logic...")
    
    try:
        config_path = repo_root / "configs" / "updates" / "planning_update_production_type.toml"
        
        from update_boards_async_batch import AsyncBatchMondayUpdater
        updater = AsyncBatchMondayUpdater(str(config_path))
        
        # Create test DataFrame matching the production type config structure
        test_data = {
            'monday_item_id': [8772699644, 8772699663, 8772699715],
            'xPRODUCTION TYPE': ['LONGSON', 'PARTNER', 'LONGSON'],
        }
        
        df = pd.DataFrame(test_data)
        logger.info(f"Test DataFrame created with {len(df)} records")
        
        # Test batch preparation
        batch_updates = updater.prepare_batch_updates(df)
        
        logger.info(f"SUCCESS: Batch preparation successful - {len(batch_updates)} updates prepared")
        
        # Validate batch structure
        for i, update in enumerate(batch_updates[:2]):  # Check first 2
            assert 'board_id' in update
            assert 'item_id' in update
            assert 'column_updates' in update
            logger.info(f"   Update {i+1}: Item {update['item_id']} with {len(update['column_updates'])} fields")
        
        return True
        
    except Exception as e:
        logger.error(f"FAILED: Batch preparation failed: {e}")
        return False

async def test_dry_run_simulation():
    """Test dry run simulation"""
    logger = logger_helper.get_logger(__name__)
    logger.info("Testing dry run simulation...")
    
    try:
        config_path = repo_root / "configs" / "updates" / "planning_update_production_type.toml"
        
        from update_boards_async_batch import AsyncBatchMondayUpdater
        updater = AsyncBatchMondayUpdater(str(config_path))
        
        # Mock query for testing production type updates
        test_query = """
        SELECT 
            8772699644 as monday_item_id,
            'LONGSON' as [xPRODUCTION TYPE]
        UNION ALL
        SELECT 
            8772699663 as monday_item_id,
            'PARTNER' as [xPRODUCTION TYPE]
        """
        
        # Execute dry run
        result = await updater.async_batch_update_from_query(
            test_query, 
            updater.update_config, 
            dry_run=True
        )
        
        # Validate dry run result
        assert result['success'] == True
        assert result['dry_run'] == True
        assert result['total_records'] > 0
        assert result['success_rate'] == 100.0
        
        logger.info("SUCCESS: Dry run simulation successful")
        logger.info(f"   Total records: {result['total_records']}")
        logger.info(f"   Success rate: {result['success_rate']}%")
        logger.info(f"   Duration: {result['duration_seconds']:.2f} seconds")
        
        return True
        
    except Exception as e:
        logger.error(f"FAILED: Dry run simulation failed: {e}")
        return False

def main():
    """Main test execution"""
    logger = logger_helper.get_logger(__name__)
    
    logger.info("STARTING: Async Batch Update Validation Tests - Production Type")
    logger.info("=" * 60)
    
    tests = [
        ("Import Validation", test_imports),
        ("Config Loading", test_config_loading), 
        ("Batch Preparation", test_batch_preparation),
        ("Dry Run Simulation", lambda: asyncio.run(test_dry_run_simulation()))
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 40)
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"FAILED: {test_name} failed with exception: {e}")
            failed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        logger.info("SUCCESS: All tests passed! Async batch update ready for production type updates.")
    else:
        logger.warning(f"WARNING: {failed} test(s) failed. Review errors above.")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
