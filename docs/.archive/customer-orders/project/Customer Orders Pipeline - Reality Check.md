# Customer Orders Pipeline - Reality Check & Execution Plan

## 📊 Reality vs Plan Assessment

### What Was Planned vs What Actually Happened

| Component | Plan Said | Reality | Gap Analysis |
|-----------|-----------|---------|--------------|
| **YAML Integration** | Load and use `orders-unified-monday-mapping.yaml` | Loaded but not used | ❌ Only extracts Title field |
| **Field Mapping** | 51 fields mapped to Monday.com | 1 field sent (Title only) | ❌ 50 fields missing |
| **GraphQL** | Use GraphQL mutations | Still using direct API | ❌ Not implemented |
| **Subitems** | Process size data | No subitem code | ❌ Not started |
| **Customer Display** | Show "GREYSON - PO" | Shows "Unknown Customer - PO" | ❌ Mapping broken |

### Root Cause Analysis

1. **YAML Loading Works** ✅ - The file loads successfully
2. **YAML Processing Broken** ❌ - `_transform_to_monday_columns()` only returns Title
3. **Column IDs Missing** ❌ - Hardcoded to `text_mkr5wzjd` instead of using YAML
4. **GraphQL Ignored** ❌ - Templates exist but aren't used

## 🚨 Critical Discovery

The implementation loaded the YAML but then **ignored it completely**, using hardcoded values instead:

```python
# What's happening now (WRONG):
column_values_dict = {
    "text_mkr5wzjd": title  # Hardcoded - ignores YAML!
}

# What should happen:
column_values_dict = self.build_from_yaml_mapping(order_data)  # Use ALL fields
```

---

# 🎯 Bulletproof Execution Checklist

## Phase 1: Fix YAML Integration (2-3 hours)

### Checkpoint 1.1: Verify YAML Loading
```yaml
validation:
  - name: "YAML file exists"
    command: "test -f sql/mappings/orders-unified-monday-mapping.yaml"
    expected: "File exists"
  
  - name: "YAML loads in Python"
    code: |
      import yaml
      with open('sql/mappings/orders-unified-monday-mapping.yaml', 'r') as f:
          mapping = yaml.safe_load(f)
      print(f"Loaded {len(mapping.get('exact_matches', []))} exact matches")
    expected: "Loaded 37 exact matches"
```

### Checkpoint 1.2: Fix Column Value Building

**File:** `dev/customer-orders/monday_api_adapter.py`

**Current Problem:**
```python
# Line 89-91 - This is WRONG:
column_values_dict = {
    "text_mkr5wzjd": title
}
```

**Required Fix:**
```python
def _transform_to_monday_columns(self, order_data: pd.Series) -> Dict[str, Any]:
    """Transform order data using YAML mapping"""
    column_values = {}
    mapping_data = self._load_mapping_data()
    
    # Process exact matches (37 fields)
    for field_config in mapping_data.get('exact_matches', []):
        source_field = field_config.get('source_field')
        target_column_id = field_config.get('target_column_id')
        
        if source_field in order_data and target_column_id:
            value = order_data[source_field]
            if pd.notna(value):
                column_values[target_column_id] = str(value)
                self.logger.debug(f"Mapped {source_field} -> {target_column_id}: {value}")
    
    # Process mapped fields
    for field_config in mapping_data.get('mapped_fields', []):
        # Similar processing...
    
    # Process computed fields
    for field_config in mapping_data.get('computed_fields', []):
        # Similar processing...
    
    self.logger.info(f"Built column values with {len(column_values)} fields")
    return column_values
```

### Validation Test 1.3: Verify All Fields Mapped
```python
# Test script: tests/debug/test_yaml_integration.py
def test_yaml_field_mapping():
    from dev.customer-orders.monday_api_adapter import MondayApiAdapter
    import pandas as pd
    
    # Test data with all fields
    test_order = pd.Series({
        'AAG ORDER NUMBER': 'TEST-001',
        'CUSTOMER NAME': 'GREYSON CLOTHIERS',
        'CUSTOMER STYLE': 'JWHD100120',
        'CUSTOMER COLOUR DESCRIPTION': 'WHITE',
        'TOTAL QTY': 100,
        # ... add more fields
    })
    
    adapter = MondayApiAdapter()
    column_values = adapter._transform_to_monday_columns(test_order)
    
    print(f"✅ Mapped {len(column_values)} fields")
    print("Sample mappings:")
    for key, value in list(column_values.items())[:5]:
        print(f"  {key}: {value}")
    
    assert len(column_values) >= 30, f"Expected 30+ fields, got {len(column_values)}"
```

## Phase 2: Implement GraphQL (2 hours)

### Checkpoint 2.1: Load GraphQL Templates

**File:** `dev/customer-orders/monday_api_adapter.py`

