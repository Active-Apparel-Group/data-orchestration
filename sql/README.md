# Enhanced SQL Folder Structure

This folder now contains consolidated database-related files for the Monday.com integration project.

## 📁 New Structure

```
sql/
├── ddl/                    # EXISTING - Database schema definitions
├── migrations/             # EXISTING - Database migrations  
├── staging/                # EXISTING - Staging queries
├── tests/                  # EXISTING - Test queries
├── utility/                # EXISTING - Utility scripts
├── warehouse/              # EXISTING - Warehouse queries
├── graphql/                # NEW - Monday.com GraphQL operations
│   ├── mutations/
│   │   ├── create-master-item.graphql
│   │   ├── create-subitem.graphql
│   │   └── update-item.graphql
│   └── queries/
│       ├── get-board-schema.graphql
│       └── validate-item.graphql
├── mappings/               # NEW - Consolidated field mappings
│   ├── orders-unified-mapping.yaml      # Primary field mapping
│   ├── orders-monday-master.json        # Master item mappings
│   ├── orders-monday-subitems.json      # Subitem mappings
│   ├── customer-canonical.yaml          # Customer name standardization
│   └── monday-column-ids.json           # Monday.com column references
└── payload-templates/      # NEW - API payload examples
    ├── monday-create-item.json
    ├── monday-create-subitem.json
    └── monday-update-item.json
```

## 🎯 **ZERO BREAKING CHANGES APPROACH**

- **✅ No files moved** - All additions to existing structure
- **✅ [`utils/config.yaml`](utils/config.yaml) stays in place** - No configuration loading changes
- **✅ All existing scripts work** - No import failures or broken references
- **✅ VS Code tasks unaffected** - No path updates needed

## 🔄 **Usage Patterns**

### **GraphQL Operations**
```python
# Load GraphQL queries
with open('sql/graphql/queries/get-board-schema.graphql', 'r') as f:
    schema_query = f.read()
```

### **Field Mappings**  
```python
# Load unified field mapping
import yaml
with open('sql/mappings/orders-unified-mapping.yaml', 'r') as f:
    field_mapping = yaml.safe_load(f)
```

### **API Payloads**
```python
# Load payload templates for testing
import json
with open('sql/payload-templates/monday-create-item.json', 'r') as f:
    payload_template = json.load(f)
```

## 📋 **Migration Notes**

**Files copied (originals kept for safety):**
- `docs/mapping/orders_unified_monday_mapping.yaml` → `sql/mappings/orders-unified-mapping.yaml`
- `docs/mapping/monday_column_ids.json` → `sql/mappings/monday-column-ids.json`
- `docs/mapping/customer_mapping.yaml` → `sql/mappings/customer-canonical.yaml`
- `utils/master_field_mapping.json` → `sql/mappings/orders-monday-master.json`
- `utils/subitems_mapping_schema.json` → `sql/mappings/orders-monday-subitems.json`

**Current GraphQL file moved:**
- `database/graphql/mutations/create-subitem.graphql` → `sql/graphql/mutations/create-subitem.graphql`

## 🚀 **Next Steps**

1. **Test GraphQL operations** using files in `sql/graphql/`
2. **Validate field mappings** using consolidated files in `sql/mappings/`
3. **Use payload templates** for API integration testing
4. **Gradually migrate scripts** to use new consolidated locations when convenient

## 🧹 **Documentation Cleanup**

This approach allows us to:
- **Consolidate scattered mapping files** without breaking existing code
- **Organize GraphQL operations** in a logical location
- **Provide working API payload examples** for development
- **Simplify the overall project structure** without risk

The original files remain in place until we're confident the new structure works well for the team.
