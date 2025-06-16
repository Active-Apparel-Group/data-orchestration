"""
Add Board Groups to Monday.com

This script provides functionality to create and manage groups on Monday.com boards.
Groups are used to organize items within a board by logical categories.

Enhanced workflow:
1. Check if group exists in MON_Boards_Groups table
2. If doesn't exist, add record to MON_Boards_Groups (without group_id)
3. Update Monday.com to create the group
4. Update the database record with the group_id from Monday.com

Functions:
- create_board_group: Create a new group on a Monday.com board
- check_group_exists: Check if a group already exists on a board
- list_board_groups: List all groups on a board
- ensure_group_exists: Create group if it doesn't exist, return group_id

Dependencies:
- requests, json, os, pyodbc, warnings
"""

import requests
import json
import os
import pyodbc
import warnings
from datetime import datetime

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# Monday.com API configuration
API_URL = "https://api.monday.com/v2"
AUTH_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
API_VERSION = "2025-04"
USER_ID = "31970889"  # Chris Kalathas
HEADERS = {
    "Content-Type": "application/json",
    "API-Version": API_VERSION,
    "Authorization": f"Bearer {AUTH_KEY}"
}

# Database configuration
DB_SERVER = 'tcp:your_server.database.windows.net'  # Update with your server
DB_DATABASE = 'your_database'  # Update with your database
DB_USERNAME = 'your_username'  # Update with your username
DB_PASSWORD = 'your_password'  # Update with your password
DB_DRIVER = '{ODBC Driver 17 for SQL Server}'

# Establish database connection
def db_connection():
    """
    Create and return a database connection
    
    Returns:
        Connection object or None: Connection object if successful, None otherwise
    """
    try:
        conn = pyodbc.connect(
            f"DRIVER={DB_DRIVER};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_USERNAME};"
            f"PWD={DB_PASSWORD};"
        )
        print("Database connection established")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
    return None

# Database configuration functions (matching sync_board_groups.py pattern)
def load_env():
    """Load .env file from repo root."""
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path=env_path)
        return True
    except ImportError:
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

def check_group_exists(board_id, group_name):
    """
    Check if a group exists on the Monday.com board
    First checks database, then Monday.com if needed
    
    Args:
        board_id (str): The Monday.com board ID
        group_name (str): The name of the group to check
        
    Returns:
        str or None: Group ID if exists, None otherwise
    """
    # First check in database
    group_id = check_group_exists_in_db(board_id, group_name)
    if group_id and group_id != '':  # Make sure we have an actual group_id, not empty string
        return group_id
    
    # If not in database or no group_id, check Monday.com directly
    query = f'''
    {{
        boards(ids: [{board_id}]) {{
            groups {{
                id
                title
            }}
        }}
    }}
    '''
    
    data = {'query': query}
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'boards' in result['data'] and result['data']['boards']:
                groups = result['data']['boards'][0]['groups']
                for group in groups:
                    if group['title'] == group_name:
                        return group['id']
        else:
            print(f"Error checking group existence: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception checking group existence: {e}")
    
    return None

def create_board_group(board_id, group_name):
    """
    Create a new group on the Monday.com board
    
    Args:
        board_id (str): The Monday.com board ID
        group_name (str): The name of the group to create
        
    Returns:
        str or None: Group ID if successful, None otherwise
    """
    mutation = f'''
    mutation {{
        create_group(
            board_id: {board_id},
            group_name: "{group_name}"
        ) {{
            id
            title
        }}
    }}
    '''
    
    data = {'query': mutation}
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'create_group' in result['data']:
                group_id = result['data']['create_group']['id']
                print(f"Successfully created group '{group_name}' with ID: {group_id}")
                return group_id
            else:
                print(f"Error in create group response: {result}")
        else:
            print(f"Error creating group: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception creating group: {e}")
    
    return None

def list_board_groups(board_id):
    """
    List all groups on a Monday.com board
    
    Args:
        board_id (str): The Monday.com board ID
        
    Returns:
        list: List of dictionaries with group info [{'id': '...', 'title': '...'}, ...]
    """
    query = f'''
    {{
        boards(ids: [{board_id}]) {{
            groups {{
                id
                title
                color
            }}
        }}
    }}
    '''
    
    data = {'query': query}
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'boards' in result['data'] and result['data']['boards']:
                return result['data']['boards'][0]['groups']
        else:
            print(f"Error listing groups: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception listing groups: {e}")
    
    return []

