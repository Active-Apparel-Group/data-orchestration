# Customer Orders Production Readiness Plan

## 🚦 Vision Flow When Complete

```
ORDERS_UNIFIED ✅
   │
   ├─► STG_MON_CustMasterSchedule ✅           ──► CreateCustItem.graphql 🔧      ──► Monday item 🔧
   │
   └─► STG_MON_CustMasterSchedule_Subitems ⏳  ──► CreateCustSubitem.graphql ⏳  ──► Monday sub-item ⏳
```

**Legend:**
- ✅ = Complete and operational
- 🔧 = Needs GraphQL integration
- ⏳ = Not yet implemented

## 🔗 How the Pieces Connect

```
ORDERS_UNIFIED
   │ (YAML-driven transform)      customer_mapper.py
   ▼
DataFrame (columns == target_field names)
   │ (bulk insert)                staging_processor.py
   ▼
STG_MON_CustMasterSchedule                    ← YAML not touched here
   │ (select + YAML second pass)  customer_batch_processor.py
   ▼
JSON column_values string
   │ (GraphQL)                    monday_api_adapter.py
   ▼
Monday board item
```

## 📑 Code Path - Order of Operations

| Step | File / Function | Description | Status |
|------|----------------|-------------|---------|
| 1 | `customer_mapper.py` – `load_mapping_config()` / `transform_orders_batch()` | YAML-driven transform | ✅ Implemented |
| 2 | `staging_processor.py` – `insert_orders_to_staging()` | Fast bulk insert | ✅ Implemented |
| 3 | `customer_batch_processor.py` – `load_new_orders_to_staging()` | Orchestrates Phases 1-2 | ✅ Implemented |
| 4 | `staging_processor.py` – `get_pending_staging_orders()` | Pull PENDING rows | ✅ Implemented |
| 5 | `customer_batch_processor.py` – `get_monday_column_values_for_staged_order()` | Build {column_id: value} | 🔧 Needs YAML integration |
| 6 | `monday_api_adapter.py` – `_safe_json()` + `create_item()` | JSON stringify & GraphQL | 🔧 Needs GraphQL |

## 🎯 Current State Assessment

### ✅ What's Working Well
1. **Core Pipeline Architecture** - Staging-centric approach is solid
2. **Database Operations** - ORDERS_UNIFIED → Staging flow operational
3. **Batch Processing** - Good separation of concerns
4. **YAML Mapping File** - Comprehensive mapping exists

### 🔧 Critical Gaps

#### 1. YAML Mapping Integration (Priority: CRITICAL)
- **Issue**: `orders_unified_monday_mapping.yaml` exists but not used in workflow
- **Impact**: Computed fields (Title, CUSTOMER) not populated
- **Fix**: Integrate YAML loading in `customer_mapper.py`

#### 2. GraphQL Integration (Priority: CRITICAL)
- **Issue**: Direct API calls instead of GraphQL mutations
- **Impact**: Limited to 4 columns, not following best practices
- **Fix**: Implement GraphQL templates from `sql/graphql/mutations/`

#### 3. Subitem Processing (Priority: HIGH)
- **Issue**: No subitem transformation or API calls
- **Impact**: Size-level data not synchronized
- **Fix**: Implement subitem pipeline branch

## 🚀 Production Readiness Milestones

### Milestone 1: YAML Integration (Day 1)
**Goal**: Fully integrate mapping file into transformation pipeline

| Task | File | Description | Success Criteria |
|------|------|-------------|------------------|
| 1.1 | `customer_mapper.py` | Load `orders_unified_monday_mapping.yaml` | Mapping config loaded at startup |
| 1.2 | `customer_mapper.py` | Apply exact_matches transformations | 37 fields mapped correctly |
| 1.3 | `customer_mapper.py` | Apply mapped_fields (CUSTOMER, STYLE) | Customer normalization working |
| 1.4 | `customer_mapper.py` | Apply computed_fields (Title) | Title = STYLE + COLOR + AAG_ORDER |
| 1.5 | `staging_processor.py` | Ensure all fields inserted to staging | All target fields populated |

### Milestone 2: GraphQL Implementation (Day 2)
**Goal**: Replace direct API calls with GraphQL mutations

| Task | File | Description | Success Criteria |
|------|------|-------------|------------------|
| 2.1 | `monday_api_adapter.py` | Load GraphQL templates | Templates loaded from `sql/graphql/` |
| 2.2 | `monday_api_adapter.py` | Implement `execute_graphql()` method | GraphQL queries execute successfully |
| 2.3 | `monday_api_adapter.py` | Update `create_item()` to use GraphQL | Items created via `create-master-item.graphql` |
| 2.4 | `customer_batch_processor.py` | Use YAML column IDs in payload | All 51 mapped fields sent to API |
| 2.5 | Integration test | Test full pipeline with GraphQL | GREYSON PO 4755 created with all fields |

