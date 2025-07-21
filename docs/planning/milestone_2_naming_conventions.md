# Milestone 2 Naming Conventions Plan
**ORDER_LIST Delta Monday Sync - File and Class Naming Standards**

📅 **Created**: 2025-07-19  
🎯 **Milestone**: 2 (Delta Engine with Business Keys)  
⚠️ **Status**: **REQUIRES APPROVAL BEFORE IMPLEMENTATION**

## 🚨 Critical Decision Point

**MUST GET APPROVAL** for all file naming before proceeding to avoid backwards refactoring!

## ✅ **APPROVED AND IMPLEMENTED**

**File Location Standards - IMPLEMENTED**

### **Utilities (Reusable Across Tables)**
```
pipelines/utils/
├── order_key_generator.py          # ✅ IMPLEMENTED: Order key generation utility
# Milestone 2 Naming Conventions & File Organization
**STATUS: ✅ IMPLEMENTED & VALIDATED**

## File Location Standards

### Modern Utils Structure (CURRENT)
```
src/pipelines/utils/
├── canonical_customer_manager.py   # ✅ IMPLEMENTED: Customer canonicalization
├── order_key_generator.py          # ✅ IMPLEMENTED: Order business keys
├── canonical_customers.yaml        # ✅ IMPLEMENTED: Customer configuration
├── db.py                           # ✅ EXISTING: Database utilities
└── logger.py                       # ✅ EXISTING: Logging utilities
```

### Legacy Utils (BEING PHASED OUT)
```
pipelines/utils/
├── canonical_customers.yaml        # ✅ COPIED TO MODERN LOCATION  
├── db_helper.py                    # 🔄 USE: src/pipelines/utils/db.py
├── logger_helper.py                # 🔄 USE: src/pipelines/utils/logger.py
└── [other legacy utilities]        # 🟡 FUTURE: Migrate to modern structure
```
├── canonical_customers.yaml        # ✅ EXISTING: Customer configuration
└── db_helper.py                     # ✅ EXISTING: Database connections
```

### **Legacy Locations (To Be Removed)**
```
src/pipelines/sync_order_list/         # ✅ NEW LOCATION: Renamed module
├── business_key_generator.py       # ❌ DEPRECATED: Renamed to order_key_generator.py
├── customer_resolver.py            # ❌ DEPRECATED: Moved to utils/
└── config_parser.py                # ❌ DEPRECATED: Replaced by direct YAML usage
```

## 🏷️ **IMPLEMENTED** Class and Function Naming

### **Primary Classes**
```python
# pipelines/utils/order_key_generator.py
class OrderKeyGenerator:           # ✅ IMPLEMENTED: Generate order business keys
    def generate_order_key()       # ✅ IMPLEMENTED: Generate single order key
    def process_dataframe()        # ✅ IMPLEMENTED: Process batch of orders
    def resolve_duplicates()       # ✅ IMPLEMENTED: Handle duplicate keys

# Class Names & Methods

## CanonicalCustomerManager (CURRENT)
```python
# src/pipelines/utils/canonical_customer_manager.py  
class CanonicalCustomerManager:            # ✅ IMPLEMENTED: Manage canonical customers
    def resolve_canonical_customer()       # ✅ IMPLEMENTED: Name resolution
    def get_unique_keys()                   # ✅ IMPLEMENTED: Customer-specific keys
    def get_customer_config()               # ✅ IMPLEMENTED: Customer configuration
```

## OrderKeyGenerator (CURRENT)  
```python
# src/pipelines/utils/order_key_generator.py
class OrderKeyGenerator:                    # ✅ IMPLEMENTED: Generate order business keys
    def generate_order_key()               # ✅ IMPLEMENTED: Create order business key
    def process_dataframe()                # ✅ IMPLEMENTED: Bulk processing
    def resolve_duplicates()               # ✅ IMPLEMENTED: Handle duplicate keys
```
    def resolve_canonical_customer()  # ✅ IMPLEMENTED: Get canonical name
    def get_customer_config()      # ✅ IMPLEMENTED: Get customer configuration
```

## 🧪 **IMPLEMENTED** Test File Naming

### **Test Categories**
```
tests/debug/
├── test_milestone_2_business_key_integration.py    # ✅ UPDATED: Now uses OrderKeyGenerator
├── test_milestone_2_merge_operations.py            # ✅ UPDATED: Order key focused tests
## Modern Import Patterns (CURRENT)

```python
# ✅ CORRECT: Use modern import structure
from pipelines.utils.canonical_customer_manager import CanonicalCustomerManager
from pipelines.utils.order_key_generator import OrderKeyGenerator
from pipelines.utils import db
from pipelines.utils import logger

