# 📁 sync_engine.py - ORCHESTRATION SEQUENCE

## Current Order of Operations

```
📁 sync_engine.py - ORCHESTRATION SEQUENCE
├── 1️⃣ run_sync()
│   ├── _get_pending_headers() → Query ORDER_LIST_DELTA
│   ├── _group_by_customer_and_uuid() → Batch by customer/record_uuid
│   └── For each customer batch:
│       ├── 2️⃣ _create_groups_first() → Create groups BEFORE items
│       │   ├── Extract unique GroupMonday values
│       │   ├── monday_client.execute('create_groups', groups, dry_run)
│       │   └── ⏳ WAIT for group creation to complete
│       ├── 3️⃣ _create_items_with_groups() → Create items with group_ids
│       │   ├── Use created group_ids in items
│       │   └── monday_client.execute('create_items', headers, dry_run)
│       └── 4️⃣ _create_subitems() → Create subitems with parent_item_ids
│           ├── _get_pending_lines() → Query ORDER_LIST_LINES_DELTA
│           └── monday_client.execute('create_subitems', lines, dry_run)
```

## Critical Requirements

### 🔄 Sequencing Dependencies
1. **Groups MUST be created FIRST** - Items require valid group_id references
2. **Items MUST exist before Subitems** - Subitems require parent_item_id
3. **Blocking Operations** - Each step must complete before next step begins

### 📊 DELTA Table Architecture
- **Headers**: `ORDER_LIST_DELTA` (sync_state: NEW → PENDING → SYNCED)
- **Lines**: `ORDER_LIST_LINES_DELTA` (sync_state: PENDING → SYNCED)
- **Sync State Propagation**: DELTA tables → Main tables (ORDER_LIST, ORDER_LIST_LINES)

### 🔗 record_uuid Consistency
- **Batch Processing**: Group by customer + record_uuid for atomic operations
- **Parent-Child Linking**: Lines reference headers via record_uuid
- **Sync State Updates**: Atomic updates across related records

### ⚠️ Implementation Gaps (Current Status)
- [ ] `_group_by_customer_and_uuid()` - Not implemented
- [ ] `_create_groups_first()` - Not implemented
- [ ] Group creation waiting/blocking logic
- [ ] record_uuid-based batch processing
- [ ] Atomic sync state updates across DELTA → Main tables

## Next Implementation Steps

1. **Phase 1**: Implement `_group_by_customer_and_uuid()` batching
2. **Phase 2**: Add `_create_groups_first()` with blocking wait
3. **Phase 3**: Update `_create_items_with_groups()` to use group_ids
4. **Phase 4**: Implement atomic record_uuid-based sync state updates

---

**Architecture Note**: This sequence ensures Monday.com API dependencies are respected while maintaining data consistency across DELTA and main tables.