**Add Method:**
```python
def _load_graphql_template(self, template_name: str) -> str:
    """Load GraphQL template from sql/graphql/mutations/"""
    template_path = Path(__file__).parent.parent.parent / "sql" / "graphql" / "mutations" / f"{template_name}.graphql"
    
    if not template_path.exists():
        raise FileNotFoundError(f"GraphQL template not found: {template_path}")
    
    with open(template_path, 'r') as f:
        return f.read()

def execute_graphql(self, query: str, variables: dict) -> dict:
    """Execute GraphQL query against Monday.com API"""
    headers = {
        "Authorization": self.api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "variables": variables
    }
    
    response = requests.post(
        "https://api.monday.com/v2",
        json=payload,
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"GraphQL failed: {response.status_code} - {response.text}")
    
    return response.json()
```

### Checkpoint 2.2: Update create_item to Use GraphQL

**Replace current create_item with:**
```python
def create_item(self, board_id: int, group_id: str, item_name: str, column_values: dict):
    """Create item using GraphQL mutation"""
    
    # Load GraphQL template
    mutation = self._load_graphql_template("create-master-item")
    
    # Prepare variables
    variables = {
        "boardId": board_id,
        "groupId": group_id,
        "itemName": item_name,
        "columnValues": json.dumps(column_values)
    }
    
    # Execute mutation
    result = self.execute_graphql(mutation, variables)
    
    if 'errors' in result:
        raise Exception(f"GraphQL errors: {result['errors']}")
    
    return result['data']['create_item']['id']
```

### Validation Test 2.3: Test GraphQL Integration
```python
# Test script: tests/debug/test_graphql_integration.py
def test_graphql_create_item():
    adapter = MondayApiAdapter()
    
    # Test column values
    test_values = {
        "text_mkr5wya6": "TEST-001",  # AAG ORDER NUMBER
        "dropdown_mkr542p2": "GREYSON",  # CUSTOMER
        "numbers_mkr123": "100"  # TOTAL QTY
    }
    
    # Create test item
    item_id = adapter.create_item(
        board_id=9200517329,
        group_id="group_mkranjfa",
        item_name="TEST GraphQL Item",
        column_values=test_values
    )
    
    print(f"✅ Created item via GraphQL: {item_id}")
    assert item_id is not None
```

## Phase 3: Implement Subitems (4 hours)

### Checkpoint 3.1: Add Subitem Processing

**File:** `dev/customer-orders/staging_processor.py`

**Current gap:** The method exists but needs YAML integration

**Enhancement needed:**
```python
def create_subitem_records(self, order_row: pd.Series, parent_uuid: str) -> List[Dict]:
    """Create subitem records from order using YAML mapping"""
    subitems = []
    
    # Load subitem field mapping
    mapping_path = Path(__file__).parent.parent.parent / "sql" / "mappings" / "orders-unified-monday-mapping.yaml"
    with open(mapping_path, 'r') as f:
        mapping = yaml.safe_load(f)
    
    # Get size columns from mapping
    size_mappings = mapping.get('subitem_fields', [])
    
    for size_config in size_mappings:
        size_column = size_config['source_field']
        size_name = size_config['size_value']
        
        if size_column in order_row and pd.notna(order_row[size_column]):
            quantity = int(order_row[size_column])
            if quantity > 0:
                subitem = {
                    'parent_source_uuid': parent_uuid,
                    'size_name': size_name,
                    'size_column_id': size_config['target_column_id'],
                    'quantity': quantity,
                    'quantity_column_id': size_config.get('quantity_column_id', 'numeric_mkra7j8e'),
                    # ... other fields
                }
                subitems.append(subitem)
    
    return subitems
```

### Checkpoint 3.2: Add GraphQL Subitem Creation

**File:** `dev/customer-orders/monday_api_adapter.py`

```python
def create_subitem(self, parent_item_id: str, subitem_name: str, column_values: dict):
    """Create subitem using GraphQL mutation"""
    
    # Load GraphQL template
    mutation = self._load_graphql_template("create-subitem")
    
    # Prepare variables
    variables = {
        "parentItemId": parent_item_id,
        "itemName": subitem_name,
        "columnValues": json.dumps(column_values)
    }
    
    # Execute mutation
    result = self.execute_graphql(mutation, variables)
    
    if 'errors' in result:
        raise Exception(f"GraphQL errors: {result['errors']}")
    
    return result['data']['create_subitem']['id']
```

## 🎯 Structured Execution Plan (JSON)