def ensure_group_exists(board_id, group_name):
    """
    Ensure a group exists on the board using the enhanced workflow:
    1. Check if group exists in MON_Boards_Groups table
    2. If doesn't exist, add record to MON_Boards_Groups (without group_id)
    3. Update Monday.com to create the group
    4. Update the database record with the group_id from Monday.com
    
    Args:
        board_id (str): The Monday.com board ID
        group_name (str): The name of the group
        
    Returns:
        str or None: Group ID if successful, None otherwise
    """
    # Step 1: Check if group exists in database
    group_id = check_group_exists_in_db(board_id, group_name)
    
    if group_id and group_id != '':
        print(f"Group '{group_name}' already exists with ID: {group_id}")
        return group_id
    
    # Step 2: Get board name from database for the new record
    board_name = get_board_name_from_db(board_id)
    if not board_name:
        print(f"Warning: Could not find board name for board_id {board_id}")
        board_name = f"Board_{board_id}"  # Fallback name
    
    # Step 3: Add record to database without group_id
    print(f"Group '{group_name}' doesn't exist, adding to database...")
    db_success = add_group_to_db_without_id(board_id, board_name, group_name)
    
    if not db_success:
        print(f"Failed to add group to database, continuing with Monday.com creation...")
    
    # Step 4: Create group in Monday.com
    print(f"Creating group '{group_name}' in Monday.com...")
    new_group_id = create_board_group(board_id, group_name)
    
    if not new_group_id:
        print(f"Failed to create group in Monday.com")
        return None
    
    # Step 5: Update database record with the group_id from Monday.com
    if db_success:
        print(f"Updating database with group_id: {new_group_id}")
        update_success = update_group_id_in_db(board_id, group_name, new_group_id)
        
        if not update_success:
            print(f"Warning: Failed to update group_id in database")
    
    return new_group_id

def delete_board_group(board_id, group_id):
    """
    Delete a group from the Monday.com board
    
    Args:
        board_id (str): The Monday.com board ID
        group_id (str): The group ID to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    mutation = f'''
    mutation {{
        delete_group(
            board_id: {board_id},
            group_id: "{group_id}"
        ) {{
            id
        }}
    }}
    '''
    
    data = {'query': mutation}
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=data, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'delete_group' in result['data']:
                print(f"Successfully deleted group with ID: {group_id}")
                return True
            else:
                print(f"Error in delete group response: {result}")
        else:
            print(f"Error deleting group: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception deleting group: {e}")
    
    return False

def check_group_exists_in_db(board_id, group_name, conn=None):
    """
    Check if a group exists in the MON_Boards_Groups database table
    
    Args:
        board_id (str): The Monday.com board ID
        group_name (str): The name of the group to check
        conn: Optional database connection (will create new one if None)
        
    Returns:
        str or None: Group ID if exists, None otherwise
    """
    close_conn = False
    if conn is None:
        conn = get_database_connection()
        close_conn = True
    
    if conn is None:
        print("Failed to get database connection")
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        SELECT group_id 
        FROM [dbo].[MON_Boards_Groups] 
        WHERE board_id = ? AND group_title = ? AND is_active = 1
        """
        cursor.execute(query, (board_id, group_name))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return None
        
    except Exception as e:
        print(f"Error checking group in database: {e}")
        return None
    finally:
        if close_conn and conn:
            conn.close()

def add_group_to_db_without_id(board_id, board_name, group_name, conn=None):
    """
    Add a group record to MON_Boards_Groups table without the group_id
    
    Args:
        board_id (str): The Monday.com board ID
        board_name (str): The name of the board
        group_name (str): The name of the group to add
        conn: Optional database connection (will create new one if None)
        
    Returns:
        bool: True if successful, False otherwise
    """
    close_conn = False
    if conn is None:
        conn = get_database_connection()
        close_conn = True
    
    if conn is None:
        print("Failed to get database connection")
        return False
    
    try:
        cursor = conn.cursor()
        now = datetime.now()
        
        # Insert record with empty group_id (will be updated later)
        insert_query = """
        INSERT INTO [dbo].[MON_Boards_Groups] 
        (board_id, board_name, group_id, group_title, created_date, updated_date, is_active)
        VALUES (?, ?, '', ?, ?, ?, 1)
        """
        
        cursor.execute(insert_query, (board_id, board_name, group_name, now, now))
        conn.commit()
        
        print(f"Added group '{group_name}' to database (awaiting group_id from Monday.com)")
        return True
        
    except Exception as e:
        print(f"Error adding group to database: {e}")
        return False
    finally:
        if close_conn and conn:
            conn.close()

