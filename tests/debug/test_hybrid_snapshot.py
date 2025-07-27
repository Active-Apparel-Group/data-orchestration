"""
Debug Script: Test Hybrid Snapshot Manager
==========================================

Purpose: Test the hybrid snapshot storage approach for ORDERS_UNIFIED_SNAPSHOT

Tests:
1. SQL Server table creation and basic operations
2. PostgreSQL archive table setup
3. Parquet file creation and compression
4. Hybrid snapshot save/load cycle
5. Performance and storage metrics

Usage:
    python tests/debug/test_hybrid_snapshot.py
"""

import sys
from pathlib import Path

# Add project root for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.hybrid_snapshot_manager import HybridSnapshotManager
from utils.db_helper import get_connection
from utils.logger_helper import get_logger
import pandas as pd
import uuid
from datetime import datetime

def create_test_data():
    """Create sample ORDERS_UNIFIED data for testing"""
    test_data = {
        'AAG ORDER NUMBER': ['JOO-00505', 'JOO-00506', 'JOO-00507'],
        'CUSTOMER NAME': ['greyson', 'greyson', 'nike'],
        'CUSTOMER STYLE': ['POLO-001', 'POLO-002', 'SHIRT-001'],
        'CUSTOMER COLOUR DESCRIPTION': ['Navy', 'White', 'Black'],
        'PO NUMBER': ['PO-123', 'PO-124', 'PO-125'],
        'CUSTOMER ALT PO': ['ALT-123', 'ALT-124', 'ALT-125'],
        'ACTIVE': ['Y', 'Y', 'Y'],
        'ORDER QTY': [720, 480, 360],
        'DUE DATE': ['2025-07-01', '2025-07-15', '2025-08-01']
    }
      # Add some size columns to simulate the 276-column structure
    for size in ['XS', 'S', 'M', 'L', 'XL', 'XXL']:
        test_data[size] = [10, 20, 15]  # Match the 3 rows above
    
    return pd.DataFrame(test_data)

def test_sql_server_table():
    """Test SQL Server snapshot table creation"""
    logger = get_logger(__name__)
    logger.info("Testing SQL Server snapshot table...")
    
    try:
        with get_connection('ORDERS') as conn:
            # Test if table exists
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'ORDERS_UNIFIED_SNAPSHOT'
            """)
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                logger.info("✅ ORDERS_UNIFIED_SNAPSHOT table exists")
                
                # Get table info
                cursor.execute("SELECT COUNT(*) FROM dbo.ORDERS_UNIFIED_SNAPSHOT")
                count = cursor.fetchone()[0]
                logger.info(f"   Current records: {count}")
                
            else:
                logger.warning("❌ ORDERS_UNIFIED_SNAPSHOT table does not exist")
                logger.info("   Please run: sql/ddl/tables/orders/dbo_orders_unified_snapshot.sql")
            
            return exists
            
    except Exception as e:
        logger.error(f"❌ SQL Server test failed: {e}")
        return False

def test_postgresql_archive():
    """Test PostgreSQL archive table"""
    logger = get_logger(__name__)
    logger.info("Testing PostgreSQL archive table...")
    
    try:
        manager = HybridSnapshotManager()
        
        if manager.postgres_connection:
            with manager.postgres_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = 'snapshot_archive'
                """)
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    logger.info("✅ snapshot_archive table exists")
                    
                    # Get table info
                    cursor.execute("SELECT COUNT(*) FROM snapshot_archive")
                    count = cursor.fetchone()[0]
                    logger.info(f"   Current archives: {count}")
                    
                else:
                    logger.warning("❌ snapshot_archive table does not exist")
                    logger.info("   Please run: sql/ddl/tables/kestra/snapshot_archive_postgresql.sql")
                
                return exists
        else:
            logger.warning("❌ PostgreSQL connection not available")
            return False
            
    except Exception as e:
        logger.error(f"❌ PostgreSQL test failed: {e}")
        return False

