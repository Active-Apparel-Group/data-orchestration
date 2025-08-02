#!/usr/bin/env python3
"""
API Logging Archiver - Extract and preserve API logging data for historical analysis

This module implements the archival system for Monday.com API logging data from the 
main ORDER_LIST tables. It extracts API interaction history after each pipeline run
to preserve troubleshooting data while maintaining efficient main table operations.

Key Features:
- Extracts API logging data from FACT_ORDER_LIST and ORDER_LIST_LINES
- Preserves essential fields for troubleshooting and audit trails  
- Supports pipeline run ide        # Get API error details for this customer - using existing columns only
        error_details_query = ""
        SELECT TOP 10
            [AAG ORDER NUMBER],
            [CUSTOMER STYLE],
            [CUSTOMER COLOUR DESCRIPTION],
            [CUSTOMER SEASON],
            sync_state,
            record_uuid
        FROM FACT_ORDER_LIST 
        WHERE [CUSTOMER NAME] = ? 
        AND sync_state IN ('ERROR', 'FAILED')
        ORDER BY record_uuid DESC
        ""
        
        cursor.execute(error_details_query, (customer_name,))
        error_records = cursor.fetchall()uping related operations
- Implements overwrite strategy for hourly pipeline runs
- Provides validation and cleanup capabilities

Author: Generated for TASK022 - API Logging Archival System
Date: 2025-07-30
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import json

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig

logger = logger.get_logger(__name__)


class APILoggingArchiver:
    """
    Manages the archival of API logging data from main tables to dedicated log table.
    
    This class handles the extraction, transformation, and storage of API logging data
    from FACT_ORDER_LIST and ORDER_LIST_LINES tables into the ORDER_LIST_API_LOG table
    for historical preservation and troubleshooting purposes.
    """
    
    def __init__(self, config: DeltaSyncConfig):
        """
        Initialize the API logging archiver.
        
        Args:
            config: DeltaSyncConfig instance with database and table configuration
        """
        self.config = config
        self.pipeline_run_id = self._generate_pipeline_run_id()
        
        # Initialize logger using the same pattern as other modules
        from pipelines.utils import logger
        self.logger = logger.get_logger(__name__)
        
    def _generate_pipeline_run_id(self) -> str:
        """
        Generate a unique identifier for this pipeline run.
        
        Returns:
            str: Unique pipeline run identifier with timestamp
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        run_uuid = str(uuid.uuid4())[:8]
        return f"sync_{timestamp}_{run_uuid}"
    
    def archive_api_logging_data(self, cursor, dry_run: bool = False) -> Dict[str, int]:
        """
        Archive API logging data from main tables to dedicated log table.
        
        Args:
            cursor: Database cursor object
            dry_run: If True, only show what would be archived without executing
            
        Returns:
            Dict[str, int]: Statistics about archived records
        """
        self.logger.info(f"🗄️ Starting API logging archival process (pipeline_run_id: {self.pipeline_run_id})")
        
        stats = {
            "pipeline_run_id": self.pipeline_run_id,
            "archive_timestamp": datetime.utcnow().isoformat(),
            "headers_archived": 0,
            "lines_archived": 0,
            "total_archived": 0,
            "errors": 0
        }
        
        # Archive header API logging data
        headers_count = self._archive_headers_data(cursor, dry_run)
        stats["headers_archived"] = headers_count
        
        # Archive lines API logging data  
        lines_count = self._archive_lines_data(cursor, dry_run)
        stats["lines_archived"] = lines_count
        
        stats["total_archived"] = headers_count + lines_count
        
        if not dry_run:
            self.logger.info(f"✅ API logging archival completed successfully")
        else:
            self.logger.info(f"🔍 Dry run completed - would archive {stats['total_archived']} records")
        
        self._log_archival_stats(stats)
        return stats
    
    def _archive_headers_data(self, cursor, dry_run: bool) -> int:
        """
        Archive API logging data from FACT_ORDER_LIST table.
        
        Args:
            cursor: Database cursor
            dry_run: If True, only count records without inserting
            
        Returns:
            int: Number of header records archived
        """
        # Query to extract API logging data from headers table
        # FIXED: Use correct column names that exist in FACT_ORDER_LIST
        select_query = """
        SELECT 
            record_uuid,
            sync_state,
            sync_completed_at,
            api_request_payload,
            api_response_payload,
            api_request_timestamp,
            api_response_timestamp,
            api_operation_type,
            api_status
        FROM FACT_ORDER_LIST
        WHERE (api_request_payload IS NOT NULL 
           OR api_response_payload IS NOT NULL
           OR api_status IS NOT NULL)
        AND sync_completed_at IS NOT NULL
        """
        
        cursor.execute(select_query)
        header_records = cursor.fetchall()
        
        if dry_run:
            self.logger.info(f"🔍 Would archive {len(header_records)} header records")
            return len(header_records)
        
        if not header_records:
            self.logger.info("📝 No header API logging data found to archive")
            return 0
        
        # Insert into archival table
        insert_count = self._insert_archival_records(cursor, header_records, "HEADER")
        self.logger.info(f"📋 Archived {insert_count} header API logging records")
        
        return insert_count
    
    def _archive_lines_data(self, cursor, dry_run: bool) -> int:
        """
        Archive API logging data from ORDER_LIST_LINES table.
        
        Args:
            cursor: Database cursor
            dry_run: If True, only count records without inserting
            
        Returns:
            int: Number of lines records archived
        """
        # Query to extract API logging data from lines table
        # FIXED: Use correct column names that exist in ORDER_LIST_LINES
        select_query = """
        SELECT 
            record_uuid,
            sync_state,
            sync_completed_at,
            api_request_payload,
            api_response_payload,
            api_request_timestamp,
            api_response_timestamp,
            api_operation_type,
            api_status
        FROM ORDER_LIST_LINES
        WHERE (api_request_payload IS NOT NULL 
           OR api_response_payload IS NOT NULL
           OR api_status IS NOT NULL)
        AND sync_completed_at IS NOT NULL
        """
        
        cursor.execute(select_query)
        lines_records = cursor.fetchall()
        
        if dry_run:
            self.logger.info(f"🔍 Would archive {len(lines_records)} lines records")
            return len(lines_records)
        
        if not lines_records:
            self.logger.info("📝 No lines API logging data found to archive")
            return 0
        
        # Insert into archival table
        insert_count = self._insert_archival_records(cursor, lines_records, "LINE")
        self.logger.info(f"📋 Archived {insert_count} lines API logging records")
        
        return insert_count
    
    def _insert_archival_records(self, cursor, records: List[tuple], source: str) -> int:
        """
        Insert API logging records into the archival table.
        
        Args:
            cursor: Database cursor
            records: List of tuples containing API logging data
            source: Source type ('HEADER' or 'LINE')
            
        Returns:
            int: Number of records inserted
        """
        if not records:
            return 0
        
        # Prepare insert statement
        insert_query = """
        INSERT INTO ORDER_LIST_API_LOG (
            record_uuid,
            source,
            sync_state,
            sync_completed_at,
            api_request_payload,
            api_response_payload,
            api_request_timestamp,
            api_response_timestamp,
            api_operation_type,
            api_status,
            archived_at,
            pipeline_run_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETUTCDATE(), ?)
        """
        
        # Transform records for insertion
        insert_data = []
        for record in records:
            insert_record = (
                record[0],  # record_uuid
                source,     # source
                record[1],  # sync_state
                record[2],  # sync_completed_at
                record[3],  # api_request_payload
                record[4],  # api_response_payload
                record[5],  # api_request_timestamp
                record[6],  # api_response_timestamp
                record[7],  # api_operation_type
                record[8],  # api_status
                self.pipeline_run_id  # pipeline_run_id
            )
            insert_data.append(insert_record)
        
        # Execute batch insert
        cursor.executemany(insert_query, insert_data)
        return len(insert_data)
    
    def _log_archival_stats(self, stats: Dict[str, int]) -> None:
        """
        Log comprehensive archival statistics.
        
        Args:
            stats: Dictionary containing archival statistics
        """
        logger.info("📊 API Logging Archival Statistics:")
        logger.info(f"  Headers archived: {stats['headers_archived']}")
        logger.info(f"  Lines archived: {stats['lines_archived']}")
        logger.info(f"  Total archived: {stats['total_archived']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"  Pipeline run ID: {self.pipeline_run_id}")
    
    def cleanup_old_archives(self, connection, retention_days: int = 30, dry_run: bool = False) -> int:
        """
        Clean up old archival records beyond retention period.
        
        Args:
            connection: Database connection object
            retention_days: Number of days to retain archival data
            dry_run: If True, only count records without deleting
            
        Returns:
            int: Number of records cleaned up
        """
        logger.info(f"🧹 Starting archival cleanup (retention: {retention_days} days)")
        
        cursor = connection.cursor()
        
        try:
            # Query to count old records
            count_query = """
            SELECT COUNT(*) FROM ORDER_LIST_API_LOG
            WHERE archived_at < DATEADD(day, -?, GETUTCDATE())
            """
            
            cursor.execute(count_query, (retention_days,))
            old_count = cursor.fetchone()[0]
            
            if dry_run:
                logger.info(f"🔍 Would clean up {old_count} old archival records")
                return old_count
            
            if old_count == 0:
                logger.info("📝 No old archival records found to clean up")
                return 0
            
            # Delete old records
            delete_query = """
            DELETE FROM ORDER_LIST_API_LOG
            WHERE archived_at < DATEADD(day, -?, GETUTCDATE())
            """
            
            cursor.execute(delete_query, (retention_days,))
            connection.commit()
            
            logger.info(f"✅ Cleaned up {old_count} old archival records")
            return old_count
            
        except Exception as e:
            connection.rollback()
            logger.error(f"❌ Archival cleanup failed: {str(e)}")
            raise
        finally:
            cursor.close()
    
    def get_archival_summary(self, cursor) -> Dict[str, any]:
        """
        Get summary statistics about the archival table.
        
        Args:
            cursor: Database cursor object
            
        Returns:
            Dict[str, any]: Summary statistics
        """
        
        # Total records by source
        summary_query = """
        SELECT 
            source,
            COUNT(*) as record_count,
            MIN(archived_at) as earliest_archive,
            MAX(archived_at) as latest_archive,
            COUNT(DISTINCT pipeline_run_id) as pipeline_runs
        FROM ORDER_LIST_API_LOG
        GROUP BY source
        """
        
        cursor.execute(summary_query)
        source_stats = cursor.fetchall()
        
        # API status distribution
        status_query = """
        SELECT 
            api_status,
            COUNT(*) as count
        FROM ORDER_LIST_API_LOG
        WHERE api_status IS NOT NULL
        GROUP BY api_status
        ORDER BY count DESC
        """
        
        cursor.execute(status_query)
        status_stats = cursor.fetchall()
        
        return {
            "source_statistics": [
                {
                    "source": row[0],
                    "record_count": row[1],
                    "earliest_archive": row[2],
                    "latest_archive": row[3],
                    "pipeline_runs": row[4]
                }
                for row in source_stats
            ],
            "status_distribution": [
                {"status": row[0], "count": row[1]}
                for row in status_stats
            ]
        }
    
    def log_essential_metrics(self, cursor, record_uuid: str, customer_name: str, 
                             aag_order_number: str, operation_type: str, status: str,
                             error_category: Optional[str] = None, error_summary: Optional[str] = None,
                             retry_count: int = 0, processing_time_ms: Optional[int] = None) -> bool:
        """
        Log essential API metrics without heavy payloads (Fix #2: Enhanced Logging).
        
        This method provides lightweight logging focused on actionable insights:
        - Customer processing results
        - Error categorization for targeted fixes
        - Retry patterns and effectiveness
        - Performance metrics
        
        Args:
            cursor: Database cursor
            record_uuid: Unique record identifier
            customer_name: Customer name for grouping
            aag_order_number: Order number for tracking
            operation_type: Type of Monday.com operation
            status: SUCCESS, ERROR, or PENDING
            error_category: Categorized error type (DROPDOWN_VALUE_MISSING, RATE_LIMIT, etc.)
            error_summary: Brief error summary (no full payloads)
            retry_count: Current retry attempt
            processing_time_ms: Operation timing
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            # Extract error category from status if not provided
            if status == 'ERROR' and not error_category:
                error_category = 'UNKNOWN_ERROR'
                error_summary = error_summary or 'Unspecified error'
            
            # Insert essential metrics only (no heavy payloads)
            insert_query = """
            INSERT INTO ORDER_LIST_API_LOG (
                record_uuid, source, sync_state, api_operation_type, api_status,
                archived_at, pipeline_run_id
            ) VALUES (?, ?, ?, ?, ?, GETUTCDATE(), ?)
            """
            
            cursor.execute(insert_query, (
                record_uuid,
                'ESSENTIAL_METRICS',  # Mark as essential logging
                status,
                operation_type,
                status,
                f"essential_{self.pipeline_run_id}"
            ))
            
            self.logger.debug(f"📊 Essential metrics logged: {customer_name} | {operation_type} | {status}")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ Essential metrics logging failed: {e}")
            return False
    
    def extract_error_category(self, response_payload: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract essential error information from response payload.
        
        Returns categorized error info without storing full payload.
        
        Args:
            response_payload: Full API response payload
            
        Returns:
            Tuple[category, summary]: Error category and brief summary
        """
        if not response_payload:
            return None, None
        
        try:
            import json
            response_data = json.loads(response_payload)
            
            if 'errors' in response_data:
                for error in response_data['errors']:
                    error_msg = error.get('message', '')
                    
                    # Categorize common Monday.com errors
                    if 'ColumnValueException' in error_msg:
                        if 'not found' in error_msg.lower():
                            return 'DROPDOWN_VALUE_MISSING', 'Dropdown value not found - needs creation'
                        else:
                            return 'DROPDOWN_VALIDATION', 'Dropdown validation error'
                    
                    elif 'rate limit' in error_msg.lower():
                        return 'RATE_LIMIT', 'API rate limit exceeded'
                    
                    elif 'authentication' in error_msg.lower():
                        return 'AUTH_ERROR', 'Authentication failure'
                    
                    elif 'not found' in error_msg.lower():
                        return 'RESOURCE_NOT_FOUND', 'Board/group/item not found'
                    
                    else:
                        # Generic error with first 100 chars
                        summary = error_msg[:100] + '...' if len(error_msg) > 100 else error_msg
                        return 'UNKNOWN_ERROR', summary
            
            return 'UNKNOWN_ERROR', 'No specific error found'
            
        except Exception:
            return 'PAYLOAD_PARSE_ERROR', 'Could not parse error response'
    
    def generate_customer_summary_report(self, cursor, customer_name: str) -> str:
        """
        Generate comprehensive diagnostic report for specific customer processing results.
        
        Includes:
        - Processing summary with detailed metrics
        - Error analysis with specific Monday.com API errors
        - Record-level diagnostics with key business columns
        - Dropdown mapping issues analysis
        - Batch processing failure details
        - Pending records analysis with actionable insights
        
        Args:
            cursor: Database cursor
            customer_name: Customer to generate report for
            
        Returns:
            str: Comprehensive markdown formatted diagnostic report
        """
        
        # Customer processing summary from FACT_ORDER_LIST
        summary_query = """
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE WHEN monday_item_id IS NOT NULL THEN 1 ELSE 0 END) as items_loaded,
            SUM(CASE WHEN api_status = 'SUCCESS' OR monday_item_id IS NOT NULL THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN api_status = 'ERROR' THEN 1 ELSE 0 END) as errors,
            SUM(CASE WHEN COALESCE(retry_count, 0) > 0 THEN 1 ELSE 0 END) as retries,
            SUM(CASE WHEN sync_state = 'PENDING' AND api_status IS NULL THEN 1 ELSE 0 END) as pending,
            COUNT(DISTINCT group_id) as groups_created,
            COUNT(DISTINCT record_uuid) as unique_orders
        FROM FACT_ORDER_LIST
        WHERE [CUSTOMER NAME] = ?
        """
        
        cursor.execute(summary_query, (customer_name,))
        stats = cursor.fetchone()
        
        if not stats:
            return f"# {customer_name}\n\n⚠️ No data found for this customer."
        
        total, loaded, successful, errors, retries, pending, groups, orders = stats
        
        # Generate markdown report
        from datetime import datetime
        report = []
        report.append(f"# {customer_name} - COMPREHENSIVE DIAGNOSTIC REPORT")
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary table
        success_rate = (successful / total * 100) if total > 0 else 0
        overall_result = "✅ Success" if success_rate >= 95 else "⚠️ Needs Attention" if success_rate >= 80 else "❌ Critical"
        
        report.append("## Executive Summary")
        report.append("")
        report.append("| Metric | Count | Percentage |")
        report.append("|--------|-------|------------|")
        report.append(f"| Total Items | {total:,} | 100.0% |")
        report.append(f"| Items Loaded | {loaded:,} | {(loaded/total*100):.1f}% |")
        report.append(f"| Successful | {successful:,} | {(successful/total*100):.1f}% |")
        report.append(f"| Errors | {errors:,} | {(errors/total*100):.1f}% |")
        report.append(f"| Retries | {retries:,} | {(retries/total*100):.1f}% |")
        report.append(f"| Pending | {pending:,} | {(pending/total*100):.1f}% |")
        report.append(f"| Groups Created | {groups} | - |")
        report.append(f"| **Overall Result** | **{overall_result}** | **{success_rate:.1f}%** |")
        report.append("")
        
        # ERROR ANALYSIS - Detailed Monday.com API errors
        report.append("## 🚨 Error Analysis")
        report.append("")
        
        error_details_query = """
        SELECT TOP 10
            [AAG ORDER NUMBER],
            [CUSTOMER STYLE],
            [CUSTOMER COLOUR DESCRIPTION],
            [CUSTOMER SEASON],
            sync_state,
            record_uuid
        FROM FACT_ORDER_LIST 
        WHERE [CUSTOMER NAME] = ? 
        AND sync_state IN ('ERROR', 'FAILED')
        ORDER BY record_uuid DESC
        """
        
        cursor.execute(error_details_query, (customer_name,))
        error_records = cursor.fetchall()
        
        # Initialize error tracking lists
        dropdown_errors = []
        other_errors = []
        
        if error_records:
            report.append("### API Error Details")
            report.append("")
            report.append("| Order | Style | Color | Season | Error Summary |")
            report.append("|-------|-------|--------|--------|---------------|")
            
            for record in error_records:
                aag_order, style, color, season, error_msg, response_data, sync_state, uuid = record
                
                # Parse error message for dropdown issues
                error_summary = "Unknown error"
                if error_msg:
                    if "dropdown label" in error_msg and "does not exist" in error_msg:
                        # Extract dropdown details
                        if "REBUY" in error_msg:
                            error_summary = "❌ Dropdown: REBUY → Should be SPRING 26 REBUY (Column: CUSTOMER SEASON)"
                            dropdown_errors.append({
                                'record': f"{aag_order} | {style}",
                                'issue': 'Invalid dropdown value: REBUY',
                                'solution': 'Map REBUY → SPRING 26 REBUY',
                                'column': 'CUSTOMER SEASON (dropdown_mkr5rgs6)'
                            })
                        else:
                            error_summary = f"❌ Dropdown mapping issue: {error_msg[:80]}..."
                    else:
                        error_summary = f"❌ API Error: {error_msg[:50]}..."
                        other_errors.append({
                            'record': f"{aag_order} | {style}",
                            'error': error_msg
                        })
                
                report.append(f"| {aag_order or 'N/A'} | {style or 'N/A'} | {color or 'N/A'} | {season or 'N/A'} | {error_summary} |")
            
            report.append("")
            
            # Dropdown Mapping Issues
            if dropdown_errors:
                report.append("### 🎯 DROPDOWN MAPPING ISSUES (CRITICAL)")
                report.append("")
                report.append("**Root Cause**: Source data contains dropdown values that don't exist in Monday.com")
                report.append("")
                for issue in dropdown_errors[:5]:  # Show top 5
                    report.append(f"- **Record**: {issue['record']}")
                    report.append(f"  - **Issue**: {issue['issue']}")
                    report.append(f"  - **Solution**: {issue['solution']}")
                    report.append(f"  - **Column**: {issue['column']}")
                    report.append("")
            
            # Other API errors
            if other_errors:
                report.append("### 🔧 OTHER API ERRORS")
                report.append("")
                for error in other_errors[:3]:  # Show top 3
                    report.append(f"- **Record**: {error['record']}")
                    report.append(f"  - **Error**: {error['error']}")
                    report.append("")
        else:
            report.append("✅ No API errors found for this customer.")
            report.append("")
        
        # PENDING RECORDS ANALYSIS
        report.append("## 📋 Pending Records Analysis")
        report.append("")
        
        pending_query = """
        SELECT TOP 15
            [AAG ORDER NUMBER],
            [CUSTOMER STYLE], 
            [CUSTOMER COLOUR DESCRIPTION],
            [CUSTOMER SEASON],
            [AAG SEASON],
            [TOTAL QTY],
            sync_state,
            record_uuid
        FROM FACT_ORDER_LIST
        WHERE [CUSTOMER NAME] = ? 
        AND sync_state = 'PENDING'
        ORDER BY [ORDER DATE PO RECEIVED] DESC
        """
        
        cursor.execute(pending_query, (customer_name,))
        pending_records = cursor.fetchall()
        
        if pending_records:
            report.append(f"### {len(pending_records)} Pending Records (showing top 15)")
            report.append("")
            report.append("| AAG Order | Style | Color | Customer Season | AAG Season | Qty | Status |")
            report.append("|-----------|-------|--------|----------------|------------|-----|--------|")
            
            for record in pending_records:
                aag_order, style, color, cust_season, aag_season, qty, sync_state, uuid = record
                qty_display = f"{int(qty):,}" if qty else "0"
                report.append(f"| {aag_order or 'N/A'} | {style or 'N/A'} | {color or 'N/A'} | {cust_season or 'N/A'} | {aag_season or 'N/A'} | {qty_display} | {sync_state} |")
            
            report.append("")
            
            # Analyze pending records for common issues
            season_analysis_query = """
            SELECT 
                [CUSTOMER SEASON],
                COUNT(*) as record_count
            FROM FACT_ORDER_LIST
            WHERE [CUSTOMER NAME] = ? 
            AND sync_state = 'PENDING'
            GROUP BY [CUSTOMER SEASON]
            ORDER BY record_count DESC
            """
            
            cursor.execute(season_analysis_query, (customer_name,))
            season_breakdown = cursor.fetchall()
            
            if season_breakdown:
                report.append("### 📊 Pending Records by Customer Season")
                report.append("")
                report.append("| Customer Season | Record Count | Likely Issue |")
                report.append("|----------------|--------------|--------------|")
                
                for season, count in season_breakdown:
                    issue_likely = "❌ Dropdown mapping" if season == "REBUY" else "⚠️ Review needed"
                    report.append(f"| {season or 'NULL'} | {count:,} | {issue_likely} |")
                
                report.append("")
        else:
            report.append("✅ No pending records found for this customer.")
            report.append("")
        
        # SUCCESSFUL RECORDS SAMPLE
        if successful > 0:
            report.append("## ✅ Successful Records Sample")
            report.append("")
            
            success_query = """
            SELECT TOP 5
                [AAG ORDER NUMBER],
                [CUSTOMER STYLE],
                [CUSTOMER COLOUR DESCRIPTION], 
                monday_item_id,
                group_id,
                api_status
            FROM FACT_ORDER_LIST
            WHERE [CUSTOMER NAME] = ? 
            AND (api_status = 'SUCCESS' OR monday_item_id IS NOT NULL)
            ORDER BY record_uuid DESC
            """
            
            cursor.execute(success_query, (customer_name,))
            success_records = cursor.fetchall()
            
            report.append("| AAG Order | Style | Color | Monday ID | Status |")
            report.append("|-----------|-------|--------|-----------|--------|")
            
            for record in success_records:
                aag_order, style, color, monday_id, group_id, status = record
                report.append(f"| {aag_order or 'N/A'} | {style or 'N/A'} | {color or 'N/A'} | {monday_id or 'N/A'} | ✅ {status or 'SUCCESS'} |")
            
            report.append("")
        
        # ACTIONABLE RECOMMENDATIONS
        report.append("## 🎯 ACTIONABLE RECOMMENDATIONS")
        report.append("")
        
        if dropdown_errors:
            report.append("### 🔧 IMMEDIATE ACTIONS REQUIRED:")
            report.append("")
            report.append("1. **Fix Dropdown Mapping Issue**:")
            report.append(f"   - **Problem**: Source data contains 'REBUY' but Monday.com expects 'SPRING 26 REBUY'")
            report.append(f"   - **Column**: CUSTOMER SEASON (dropdown_mkr5rgs6)")  
            report.append(f"   - **Solution**: Update data transformation to map REBUY → SPRING 26 REBUY")
            report.append(f"   - **Records Affected**: {len(dropdown_errors)} records")
            report.append("")
        
        if pending > 0:
            report.append("2. **Process Pending Records**:")
            report.append(f"   - **Count**: {pending:,} records waiting for sync")
            report.append("   - **Action**: Re-run sync after fixing dropdown mapping issues")
            report.append("")
        
        if success_rate < 95:
            report.append("3. **Improve Success Rate**:")
            report.append(f"   - **Current**: {success_rate:.1f}% (Target: >95%)")
            report.append("   - **Action**: Address error causes above and re-process")
            report.append("")
        
        return "\n".join(report)
def main():
    """
    Main function for testing the API logging archiver.
    """
    import sys
    from pathlib import Path
    
    # Add repository root to path
    repo_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "src"))
    
    # Configuration and database setup
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    with db.get_connection(config.db_key) as connection:
        archiver = APILoggingArchiver(config)
        
        # Test archival process
        logger.info("🧪 Testing API logging archival process...")
        stats = archiver.archive_api_logging_data(connection, dry_run=True)
        
        # Get summary
        summary = archiver.get_archival_summary(connection)
        logger.info(f"📊 Current archival summary: {json.dumps(summary, indent=2, default=str)}")


if __name__ == "__main__":
    main()