def update_group_id_in_db(board_id, group_name, group_id, conn=None):
    """
    Update the group_id in the MON_Boards_Groups table after Monday.com creation
    
    Args:
        board_id (str): The Monday.com board ID
        group_name (str): The name of the group
        group_id (str): The group ID from Monday.com
        conn: Optional database connection (will create new one if None)
        
    Returns:
        bool: True if successful, False otherwise
    """
    close_conn = False
    if conn is None:
        conn = get_database_connection()
        close_conn = True
    
    if conn is None:
        print("Failed to get database connection")
        return False
    
    try:
        cursor = conn.cursor()
        now = datetime.now()
        
        # Update the record with the group_id from Monday.com
        update_query = """
        UPDATE [dbo].[MON_Boards_Groups] 
        SET group_id = ?, updated_date = ?
        WHERE board_id = ? AND group_title = ? AND group_id = ''
        """
        
        cursor.execute(update_query, (group_id, now, board_id, group_name))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"Updated group '{group_name}' with group_id: {group_id}")
            return True
        else:
            print(f"No records updated for group '{group_name}'")
            return False
        
    except Exception as e:
        print(f"Error updating group_id in database: {e}")
        return False
    finally:
        if close_conn and conn:
            conn.close()

def get_board_name_from_db(board_id, conn=None):
    """
    Get board name from the MON_Boards_Groups table
    
    Args:
        board_id (str): The Monday.com board ID
        conn: Optional database connection (will create new one if None)
        
    Returns:
        str or None: Board name if found, None otherwise
    """
    close_conn = False
    if conn is None:
        conn = get_database_connection()
        close_conn = True
    
    if conn is None:
        return None
    
    try:
        cursor = conn.cursor()
        query = """
        SELECT DISTINCT board_name 
        FROM [dbo].[MON_Boards_Groups] 
        WHERE board_id = ? AND is_active = 1
        """
        cursor.execute(query, (board_id,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return None
        
    except Exception as e:
        print(f"Error getting board name from database: {e}")
        return None
    finally:
        if close_conn and conn:
            conn.close()

def cleanup_orphaned_groups(board_id, conn=None):
    """
    Clean up groups that exist in database but not in Monday.com
    This can happen if Monday.com groups are deleted outside of our system
    
    Args:
        board_id (str): The Monday.com board ID
        conn: Optional database connection (will create new one if None)
        
    Returns:
        int: Number of orphaned groups cleaned up
    """
    close_conn = False
    if conn is None:
        conn = get_database_connection()
        close_conn = True
    
    if conn is None:
        print("Failed to get database connection")
        return 0
    
    try:
        # Get groups from Monday.com
        monday_groups = list_board_groups(board_id)
        monday_group_names = [group['title'] for group in monday_groups]
        
        # Get groups from database
        cursor = conn.cursor()
        db_query = """
        SELECT group_title, group_id 
        FROM [dbo].[MON_Boards_Groups] 
        WHERE board_id = ? AND is_active = 1 AND group_id != ''
        """
        cursor.execute(db_query, (board_id,))
        db_groups = cursor.fetchall()
        
        # Find orphaned groups (in database but not in Monday.com)
        orphaned_count = 0
        for db_group_title, db_group_id in db_groups:
            if db_group_title not in monday_group_names:
                print(f"Found orphaned group in database: {db_group_title} (ID: {db_group_id})")
                
                # Mark as inactive instead of deleting
                update_query = """
                UPDATE [dbo].[MON_Boards_Groups] 
                SET is_active = 0, updated_date = ?
                WHERE board_id = ? AND group_title = ? AND group_id = ?
                """
                cursor.execute(update_query, (datetime.now(), board_id, db_group_title, db_group_id))
                orphaned_count += 1
        
        if orphaned_count > 0:
            conn.commit()
            print(f"Cleaned up {orphaned_count} orphaned groups")
        
        return orphaned_count
        
    except Exception as e:
        print(f"Error cleaning up orphaned groups: {e}")
        return 0
    finally:
        if close_conn and conn:
            conn.close()

# Example usage and testing functions
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Manage Monday.com board groups')
    parser.add_argument('--board-id', type=str, default="9200517329", help='Monday.com board ID (default: Customer Master Schedule)')
    parser.add_argument('--group-name', type=str, help='Name of the group to create/ensure exists')
    parser.add_argument('--list-groups', action='store_true', help='List all groups on the board')
    parser.add_argument('--test', action='store_true', help='Run the test workflow')
    parser.add_argument('--cleanup', action='store_true', help='Clean up orphaned groups')
    
    args = parser.parse_args()
    
    if args.list_groups:
        print(f"Listing groups for board ID: {args.board_id}")
        print("=" * 50)
        groups = list_board_groups(args.board_id)
        for i, group in enumerate(groups, 1):
            print(f"{i:2d}. {group['title']} (ID: {group['id']}, Color: {group.get('color', 'N/A')})")
        print(f"\nTotal groups: {len(groups)}")
        
    elif args.group_name:
        print(f"Ensuring group '{args.group_name}' exists on board {args.board_id}")
        print("=" * 50)
        group_id = ensure_group_exists(args.board_id, args.group_name)
        if group_id:
            print(f"✅ Group '{args.group_name}' is ready with ID: {group_id}")
        else:
            print(f"❌ Failed to ensure group '{args.group_name}' exists")
            
    elif args.cleanup:
        print(f"Cleaning up orphaned groups for board ID: {args.board_id}")
        print("=" * 50)
        cleaned_count = cleanup_orphaned_groups(args.board_id)
        print(f"Cleaned up {cleaned_count} orphaned groups")
        
    elif args.test:
        # Run the original test workflow
        EXAMPLE_BOARD_ID = args.board_id
        
        print("Monday.com Board Groups Management")
        print("=" * 50)
        print("Enhanced workflow with database integration")
        print("=" * 50)
        
        # List existing groups
        print("\n1. Listing existing groups:")
        groups = list_board_groups(EXAMPLE_BOARD_ID)
        for group in groups:
            print(f"  - {group['title']} (ID: {group['id']})")
        
        # Test the enhanced ensure_group_exists workflow
        test_group_name = "TEST_ENHANCED_WORKFLOW_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n2. Testing enhanced workflow with group '{test_group_name}':")
        print("-" * 50)
        
        group_id = ensure_group_exists(EXAMPLE_BOARD_ID, test_group_name)
        
        if group_id:
            print(f"\n✅ Full workflow completed successfully!")
            print(f"   Group '{test_group_name}' created with ID: {group_id}")
            
            # Verify it exists in database
            db_group_id = check_group_exists_in_db(EXAMPLE_BOARD_ID, test_group_name)
            if db_group_id == group_id:
                print(f"✅ Database verification successful - group_id matches")
            else:
                print(f"❌ Database verification failed - IDs don't match")
            
            # Cleanup
            print(f"\n3. Cleaning up test group:")
            deleted = delete_board_group(EXAMPLE_BOARD_ID, group_id)
            if deleted:
                print(f"✅ Test group deleted from Monday.com")
                
                # Clean up database record
                conn = get_database_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE [dbo].[MON_Boards_Groups] SET is_active = 0 WHERE board_id = ? AND group_title = ?",
                            (EXAMPLE_BOARD_ID, test_group_name)
                        )
                        conn.commit()
                        print(f"✅ Test group marked as inactive in database")
                    except Exception as e:
                        print(f"❌ Failed to cleanup database: {e}")
                    finally:
                        conn.close()
        else:
            print(f"❌ Enhanced workflow failed")
            
    else:
        print("Monday.com Board Groups Management")
        print("=" * 50)
        print("Usage examples:")
        print(f"  python {__file__} --list-groups")
        print(f"  python {__file__} --group-name 'MY_NEW_GROUP'")
        print(f"  python {__file__} --board-id 9200517329 --group-name 'CUSTOMER_ORDERS'")
        print(f"  python {__file__} --test")
        print(f"  python {__file__} --cleanup")
        print("\nUse --help for more options")
