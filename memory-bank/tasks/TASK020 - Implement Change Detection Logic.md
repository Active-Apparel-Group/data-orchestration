# TASK020 - Implement Change Detection Logic

**Status:** Pending  
**Added:** 2025-07-23  
**Updated:** 2025-07-23  
**Priority:** High - Required for production ORDER_LIST merges

## Original Request
Implement comprehensive change detection logic to manage order list changes properly, focusing on orders with `action_type = 'UPDATE'` and handling special cases like cancelled orders. This builds on the successful architecture from Task 19 (DELTA elimination) and ensures production-ready merge operations.

## Thought Process
With Task 19 successfully eliminating DELTA tables and implementing direct main table operations, we now need robust change detection to handle:

1. **UPDATE Orders**: When existing orders change, we need to:
   - Update header information in ORDER_LIST_V2
   - Update/recreate ORDER_LIST_LINES with new quantities
   - Properly sync all changes to Monday.com

2. **Cancelled Orders**: When orders are cancelled (`ORDER_TYPE = 'CANCELLED'`):
   - Header remains in ORDER_LIST_V2 with updated status
   - **All ORDER_LIST_LINES for that record_uuid must be updated**:
     - Set all quantities to 0
     - Update `sync_status` and `action_type` to reflect cancellation
     - Ensure Monday.com sync updates all size quantities to 0

3. **Success Metrics**: Production merges must account for cancelled orders correctly:
   - Active orders: Should have ORDER_LIST_LINES (measured for sync consistency)
   - Cancelled orders: No new lines expected (excluded from consistency checks)
   - Overall success measured like Task 19.14.3: 100% for active orders only

## Reference Implementation
Based on successful test implementations:
- **tests/debug/check_zero_qty_cancelled_orders.py**: Demonstrates proper cancelled order detection
- **tests/sync-order-list-monday/integration/test_task19_data_merge_integration.py**: Shows correct validation logic that excludes cancelled orders from sync consistency checks

## Implementation Plan

### Phase 1: Change Detection Framework
- 20.1 Implement order change detection logic (INSERT vs UPDATE vs CANCELLED)
- 20.2 Create change impact analysis (header-only vs header+lines changes)
- 20.3 Build validation framework for change detection accuracy

### Phase 2: UPDATE Order Handling
- 20.4 Implement header update logic for changed orders
- 20.5 Implement line regeneration for quantity changes
- 20.6 Ensure sync state inheritance for UPDATE operations

### Phase 3: Cancelled Order Handling ⚠️ CRITICAL
- 20.7 Implement cancelled order detection (ORDER_TYPE = 'CANCELLED')
- 20.8 **CRITICAL**: Update all existing ORDER_LIST_LINES for cancelled orders:
  - Find all lines with matching record_uuid
  - Set all size quantities to 0
  - Update sync_status and action_type for Monday.com sync
- 20.9 Ensure cancelled order exclusion from success metrics
- 20.10 Validate cancelled order Monday.com sync (all quantities → 0)

### Phase 4: Production Merge Integration
- 20.11 Integrate change detection with merge_orchestrator.py
- 20.12 Update merge templates to handle UPDATE scenarios properly
- 20.13 Ensure production batch logging accounts for cancelled orders

### Phase 5: Testing & Validation
- 20.14 Create comprehensive test suite for change detection scenarios
- 20.15 Validate UPDATE order scenarios end-to-end
- 20.16 Validate cancelled order scenarios (header + all lines updated)
- 20.17 Performance testing with mixed INSERT/UPDATE/CANCELLED batches

## Definition of Done
- ✅ Change detection accurately identifies INSERT, UPDATE, and CANCELLED orders
- ✅ UPDATE orders properly regenerate ORDER_LIST_LINES with new quantities
- ✅ CANCELLED orders update all existing ORDER_LIST_LINES to quantity 0
- ✅ Success metrics properly account for cancelled orders (exclude from consistency)
- ✅ Production merge operations handle all change types correctly
- ✅ Monday.com sync properly handles cancelled order updates (all sizes → 0)
- ✅ Comprehensive test coverage for all change scenarios

## Progress Tracking

**Overall Status:** Not Started - 0%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 20.1 | Order change detection logic | Not Started | 2025-07-23 | Identify INSERT vs UPDATE vs CANCELLED |
| 20.2 | Change impact analysis | Not Started | 2025-07-23 | Determine header-only vs header+lines changes |
| 20.3 | Build validation framework | Not Started | 2025-07-23 | Accuracy testing for change detection |
| 20.4 | Header update logic | Not Started | 2025-07-23 | Handle changed order headers |
| 20.5 | Line regeneration logic | Not Started | 2025-07-23 | Recreate ORDER_LIST_LINES for quantity changes |
| 20.6 | Sync state inheritance for UPDATEs | Not Started | 2025-07-23 | Ensure proper sync tracking |
| 20.7 | Cancelled order detection | Not Started | 2025-07-23 | Identify ORDER_TYPE = 'CANCELLED' |
| 20.8 | **CRITICAL**: Update existing lines for cancelled orders | Not Started | 2025-07-23 | Set all quantities to 0, update sync status for Monday.com |
| 20.9 | Exclude cancelled orders from metrics | Not Started | 2025-07-23 | Success rate calculation like Task 19.14.3 |
| 20.10 | Cancelled order Monday.com sync validation | Not Started | 2025-07-23 | Ensure all size quantities sync to 0 |
| 20.11 | Integrate with merge orchestrator | Not Started | 2025-07-23 | Production merge compatibility |
| 20.12 | Update merge templates | Not Started | 2025-07-23 | Handle UPDATE scenarios |
| 20.13 | Production batch logging | Not Started | 2025-07-23 | Account for cancelled orders in success metrics |
| 20.14 | Comprehensive test suite | Not Started | 2025-07-23 | All change detection scenarios |
| 20.15 | UPDATE order validation | Not Started | 2025-07-23 | End-to-end testing |
| 20.16 | Cancelled order validation | Not Started | 2025-07-23 | Header + all lines updated correctly |
| 20.17 | Performance testing | Not Started | 2025-07-23 | Mixed change type batches |

## Success Criteria Reference
Based on Task 19.14.3 successful implementation:
- **Active orders**: Must have ORDER_LIST_LINES with proper sync consistency (measured)
- **Cancelled orders**: No new lines expected, excluded from consistency checks
- **Overall success**: 100% for active orders, cancelled orders handled correctly
- **Logging pattern**: Clear metrics like "53/53 action_type, 53/53 sync_state" for active orders

## Technical Notes
- **action_type = 'UPDATE'**: Confirmed as the indicator for changed orders
- **Cancelled order impact**: Must update ALL existing ORDER_LIST_LINES for the record_uuid
- **Success measurement**: Follow Task 19.14.3 pattern - exclude cancelled orders from sync consistency checks
- **Reference tests**: Use existing test patterns for validation logic