# ❌ DEPRECATED: Old sys.path patterns  
sys.path.insert(0, "pipelines/utils")
import customer_resolver  # File doesn't exist anymore
```

## Test File Updates (CURRENT)

```python
# ✅ IMPLEMENTED: tests/debug/test_milestone_2_business_key_integration.py
class Milestone2OrderKeyTestFramework:
    def __init__(self):
        self.customer_manager = CanonicalCustomerManager()
        self.order_key_generator = OrderKeyGenerator()

# ✅ IMPLEMENTED: tests/debug/test_milestone_2_merge_operations.py  
class Milestone2MergeOperationTest:
    def __init__(self):
        self.customer_manager = CanonicalCustomerManager()
        self.order_key_generator = OrderKeyGenerator()
```

tests/end_to_end/
└── test_sync_order_list_complete.py              # 🟡 FUTURE: E2E workflow tests
```

## 📝 Documentation Naming

### **Architecture Documents**
```
docs/architecture/
├── milestone_2_delta_engine_design.md       # ✅ EXISTING: Technical design
├── business_key_architecture.md             # ✅ EXISTING: Business key approach
└── shadow_table_specifications.md           # 🟡 FUTURE: Table specifications

docs/planning/
├── milestone_2_naming_conventions.md        # ✅ THIS FILE: Naming standards
├── milestone_2_implementation_plan.md       # 🟡 FUTURE: Detailed implementation
└── milestone_2_testing_strategy.md          # 🟡 FUTURE: Test approach
```

## 🔧 Variable and Parameter Naming

### **Standard Conventions**
```python
# Business Keys
order_business_key                 # ✅ Full business key string
customer_canonical_name           # ✅ Resolved canonical customer name
unique_key_fields                 # ✅ List of fields for key generation

# Delta Tracking
sync_state                        # ✅ NEW, EXISTING, UPDATED, DELETED
row_hash                         # ✅ MD5 hash of record content
monday_item_id                   # ✅ Monday.com item reference

# Configuration
customer_config                  # ✅ Customer-specific configuration
order_key_config                # ✅ Order key generation rules
delta_sync_config               # ✅ Delta sync settings
```

## 🚀 Migration Strategy

### **Phase 1: Core Refactoring (Current)**
1. ✅ **Rename**: `business_key_generator.py` → `order_key_generator.py`
2. ✅ **Move**: `src/pipelines/sync_order_list/` → Updated module structure
3. ✅ **Update**: All import statements and class references
4. ✅ **Validate**: All tests pass with new naming

### **Phase 2: Enhanced Organization (Next)**
1. 🟡 **Move**: `customer_resolver.py` → `utils/`
2. 🟡 **Rename**: SQL files with `order_list_` prefix
3. 🟡 **Update**: Documentation with new conventions
4. 🟡 **Validate**: Complete integration testing

### **Phase 3: Future Extensibility (Later)**
1. 🟡 **Create**: Additional key generators for other tables
2. 🟡 **Extend**: `canonical_customers.yaml` with new table configs
3. 🟡 **Implement**: Unified key generation interface
4. 🟡 **Document**: Multi-table architecture patterns

## ⚠️ **APPROVAL REQUIRED**

**Before proceeding with ANY file moves or renames, confirm:**

### **Primary Questions**
1. ✅ **Utility Location**: Move `order_key_generator.py` to `utils/` folder?
2. ✅ **Class Naming**: `OrderKeyGenerator` as primary class name?
3. ✅ **Customer Resolver**: Also move `customer_resolver.py` to `utils/`?
4. ✅ **SQL Naming**: Prefix SQL files with `order_list_` for clarity?

### **Secondary Questions**
1. 🔍 **Test Structure**: Keep test files in `tests/debug/` or create `tests/sync_order_list/`?
2. 🔍 **Config Location**: Current TOML location acceptable or move to `configs/sync_order_list/`?
3. 🔍 **Future Planning**: Naming pattern for shipment/inventory key generators?

---

**🚨 IMPORTANT**: Get explicit approval for naming conventions before implementing!
**📋 NEXT STEP**: Review and approve this naming plan, then proceed with refactoring.
