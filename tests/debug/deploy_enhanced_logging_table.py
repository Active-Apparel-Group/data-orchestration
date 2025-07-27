#!/usr/bin/env python3
"""
Deploy Enhanced API Logging Table
"""

import sys
from pathlib import Path

# Standard import pattern for this project
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger

logger = logger.get_logger(__name__)

def main():
    print("🚀 DEPLOYING ENHANCED API LOGGING TABLE")
    print("=" * 50)
    
    # Read SQL file from migrations folder
    sql_file = repo_root / "db" / "migrations" / "enhanced_api_logging_table.sql"
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    with db.get_connection('orders') as connection:
        cursor = connection.cursor()
        
        try:
            # Execute SQL
            cursor.execute(sql_content)
            connection.commit()
            
            print("✅ Enhanced API logging table deployed successfully!")
            
            # Verify deployment
            cursor.execute("SELECT COUNT(*) FROM ORDER_LIST_API_LOG_ENHANCED")
            count = cursor.fetchone()[0]
            print(f"📊 Table contains {count} sample records")
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            connection.rollback()
        
        cursor.close()

if __name__ == "__main__":
    main()
