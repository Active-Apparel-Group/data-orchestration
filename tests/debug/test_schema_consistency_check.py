#!/usr/bin/env python3
"""
Quick SQL Schema Consistency Check for ORDER_LIST Tables
"""
import sys
from pathlib import Path

# Add project paths
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from pipelines.utils import db, logger

def run_schema_check():
    """Run schema consistency check"""
    print("🔍 Checking schema consistency for ORDER_LIST tables...")
    
    # Read SQL file
    sql_file = repo_root / "sql" / "tests" / "check_order_list_schema_consistency.sql"
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    try:
        # Execute using our working db connection
        with db.get_connection_by_key('orders') as conn:
            cursor = conn.cursor()
            
            # Split and execute each statement
            statements = sql_content.split(';')
            
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        print(f"\n--- Executing statement {i+1} ---")
                        cursor.execute(statement)
                        
                        # If it's a SELECT, fetch results
                        if statement.upper().strip().startswith('SELECT'):
                            results = cursor.fetchall()
                            if results:
                                # Print column headers
                                columns = [desc[0] for desc in cursor.description]
                                print(f"{'  '.join(columns)}")
                                print("-" * 50)
                                
                                # Print rows
                                for row in results:
                                    print(f"{'  '.join(str(val) if val is not None else 'NULL' for val in row)}")
                            else:
                                print("No results returned")
                    except Exception as e:
                        print(f"Statement {i+1} failed: {e}")
                        continue
    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    print("\n✅ Schema check completed")
    return True

if __name__ == "__main__":
    run_schema_check()
