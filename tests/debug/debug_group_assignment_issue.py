#!/usr/bin/env python3
"""
Debug Group Assignment Issue - Analyze Critical Problems
=======================================================
1. Why 21/22 batches are considered 'SUCCESS' 
2. How internal server errors (500/timeouts) are handled
3. CRITICAL: Why all items loaded into same group despite two customers/POs
4. Why group_id is NULL in FACT_ORDER_LIST but items exist in Monday.com groups
5. Dropdown label creation error for 'O/S' vs 'OS' mismatch
"""

import sys
from pathlib import Path

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

def main():
    print("🔍 DEBUGGING GROUP ASSIGNMENT CRITICAL ISSUES")
    print("=" * 60)
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Database connection using config.db_key
    with db.get_connection(config.db_key) as connection:
        cursor = connection.cursor()
        
        print("\n1. INVESTIGATING GROUP ASSIGNMENT ISSUE")
        print("-" * 40)
        
        # Query 1: Group names and IDs in target table
        query1 = f"""
        SELECT DISTINCT 
            [AAG SEASON], 
            [CUSTOMER SEASON], 
            group_name, 
            group_id,
            COUNT(*) as record_count
        FROM {config.target_table}
        WHERE group_name IS NOT NULL
        GROUP BY [AAG SEASON], [CUSTOMER SEASON], group_name, group_id
        ORDER BY group_name
        """
        
        print("🔍 Target Table Group Analysis:")
        cursor.execute(query1)
        results1 = cursor.fetchall()
        for row in results1:
            aag_season, customer_season, group_name, group_id, count = row
            print(f"   AAG: {aag_season} | CUST: {customer_season} | GROUP: {group_name} | ID: {group_id} | COUNT: {count}")
        
        print("\n2. CUSTOMER NAME AND PO ANALYSIS")
        print("-" * 40)
        
        # Query 2: Customer names and POs
        query2 = f"""
        SELECT DISTINCT 
            [CUSTOMER NAME],
            [PO NUMBER],
            group_name,
            group_id,
            COUNT(*) as record_count
        FROM {config.target_table}
        WHERE group_name IS NOT NULL
        GROUP BY [CUSTOMER NAME], [PO NUMBER], group_name, group_id
        ORDER BY [CUSTOMER NAME], [PO NUMBER]
        """
        
        print("🔍 Customer/PO to Group Mapping:")
        cursor.execute(query2)
        results2 = cursor.fetchall()
        for row in results2:
            customer, po, group_name, group_id, count = row
            print(f"   CUSTOMER: {customer} | PO: {po} | GROUP: {group_name} | ID: {group_id} | COUNT: {count}")
        
        print("\n3. SYNC STATE ANALYSIS")
        print("-" * 40)
        
        # Query 3: Sync states and error analysis
        query3 = f"""
        SELECT 
            sync_state,
            action_type,
            COUNT(*) as record_count,
            COUNT(CASE WHEN sync_error_message IS NOT NULL THEN 1 END) as error_count
        FROM {config.target_table}
        WHERE group_name IS NOT NULL
        GROUP BY sync_state, action_type
        ORDER BY sync_state, action_type
        """
        
        print("🔍 Sync State Analysis:")
        cursor.execute(query3)
        results3 = cursor.fetchall()
        for row in results3:
            sync_state, action_type, count, error_count = row
            print(f"   STATE: {sync_state} | ACTION: {action_type} | COUNT: {count} | ERRORS: {error_count}")
        
        print("\n4. ERROR MESSAGE ANALYSIS")
        print("-" * 40)
        
        # Query 4: Error messages
        query4 = f"""
        SELECT DISTINCT 
            sync_error_message,
            COUNT(*) as frequency
        FROM {config.target_table}
        WHERE sync_error_message IS NOT NULL
        GROUP BY sync_error_message
        ORDER BY frequency DESC
        """
        
        print("🔍 Error Message Analysis:")
        cursor.execute(query4)
        results4 = cursor.fetchall()
        if results4:
            for row in results4:
                error_msg, frequency = row
                print(f"   ERROR: {error_msg[:100]}... | FREQUENCY: {frequency}")
        else:
            print("   No error messages found in target table")
        
        print("\n5. SIZE COLUMN DATA ANALYSIS (O/S vs OS issue)")
        print("-" * 40)
        
        # Query 5: Size data analysis
        query5 = f"""
        SELECT DISTINCT 
            size_code,
            COUNT(*) as frequency
        FROM {config.lines_table}
        WHERE size_code IS NOT NULL
           AND size_code LIKE '%O%'  -- Looking for O/S vs OS variations
        GROUP BY size_code
        ORDER BY frequency DESC
        """
        
        print("🔍 Size Code Analysis (O/S variations):")
        cursor.execute(query5)
        results5 = cursor.fetchall()
        for row in results5:
            size_code, frequency = row
            print(f"   SIZE: '{size_code}' | FREQUENCY: {frequency}")
        
        print("\n6. GROUP TRANSFORMATION LOGIC ANALYSIS")
        print("-" * 40)
        
        # Query 6: Group name construction analysis
        query6 = f"""
        SELECT DISTINCT 
            [CUSTOMER NAME],
            [CUSTOMER SEASON],
            [AAG SEASON],
            group_name,
            CASE 
                WHEN group_name = CONCAT([CUSTOMER NAME], ' ', [CUSTOMER SEASON]) THEN 'CUSTOMER+CUSTOMER_SEASON'
                WHEN group_name = CONCAT([CUSTOMER NAME], ' ', [AAG SEASON]) THEN 'CUSTOMER+AAG_SEASON'
                ELSE 'OTHER_PATTERN'
            END as pattern_match
        FROM {config.target_table}
        WHERE group_name IS NOT NULL
        ORDER BY [CUSTOMER NAME], group_name
        """
        
        print("🔍 Group Name Construction Pattern Analysis:")
        cursor.execute(query6)
        results6 = cursor.fetchall()
        for row in results6:
            customer, customer_season, aag_season, group_name, pattern = row
            print(f"   CUSTOMER: {customer}")
            print(f"   CUST_SEASON: {customer_season}")
            print(f"   AAG_SEASON: {aag_season}")
            print(f"   GROUP_NAME: {group_name}")
            print(f"   PATTERN: {pattern}")
            print("   ---")
        
        cursor.close()

if __name__ == "__main__":
    main()
