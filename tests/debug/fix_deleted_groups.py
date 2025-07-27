#!/usr/bin/env python3
"""
Fix Deleted Groups - Clear group_id references for deleted groups
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔧 Fixing deleted group references in database...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        # Clear group_id for records with deleted groups
        print("🗑️ Clearing group_id references for deleted groups...")
        
        update_sql = """
        UPDATE FACT_ORDER_LIST 
        SET group_id = NULL, group_name = NULL
        WHERE group_id IS NOT NULL
        AND group_id NOT IN (
            -- Keep only existing groups (the ones we excluded)
            'group_mktbetb', 'group_mktbm2xg', 'group_mkt9z71k'
        )
        """
        
        cursor.execute(update_sql)
        updated_count = cursor.rowcount
        
        print(f"✅ Cleared group_id for {updated_count} records")
        
        # Also clear any group references in the lines table if it exists
        try:
            lines_update_sql = """
            UPDATE ORDER_LIST_LINES 
            SET group_id = NULL, group_name = NULL
            WHERE group_id IS NOT NULL
            AND group_id NOT IN (
                'group_mktbetb', 'group_mktbm2xg', 'group_mkt9z71k'
            )
            """
            
            cursor.execute(lines_update_sql)
            lines_updated = cursor.rowcount
            print(f"✅ Cleared group_id for {lines_updated} line records")
            
        except Exception as e:
            print(f"⚠️ Lines table update skipped: {e}")
        
        # Commit the changes
        connection.commit()
        print("✅ Database updates committed successfully")
        
        # Show current state
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST WHERE group_id IS NOT NULL")
        remaining_groups = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM FACT_ORDER_LIST WHERE sync_state = 'PENDING'")
        pending_records = cursor.fetchone()[0]
        
        print(f"📊 Current state:")
        print(f"   Records with group_id: {remaining_groups}")
        print(f"   Records pending sync: {pending_records}")
        
        cursor.close()

if __name__ == "__main__":
    main()
