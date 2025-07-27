#!/usr/bin/env python3
"""
Check Lines Table Sync State Issue
"""

import sys
from pathlib import Path

# Legacy transition support pattern (SAME AS WORKING TEST)
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 CHECKING LINES TABLE SYNC STATE")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n📊 HEADERS TABLE:")
        cursor.execute("""
            SELECT TOP 3
                [AAG ORDER NUMBER],
                action_type,
                sync_state,
                LEN(action_type) as action_len,
                LEN(sync_state) as sync_len
            FROM ORDER_LIST_V2
        """)
        
        headers = cursor.fetchall()
        for row in headers:
            order, action_type, sync_state, action_len, sync_len = row
            print(f"  {order} | '{action_type}' ({action_len}) | '{sync_state}' ({sync_len})")
        
        print("\n📊 LINES TABLE:")
        cursor.execute("""
            SELECT TOP 3
                record_uuid,
                size_code,
                action_type,
                sync_state,
                LEN(action_type) as action_len,
                LEN(sync_state) as sync_len
            FROM ORDER_LIST_LINES
        """)
        
        lines = cursor.fetchall()
        for row in lines:
            record_uuid, size_code, action_type, sync_state, action_len, sync_len = row
            print(f"  {record_uuid} | {size_code} | '{action_type}' ({action_len}) | '{sync_state}' ({sync_len})")
        
        print("\n🔍 DIRECT COMPARISON TEST:")
        cursor.execute("""
            SELECT TOP 1
                h.action_type as h_action,
                l.action_type as l_action,
                h.sync_state as h_sync,
                l.sync_state as l_sync,
                CASE WHEN h.action_type = l.action_type THEN 'MATCH' ELSE 'NO MATCH' END as action_match,
                CASE WHEN h.sync_state = l.sync_state THEN 'MATCH' ELSE 'NO MATCH' END as sync_match
            FROM ORDER_LIST_V2 h
            JOIN ORDER_LIST_LINES l ON h.record_uuid = l.record_uuid
        """)
        
        comparison = cursor.fetchone()
        if comparison:
            h_action, l_action, h_sync, l_sync, action_match, sync_match = comparison
            print(f"  Header action_type: '{h_action}'")
            print(f"  Line action_type:   '{l_action}'")
            print(f"  Action match:       {action_match}")
            print(f"  Header sync_state:  '{h_sync}'")
            print(f"  Line sync_state:    '{l_sync}'")
            print(f"  Sync match:         {sync_match}")
        
        print("\n🔍 WHITESPACE CHECK:")
        cursor.execute("""
            SELECT TOP 1
                ASCII(LEFT(sync_state, 1)) as first_char,
                ASCII(RIGHT(sync_state, 1)) as last_char,
                DATALENGTH(sync_state) as byte_length,
                LEN(sync_state) as char_length
            FROM ORDER_LIST_V2
        """)
        
        header_check = cursor.fetchone()
        if header_check:
            first, last, byte_len, char_len = header_check
            print(f"  Headers - First char: {first}, Last char: {last}, Bytes: {byte_len}, Chars: {char_len}")
        
        cursor.execute("""
            SELECT TOP 1
                ASCII(LEFT(sync_state, 1)) as first_char,
                ASCII(RIGHT(sync_state, 1)) as last_char,
                DATALENGTH(sync_state) as byte_length,
                LEN(sync_state) as char_length
            FROM ORDER_LIST_LINES
        """)
        
        lines_check = cursor.fetchone()
        if lines_check:
            first, last, byte_len, char_len = lines_check
            print(f"  Lines   - First char: {first}, Last char: {last}, Bytes: {byte_len}, Chars: {char_len}")
        
        cursor.close()

if __name__ == "__main__":
    main()