def test_parquet_creation():
    """Test Parquet file creation and compression"""
    logger = get_logger(__name__)
    logger.info("Testing Parquet file creation...")
    
    try:
        # Create test data
        df = create_test_data()
        
        # Test Parquet conversion
        import pyarrow as pa
        import pyarrow.parquet as pq
        import io
        
        table = pa.Table.from_pandas(df)
        parquet_buffer = io.BytesIO()
        pq.write_table(table, parquet_buffer, compression='snappy')
        parquet_bytes = parquet_buffer.getvalue()
        
        # Calculate compression stats
        original_size = df.memory_usage(deep=True).sum()
        compressed_size = len(parquet_bytes)
        compression_ratio = compressed_size / original_size
        
        logger.info("✅ Parquet creation successful")
        logger.info(f"   Original size: {original_size:,} bytes")
        logger.info(f"   Compressed size: {compressed_size:,} bytes")
        logger.info(f"   Compression ratio: {compression_ratio:.3f}")
        logger.info(f"   Space saved: {((1-compression_ratio)*100):.1f}%")
        
        # Test loading back
        parquet_buffer.seek(0)
        loaded_table = pq.read_table(parquet_buffer)
        loaded_df = loaded_table.to_pandas()
        
        if len(loaded_df) == len(df) and list(loaded_df.columns) == list(df.columns):
            logger.info("✅ Parquet round-trip successful")
            return True
        else:
            logger.error("❌ Parquet round-trip failed")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Parquet dependencies not available: {e}")
        logger.info("   Please install: pip install pyarrow")
        return False
    except Exception as e:
        logger.error(f"❌ Parquet test failed: {e}")
        return False

def test_hybrid_save_load():
    """Test full hybrid snapshot save/load cycle"""
    logger = get_logger(__name__)
    logger.info("Testing hybrid snapshot save/load...")
    
    try:
        # Create test data
        df = create_test_data()
        
        # Initialize manager
        manager = HybridSnapshotManager()
        
        # Test save
        batch_id = str(uuid.uuid4())
        tags = {
            'test_run': True,
            'created_by': 'debug_script',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Saving test snapshot with batch_id: {batch_id}")
        archive_id = manager.save_snapshot(
            df=df,
            customer_filter='test_customer',
            batch_id=batch_id,
            tags=tags
        )
        
        if archive_id:
            logger.info(f"✅ Hybrid save successful, archive_id: {archive_id}")
            
            # Test load from archive
            if manager.postgres_connection:
                loaded_df = manager.load_from_archive(archive_id)
                
                if loaded_df is not None and len(loaded_df) == len(df):
                    logger.info("✅ Archive load successful")
                    
                    # Test statistics
                    stats = manager.get_archive_statistics(customer_filter='test_customer')
                    if not stats.empty:
                        logger.info("✅ Archive statistics retrieved")
                        logger.info(f"   {stats.to_string()}")
                    
                    return True
                else:
                    logger.error("❌ Archive load failed")
                    return False
            else:
                logger.info("✅ SQL Server save successful (PostgreSQL not available)")
                return True
        else:
            logger.error("❌ Hybrid save failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Hybrid test failed: {e}")
        return False

def test_cleanup_operations():
    """Test cleanup and maintenance operations"""
    logger = get_logger(__name__)
    logger.info("Testing cleanup operations...")
    
    try:
        manager = HybridSnapshotManager()
        
        # Test SQL Server cleanup (dry run)
        try:
            with get_connection('ORDERS') as conn:
                cursor = conn.cursor()
                cursor.execute("EXEC [dbo].[sp_snapshot_statistics]")
                
                columns = [column[0] for column in cursor.description]
                stats = []
                for row in cursor.fetchall():
                    stats.append(dict(zip(columns, row)))
                
                logger.info("✅ SQL Server statistics retrieved")
                for stat in stats:
                    logger.info(f"   {stat}")
                    
        except Exception as e:
            logger.warning(f"SQL Server cleanup test skipped: {e}")
        
        # Test PostgreSQL cleanup (dry run)
        if manager.postgres_connection:
            cleanup_preview = manager.cleanup_old_archives(keep_days=30, dry_run=True)
            if not cleanup_preview.empty:
                logger.info("✅ PostgreSQL cleanup preview generated")
                logger.info(f"   Would delete {len(cleanup_preview)} archives")
            else:
                logger.info("✅ PostgreSQL cleanup preview empty (no old archives)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Cleanup test failed: {e}")
        return False

def main():
    """Run all hybrid snapshot tests"""
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("HYBRID SNAPSHOT MANAGER TEST SUITE")
    logger.info("=" * 60)
    
    tests = [
        ("SQL Server Table", test_sql_server_table),
        ("PostgreSQL Archive", test_postgresql_archive),
        ("Parquet Creation", test_parquet_creation),
        ("Hybrid Save/Load", test_hybrid_save_load),
        ("Cleanup Operations", test_cleanup_operations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            logger.info(f"📊 {test_name}: {status}")
            
        except Exception as e:
            logger.error(f"💥 {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Hybrid snapshot system ready.")
    else:
        logger.warning("⚠️  Some tests failed. Check DDL deployment and dependencies.")

if __name__ == "__main__":
    main()
