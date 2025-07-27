"""
Test the actual MERGE execution to see what's failing
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db

print('🔍 Testing MERGE execution with minimal columns...')

# Simplified MERGE with just a few columns to isolate the issue
test_merge_sql = '''
DECLARE @StartTime DATETIME2 = GETUTCDATE();
DECLARE @ProcessedCount INT = 0;

BEGIN TRY
    BEGIN TRANSACTION;
    
    MERGE dbo.ORDER_LIST_V2 AS target
    USING (
        SELECT 
            record_uuid,
            [AAG ORDER NUMBER],
            [PO NUMBER],
            [CUSTOMER NAME],
            row_hash,
            sync_state,
            created_at,
            updated_at
        FROM dbo.swp_ORDER_LIST_V2
        WHERE sync_state = 'NEW'
        AND [AAG ORDER NUMBER] IS NOT NULL
    ) AS source
    ON target.[AAG ORDER NUMBER] = source.[AAG ORDER NUMBER]
    
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            record_uuid,
            [AAG ORDER NUMBER],
            [PO NUMBER],
            [CUSTOMER NAME],
            row_hash,
            action_type,
            sync_state,
            sync_attempted_at,
            created_at,
            updated_at
        )
        VALUES (
            source.record_uuid,
            source.[AAG ORDER NUMBER],
            source.[PO NUMBER],
            source.[CUSTOMER NAME],
            source.row_hash,
            'INSERT',
            'PENDING',
            GETUTCDATE(),
            GETUTCDATE(),
            GETUTCDATE()
        )
    
    WHEN MATCHED AND (target.row_hash IS NULL OR target.row_hash <> source.row_hash) THEN
        UPDATE SET
            [PO NUMBER] = source.[PO NUMBER],
            [CUSTOMER NAME] = source.[CUSTOMER NAME],
            row_hash = source.row_hash,
            action_type = 'UPDATE',
            sync_state = 'PENDING',
            sync_attempted_at = GETUTCDATE(),
            updated_at = GETUTCDATE();
    
    SET @ProcessedCount = @@ROWCOUNT;
    
    COMMIT TRANSACTION;
    
    SELECT 
        @ProcessedCount AS records_processed,
        'SUCCESS' AS status,
        DATEDIFF(SECOND, @StartTime, GETUTCDATE()) AS execution_seconds;
        
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    
    SELECT
        ERROR_NUMBER() AS error_number,
        ERROR_MESSAGE() AS error_message,
        'FAILED' AS status;
END CATCH
'''

try:
    conn = db.get_connection('orders')
    result = pd.read_sql_query(test_merge_sql, conn)
    
    print(f'📊 MERGE Result:')
    for _, row in result.iterrows():
        if 'status' in row and row['status'] == 'SUCCESS':
            print(f'  ✅ Records processed: {row["records_processed"]}')
            print(f'  ⏱️ Execution time: {row["execution_seconds"]} seconds')
        else:
            print(f'  ❌ Error {row["error_number"]}: {row["error_message"]}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ Error executing MERGE: {e}')
    import traceback
    traceback.print_exc()
