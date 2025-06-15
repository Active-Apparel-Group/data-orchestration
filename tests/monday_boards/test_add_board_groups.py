"""
Test script for add_board_groups.py

This script tests the board group management functionality by:
1. Querying MON_Board_Groups table to get available boards
2. Testing group creation, checking, and listing functions
3. Verifying the cross-reference logic between database and Monday.com

Usage:
    python test_add_board_groups.py
    python test_add_board_groups.py --board-name "Customer Master Schedule"
"""

import pandas as pd
import pyodbc
import sys
import os
import argparse
import warnings
import urllib3
from datetime import datetime

# Suppress warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# Add the current directory to path to import add_board_groups
sys.path.append(os.path.dirname(__file__))
from add_board_groups import (
    check_group_exists,
    create_board_group,
    list_board_groups,
    ensure_group_exists,
    delete_board_group,
    check_group_exists_in_db,
    cleanup_orphaned_groups
)

def load_env():
    """Load .env file from repo root."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)
        return True
    except ImportError:
        print("python-dotenv not available, using system environment variables")
        return False
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return False

def get_db_config(db_key='ORDERS'):
    """Get DB config from environment variables."""
    load_env()  # Ensure environment is loaded
    
    # Get password from either SECRET_xxx_PWD (base64) or DB_xxx_PASSWORD (plain)
    import base64
    password = os.getenv(f'SECRET_{db_key.upper()}_PWD')
    if password:
        # Decode base64 password
        try:
            password = base64.b64decode(password).decode()
        except:
            pass  # Use as plain text if not base64
    else:
        password = os.getenv(f'DB_{db_key.upper()}_PASSWORD')
    
    return {
        'host': os.getenv(f'DB_{db_key.upper()}_HOST'),
        'port': int(os.getenv(f'DB_{db_key.upper()}_PORT', 1433)),
        'database': os.getenv(f'DB_{db_key.upper()}_DATABASE'),
        'username': os.getenv(f'DB_{db_key.upper()}_USERNAME'),
        'password': password
    }

def get_database_connection():
    """Create database connection using environment variables"""
    try:
        orders_cfg = get_db_config('ORDERS')
        
        # Validate that we have all required config
        required_keys = ['host', 'database', 'username', 'password']
        missing_keys = [key for key in required_keys if not orders_cfg.get(key)]
        
        if missing_keys:
            print(f"❌ Missing database configuration: {missing_keys}")
            print("💡 Make sure to set the following environment variables:")
            for key in missing_keys:
                print(f"   - DB_ORDERS_{key.upper()}")
            return None
        
        # Use ODBC Driver 17 for SQL Server if available, fallback to SQL Server
        driver = "{ODBC Driver 17 for SQL Server}"
        try:
            test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
            pyodbc.connect(test_conn_str, timeout=1)  # This will fail but tests driver availability
        except:
            driver = "{SQL Server}"
        
        conn_str = (
            f"DRIVER={driver};"
            f"SERVER={orders_cfg['host']},{orders_cfg['port']};"
            f"DATABASE={orders_cfg['database']};"
            f"UID={orders_cfg['username']};PWD={orders_cfg['password']};"
            "Encrypt=no;TrustServerCertificate=yes;"
        )
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_available_boards(conn):
    """Query MON_Board_Groups table to get available boards"""
    try:
        query = """
        SELECT DISTINCT 
            board_id,
            board_name,
            COUNT(group_id) as group_count,
            MAX(updated_date) as last_updated
        FROM [dbo].[MON_Boards_Groups]
        WHERE is_active = 1
        GROUP BY board_id, board_name
        ORDER BY board_name
        """
        
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Error querying boards: {e}")
        return pd.DataFrame()

def test_board_groups_functionality(board_id, board_name):
    """Test all board group functions with a specific board"""
    print(f"\n{'='*60}")
    print(f"Testing Board: {board_name} (ID: {board_id})")
    print(f"{'='*60}")
    
    # Test 1: List existing groups
    print(f"\n1. Listing existing groups on board '{board_name}':")
    print("-" * 50)
    existing_groups = list_board_groups(board_id)
    
    if existing_groups:
        for i, group in enumerate(existing_groups, 1):
            print(f"  {i}. {group['title']} (ID: {group['id']}, Color: {group.get('color', 'N/A')})")
        print(f"\nTotal groups found: {len(existing_groups)}")
    else:
        print("  No groups found or error occurred")
    
    # Test 2: Check if a specific group exists
    test_group_name = "TEST_GROUP_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n2. Checking if test group '{test_group_name}' exists:")
    print("-" * 50)
    group_id = check_group_exists(board_id, test_group_name)
    
    if group_id:
        print(f"  ✅ Group exists with ID: {group_id}")
    else:
        print(f"  ❌ Group does not exist")
    
    # Test 3: Create a new test group
    print(f"\n3. Creating new test group '{test_group_name}':")
    print("-" * 50)
    new_group_id = create_board_group(board_id, test_group_name)
    
    if new_group_id:
        print(f"  ✅ Successfully created group with ID: {new_group_id}")
        
        # Test 4: Verify the group was created
        print(f"\n4. Verifying group creation:")
        print("-" * 50)
        verified_group_id = check_group_exists(board_id, test_group_name)
        if verified_group_id == new_group_id:
            print(f"  ✅ Group verified successfully")
        else:
            print(f"  ❌ Group verification failed")
        
        # Test 5: Test ensure_group_exists with existing group
        print(f"\n5. Testing ensure_group_exists with existing group:")
        print("-" * 50)
        ensured_group_id = ensure_group_exists(board_id, test_group_name)
        if ensured_group_id == new_group_id:
            print(f"  ✅ ensure_group_exists returned correct existing group ID")
        else:
            print(f"  ❌ ensure_group_exists failed")
        
        # Test 6: Cleanup - delete the test group
        print(f"\n6. Cleaning up - deleting test group:")
        print("-" * 50)
        deleted = delete_board_group(board_id, new_group_id)
        if deleted:
            print(f"  ✅ Test group deleted successfully")
            
            # Verify deletion
            final_check = check_group_exists(board_id, test_group_name)
            if final_check is None:
                print(f"  ✅ Group deletion verified")
            else:
                print(f"  ❌ Group still exists after deletion")
        else:
            print(f"  ❌ Failed to delete test group")
    else:
        print(f"  ❌ Failed to create test group")
    
    # Test 7: Test ensure_group_exists with non-existing group
    new_test_group = "ENSURE_TEST_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"\n7. Testing ensure_group_exists with new group '{new_test_group}':")
    print("-" * 50)
    ensured_new_group_id = ensure_group_exists(board_id, new_test_group)
    
    if ensured_new_group_id:
        print(f"  ✅ ensure_group_exists created new group with ID: {ensured_new_group_id}")
        
        # Clean up the new group
        delete_board_group(board_id, ensured_new_group_id)
        print(f"  🧹 Cleaned up test group")
    else:
        print(f"  ❌ ensure_group_exists failed to create new group")

def test_enhanced_workflow(board_id, board_name):
    """Test the enhanced database-integrated workflow"""
    print(f"\n{'='*60}")
    print(f"Testing Enhanced Database-Integrated Workflow")
    print(f"Board: {board_name} (ID: {board_id})")
    print(f"{'='*60}")
    
    test_group_name = "TEST_DB_WORKFLOW_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test 1: Enhanced ensure_group_exists (full workflow)
    print(f"\n1. Testing enhanced ensure_group_exists workflow:")
    print(f"   Group: '{test_group_name}'")
    print("-" * 50)
    
    # This should:
    # 1. Check database - not found
    # 2. Add to database without group_id
    # 3. Create in Monday.com
    # 4. Update database with group_id
    group_id = ensure_group_exists(board_id, test_group_name)
    
    if group_id:
        print(f"✅ Enhanced workflow completed - Group ID: {group_id}")
        
        # Test 2: Verify database consistency
        print(f"\n2. Verifying database consistency:")
        print("-" * 50)
        db_group_id = check_group_exists_in_db(board_id, test_group_name)
        if db_group_id == group_id:
            print(f"✅ Database verification successful")
        else:
            print(f"❌ Database verification failed - Expected: {group_id}, Got: {db_group_id}")
        
        # Test 3: Test ensure_group_exists with existing group (should find in database)
        print(f"\n3. Testing with existing group (should use database):")
        print("-" * 50)
        existing_group_id = ensure_group_exists(board_id, test_group_name)
        if existing_group_id == group_id:
            print(f"✅ Found existing group in database correctly")
        else:
            print(f"❌ Failed to find existing group correctly")
        
        # Cleanup
        print(f"\n4. Cleaning up test group:")
        print("-" * 50)
        deleted = delete_board_group(board_id, group_id)
        if deleted:
            print(f"✅ Test group deleted from Monday.com")
            
            # Mark as inactive in database
            conn = get_database_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """UPDATE [dbo].[MON_Boards_Groups] 
                           SET is_active = 0, updated_date = ? 
                           WHERE board_id = ? AND group_title = ?""",
                        (datetime.now(), board_id, test_group_name)
                    )
                    conn.commit()
                    print(f"✅ Test group marked as inactive in database")
                except Exception as e:
                    print(f"❌ Failed to cleanup database: {e}")
                finally:
                    conn.close()
        else:
            print(f"❌ Failed to delete test group")
    else:
        print(f"❌ Enhanced workflow failed")
    
    # Test 4: Orphaned groups cleanup
    print(f"\n5. Testing orphaned groups cleanup:")
    print("-" * 50)
    cleaned_count = cleanup_orphaned_groups(board_id)
    print(f"Cleaned up {cleaned_count} orphaned groups")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Test add_board_groups.py functionality')
    parser.add_argument('--board-name', type=str, help='Specific board name to test')
    parser.add_argument('--board-id', type=str, help='Specific board ID to test')
    args = parser.parse_args()
    
    print("Monday.com Board Groups Testing")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    conn = get_database_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        # Get available boards from database
        print(f"\n📋 Querying available boards from MON_Board_Groups table...")
        boards_df = get_available_boards(conn)
        
        if boards_df.empty:
            print("❌ No boards found in MON_Board_Groups table")
            print("💡 Make sure to run sync_board_groups.py first to populate the table")
            return
        
        print(f"\n✅ Found {len(boards_df)} boards in database:")
        print("-" * 60)
        for _, board in boards_df.iterrows():
            print(f"  • {board['board_name']} (ID: {board['board_id']}) - {board['group_count']} groups")
        
        # Filter boards based on arguments
        if args.board_name:
            boards_df = boards_df[boards_df['board_name'].str.contains(args.board_name, case=False, na=False)]
            if boards_df.empty:
                print(f"❌ No boards found matching name: {args.board_name}")
                return
        
        if args.board_id:
            boards_df = boards_df[boards_df['board_id'] == args.board_id]
            if boards_df.empty:
                print(f"❌ No boards found with ID: {args.board_id}")
                return
        
        # Test each board with both workflows
        for _, board in boards_df.iterrows():
            board_id = str(board['board_id'])
            board_name = board['board_name']
            
            try:
                # Original functionality test
                test_board_groups_functionality(board_id, board_name)
                
                # Enhanced workflow test
                test_enhanced_workflow(board_id, board_name)
                
            except Exception as e:
                print(f"\n❌ Error testing board {board_name}: {e}")
        
        print(f"\n{'='*60}")
        print(f"Testing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
