"""
Hybrid Snapshot Manager - ORDERS_UNIFIED_SNAPSHOT
=================================================

Purpose: Manages hybrid snapshot storage approach:
- Primary: SQL Server table for fast queries (existing change_detector.py compatibility)  
- Archive: Parquet files in Kestra PostgreSQL for long-term storage

Architecture:
- SQL Server: dbo.ORDERS_UNIFIED_SNAPSHOT (fast hash comparisons)
- Kestra PostgreSQL: snapshot_archive table with BYTEA Parquet storage

Usage:
    from utils.hybrid_snapshot_manager import HybridSnapshotManager
    
    manager = HybridSnapshotManager()
    
    # Save snapshot (both SQL Server + Parquet archive)
    archive_id = manager.save_snapshot(
        df=orders_df, 
        customer_filter='greyson',
        tags={'pipeline': 'orders_v3', 'run_id': 'abc123'}
    )
    
    # Load from archive for analysis
    historical_df = manager.load_from_archive(archive_id)
    
    # Compare snapshots
    changes = manager.compare_with_archive(current_df, days_back=7)
"""

import sys
from pathlib import Path
import hashlib
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

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

import db_helper as db
import logger_helper

class HybridSnapshotManager:
    """
    Manages hybrid snapshot storage for ORDERS_UNIFIED change detection
    
    Features:
    - Primary storage in SQL Server for fast queries
    - Archive storage in Kestra PostgreSQL as compressed Parquet
    - Automatic cleanup and retention management
    - Schema validation and integrity checks
    """
    
    def __init__(self):
        self.logger = logger_helper.get_logger(__name__)
        self.sql_server_db = "ORDERS"
        self.postgres_connection = self._get_postgres_connection()
        
    def _get_postgres_connection(self):
        """Get connection to Kestra PostgreSQL"""
        # TODO: Add PostgreSQL connection to db_helper.py
        # For now, placeholder for the connection string
        # This would connect to the Kestra PostgreSQL from docker-compose.yml
        try:
            import psycopg2
            return psycopg2.connect(
                host="localhost",  # From docker-compose.yml
                port=5432,
                database="kestra",
                user="kestra", 
                password="k3str4"
            )
        except ImportError:
            self.logger.warning("psycopg2 not installed - PostgreSQL archive disabled")
            return None
        except Exception as e:
            self.logger.warning(f"Could not connect to Kestra PostgreSQL: {e}")
            return None
    
    def save_snapshot(
        self, 
        df: pd.DataFrame, 
        customer_filter: str = None,
        batch_id: str = None,
        tags: Dict[str, Any] = None
    ) -> Optional[int]:
        """
        Save snapshot to both SQL Server and Parquet archive
        
        Args:
            df: DataFrame to snapshot
            customer_filter: Customer filter used (for partitioning)
            batch_id: Optional batch identifier
            tags: Optional metadata tags for archive
            
        Returns:
            Archive ID if successful, None if failed
        """
        try:
            # Step 1: Save to SQL Server (existing change_detector.py logic)
            sql_success = self._save_to_sql_server(df, customer_filter, batch_id)
            if not sql_success:
                self.logger.error("Failed to save to SQL Server")
                return None
            
            # Step 2: Save to Parquet archive (new functionality)
            if self.postgres_connection:
                archive_id = self._save_to_parquet_archive(df, customer_filter, batch_id, tags)
                
                # Step 3: Update SQL Server with archive reference
                if archive_id:
                    self._update_sql_server_archive_reference(batch_id, archive_id)
                
                return archive_id
            else:
                self.logger.info("PostgreSQL archive not available - SQL Server snapshot only")
                return None
                
        except Exception as e:
            self.logger.error(f"Error saving hybrid snapshot: {e}")
            return None
    
    def _save_to_sql_server(self, df: pd.DataFrame, customer_filter: str, batch_id: str) -> bool:
        """Save snapshot to SQL Server table (existing change_detector.py logic)"""
        try:
            # Generate hash and UUID for each row
            df_snapshot = df.copy()
            
            # Create row hashes (same logic as change_detector.py)
            key_columns = ['AAG ORDER NUMBER', 'CUSTOMER NAME', 'CUSTOMER STYLE']
            df_snapshot['row_hash'] = df_snapshot[key_columns].apply(
                lambda row: hashlib.sha256('|'.join(str(row[col]) for col in key_columns).encode()).hexdigest(),
                axis=1
            )
            df_snapshot['record_uuid'] = [str(uuid.uuid4()) for _ in range(len(df))]
            df_snapshot['snapshot_date'] = datetime.now()
            df_snapshot['customer_filter'] = customer_filter or 'ALL'
            df_snapshot['batch_id'] = batch_id
            df_snapshot['records_count'] = len(df)
            
            # Save to SQL Server
            with db.get_connection(self.sql_server_db) as conn:
                # Clear previous snapshots for this customer
                cursor = conn.cursor()
                if customer_filter:
                    cursor.execute(
                        "DELETE FROM dbo.ORDERS_UNIFIED_SNAPSHOT WHERE customer_filter = ?", 
                        customer_filter
                    )
                else:
                    cursor.execute(
                        "DELETE FROM dbo.ORDERS_UNIFIED_SNAPSHOT WHERE customer_filter = 'ALL'"
                    )
                
                # Insert new snapshot
                snapshot_cols = [
                    'record_uuid', 'row_hash', 'AAG ORDER NUMBER', 'CUSTOMER NAME', 
                    'CUSTOMER STYLE', 'snapshot_date', 'customer_filter', 'batch_id', 'records_count'
                ]
                df_snapshot[snapshot_cols].to_sql(
                    'ORDERS_UNIFIED_SNAPSHOT', 
                    conn, 
                    if_exists='append', 
                    index=False, 
                    method='multi'
                )
                
                conn.commit()
                
            self.logger.info(f"Saved {len(df_snapshot)} records to SQL Server snapshot")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving to SQL Server: {e}")
            return False
    
    def _save_to_parquet_archive(
        self, 
        df: pd.DataFrame, 
        customer_filter: str, 
        batch_id: str, 
        tags: Dict[str, Any]
    ) -> Optional[int]:
        """Save snapshot to Parquet archive in PostgreSQL"""
        try:
            # Convert DataFrame to Parquet bytes
            table = pa.Table.from_pandas(df)
            parquet_buffer = io.BytesIO()
            pq.write_table(table, parquet_buffer, compression='snappy')
            parquet_bytes = parquet_buffer.getvalue()
            
            # Calculate metadata
            original_size = df.memory_usage(deep=True).sum()
            compressed_size = len(parquet_bytes)
            compression_ratio = compressed_size / original_size if original_size > 0 else 0
            
            # Generate schema hash for validation
            schema_string = '|'.join([f"{col}:{str(dtype)}" for col, dtype in df.dtypes.items()])
            schema_hash = hashlib.sha256(schema_string.encode()).hexdigest()
            
            # File checksum
            file_checksum = hashlib.md5(parquet_bytes).hexdigest()
            
            # Insert into PostgreSQL archive
            with self.postgres_connection.cursor() as cursor:
                insert_sql = """
                INSERT INTO snapshot_archive (
                    snapshot_date, customer_filter, batch_id, records_count,
                    source_database, source_table, parquet_data, parquet_size,
                    compression_ratio, original_columns, schema_hash, 
                    file_checksum, tags
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING archive_id;
                """
                
                cursor.execute(insert_sql, (
                    datetime.now(),
                    customer_filter or 'ALL',
                    batch_id,
                    len(df),
                    self.sql_server_db,
                    'ORDERS_UNIFIED',
                    parquet_bytes,
                    compressed_size,
                    compression_ratio,
                    len(df.columns),
                    schema_hash,
                    file_checksum,
                    json.dumps(tags) if tags else None
                ))
                
                archive_id = cursor.fetchone()[0]
                self.postgres_connection.commit()
                
                self.logger.info(
                    f"Saved Parquet archive {archive_id}: {len(df)} records, "
                    f"{compressed_size/1024/1024:.2f}MB "
                    f"(compression: {compression_ratio:.2f})"
                )
                
                return archive_id
                
        except Exception as e:
            self.logger.error(f"Error saving to Parquet archive: {e}")
            return None
    
    def _update_sql_server_archive_reference(self, batch_id: str, archive_id: int):
        """Update SQL Server records with archive reference"""
        try:
            with db.get_connection(self.sql_server_db) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE dbo.ORDERS_UNIFIED_SNAPSHOT SET parquet_archive_id = ? WHERE batch_id = ?",
                    archive_id, batch_id
                )
                conn.commit()
                
                self.logger.debug(f"Updated SQL Server records with archive_id {archive_id}")
                
        except Exception as e:
            self.logger.warning(f"Could not update archive reference: {e}")
    
    def load_from_archive(self, archive_id: int) -> Optional[pd.DataFrame]:
        """Load snapshot from Parquet archive"""
        try:
            if not self.postgres_connection:
                self.logger.error("PostgreSQL connection not available")
                return None
            
            with self.postgres_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT parquet_data, schema_hash, file_checksum FROM snapshot_archive WHERE archive_id = %s",
                    (archive_id,)
                )
                result = cursor.fetchone()
                
                if not result:
                    self.logger.error(f"Archive {archive_id} not found")
                    return None
                
                parquet_bytes, schema_hash, expected_checksum = result
                
                # Validate checksum
                actual_checksum = hashlib.md5(parquet_bytes).hexdigest()
                if actual_checksum != expected_checksum:
                    self.logger.error(f"Checksum mismatch for archive {archive_id}")
                    return None
                
                # Load Parquet data
                parquet_buffer = io.BytesIO(parquet_bytes)
                table = pq.read_table(parquet_buffer)
                df = table.to_pandas()
                
                self.logger.info(f"Loaded {len(df)} records from archive {archive_id}")
                return df
                
        except Exception as e:
            self.logger.error(f"Error loading from archive: {e}")
            return None
    
    def get_archive_statistics(self, customer_filter: str = None, days_back: int = 30) -> pd.DataFrame:
        """Get archive storage statistics"""
        try:
            if not self.postgres_connection:
                return pd.DataFrame()
            
            with self.postgres_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM get_archive_statistics(%s, %s)",
                    (customer_filter, days_back)
                )
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            self.logger.error(f"Error getting archive statistics: {e}")
            return pd.DataFrame()
    
    def cleanup_old_archives(self, keep_days: int = 90, dry_run: bool = True) -> pd.DataFrame:
        """Cleanup old archive files"""
        try:
            if not self.postgres_connection:
                return pd.DataFrame()
            
            with self.postgres_connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM cleanup_old_archives(%s, %s)",
                    (keep_days, dry_run)
                )
                
                columns = [desc[0] for desc in cursor.description]
                data = cursor.fetchall()
                
                return pd.DataFrame(data, columns=columns)
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return pd.DataFrame()
