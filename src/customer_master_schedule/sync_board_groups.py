"""
Monday.com Board Groups Sync Script
===================================

This script fetches board groups from Monday.com Customer Master Schedule board 
and upserts them into the ORDERS database MON_Board_Groups table.

Author: System
Created: June 15, 2025

Usage:
    python sync_board_groups.py [board_id]
    
Example:
    python sync_board_groups.py 9200517329
"""

import os
import sys
import json
import logging
import requests
import argparse
import yaml
import pyodbc
import pandas as pd
import warnings
import urllib3
from datetime import datetime
from typing import Dict, List, Optional, Any

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

# --- Monday.com API Configuration ---
API_URL = "https://api.monday.com/v2"
AUTH_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjE5NzM0MzUxMiwiYWFpIjoxMSwidWlkIjozMTk3MDg4OSwiaWFkIjoiMjAyMi0xMS0yMVQwNTo1MTowNi4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MTI3NDEyODgsInJnbiI6InVzZTEifQ.K2zXiugzNiYW5xo0tuXpAuZexBdv5xaAXPxubwxhNAM"
API_VERSION = "2025-04"
HEADERS = {
    "Content-Type": "application/json",
    "API-Version": API_VERSION,
    "Authorization": f"Bearer {AUTH_KEY}"
}

# --- Load config ---
def load_env():
    """Load .env file from repo root."""
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    load_dotenv(dotenv_path=env_path)

def get_db_config(db_key):
    """Get DB config from environment variables."""
    load_env()  # Ensure environment is loaded
    # Get password from either SECRET_xxx_PWD (base64) or DB_xxx_PASSWORD (plain)
    import base64
    password = os.getenv(f'SECRET_{db_key.upper()}_PWD')
    if password:
        # Decode base64 password
        password = base64.b64decode(password).decode()
    else:
        # Fallback to plain password
        password = os.getenv(f'DB_{db_key.upper()}_PASSWORD')
    
    config = {
        'host': os.getenv(f'DB_{db_key.upper()}_HOST'),
        'port': int(os.getenv(f'DB_{db_key.upper()}_PORT', 1433)),
        'database': os.getenv(f'DB_{db_key.upper()}_DATABASE'),
        'username': os.getenv(f'DB_{db_key.upper()}_USERNAME'),
        'password': password,
        'encrypt': os.getenv(f'DB_{db_key.upper()}_ENCRYPT', 'yes'),
        'trustServerCertificate': os.getenv(f'DB_{db_key.upper()}_TRUSTSERVERCERTIFICATE', 'no'),
    }
    return config

# Try to load config - fallback gracefully if not available
try:
    DB_CONFIG = {'orders': get_db_config('orders')}
    LOGGING_ENABLED = True
except Exception as e:
    print(f"Warning: Could not load database configuration: {e}")
    DB_CONFIG = {}
    LOGGING_ENABLED = True