```json
{
  "execution_plan": {
    "version": "2.0",
    "created": "2025-06-25",
    "total_phases": 3,
    "estimated_hours": 10,
    
    "phases": [
      {
        "id": "phase_1",
        "name": "Fix YAML Integration",
        "priority": "CRITICAL",
        "duration": "3 hours",
        "checkpoints": [
          {
            "id": "1.1",
            "task": "Verify YAML file loads",
            "validation": {
              "method": "python_test",
              "script": "import yaml; mapping = yaml.safe_load(open('sql/mappings/orders-unified-monday-mapping.yaml')); assert len(mapping['exact_matches']) == 37"
            }
          },
          {
            "id": "1.2",
            "task": "Fix _transform_to_monday_columns method",
            "file": "dev/customer-orders/monday_api_adapter.py",
            "line_range": [85, 150],
            "validation": {
              "method": "field_count",
              "expected": ">=30",
              "test_script": "tests/debug/test_yaml_integration.py"
            }
          },
          {
            "id": "1.3",
            "task": "Remove hardcoded column_values_dict",
            "validation": {
              "method": "code_review",
              "forbidden_patterns": ["text_mkr5wzjd", "hardcoded_column_id"],
              "required_patterns": ["mapping_data.get", "for field_config in"]
            }
          }
        ],
        "success_criteria": {
          "fields_mapped": ">=30",
          "test_pass_rate": "100%",
          "no_hardcoded_values": true
        }
      },
      
      {
        "id": "phase_2",
        "name": "Implement GraphQL",
        "priority": "HIGH",
        "duration": "2 hours",
        "dependencies": ["phase_1"],
        "checkpoints": [
          {
            "id": "2.1",
            "task": "Add GraphQL template loader",
            "methods_to_add": [
              "_load_graphql_template(template_name: str) -> str",
              "execute_graphql(query: str, variables: dict) -> dict"
            ]
          },
          {
            "id": "2.2",
            "task": "Replace create_item with GraphQL version",
            "validation": {
              "method": "integration_test",
              "test_script": "tests/debug/test_graphql_integration.py"
            }
          }
        ],
        "success_criteria": {
          "graphql_templates_load": true,
          "api_calls_use_graphql": true,
          "test_item_created": true
        }
      },
      
      {
        "id": "phase_3",
        "name": "Implement Subitems",
        "priority": "MEDIUM",
        "duration": "4 hours",
        "dependencies": ["phase_2"],
        "checkpoints": [
          {
            "id": "3.1",
            "task": "Fix create_subitem_records to use YAML",
            "file": "dev/customer-orders/staging_processor.py"
          },
          {
            "id": "3.2",
            "task": "Add create_subitem GraphQL method",
            "file": "dev/customer-orders/monday_api_adapter.py"
          },
          {
            "id": "3.3",
            "task": "Update batch processor to handle subitems",
            "file": "dev/customer-orders/customer_batch_processor.py"
          }
        ],
        "success_criteria": {
          "subitems_created": true,
          "size_data_processed": true,
          "end_to_end_test_passes": true
        }
      }
    ],
    
    "validation_gates": [
      {
        "after_phase": "phase_1",
        "tests": [
          "python tests/debug/test_yaml_integration.py",
          "python dev/customer-orders/main_customer_orders.py --test --po GRE-04755"
        ],
        "expected_output": [
          "Mapped 30+ fields",
          "No hardcoded column IDs found"
        ]
      },
      {
        "after_phase": "phase_2",
        "tests": [
          "python tests/debug/test_graphql_integration.py"
        ],
        "expected_output": [
          "GraphQL mutation successful",
          "Item created with ID"
        ]
      }
    ],
    
    "rollback_procedures": {
      "phase_1": "git checkout dev/customer-orders/monday_api_adapter.py",
      "phase_2": "Revert to direct API calls",
      "phase_3": "Disable subitem processing flag"
    }
  }
}
```

## 🚨 Critical Guardrails

### DO NOT:
1. **Skip validation tests** - Each checkpoint must pass
2. **Modify working code** - Only fix the broken parts
3. **Create new files** - Use existing structure
4. **Change database schema** - It's already correct
5. **Ignore error messages** - They show what's wrong

### ALWAYS:
1. **Test after each change** - Use provided test scripts
2. **Check field count** - Should be 30+ not 1
3. **Use YAML column IDs** - Never hardcode
4. **Follow existing patterns** - Copy from working code
5. **Validate with real data** - Use GREYSON PO 4755

## 📊 Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Fields Sent to API | 1 | 30+ | Count keys in column_values dict |
| Customer Display | "Unknown" | "GREYSON" | Check item name in Monday |
| GraphQL Usage | 0% | 100% | Check API calls use mutations |
| Subitems Created | 0 | 20+ | Query subitem table |
| Test Pass Rate | 40% | 100% | Run test suite |

## 🎯 Immediate First Step

**Before anything else, run this diagnostic:**

```python
# diagnostic.py - Save and run this first
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from dev.customer_orders.monday_api_adapter import MondayApiAdapter
import pandas as pd

# Test data
test_order = pd.Series({
    'AAG ORDER NUMBER': 'TEST-001',
    'CUSTOMER NAME': 'GREYSON CLOTHIERS',
    'TOTAL QTY': 100
})

adapter = MondayApiAdapter()
result = adapter._transform_to_monday_columns(test_order)

print(f"Current implementation returns: {len(result)} fields")
print(f"Fields: {list(result.keys())}")
print("\nThis should be 30+ fields, not 1!")
```

This will confirm the exact problem before starting fixes.