### Milestone 3: Subitem Pipeline (Days 3-4)
**Goal**: Implement size-level subitem processing

| Task | File | Description | Success Criteria |
|------|------|-------------|------------------|
| 3.1 | `orders_unified_monday_mapping.yaml` | Add `subitem_fields` section | Size columns mapped to Monday IDs |
| 3.2 | `customer_mapper.py` | Add `transform_orders_to_subitems()` | Wide → tall transformation |
| 3.3 | `staging_processor.py` | Add `insert_subitems_to_staging()` | Bulk insert to subitems table |
| 3.4 | `monday_api_adapter.py` | Add `create_subitem()` method | Use `create-subitem.graphql` |
| 3.5 | `customer_batch_processor.py` | Add subitem processing flow | Process after master items |
| 3.6 | End-to-end test | Test with multi-size order | 264 subitems for GREYSON PO 4755 |

### Milestone 4: Error Handling & Resilience (Day 5)
**Goal**: Production-grade error recovery

| Task | File | Description | Success Criteria |
|------|------|-------------|------------------|
| 4.1 | `utils/retry_helper.py` | Create retry decorator | Exponential backoff for 429 errors |
| 4.2 | `monday_api_adapter.py` | Add retry logic to API calls | Automatic retry on transient failures |
| 4.3 | `error_handler.py` | Implement error categorization | Errors logged to ERR_ tables |
| 4.4 | `customer_batch_processor.py` | Add batch recovery | Resume from last successful record |
| 4.5 | Stress test | Test with rate limiting | 95%+ success rate under load |

### Milestone 5: Production Hardening (Days 6-7)
**Goal**: Monitoring, documentation, and deployment

| Task | File | Description | Success Criteria |
|------|------|-------------|------------------|
| 5.1 | `monitoring/` | Create monitoring dashboards | Real-time batch status visibility |
| 5.2 | `docs/RUNBOOK.md` | Operations runbook | Troubleshooting procedures documented |
| 5.3 | Performance tuning | Optimize batch sizes | <5 seconds per order processing |
| 5.4 | `workflows/` | Update Kestra workflows | Scheduled execution configured |
| 5.5 | Production validation | Full production test | 1000+ orders processed successfully |

## 📊 Success Metrics

### Phase Completion Criteria

| Phase | Metric | Target | Current |
|-------|--------|--------|---------|
| YAML Integration | Fields mapped | 51 | 4 |
| GraphQL | API success rate | 95% | N/A |
| Subitems | Size records created | 264 (GREYSON) | 0 |
| Error Handling | Retry success | 95% | 0% |
| Production | Orders/hour | 1000+ | Unknown |

### Overall Production Readiness

```
Current State:  [████░░░░░░] 40% - Basic pipeline working
Target State:   [██████████] 100% - Full production ready

Missing Components:
- [ ] YAML mapping integration
- [ ] GraphQL implementation  
- [ ] Subitem processing
- [ ] Error recovery
- [ ] Monitoring
```

## 🎯 Immediate Next Steps

1. **TODAY**: 
   - Review and validate `orders_unified_monday_mapping.yaml`
   - Update `customer_mapper.py` to load mapping file
   - Test Title computation with GREYSON data

2. **TOMORROW**:
   - Review GraphQL templates in `sql/graphql/mutations/`
   - Implement GraphQL execution in `monday_api_adapter.py`
   - Test with full field mapping

3. **THIS WEEK**:
   - Complete subitem pipeline implementation
   - Add comprehensive error handling
   - Run full production validation

## 📚 Reference Implementation

The handover documentation shows the intended patterns:

- **YAML Loading**: See `order_mapping.py` pattern in handover
- **GraphQL Usage**: Templates exist in `sql/graphql/mutations/`
- **Subitem Creation**: Reference `create-subitem.graphql`
- **Error Handling**: Pattern shown in `error_handler.py` stub

## 🚨 Risk Mitigation

1. **Data Loss**: Implement idempotent operations
2. **API Limits**: Add rate limiting and backoff
3. **Mapping Errors**: Validate all transformations
4. **Production Issues**: Comprehensive rollback procedures

---

**Document Version**: 1.0  
**Created**: 2025-06-25  
**Status**: Active Production Readiness Plan