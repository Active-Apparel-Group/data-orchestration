#!/usr/bin/env python3
"""
Change Detector - Hash-based change detection for ORDERS_UNIFIED

Implements Methods 1 & 2 from the change detection analysis:
- Method 1: Outer Join with _merge indicator (comprehensive classification)
- Method 2: Hash Comparison (quick detection)

Features:
- Row-level hashing for change detection
- Delta comparison with clear status classification
- Support for customer filtering and limits
"""

import os
import sys
from pathlib import Path
import hashlib
import pandas as pd

# Add utils to path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))

# Import utilities using working production pattern
import db_helper as db
import logger_helper

class ChangeDetector:
    """Detects changes between ORDERS_UNIFIED and existing Monday.com records"""
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.database = "ORDERS"        # Key fields for change detection (business key to identify unique records)
        self.key_fields = [
            'AAG ORDER NUMBER',
            'CUSTOMER NAME', 
            'CUSTOMER STYLE',
            'CUSTOMER COLOUR DESCRIPTION',
            'PO NUMBER',
            'CUSTOMER ALT PO',
            'ACTIVE',

        ]
        
        # Hash ALL columns except system fields - no need to list every column!
        self.exclude_from_hash = [
            'record_uuid',           # System generated UUID
            'snapshot_date',         # System timestamp 
            'customer_filter',       # System metadata            'row_hash'              # The hash itself
        ]
    
    def detect_changes(self, customer_filter: str = None, limit: int = None, po_number_filter: str = None) -> pd.DataFrame:
        """
        Detect changes using hash-based comparison (Method 1 & 2)
        
        Args:
            customer_filter: Filter to specific customer
            limit: Limit number of records processed
            po_number_filter: Filter to specific PO number (for testing)
            
        Returns:
            DataFrame with change classification (NEW, UNCHANGED, CHANGED, DELETED)
        """
        
        try:
            self.logger.info("Starting change detection...")
            
            # Get source data with hashes
            source_data = self._get_source_data_with_hashes(customer_filter, limit, po_number_filter)
            self.logger.info(f"   Source records: {len(source_data)}")
            
            # Get target data (existing Monday.com records)
            target_data = self._get_target_data()
            self.logger.info(f"   Target records: {len(target_data)}")
            
            # Method 1: Outer join with _merge indicator
            changes = self._method1_outer_join_classification(source_data, target_data)
            
            # Method 2: Enhanced with hash comparison details
            changes = self._method2_hash_comparison_details(changes)
            
            # Classify changes
            change_summary = changes['change_type'].value_counts().to_dict()
            self.logger.info(f"   Change classification: {change_summary}")
            
            return changes            
        except Exception as e:
            self.logger.error(f"Change detection failed: {str(e)}")
            raise
    
    def _get_source_data_with_hashes(self, customer_filter: str = None, limit: int = None, po_number_filter: str = None) -> pd.DataFrame:
        """Get ORDERS_UNIFIED data with row hashes"""
        
        # Build query with optional filters
        where_clause = "WHERE [record_uuid] IS NOT NULL"
        
        if customer_filter:
            # Map common customer names to their canonical form in ORDERS_UNIFIED
            customer_mapping = {
                'GREYSON': 'GREYSON CLOTHIERS'
            }
            canonical_customer = customer_mapping.get(customer_filter, customer_filter)
            where_clause += f" AND [CUSTOMER NAME] = '{canonical_customer}'"
            
        if po_number_filter:
            where_clause += f" AND [PO NUMBER] = '{po_number_filter}'"
        
        limit_clause = f"TOP {limit}" if limit else ""
        
        query = f"""
        SELECT {limit_clause}
            [record_uuid],
            [AAG ORDER NUMBER],
            [CUSTOMER NAME],
            [CUSTOMER STYLE], 
            [CUSTOMER COLOUR DESCRIPTION],
            [TOTAL QTY],
            [ORDER DATE PO RECEIVED],
            [PO NUMBER],
            [CUSTOMER ALT PO],
            [DESTINATION],
            [DELIVERY TERMS],
            [CUSTOMER SEASON],
            [DROP],
            [CATEGORY],
            [PATTERN ID]
        FROM [dbo].[ORDERS_UNIFIED]
        {where_clause}
        ORDER BY [CUSTOMER NAME], [AAG ORDER NUMBER]
        """
        
        print(f"   🔍 DEBUG - Source Data Query:\n{query}")
        
        df = db.run_query(query, self.database)
        print(f"   🔍 DEBUG - Source Data Results: {len(df)} records")
        if not df.empty:
            print(f"   🔍 DEBUG - Source UUID samples: {df['record_uuid'].head(3).tolist()}")
        
        # Generate row hashes
        df['record_hash'] = df.apply(self._generate_row_hash, axis=1)
        
        return df
    
    def _get_target_data(self) -> pd.DataFrame:
        """Get existing Monday.com records for comparison"""
        
        # For now, get from MON_CustMasterSchedule
        # Later we'll enhance this to get from staging history
        query = """
        SELECT 
            [source_uuid],
            [source_hash],
            [AAG ORDER NUMBER],
            [CUSTOMER],
            [STYLE],
            [COLOR],
            [TOTAL QTY],
            [Item ID]
        FROM [dbo].[MON_CustMasterSchedule]
        WHERE [source_uuid] IS NOT NULL
        """
        
        print(f"   🔍 DEBUG - Target Data Query:\n{query}")
        
        try:
            df = db.run_query(query, self.database)
            print(f"   🔍 DEBUG - Target Data Results: {len(df)} records")
            if not df.empty:
                print(f"   🔍 DEBUG - Target Data Columns: {list(df.columns)}")
                print(f"   🔍 DEBUG - Target Data Sample: {df.head(2).to_dict('records')}")
            return df
        except Exception as e:
            # If columns don't exist yet, return empty DataFrame
            print(f"   🔍 DEBUG - Target Data Query Failed: {e}")
            self.logger.warning("Target table doesn't have UUID columns yet, treating all as NEW")
            return pd.DataFrame()
    
    def _method1_outer_join_classification(self, source_df: pd.DataFrame, target_df: pd.DataFrame) -> pd.DataFrame:
        """
        Method 1: Outer Join with _merge indicator
        Best for: Full syncs, new vs missing vs changed classification
        """
        
        if target_df.empty:
            # All records are NEW if no target data
            source_df['change_type'] = 'NEW'
            source_df['target_hash'] = None
            return source_df
        
        # Merge on UUID
        merged = source_df.merge(
            target_df[['source_uuid', 'source_hash']],
            left_on='record_uuid',
            right_on='source_uuid',
            how='outer',
            suffixes=('_src', '_tgt'),
            indicator=True
        )
        
        # Classify changes
        def classify_change(row):
            if row['_merge'] == 'left_only':
                return 'NEW'
            elif row['_merge'] == 'right_only':
                return 'DELETED' 
            elif row['record_hash'] != row['source_hash']:
                return 'CHANGED'
            else:
                return 'UNCHANGED'
        
        merged['change_type'] = merged.apply(classify_change, axis=1)
        merged['target_hash'] = merged['source_hash']
        
        # Return only source records with classification
        result = merged[merged['_merge'].isin(['left_only', 'both'])].copy()
        
        return result
    
    def _method2_hash_comparison_details(self, changes_df: pd.DataFrame) -> pd.DataFrame:
        """
        Method 2: Hash Comparison with detailed change analysis
        Best for: Quick detection and change field identification
        """
        
        # For CHANGED records, identify which fields changed
        changed_records = changes_df[changes_df['change_type'] == 'CHANGED'].copy()
        
        if not changed_records.empty:
            changed_records['changed_fields'] = changed_records.apply(self._identify_changed_fields, axis=1)
          # Update the main DataFrame
        if not changed_records.empty:
            changes_df.loc[changes_df['change_type'] == 'CHANGED', 'changed_fields'] = changed_records['changed_fields']
        
        return changes_df
    
    def _generate_row_hash(self, row) -> str:
        """Generate hash for a row using ALL columns"""
        
        # Get ALL column names except excluded ones
        all_columns = [col for col in row.index if col not in self.exclude_from_hash]
        
        # Create hash string
        hash_components = []
        for field in sorted(all_columns):  # Sort for consistency
            value = str(row.get(field, '')) if pd.notna(row.get(field, '')) else ''
            hash_components.append(value)
        
        hash_string = '|'.join(hash_components)
        
        # Generate SHA256 hash
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def _identify_changed_fields(self, row) -> str:
        """Identify which specific fields changed (placeholder for now)"""
        
        # This would require field-by-field comparison with target data
        # For now, just return that hash changed
        return "hash_changed"
        
    def calculate_row_hash(self, row_data):
        """Calculate SHA256 hash for ALL columns in a data row"""
        try:
            # Get ALL column names except excluded ones
            all_columns = [col for col in row_data.index if col not in self.exclude_from_hash]
            
            # Create concatenated string of ALL field values
            hash_values = []
            for field in sorted(all_columns):  # Sort for consistency
                value = row_data.get(field, '')
                # Convert to string and handle nulls
                if pd.isna(value) or value is None:
                    hash_values.append('')
                else:
                    hash_values.append(str(value).strip())
            
            # Create hash string
            hash_string = '|'.join(hash_values)
            
            # Generate SHA256 hash
            hash_result = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
            
            # Log first few for debugging
            if len(hash_values) > 0:
                self.logger.debug(f"Hashing {len(all_columns)} columns: {hash_result[:12]}...")
            
            return hash_result
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for row: {e}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error calculating hash for row: {e}")
            return None
    
    def get_current_orders(self, customer_filter=None, limit=None):
        """Get current ORDERS_UNIFIED data with calculated hashes"""
        try:            # Build query - SELECT ALL columns since we're hashing entire rows
            sql = """
            SELECT *
            FROM dbo.ORDERS_UNIFIED
            WHERE 1=1
            """
            
            if customer_filter:
                sql += f" AND [CUSTOMER NAME] = '{customer_filter}'"
            
            if limit:
                sql = f"SELECT TOP {limit} * FROM ({sql}) subq"
                
            self.logger.info(f"Fetching current orders - Customer: {customer_filter}, Limit: {limit}")
            
            conn = db.get_connection(self.database)
            df = pd.read_sql(sql, conn)
            conn.close()
            
            # Calculate hashes
            df['row_hash'] = df.apply(self.calculate_row_hash, axis=1)
            
            self.logger.info(f"Retrieved {len(df)} current orders with hashes")
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting current orders: {e}")
            return pd.DataFrame()
    
    def get_previous_snapshot(self, customer_filter=None):
        """Get previous snapshot from staging table (if exists)"""
        try:
            sql = """
            SELECT 
                record_uuid,
                row_hash,
                [AAG ORDER NUMBER],
                [CUSTOMER NAME],
                [CUSTOMER STYLE],
                snapshot_date
            FROM dbo.ORDERS_UNIFIED_SNAPSHOT
            WHERE 1=1
            """
            
            if customer_filter:
                sql += f" AND [CUSTOMER NAME] = '{customer_filter}'"
                
            sql += " ORDER BY snapshot_date DESC"
            
            conn = db.get_connection(self.database)
            df = pd.read_sql(sql, conn)
            conn.close()
            
            self.logger.info(f"Retrieved {len(df)} previous snapshot records")
            return df
            
        except Exception as e:
            self.logger.warning(f"No previous snapshot found or error: {e}")
            return pd.DataFrame()
    
    def detect_changes_method1(self, current_df, previous_df):
        """Method 1: Outer Join with _merge indicator"""
        try:
            if previous_df.empty:
                # No previous data - all current records are new
                result = current_df.copy()
                result['change_type'] = 'new'
                result['_merge'] = 'left_only'
                return result
            
            # Perform outer join on record_uuid
            merged = pd.merge(
                current_df[['record_uuid', 'row_hash'] + self.key_fields],
                previous_df[['record_uuid', 'row_hash'] + self.key_fields],
                on='record_uuid',
                how='outer',
                indicator=True,
                suffixes=('_current', '_previous')
            )
            
            # Classify changes
            conditions = [
                merged['_merge'] == 'left_only',  # New records
                merged['_merge'] == 'right_only', # Deleted records  
                (merged['_merge'] == 'both') & (merged['row_hash_current'] != merged['row_hash_previous']), # Changed
                (merged['_merge'] == 'both') & (merged['row_hash_current'] == merged['row_hash_previous'])   # Unchanged
            ]
            
            choices = ['new', 'deleted', 'changed', 'unchanged']
            merged['change_type'] = pd.Series.map(pd.cut(range(len(conditions)), 
                                                       bins=len(conditions), 
                                                       labels=choices))
            
            # Use numpy.select for proper condition mapping
            import numpy as np
            merged['change_type'] = np.select(conditions, choices, default='unknown')
            
            self.logger.info(f"Method 1 Results: {merged['change_type'].value_counts().to_dict()}")
            return merged
            
        except Exception as e:
            self.logger.error(f"Error in detect_changes_method1: {e}")
            return pd.DataFrame()
    
    def detect_changes_method2(self, current_df, previous_df):
        """Method 2: Quick hash comparison"""
        try:
            if previous_df.empty:
                return {
                    'new_count': len(current_df),
                    'changed_count': 0,
                    'deleted_count': 0,
                    'unchanged_count': 0,
                    'total_changes': len(current_df)
                }
            
            # Get hash sets
            current_hashes = set(current_df['row_hash'].dropna())
            previous_hashes = set(previous_df['row_hash'].dropna())
            
            # Calculate differences
            new_hashes = current_hashes - previous_hashes
            deleted_hashes = previous_hashes - current_hashes
            unchanged_hashes = current_hashes & previous_hashes
            
            result = {
                'new_count': len(new_hashes),
                'changed_count': len(new_hashes),  # New hashes represent changes + new records
                'deleted_count': len(deleted_hashes),
                'unchanged_count': len(unchanged_hashes),
                'total_changes': len(new_hashes) + len(deleted_hashes)
            }
            
            self.logger.info(f"Method 2 Results: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in detect_changes_method2: {e}")
            return {}
    
    def run_change_detection(self, customer_filter=None, limit=None, method='both'):
        """Main entry point for change detection"""
        try:
            self.logger.info(f"Starting change detection - Method: {method}, Customer: {customer_filter}")
            
            # Get current data
            current_df = self.get_current_orders(customer_filter, limit)
            if current_df.empty:
                self.logger.warning("No current orders found")
                return {}
            
            # Get previous snapshot
            previous_df = self.get_previous_snapshot(customer_filter)
            
            results = {
                'current_count': len(current_df),
                'previous_count': len(previous_df),
                'timestamp': pd.Timestamp.now(),
                'customer_filter': customer_filter,
                'limit': limit
            }
            
            # Run selected method(s)
            if method in ['method1', 'both']:
                results['method1'] = self.detect_changes_method1(current_df, previous_df)
                
            if method in ['method2', 'both']:
                results['method2'] = self.detect_changes_method2(current_df, previous_df)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in run_change_detection: {e}")
            return {}
    
    def save_current_snapshot(self, customer_filter=None):
        """Save current state as snapshot for future comparison"""
        try:
            current_df = self.get_current_orders(customer_filter)
            if current_df.empty:
                self.logger.warning("No current orders to snapshot")
                return False
            
            # Add snapshot metadata
            current_df['snapshot_date'] = pd.Timestamp.now()
            current_df['customer_filter'] = customer_filter or 'ALL'
            
            # Save to snapshot table (create if doesn't exist)
            conn = db.get_connection(self.database)
            
            # Create snapshot table if needed
            create_sql = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ORDERS_UNIFIED_SNAPSHOT' AND xtype='U')
            BEGIN
                CREATE TABLE dbo.ORDERS_UNIFIED_SNAPSHOT (
                    record_uuid UNIQUEIDENTIFIER,
                    row_hash NVARCHAR(64),
                    [AAG ORDER NUMBER] NVARCHAR(255),
                    [CUSTOMER NAME] NVARCHAR(255),
                    [CUSTOMER STYLE] NVARCHAR(255),
                    snapshot_date DATETIME2,
                    customer_filter NVARCHAR(255)
                )
            END
            """
            
            cursor = conn.cursor()
            cursor.execute(create_sql)
            conn.commit()
            
            # Clear previous snapshots for this customer
            if customer_filter:
                cursor.execute("DELETE FROM dbo.ORDERS_UNIFIED_SNAPSHOT WHERE customer_filter = ?", customer_filter)
            else:
                cursor.execute("DELETE FROM dbo.ORDERS_UNIFIED_SNAPSHOT WHERE customer_filter = 'ALL'")
            
            # Insert new snapshot
            snapshot_cols = ['record_uuid', 'row_hash', 'AAG ORDER NUMBER', 'CUSTOMER NAME', 'CUSTOMER STYLE', 'snapshot_date', 'customer_filter']
            current_df[snapshot_cols].to_sql('ORDERS_UNIFIED_SNAPSHOT', conn, if_exists='append', index=False, method='multi')
            
            conn.close()
            
            self.logger.info(f"Saved snapshot with {len(current_df)} records")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving snapshot: {e}")
            return False


def main():
    """Test the change detector"""
    detector = ChangeDetector()
    
    # Test with ACTIVELY BLACK customer (limit 5 for testing)
    results = detector.run_change_detection(
        customer_filter='ACTIVELY BLACK',
        limit=5,
        method='both'
    )
    
    print("Change Detection Results:")
    print("=" * 50)
    for key, value in results.items():
        if key in ['method1', 'method2']:
            continue
        print(f"{key}: {value}")
    
    if 'method1' in results:
        method1 = results['method1']
        if not method1.empty:
            print(f"\nMethod 1 - Change Types:")
            print(method1['change_type'].value_counts())
    
    if 'method2' in results:
        print(f"\nMethod 2 - Summary:")
        print(results['method2'])


if __name__ == "__main__":
    main()
