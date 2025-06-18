# Master Data Mapping System Implementation Plan

## Overview
Create a centralized data mapping system in `utils/` while preserving all existing mapping files in `docs/mapping/` to ensure zero disruption to current dependencies.

## Implementation Strategy

### Phase 1: Foundation Setup (No Disruption)
**Goal**: Create new master system without touching existing files

**Tasks**:
1. Create `utils/data_mapping.yaml` - Master mapping registry
2. Create `utils/mapping_helper.py` - Utility functions for accessing mappings
3. Copy (don't move) all content from existing mapping files
4. Consolidate and normalize all mapping structures
5. Add placeholders for future data sources

**Duration**: 1-2 hours
**Risk**: Zero - no existing files modified

### Phase 2: Content Consolidation
**Goal**: Analyze and consolidate all mapping references from codebase

**Tasks**:
1. Scan entire codebase for hardcoded mappings, field names, types
2. Extract mapping patterns from existing scripts
3. Normalize field naming conventions
4. Create comprehensive type conversion mappings
5. Add Monday.com board configurations discovered from scripts

**Duration**: 2-3 hours
**Risk**: Zero - only adding to new files

### Phase 3: Enhanced Structure
**Goal**: Create comprehensive mapping system with future extensibility

**Tasks**:
1. Add database schema definitions
2. Create field type conversion matrices
3. Add validation rules and constraints
4. Create mapping templates for common patterns
5. Add metadata and documentation within YAML

**Duration**: 1-2 hours
**Risk**: Zero - purely additive

### Phase 4: Migration Utilities
**Goal**: Prepare for future migration of dependent code

**Tasks**:
1. Create migration helper functions
2. Add backward compatibility layer
3. Create validation tools to ensure mapping consistency
4. Document migration path for future use

**Duration**: 1 hour
**Risk**: Zero - preparation only

## File Structure (New)

```
utils/
├── config.yaml                    # Existing - preserved
├── db_helper.py                   # Existing - preserved
├── data_mapping.yaml              # NEW - Master mapping registry
├── mapping_helper.py              # NEW - Mapping access utilities
└── mapping_migration_helper.py    # NEW - Future migration tools

docs/
├── mapping/                       # Existing - all files preserved
│   ├── *.yaml                    # All existing files untouched
│   └── ...
└── plans/                         # Existing
    └── master_mapping_implementation.md  # This plan
```

## Master Mapping File Structure

```yaml
# utils/data_mapping.yaml
metadata:
  version: "1.0"
  created: "2025-06-17"
  description: "Master data mapping registry for entire data orchestration system"
  migration_status: "phase_1_complete"
  
# Monday.com board configurations
monday_boards:
  # From existing scripts and configs
  coo_planning: { ... }
  customer_master_schedule: { ... }
  customer_master_schedule_subitems: { ... }
  
# Database schemas and tables  
database_schemas:
  # From DDL files and existing queries
  orders_unified: { ... }
  mon_tables: { ... }
  infor_systems: { ... }
  
# Field type mappings and conversions
field_types:
  # From existing conversion logic in scripts
  monday_to_sql: { ... }
  sql_to_monday: { ... }
  type_conversions: { ... }
  
# Data source mappings
data_sources:
  # From existing configurations
  monday_com: { ... }
  sql_server: { ... }
  external_apis: { ... }
  
# Mapping patterns and templates
mapping_patterns:
  # Common patterns extracted from scripts
  standard_monday_fields: { ... }
  audit_fields: { ... }
  relationship_fields: { ... }
  
# Future placeholders
future_mappings:
  # Placeholders for anticipated data sources
  power_bi: { placeholder: true }
  excel_imports: { placeholder: true }
  external_vendors: { placeholder: true }
```

## Content Sources to Consolidate

### From Existing Mapping Files:
- `docs/mapping/orders_unified_monday_mapping.yaml`
- `docs/mapping/field_mapping_matrix.yaml` 
- `docs/mapping/customer_mapping.yaml`
- `docs/mapping/mapping_fields.yaml`
- `docs/mapping/monday_column_ids.json`

### From Codebase Analysis:
- Hardcoded board IDs in scripts
- Field name mappings in Python scripts
- Type conversion logic patterns
- Database table/column references
- DDL files for schema definitions

### From Configuration Files:
- `utils/config.yaml` - database connections
- Workflow files - board and table references
- SQL files - schema and field references

## Migration Strategy (Future)

### Immediate Benefits (Phase 1):
- Centralized mapping access for new development
- Comprehensive documentation of all mappings
- Single source of truth for data relationships

### Future Migration Path:
1. **Phase A**: Update new scripts to use `mapping_helper`
2. **Phase B**: Create compatibility layer for existing scripts
3. **Phase C**: Gradual migration of existing scripts (optional)
4. **Phase D**: Deprecate old mapping files (far future)

## Success Criteria

### Phase 1 Complete When:
- [ ] `utils/data_mapping.yaml` contains all mapping information from existing files
- [ ] `utils/mapping_helper.py` provides easy access to all mappings
- [ ] All existing files remain untouched and functional
- [ ] New system is ready for immediate use in new development

### Quality Gates:
- [ ] All existing YAML content preserved and normalized
- [ ] All hardcoded values from scripts extracted and documented
- [ ] Comprehensive field type mappings available
- [ ] Future extensibility planned and structured
- [ ] Zero impact on existing functionality

## Implementation Notes

### Preservation Strategy:
- **Copy, never move**: All existing content copied to new structure
- **Normalize naming**: Standardize field names and types in new system
- **Maintain compatibility**: Keep existing structures intact for current dependencies
- **Add metadata**: Enhance with creation dates, sources, and documentation

### Future-Proofing:
- **Extensible schema**: Easy to add new data sources and board types
- **Version tracking**: Track changes and evolution of mappings
- **Validation ready**: Structure supports automated validation
- **Migration ready**: Designed for eventual consolidation

## Risk Mitigation

### Zero Risk Approach:
- No existing files modified
- No existing code dependencies broken  
- New system operates independently
- Can be rolled back by simply deleting new files

### Validation Strategy:
- Compare new system output with existing mapping results
- Cross-reference all extracted mappings with source files
- Validate all field types and conversions
- Test mapping helper functions thoroughly

## Next Steps

1. **Execute Phase 1**: Create foundation files
2. **Validate content**: Ensure all mappings captured correctly
3. **Test utilities**: Verify mapping helper functions work
4. **Document usage**: Create developer guide for new system
5. **Plan integration**: Define how new development will use the system

## Long-term Vision

The master mapping system will become the authoritative source for:
- All data transformations and ETL processes
- Schema generation and DDL creation
- Field validation and type checking
- API integration mappings
- Business intelligence and reporting field definitions

This foundation enables the dynamic Monday.com board template system and future data integration automation.
