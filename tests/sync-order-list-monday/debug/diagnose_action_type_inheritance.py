

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

#!/usr/bin/env pytdef main():
print("🔍 Diagnosing action_type inheritance issue...")

# Config FIRST
config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
config = DeltaSyncConfig.from_toml(config_path)

# Database connection using config.db_key
with db.get_connection(config.db_key) as connection:
    cursor = connection.cursor()

def main():
    print("🔍 Diagnosing action_type inheritance issue...")
    
    cursor, connection = db.get_connection()
    config = DeltaSyncConfig("development")
    
    # Step 1: Check action_type values in headers
    print("\n📋 Step 1: Checking action_type in ORDER_LIST_V2 headers...")
    cursor.execute("""
    SELECT 
        action_type,
        COUNT(*) as count,
        COUNT(CASE WHEN sync_state = 'PENDING' THEN 1 END) as pending_count
    FROM dbo.ORDER_LIST_V2 
    GROUP BY action_type
    ORDER BY count DESC
    """)
    
    header_results = cursor.fetchall()
    print("   Header action_type distribution:")
    for row in header_results:
        print(f"     {row[0] or 'NULL'}: {row[1]} total ({row[2]} PENDING)")
    
    # Step 2: Check action_type values in lines 
    print("\n📋 Step 2: Checking action_type in ORDER_LIST_LINES...")
    cursor.execute("""
    SELECT 
        action_type,
        COUNT(*) as count
    FROM dbo.ORDER_LIST_LINES 
    GROUP BY action_type
    ORDER BY count DESC
    """)
    
    lines_results = cursor.fetchall()
    print("   Lines action_type distribution:")
    for row in lines_results:
        print(f"     {row[0] or 'NULL'}: {row[1]}")
    
    # Step 3: Check the template to see if action_type is being selected
    print("\n📋 Step 3: Checking if lines inherit from headers properly...")
    cursor.execute("""
    SELECT DISTINCT
        h.action_type as header_action_type,
        l.action_type as line_action_type,
        COUNT(*) as line_count
    FROM dbo.ORDER_LIST_LINES l
    INNER JOIN dbo.ORDER_LIST_V2 h ON l.record_uuid = h.record_uuid
    GROUP BY h.action_type, l.action_type
    ORDER BY line_count DESC
    """)
    
    inheritance_results = cursor.fetchall()
    print("   Header → Line action_type inheritance:")
    for row in inheritance_results:
        print(f"     Header: {row[0] or 'NULL'} → Line: {row[1] or 'NULL'} ({row[2]} records)")
    
    # Step 4: Find PENDING records that should have action_type
    print("\n📋 Step 4: Checking PENDING records with missing action_type...")
    cursor.execute("""
    SELECT 
        h.record_uuid,
        h.action_type as should_be,
        l.action_type as currently_is,
        COUNT(l.size_code) as line_count
    FROM dbo.ORDER_LIST_V2 h
    LEFT JOIN dbo.ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
    WHERE h.sync_state = 'PENDING'
    AND h.action_type IS NOT NULL
    GROUP BY h.record_uuid, h.action_type, l.action_type
    HAVING COUNT(l.size_code) > 0
    ORDER BY line_count DESC
    """)
    
    missing_results = cursor.fetchall()
    print(f"   Found {len(missing_results)} PENDING records with lines:")
    if missing_results:
        for i, row in enumerate(missing_results[:5]):  # Show first 5
            print(f"     {i+1}. UUID: {row[0][:8]}... should be '{row[1]}', currently '{row[2] or 'NULL'}' ({row[3]} lines)")
        if len(missing_results) > 5:
            print(f"     ... and {len(missing_results) - 5} more")
    
        print(f"\n🎯 DIAGNOSIS COMPLETE:")
        print(f"   - Lines missing action_type inheritance")
        print(f"   - Need to fix template to include action_type from headers")
        
        cursor.close()

if __name__ == "__main__":
    main()