class MondayBoardGroupsSync:
    """Handles syncing board groups from Monday.com to ORDERS database"""
    
    def __init__(self, board_id: str):
        self.logger = self._setup_logging()
        self.board_id = board_id
        
        if not AUTH_KEY:
            raise ValueError("Monday.com API key is not configured")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger(__name__)
        if LOGGING_ENABLED:
            logger.setLevel(logging.INFO)
            
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        
        return logger
    
    def _get_db_connection(self):
        """Create database connection using environment variables"""
        orders_cfg = DB_CONFIG.get('orders', {})
        if not orders_cfg:
            raise ValueError("Orders database configuration not found. Please check your .env file.")
        
        # Use ODBC Driver 17 for SQL Server if available, fallback to SQL Server
        driver = "{ODBC Driver 17 for SQL Server}"
        try:
            # Test if ODBC Driver 17 is available
            test_conn_str = f"DRIVER={driver};SERVER=test;DATABASE=test;"
            pyodbc.connect(test_conn_str, timeout=1)
        except:
            # Fallback to older driver
            driver = "{SQL Server}"
        
        # Build connection string with proper SSL handling
        conn_str_parts = [
            f"DRIVER={driver}",
            f"SERVER={orders_cfg['host']},{orders_cfg['port']}",
            f"DATABASE={orders_cfg['database']}",
            f"UID={orders_cfg['username']}",
            f"PWD={orders_cfg['password']}"
        ]
        
        # Handle SSL settings properly for older SQL Server drivers
        encrypt = orders_cfg['encrypt'].lower()
        trust_cert = orders_cfg['trustServerCertificate'].lower()
        
        if encrypt == 'yes':
            conn_str_parts.append("Encrypt=yes")
        elif encrypt == 'no':
            conn_str_parts.append("Encrypt=no")
        
        if trust_cert == 'yes':
            conn_str_parts.append("TrustServerCertificate=yes")
        elif trust_cert == 'no':
            conn_str_parts.append("TrustServerCertificate=no")
        
        # For older drivers, also try these alternative SSL settings
        if driver == "{SQL Server}":
            if encrypt == 'no':
                conn_str_parts.append("Integrated Security=no")
            # Remove problematic SSL settings for very old servers
            conn_str_parts = [part for part in conn_str_parts 
                             if not part.startswith(('Encrypt=', 'TrustServerCertificate='))]
        
        conn_str = ";".join(conn_str_parts) + ";"
        
        try:
            # Add connection timeout
            return pyodbc.connect(conn_str, timeout=30)
        except pyodbc.Error as e:
            # If modern settings fail, try with minimal connection string
            if "SSL Security error" in str(e) or "Invalid connection string attribute" in str(e):
                self.logger.warning(f"SSL connection failed, trying without SSL settings...")
                basic_conn_str = (
                    f"DRIVER={{SQL Server}};SERVER={orders_cfg['host']},{orders_cfg['port']};"
                    f"DATABASE={orders_cfg['database']};UID={orders_cfg['username']};PWD={orders_cfg['password']};"
                )
                return pyodbc.connect(basic_conn_str, timeout=30)
            else:
                raise
    
    def _make_monday_request(self, query: str) -> Dict[str, Any]:
        """Make GraphQL request to Monday.com API"""
        payload = {"query": query}
        
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json=payload,
                timeout=30,
                verify=False
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                raise Exception(f"Monday.com API error: {result['errors']}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making Monday.com API request: {e}")
            raise
    
    def get_board_groups(self) -> List[Dict[str, Any]]:
        """Fetch board groups from Monday.com"""
        self.logger.info(f"Fetching board groups for board {self.board_id}")
        
        query = f"""
        query {{
            boards(ids: [{self.board_id}]) {{
                id
                name
                groups {{
                    id
                    title
                }}
            }}
        }}
        """
        
        try:
            result = self._make_monday_request(query)
            boards = result.get("data", {}).get("boards", [])
            
            if not boards:
                self.logger.warning(f"No board found with ID {self.board_id}")
                return []
            
            board = boards[0]
            board_name = board.get("name", "")
            groups = board.get("groups", [])
            
            # Transform data for database insertion
            board_groups = []
            for group in groups:
                board_groups.append({
                    "board_id": self.board_id,
                    "board_name": board_name,
                    "group_id": group.get("id", ""),
                    "group_title": group.get("title", "")                })
            
            self.logger.info(f"Retrieved {len(board_groups)} groups from board '{board_name}'")
            return board_groups
            
        except Exception as e:
            self.logger.error(f"Error fetching board groups: {e}")
            raise
    
    def _table_exists(self, conn, table_name: str) -> bool:
        """Check if table exists in database"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'dbo' 
            AND TABLE_NAME = ?
        """, (table_name,))
        return cursor.fetchone()[0] > 0
    
    def _create_table(self, conn) -> None:
        """Create MON_Board_Groups table if it doesn't exist"""
        cursor = conn.cursor()
        
        # Create table first
        create_table_sql = """
        CREATE TABLE [dbo].[MON_Board_Groups] (
            [board_id] NVARCHAR(20) NOT NULL,
            [board_name] NVARCHAR(255) NOT NULL,
            [group_id] NVARCHAR(50) NOT NULL,
            [group_title] NVARCHAR(255) NOT NULL,
            [created_date] DATETIME2 NOT NULL DEFAULT GETDATE(),
            [updated_date] DATETIME2 NOT NULL DEFAULT GETDATE(),
            [is_active] BIT NOT NULL DEFAULT 1,
            
            CONSTRAINT [PK_MON_Board_Groups] PRIMARY KEY CLUSTERED ([board_id], [group_id])
        )
        """
        cursor.execute(create_table_sql)
        
        # Create indexes separately (skip filtered index for compatibility)
        index_sqls = [
            """CREATE NONCLUSTERED INDEX [IX_MON_Board_Groups_BoardId] 
               ON [dbo].[MON_Board_Groups] ([board_id]) 
               INCLUDE ([board_name], [group_title], [is_active])""",
            """CREATE NONCLUSTERED INDEX [IX_MON_Board_Groups_GroupTitle] 
               ON [dbo].[MON_Board_Groups] ([group_title]) 
               INCLUDE ([board_id], [group_id], [is_active])"""
        ]
        
        for index_sql in index_sqls:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"Could not create index: {e}")
        
        self.logger.info("Created MON_Board_Groups table with indexes")
    
    def upsert_board_groups(self, board_groups: List[Dict[str, Any]]) -> None:
        """Upsert board groups into ORDERS database"""
        if not board_groups:
            self.logger.info("No board groups to upsert")
            return
        
        try:
            # Get database connection
            with self._get_db_connection() as conn:
                # Check if table exists, create if not
                if not self._table_exists(conn, 'MON_Board_Groups'):
                    self.logger.info("MON_Board_Groups table does not exist, creating...")
                    self._create_table(conn)
                    conn.commit()
                
                cursor = conn.cursor()
                
                # Upsert logic
                upsert_sql = """
                MERGE [dbo].[MON_Board_Groups] AS target
                USING (VALUES (?, ?, ?, ?)) AS source ([board_id], [board_name], [group_id], [group_title])
                ON target.[board_id] = source.[board_id] AND target.[group_id] = source.[group_id]
                WHEN MATCHED THEN
                    UPDATE SET 
                        [board_name] = source.[board_name],
                        [group_title] = source.[group_title],
                        [updated_date] = GETDATE(),
                        [is_active] = 1
                WHEN NOT MATCHED THEN
                    INSERT ([board_id], [board_name], [group_id], [group_title], [created_date], [updated_date], [is_active])
                    VALUES (source.[board_id], source.[board_name], source.[group_id], source.[group_title], GETDATE(), GETDATE(), 1);
                """
                
                # Execute upsert for each group
                rows_affected = 0
                for group in board_groups:
                    cursor.execute(upsert_sql, (
                        group['board_id'],
                        group['board_name'],
                        group['group_id'],
                        group['group_title']
                    ))
                    rows_affected += cursor.rowcount
                
                # Mark groups not in current fetch as inactive
                current_group_ids = [g['group_id'] for g in board_groups]
                if current_group_ids:
                    placeholders = ','.join(['?' for _ in current_group_ids])
                    deactivate_sql = f"""
                    UPDATE [dbo].[MON_Board_Groups] 
                    SET [is_active] = 0, [updated_date] = GETDATE()
                    WHERE [board_id] = ? AND [group_id] NOT IN ({placeholders})
                    """
                    cursor.execute(deactivate_sql, [self.board_id] + current_group_ids)
                
                conn.commit()
                self.logger.info(f"Successfully upserted {len(board_groups)} board groups")
                
        except Exception as e:
            self.logger.error(f"Error upserting board groups: {e}")
            raise
    
    def sync_board_groups(self) -> None:
        """Main method to sync board groups from Monday.com to database"""
        try:
            self.logger.info("Starting Monday.com board groups sync")
            
            # Fetch groups from Monday.com
            board_groups = self.get_board_groups()
            
            # Upsert to database
            self.upsert_board_groups(board_groups)
            
            self.logger.info("Board groups sync completed successfully")
            
        except Exception as e:
            self.logger.error(f"Board groups sync failed: {e}")
            raise


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Sync Monday.com board groups to ORDERS database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sync_board_groups.py 9200517329
    python sync_board_groups.py --board-id 9200517329
        """
    )
    parser.add_argument(
        'board_id', 
        nargs='?',
        default='9200517329',
        help='Monday.com board ID (default: 9200517329 - Customer Master Schedule)'
    )
    parser.add_argument(
        '--board-id',
        dest='board_id',
        help='Monday.com board ID (alternative flag)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    if not AUTH_KEY or AUTH_KEY == 'YOUR_API_KEY_HERE':
        print("[ERROR] Monday.com API key is missing or not set. Please configure AUTH_KEY.")
        sys.exit(1)
    
    try:
        print(f"[INFO] Starting Monday.com board groups sync for board: {args.board_id}")
        syncer = MondayBoardGroupsSync(args.board_id)
        syncer.sync_board_groups()
        print("[SUCCESS] Board groups sync completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Script execution failed: {e}")
        if LOGGING_ENABLED:
            logging.error(f"Script execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
