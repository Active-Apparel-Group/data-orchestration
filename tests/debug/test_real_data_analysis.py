#!/usr/bin/env python3
"""
Real Data Analysis for Enhanced Merge Orchestrator Testing
===========================================================
Purpose: Analyze available real data for testing and validation
Pattern: EXACT pattern from imports.guidance.instructions.md - WORKING PATTERN

This script provides:
1. Available customers and PO analysis
2. Current FACT_ORDER_LIST state analysis
3. Current ORDER_LIST_LINES state analysis
4. Clean test data recommendations
5. Monday.com sync state validation

Use this script to:
- Find suitable test data (customers/POs with no existing groups)
- Validate current database state before testing
- Monitor test progress and results
- Plan clean test runs
"""

import sys
from pathlib import Path
import pandas as pd
from typing import Dict, List, Tuple

# EXACT WORKING IMPORT PATTERN from imports.guidance.instructions.md
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)

class RealDataAnalyzer:
    """Real data analyzer for enhanced merge orchestrator testing"""
    
    def __init__(self):
        # EXACT CONFIG PATTERN from imports.guidance.instructions.md
        config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
        self.config = DeltaSyncConfig.from_toml(config_path)
        logger.info(f"✅ Real Data Analyzer initialized with config: {config_path}")
        logger.info(f"✅ Database key: {self.config.db_key}")
    
    def analyze_available_source_data(self) -> Dict:
        """Analyze available source data in swp_ORDER_LIST_SYNC"""
        logger.info("🔍 Analyzing available source data...")
        
        with db.get_connection(self.config.db_key) as conn:
            # Get top customers with data
            customers_query = """
            SELECT TOP 15
                [CUSTOMER NAME],
                COUNT(*) as record_count,
                COUNT(DISTINCT [PO NUMBER]) as unique_pos,
                MIN([PO NUMBER]) as first_po,
                MAX([PO NUMBER]) as last_po
            FROM swp_ORDER_LIST_SYNC 
            WHERE [CUSTOMER NAME] IS NOT NULL
            GROUP BY [CUSTOMER NAME]
            ORDER BY COUNT(*) DESC
            """
            
            customers_df = pd.read_sql(customers_query, conn)
            
            # Get sample POs for testing
            sample_pos_query = """
            SELECT TOP 20
                [CUSTOMER NAME],
                [PO NUMBER],
                COUNT(*) as record_count,
                COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_orders
            FROM swp_ORDER_LIST_SYNC 
            WHERE [CUSTOMER NAME] IN (
                SELECT TOP 5 [CUSTOMER NAME] 
                FROM swp_ORDER_LIST_SYNC 
                WHERE [CUSTOMER NAME] IS NOT NULL
                GROUP BY [CUSTOMER NAME]
                ORDER BY COUNT(*) DESC
            )
            GROUP BY [CUSTOMER NAME], [PO NUMBER]
            ORDER BY [CUSTOMER NAME], COUNT(*) DESC
            """
            
            sample_pos_df = pd.read_sql(sample_pos_query, conn)
            
            logger.info("📊 Source Data Analysis Results:")
            logger.info(f"   Total customers available: {len(customers_df)}")
            logger.info(f"   Sample POs available: {len(sample_pos_df)}")
            
            logger.info("\n📋 Top 10 Customers by Record Count:")
            for idx, row in customers_df.head(10).iterrows():
                logger.info(f"   {row['CUSTOMER NAME']:30} | {row['record_count']:5} records | {row['unique_pos']:3} POs | PO range: {row['first_po']}-{row['last_po']}")
            
            logger.info("\n📋 Sample POs for Testing:")
            current_customer = None
            for idx, row in sample_pos_df.iterrows():
                if row['CUSTOMER NAME'] != current_customer:
                    current_customer = row['CUSTOMER NAME']
                    logger.info(f"\n   📂 {current_customer}:")
                logger.info(f"      PO {row['PO NUMBER']:10} | {row['record_count']:3} records | {row['unique_orders']:3} orders")
            
            return {
                'customers': customers_df.to_dict('records'),
                'sample_pos': sample_pos_df.to_dict('records')
            }
    
    def analyze_current_fact_state(self) -> Dict:
        """Analyze current FACT_ORDER_LIST state"""
        logger.info("\n🔍 Analyzing current FACT_ORDER_LIST state...")
        
        with db.get_connection(self.config.db_key) as conn:
            # Check if table exists first
            table_check_query = """
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'FACT_ORDER_LIST'
            """
            
            table_check_result = pd.read_sql(table_check_query, conn)
            table_exists = table_check_result.iloc[0]['table_exists'] > 0 if not table_check_result.empty else False
            
            if not table_exists:
                logger.warning("⚠️  FACT_ORDER_LIST table does not exist")
                return {'table_exists': False, 'overview': {}, 'customer_breakdown': []}
            
            # Check actual columns in FACT_ORDER_LIST (PROVEN PATTERN from working tests)
            column_check_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'FACT_ORDER_LIST'
            AND COLUMN_NAME IN ('monday_item_id', 'monday_group_id', 'sync_state', 'action_type')
            """
            
            column_check_result = pd.read_sql(column_check_query, conn)
            available_columns = [row['COLUMN_NAME'] for _, row in column_check_result.iterrows()]
            
            logger.info(f"📋 Available Monday.com columns: {available_columns}")
            
            # Build query based on available columns (SAFE PATTERN)
            base_columns = """
                COUNT(*) as total_records,
                COUNT(DISTINCT [CUSTOMER NAME]) as unique_customers,
                COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_orders
            """
            
            conditional_columns = []
            if 'monday_item_id' in available_columns:
                conditional_columns.append("COUNT(CASE WHEN [monday_item_id] IS NOT NULL THEN 1 END) as synced_items")
            else:
                conditional_columns.append("0 as synced_items")
                
            if 'monday_group_id' in available_columns:
                conditional_columns.append("COUNT(CASE WHEN [monday_group_id] IS NOT NULL THEN 1 END) as with_groups")
            else:
                conditional_columns.append("0 as with_groups")
                
            if 'sync_state' in available_columns:
                conditional_columns.append("COUNT(CASE WHEN [sync_state] = 'COMPLETED' THEN 1 END) as completed_sync")
                conditional_columns.append("COUNT(CASE WHEN [sync_state] = 'PENDING' THEN 1 END) as pending_sync")
            else:
                conditional_columns.append("0 as completed_sync")
                conditional_columns.append("0 as pending_sync")
            
            # Overall state query (FIXED COLUMN NAMES)
            fact_overview_query = f"""
            SELECT 
                {base_columns},
                {', '.join(conditional_columns)}
            FROM FACT_ORDER_LIST
            """
            
            overview_result = pd.read_sql(fact_overview_query, conn)
            
            # Customer breakdown query (FIXED COLUMN NAMES)
            customer_base_columns = """
                [CUSTOMER NAME],
                COUNT(*) as total_records,
                COUNT(DISTINCT [PO NUMBER]) as unique_pos
            """
            
            customer_conditional_columns = []
            if 'monday_item_id' in available_columns:
                customer_conditional_columns.append("COUNT(CASE WHEN [monday_item_id] IS NOT NULL THEN 1 END) as synced_items")
            else:
                customer_conditional_columns.append("0 as synced_items")
                
            if 'monday_group_id' in available_columns:
                customer_conditional_columns.append("COUNT(CASE WHEN [monday_group_id] IS NOT NULL THEN 1 END) as with_groups")
            else:
                customer_conditional_columns.append("0 as with_groups")
            
            customer_breakdown_query = f"""
            SELECT 
                {customer_base_columns},
                {', '.join(customer_conditional_columns)}
            FROM FACT_ORDER_LIST
            GROUP BY [CUSTOMER NAME]
            ORDER BY COUNT(*) DESC
            """
            
            customer_breakdown_df = pd.read_sql(customer_breakdown_query, conn)
            
            if not overview_result.empty:
                row = overview_result.iloc[0]
                logger.info("📊 FACT_ORDER_LIST Current State:")
                logger.info(f"   Total records: {row['total_records']:,}")
                logger.info(f"   Unique customers: {row['unique_customers']}")
                logger.info(f"   Unique orders: {row['unique_orders']:,}")
                logger.info(f"   Synced items: {row['synced_items']:,}")
                logger.info(f"   With groups: {row['with_groups']:,}")
                logger.info(f"   Completed sync: {row['completed_sync']:,}")
                logger.info(f"   Pending sync: {row['pending_sync']:,}")
                
                if row['total_records'] > 0:
                    sync_rate = (row['synced_items'] / row['total_records']) * 100
                    group_rate = (row['with_groups'] / row['total_records']) * 100
                    logger.info(f"   Sync rate: {sync_rate:.1f}%")
                    logger.info(f"   Group rate: {group_rate:.1f}%")
            
            logger.info("\n📋 Customer Breakdown (Top 10):")
            for idx, row in customer_breakdown_df.head(10).iterrows():
                sync_rate = (row['synced_items'] / row['total_records']) * 100 if row['total_records'] > 0 else 0
                logger.info(f"   {row['CUSTOMER NAME']:30} | {row['total_records']:4} records | {row['synced_items']:4} synced ({sync_rate:5.1f}%) | {row['with_groups']:4} groups")
            
            return {
                'overview': overview_result.to_dict('records')[0] if not overview_result.empty else {},
                'customer_breakdown': customer_breakdown_df.to_dict('records')
            }
    
    def analyze_current_lines_state(self) -> Dict:
        """Analyze current ORDER_LIST_LINES state"""
        logger.info("\n🔍 Analyzing current ORDER_LIST_LINES state...")
        
        with db.get_connection(self.config.db_key) as conn:
            # Check if table exists first
            table_check_query = """
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ORDER_LIST_LINES'
            """
            
            table_check_result = pd.read_sql(table_check_query, conn)
            table_exists = table_check_result.iloc[0]['table_exists'] > 0 if not table_check_result.empty else False
            
            if not table_exists:
                logger.warning("⚠️  ORDER_LIST_LINES table does not exist")
                return {'table_exists': False, 'overview': {}}
            
            # Check actual columns in ORDER_LIST_LINES (PROVEN PATTERN from working tests)
            column_check_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'ORDER_LIST_LINES'
            AND COLUMN_NAME IN ('monday_subitem_id', 'parent_monday_item_id', 'sync_state', 'SIZE', 'size_code')
            """
            
            column_check_result = pd.read_sql(column_check_query, conn)
            available_columns = [row['COLUMN_NAME'] for _, row in column_check_result.iterrows()]
            
            logger.info(f"📋 Available ORDER_LIST_LINES columns: {available_columns}")
            
            # Build query based on available columns (SAFE PATTERN)
            base_columns = """
                COUNT(*) as total_lines,
                COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_orders
            """
            
            conditional_columns = []
            if 'monday_subitem_id' in available_columns:
                conditional_columns.append("COUNT(CASE WHEN [monday_subitem_id] IS NOT NULL THEN 1 END) as synced_subitems")
            else:
                conditional_columns.append("0 as synced_subitems")
                
            if 'parent_monday_item_id' in available_columns:
                conditional_columns.append("COUNT(CASE WHEN [parent_monday_item_id] IS NOT NULL THEN 1 END) as linked_to_parent")
            else:
                conditional_columns.append("0 as linked_to_parent")
                
            if 'sync_state' in available_columns:
                conditional_columns.append("COUNT(CASE WHEN [sync_state] = 'COMPLETED' THEN 1 END) as completed_sync")
            else:
                conditional_columns.append("0 as completed_sync")
                
            # Use size_code if available, otherwise use SIZE (PROVEN PATTERN from working tests)
            if 'size_code' in available_columns:
                conditional_columns.append("COUNT(DISTINCT [size_code]) as unique_sizes")
            elif 'SIZE' in available_columns:
                conditional_columns.append("COUNT(DISTINCT [SIZE]) as unique_sizes")
            else:
                conditional_columns.append("0 as unique_sizes")
            
            # Overall lines state query (FIXED COLUMN NAMES)
            lines_overview_query = f"""
            SELECT 
                {base_columns},
                {', '.join(conditional_columns)}
            FROM ORDER_LIST_LINES
            """
            
            lines_overview_result = pd.read_sql(lines_overview_query, conn)
            
            if not lines_overview_result.empty:
                row = lines_overview_result.iloc[0]
                logger.info("📊 ORDER_LIST_LINES Current State:")
                logger.info(f"   Total lines: {row['total_lines']:,}")
                logger.info(f"   Synced subitems: {row['synced_subitems']:,}")
                logger.info(f"   Linked to parent: {row['linked_to_parent']:,}")
                logger.info(f"   Completed sync: {row['completed_sync']:,}")
                logger.info(f"   Unique orders: {row['unique_orders']:,}")
                logger.info(f"   Unique sizes: {row['unique_sizes']}")
                
                if row['total_lines'] > 0:
                    subitem_sync_rate = (row['synced_subitems'] / row['total_lines']) * 100
                    parent_link_rate = (row['linked_to_parent'] / row['total_lines']) * 100
                    logger.info(f"   Subitem sync rate: {subitem_sync_rate:.1f}%")
                    logger.info(f"   Parent link rate: {parent_link_rate:.1f}%")
            
            return {
                'overview': lines_overview_result.to_dict('records')[0] if not lines_overview_result.empty else {}
            }
    
    def find_clean_test_candidates(self) -> List[Dict]:
        """Find clean test candidates (customers/POs with no existing Monday.com sync)"""
        logger.info("\n🔍 Finding clean test candidates...")
        
        with db.get_connection(self.config.db_key) as conn:
            # Find customers/POs with source data but no FACT_ORDER_LIST entries
            clean_candidates_query = """
            SELECT 
                src.[CUSTOMER NAME],
                src.[PO NUMBER],
                COUNT(*) as source_records,
                COUNT(DISTINCT src.[AAG ORDER NUMBER]) as unique_orders
            FROM swp_ORDER_LIST_SYNC src
            LEFT JOIN FACT_ORDER_LIST fact 
                ON src.[CUSTOMER NAME] = fact.[CUSTOMER NAME] 
                AND src.[PO NUMBER] = fact.[PO NUMBER]
            WHERE fact.[CUSTOMER NAME] IS NULL
                AND src.[CUSTOMER NAME] IS NOT NULL
                AND src.[PO NUMBER] IS NOT NULL
            GROUP BY src.[CUSTOMER NAME], src.[PO NUMBER]
            HAVING COUNT(*) >= 5  -- At least 5 records for meaningful testing
            ORDER BY COUNT(*) DESC
            """
            
            clean_candidates_df = pd.read_sql(clean_candidates_query, conn)
            
            logger.info(f"📊 Clean Test Candidates Found: {len(clean_candidates_df)}")
            
            if not clean_candidates_df.empty:
                logger.info("\n📋 Top 15 Clean Test Candidates (No existing FACT_ORDER_LIST entries):")
                for idx, row in clean_candidates_df.head(15).iterrows():
                    logger.info(f"   {row['CUSTOMER NAME']:30} | PO {row['PO NUMBER']:10} | {row['source_records']:3} records | {row['unique_orders']:3} orders")
                
                # Recommend top candidates
                top_candidates = clean_candidates_df.head(5).to_dict('records')
                logger.info("\n🎯 RECOMMENDED TEST CANDIDATES:")
                for i, candidate in enumerate(top_candidates, 1):
                    logger.info(f"   {i}. {candidate['CUSTOMER NAME']} PO {candidate['PO NUMBER']} ({candidate['source_records']} records)")
            else:
                logger.warning("⚠️  No clean test candidates found - all source data already processed")
            
            return clean_candidates_df.to_dict('records')
    
    def check_specific_customer_po(self, customer: str, po: str) -> Dict:
        """Check specific customer/PO for testing suitability"""
        logger.info(f"\n🔍 Analyzing specific test case: {customer} PO {po}")
        
        with db.get_connection(self.config.db_key) as conn:
            # Check source data (PROVEN PATTERN from working tests)
            source_query = """
            SELECT 
                COUNT(*) as source_count,
                COUNT(DISTINCT [AAG ORDER NUMBER]) as unique_orders,
                MIN([AAG ORDER NUMBER]) as first_order,
                MAX([AAG ORDER NUMBER]) as last_order
            FROM swp_ORDER_LIST_SYNC 
            WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
            """
            
            source_result = pd.read_sql(source_query, conn, params=(customer, po))
            
            # Check existing FACT_ORDER_LIST data (SAFE QUERY with column checks)
            fact_table_check = """
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'FACT_ORDER_LIST'
            """
            
            fact_table_result = pd.read_sql(fact_table_check, conn)
            fact_table_exists = fact_table_result.iloc[0]['table_exists'] > 0 if not fact_table_result.empty else False
            
            if fact_table_exists:
                # Check available Monday.com columns
                fact_column_check = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'FACT_ORDER_LIST'
                AND COLUMN_NAME IN ('monday_item_id', 'monday_group_id')
                """
                
                fact_columns_result = pd.read_sql(fact_column_check, conn)
                fact_available_columns = [row['COLUMN_NAME'] for _, row in fact_columns_result.iterrows()]
                
                # Build fact query based on available columns
                fact_base_query = "SELECT COUNT(*) as fact_count"
                
                if 'monday_item_id' in fact_available_columns:
                    fact_base_query += ", COUNT(CASE WHEN [monday_item_id] IS NOT NULL THEN 1 END) as synced_items"
                else:
                    fact_base_query += ", 0 as synced_items"
                    
                if 'monday_group_id' in fact_available_columns:
                    fact_base_query += ", COUNT(CASE WHEN [monday_group_id] IS NOT NULL THEN 1 END) as with_groups"
                else:
                    fact_base_query += ", 0 as with_groups"
                
                fact_query = f"""
                {fact_base_query}
                FROM FACT_ORDER_LIST 
                WHERE [CUSTOMER NAME] = ? AND [PO NUMBER] = ?
                """
                
                fact_result = pd.read_sql(fact_query, conn, params=(customer, po))
            else:
                logger.warning("⚠️  FACT_ORDER_LIST table does not exist")
                fact_result = pd.DataFrame([{'fact_count': 0, 'synced_items': 0, 'with_groups': 0}])
            
            # Check existing ORDER_LIST_LINES data (SAFE QUERY with correct joins from working tests)
            lines_table_check = """
            SELECT COUNT(*) as table_exists
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'ORDER_LIST_LINES'
            """
            
            lines_table_result = pd.read_sql(lines_table_check, conn)
            lines_table_exists = lines_table_result.iloc[0]['table_exists'] > 0 if not lines_table_result.empty else False
            
            if lines_table_exists and fact_table_exists:
                # Use correct join pattern from working tests (record_uuid join)
                lines_query = """
                SELECT 
                    COUNT(*) as lines_count,
                    COUNT(CASE WHEN ol.[monday_subitem_id] IS NOT NULL THEN 1 END) as synced_subitems
                FROM ORDER_LIST_LINES ol
                JOIN FACT_ORDER_LIST fact ON ol.record_uuid = fact.record_uuid
                WHERE fact.[CUSTOMER NAME] = ? AND fact.[PO NUMBER] = ?
                """
                
                lines_result = pd.read_sql(lines_query, conn, params=(customer, po))
            else:
                logger.warning("⚠️  ORDER_LIST_LINES or FACT_ORDER_LIST table does not exist")
                lines_result = pd.DataFrame([{'lines_count': 0, 'synced_subitems': 0}])
            
            # Analyze results
            source_count = source_result.iloc[0]['source_count'] if not source_result.empty else 0
            fact_count = fact_result.iloc[0]['fact_count'] if not fact_result.empty else 0
            lines_count = lines_result.iloc[0]['lines_count'] if not lines_result.empty else 0
            
            logger.info(f"📊 Analysis for {customer} PO {po}:")
            logger.info(f"   Source records: {source_count}")
            logger.info(f"   FACT_ORDER_LIST records: {fact_count}")
            logger.info(f"   ORDER_LIST_LINES records: {lines_count}")
            
            # Determine test suitability
            if source_count == 0:
                status = "❌ NO SOURCE DATA"
                recommendation = "Cannot test - no source data available"
            elif fact_count == 0:
                status = "✅ CLEAN TEST CANDIDATE"
                recommendation = "Perfect for testing - no existing processed data"
            elif fact_count > 0:
                synced_items = fact_result.iloc[0]['synced_items'] if not fact_result.empty else 0
                with_groups = fact_result.iloc[0]['with_groups'] if not fact_result.empty else 0
                
                if synced_items == 0 and with_groups == 0:
                    status = "⚠️  PROCESSED BUT NOT SYNCED"
                    recommendation = "Needs cleanup - delete from FACT_ORDER_LIST and ORDER_LIST_LINES first"
                else:
                    status = "❌ ALREADY SYNCED"
                    recommendation = "Avoid for testing - already has Monday.com sync data"
            else:
                status = "❓ UNKNOWN STATE"
                recommendation = "Manual investigation needed"
            
            logger.info(f"   Status: {status}")
            logger.info(f"   Recommendation: {recommendation}")
            
            return {
                'customer': customer,
                'po': po,
                'source_count': source_count,
                'fact_count': fact_count,
                'lines_count': lines_count,
                'status': status,
                'recommendation': recommendation,
                'source_data': source_result.to_dict('records')[0] if not source_result.empty else {},
                'fact_data': fact_result.to_dict('records')[0] if not fact_result.empty else {},
                'lines_data': lines_result.to_dict('records')[0] if not lines_result.empty else {}
            }
    
    def generate_cleanup_commands(self, customer: str, po: str) -> List[str]:
        """Generate cleanup SQL commands for testing"""
        logger.info(f"\n🧹 Generating cleanup commands for {customer} PO {po}")
        
        # Use correct join pattern from working tests (record_uuid join)
        cleanup_commands = [
            f"-- Cleanup commands for {customer} PO {po}",
            f"-- DANGER: These commands will DELETE existing data!",
            f"-- Pattern: Uses record_uuid join from proven working tests",
            f"",
            f"-- Step 1: Delete from ORDER_LIST_LINES (foreign key constraint)",
            f"DELETE ol FROM ORDER_LIST_LINES ol",
            f"JOIN FACT_ORDER_LIST fact ON ol.record_uuid = fact.record_uuid",
            f"WHERE fact.[CUSTOMER NAME] = '{customer}' AND fact.[PO NUMBER] = '{po}';",
            f"",
            f"-- Step 2: Delete from FACT_ORDER_LIST",
            f"DELETE FROM FACT_ORDER_LIST",
            f"WHERE [CUSTOMER NAME] = '{customer}' AND [PO NUMBER] = '{po}';",
            f"",
            f"-- Verification: Check cleanup was successful",
            f"SELECT 'FACT_ORDER_LIST' as table_name, COUNT(*) as remaining_records",
            f"FROM FACT_ORDER_LIST",
            f"WHERE [CUSTOMER NAME] = '{customer}' AND [PO NUMBER] = '{po}'",
            f"UNION ALL",
            f"SELECT 'ORDER_LIST_LINES' as table_name, COUNT(*) as remaining_records",
            f"FROM ORDER_LIST_LINES ol",
            f"JOIN FACT_ORDER_LIST fact ON ol.record_uuid = fact.record_uuid",
            f"WHERE fact.[CUSTOMER NAME] = '{customer}' AND fact.[PO NUMBER] = '{po}';",
        ]
        
        logger.info("🔧 Cleanup SQL commands generated:")
        for cmd in cleanup_commands:
            if cmd.strip() and not cmd.startswith('--'):
                logger.info(f"   {cmd}")
        
        return cleanup_commands
    
    def run_complete_analysis(self) -> Dict:
        """Run complete real data analysis"""
        logger.info("=" * 80)
        logger.info("🎯 REAL DATA ANALYSIS FOR ENHANCED MERGE ORCHESTRATOR TESTING")
        logger.info("=" * 80)
        logger.info("Purpose: Analyze available real data and provide testing recommendations")
        logger.info("Pattern: EXACT working pattern from imports.guidance.instructions.md")
        logger.info("=" * 80)
        
        try:
            # Run all analyses
            source_data = self.analyze_available_source_data()
            fact_state = self.analyze_current_fact_state()
            lines_state = self.analyze_current_lines_state()
            clean_candidates = self.find_clean_test_candidates()
            
            # Generate summary recommendations
            logger.info("\n" + "=" * 80)
            logger.info("🎯 TESTING RECOMMENDATIONS:")
            logger.info("=" * 80)
            
            if clean_candidates:
                logger.info("✅ CLEAN TEST CANDIDATES AVAILABLE:")
                for i, candidate in enumerate(clean_candidates[:3], 1):
                    logger.info(f"   {i}. Use {candidate['CUSTOMER NAME']} PO {candidate['PO NUMBER']} ({candidate['source_records']} records)")
                logger.info("\n   💡 These candidates have source data but no existing FACT_ORDER_LIST entries")
                logger.info("   💡 Perfect for clean testing of enhanced merge orchestrator")
            else:
                logger.info("⚠️  NO CLEAN CANDIDATES - All data already processed")
                logger.info("   💡 Consider using existing data with cleanup commands")
                
            # Data state summary
            fact_overview = fact_state.get('overview', {})
            lines_overview = lines_state.get('overview', {})
            
            if fact_overview.get('total_records', 0) > 0:
                logger.info(f"\n📊 CURRENT STATE SUMMARY:")
                logger.info(f"   FACT_ORDER_LIST: {fact_overview['total_records']:,} records")
                logger.info(f"   ORDER_LIST_LINES: {lines_overview.get('total_lines', 0):,} records")
                logger.info(f"   Monday.com sync rate: {(fact_overview.get('synced_items', 0) / fact_overview['total_records']) * 100:.1f}%")
            
            logger.info("\n🚀 READY FOR TESTING:")
            logger.info("   1. Choose clean test candidate OR cleanup existing data")
            logger.info("   2. Run enhanced merge orchestrator test")
            logger.info("   3. Validate Monday.com group/item/subitem creation")
            logger.info("   4. Use this script to monitor progress")
            
            logger.info("=" * 80)
            
            return {
                'source_data': source_data,
                'fact_state': fact_state,
                'lines_state': lines_state,
                'clean_candidates': clean_candidates,
                'analysis_complete': True
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {'analysis_complete': False, 'error': str(e)}

def main():
    """Run complete real data analysis"""
    try:
        logger.info("🚀 Starting Real Data Analysis...")
        
        analyzer = RealDataAnalyzer()
        results = analyzer.run_complete_analysis()
        
        # Example specific customer/PO check
        logger.info("\n" + "=" * 60)
        logger.info("📋 EXAMPLE: Specific Customer/PO Analysis")
        logger.info("=" * 60)
        
        # Check a few specific cases for demonstration
        test_cases = [
            ("GREYSON", "4755"),
            ("JOHNNIE O", "12345"),  # Example - may not exist
            ("TRACKSMITH", "98765")   # Example - may not exist
        ]
        
        for customer, po in test_cases:
            specific_analysis = analyzer.check_specific_customer_po(customer, po)
            
            if specific_analysis['status'] == "⚠️  PROCESSED BUT NOT SYNCED":
                logger.info(f"\n🧹 Cleanup commands for {customer} PO {po}:")
                cleanup_commands = analyzer.generate_cleanup_commands(customer, po)
        
        return 0 if results.get('analysis_complete', False) else 1
        
    except Exception as e:
        logger.error(f"Real data analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    logger.info(f"🏁 Real data analysis completed with exit code: {exit_code}")
    sys.exit(exit_code)
