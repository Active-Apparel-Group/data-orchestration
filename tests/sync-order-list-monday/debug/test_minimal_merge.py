"""
Test the minimal merge statement directly to see what SQL Server reports
"""
import sys
from pathlib import Path
import pandas as pd

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipelines.utils import db

print('🔍 Testing minimal MERGE statement...')

# Test a very simple merge with just a few columns
minimal_merge = '''
BEGIN TRANSACTION;

DECLARE @ProcessedCount INT = 0;

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
    );

SET @ProcessedCount = @@ROWCOUNT;

PRINT 'Minimal Merge Test Results:';
PRINT 'Records Processed: ' + CAST(@ProcessedCount AS VARCHAR(10));

-- Check what was actually inserted
SELECT 
    COUNT(*) as total_inserted,
    COUNT(CASE WHEN action_type = 'INSERT' THEN 1 END) as insert_actions,
    COUNT(CASE WHEN sync_state = 'PENDING' THEN 1 END) as pending_state
FROM dbo.ORDER_LIST_V2;

ROLLBACK TRANSACTION;  -- Rollback for testing
'''

try:
    print('📊 Executing minimal merge...')
    conn = db.get_connection('orders')
    cursor = conn.cursor()
    
    # Execute the merge and capture all results
    cursor.execute(minimal_merge)
    
    # Get all result sets
    results = []
    while True:
        try:
            # Try to get next result set  
            rows = cursor.fetchall()
            if rows:
                results.append(rows)
            if not cursor.nextset():
                break
        except:
            break
            
    print('📊 Merge execution results:')
    for i, result_set in enumerate(results):
        print(f'Result Set {i+1}: {len(result_set)} rows')
        for row in result_set:
            print(f'  {row}')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'❌ Error executing minimal merge: {e}')
    import traceback
    traceback.print_exc()
