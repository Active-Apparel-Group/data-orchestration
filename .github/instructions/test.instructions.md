---
applyTo: '**'
---

# Test Framework Instructions - Data Orchestration Project

## 🎯 Testing Philosophy

### Modular Testing Approach
Our testing framework follows a **modular, iterative approach** where each test phase validates specific functionality with measurable criteria. This allows developers to:

- **Run individual test phases** when debugging specific issues
- **Build comprehensive test suites** that validate end-to-end workflows  
- **Iterate and expand tests** as new functionality is added
- **Validate against actual production data** (no test/mock data)
- **Generate detailed reports** with actionable metrics

## 📋 Test Framework Structure

### Core Components

#### 1. Test Class Structure
```python
class FeatureTestFramework:
    """
    Comprehensive test framework for specific feature/workflow
    Provides modular testing with detailed validation and reporting
    """
    
    def __init__(self):
        self.test_results = {}  # Store all test results
        self.config = db.load_config()  # Use project configuration
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite with all phases"""
        
    def test_phase_name(self) -> Dict[str, Any]:
        """Individual test phase with specific validation"""
```

#### 2. Test Phases Pattern
Each test follows this consistent pattern:

```python
def test_phase_name(self) -> Dict[str, Any]:
    """Test Phase N: Description of what this phase validates"""
    print(f"\n{N}️⃣ PHASE NAME")
    print("-" * 40)
    
    try:
        # 1. Execute the functionality being tested
        # 2. Query database for actual results
        # 3. Validate against expected criteria
        # 4. Return structured results
        
        result = {
            'success': True,  # Boolean success/failure
            'data': {},       # Actual measurements
            'metrics': {}     # Calculated metrics
        }
        
        print(f"   ✅ [Phase]: PASSED")
        return result
        
    except Exception as e:
        logger.exception(f"[Phase] test failed: {e}")
        return {'success': False, 'error': str(e)}
```

## 🔧 Implementation Standards

### Database Validation Pattern
Every test phase must validate against actual database records:

```python
# Query actual data from database
with db.get_connection('database_name') as conn:
    sql = """
    SELECT 
        COUNT(*) as total_records,
        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_records
    FROM [actual_table]
    WHERE [specific_criteria]
    """
    result = pd.read_sql(sql, conn, params=[test_parameters])

# Validate against expected criteria
success_rate = (successful_records / total_records * 100) if total_records > 0 else 0
validation = {
    'success': success_rate >= 95,  # Define clear success criteria
    'success_rate': success_rate,
    'total_records': total_records,
    'successful_records': successful_records
}
```

### Success Criteria Definition
Each test phase must define clear, measurable success criteria:

```python
# Example success criteria
VALIDATION_CRITERIA = {
    'data_availability': {'min_records': 1, 'required_fields': ['PO_NUMBER', 'CUSTOMER']},
    'batch_processing': {'success_rate': 95, 'max_duration_seconds': 300},
    'api_integration': {'success_rate': 95, 'max_errors': 5},
    'database_consistency': {'staging_to_prod_match': 100}
}
```

### Error Handling and Reporting
Comprehensive error analysis with actionable details:

```python
# Error analysis pattern
error_analysis = {
    'total_errors': error_count,
    'unique_error_types': unique_errors,
    'sample_errors': sample_error_messages,
    'actionable_items': [
        'Check API rate limiting if HTTP 429 errors',
        'Validate data types if conversion errors',
        'Review network connectivity if timeout errors'
    ]
}
```

## 📊 Test Execution Patterns

### 1. Complete Test Suite
```python
# Run all test phases in sequence
test_framework = FeatureTestFramework()
results = test_framework.run_all_tests()
```

### 2. Individual Phase Testing (for debugging)
```python
# Run specific test phase
test_framework = FeatureTestFramework()
data_validation = test_framework.test_data_availability()
batch_processing = test_framework.test_batch_processing()
```

### 3. Iterative Development
```python
# As you develop new functionality, add new test phases
def test_new_feature(self) -> Dict[str, Any]:
    """Test Phase N+1: Validate new feature"""
    # Follow the same pattern
    # Update run_all_tests() to include this phase
```

## 📁 File Organization

### Test File Locations
```
tests/
├── end_to_end/              # Complete workflow tests
│   ├── test_[feature]_complete_workflow.py
│   └── test_[customer]_[po]_workflow.py
├── integration/             # Multi-component integration tests
│   ├── test_database_api_integration.py
│   └── test_staging_production_sync.py
├── unit/                    # Individual component tests
│   ├── test_data_mapping.py
│   └── test_api_client.py
└── debug/                   # Debug and development tests
    ├── debug_[specific_issue].py
    └── validate_[specific_data].py
```

### Test Naming Conventions
- **End-to-End**: `test_[customer]_[po]_complete_workflow.py`
- **Integration**: `test_[component1]_[component2]_integration.py`
- **Unit**: `test_[module]_[function].py`
- **Debug**: `debug_[issue_description].py`

## 🎯 Best Practices

### 1. Use Actual Production Data
```python
# ✅ CORRECT - Test against actual data
sql = """
SELECT * FROM ORDERS_UNIFIED 
WHERE CUSTOMER = 'GREYSON' AND PO_NUMBER = '4755'
"""

# ❌ WRONG - Don't use mock/test data
test_data = {'customer': 'TEST_CUSTOMER', 'po': 'TEST_PO'}
```

### 2. Validate Each Step
```python
# ✅ CORRECT - Validate intermediate steps
# Step 1: Check source data exists
source_validation = self.validate_source_data()
# Step 2: Check staging data created
staging_validation = self.validate_staging_data()
# Step 3: Check API integration worked
api_validation = self.validate_api_results()
```

### 3. Measurable Success Criteria
```python
# ✅ CORRECT - Clear numeric criteria
success_criteria = {
    'item_success_rate': 95,  # 95% of items processed successfully
    'subitem_accuracy': 95,   # 95% of expected subitems created
    'api_error_rate': 5       # Less than 5% API errors
}

# ❌ WRONG - Vague success criteria
# "Check if it works"
# "Verify data looks correct"
```

### 4. Comprehensive Reporting
```python
# Generate detailed final report
def generate_final_report(self):
    print("📊 FINAL TEST REPORT")
    
    for phase, result in self.test_results.items():
        status = "✅ PASSED" if result.get('success') else "❌ FAILED"
        print(f"{phase}: {status}")
        
        # Show key metrics
        if 'metrics' in result:
            for metric, value in result['metrics'].items():
                print(f"   {metric}: {value}")
        
        # Show errors if any
        if 'error' in result:
            print(f"   Error: {result['error']}")
```

## 🔄 Test Development Workflow

### 1. Initial Test Creation
```python
# Start with basic test structure
class NewFeatureTestFramework:
    def __init__(self):
        self.test_results = {}
    
    def test_basic_functionality(self):
        # Start with simple validation
        pass
    
    def run_all_tests(self):
        self.test_results['basic'] = self.test_basic_functionality()
        return self.test_results
```

### 2. Iterative Enhancement
```python
# Add more test phases as you develop
def test_advanced_functionality(self):
    # Add more comprehensive validation
    pass

def test_error_scenarios(self):
    # Test edge cases and error handling
    pass

# Update run_all_tests() to include new phases
```

### 3. Integration with VS Code Tasks
```json
// Add to .vscode/tasks.json
{
    "label": "Test: [Feature] Complete Workflow",
    "type": "shell",
    "command": "python",
    "args": ["tests/end_to_end/test_[feature]_complete_workflow.py"],
    "group": "test",
    "detail": "Run comprehensive [feature] test with validation"
}
```

## 📈 Metrics and Success Criteria

### Standard Metrics to Track
- **Data Availability**: Source records found vs expected
- **Processing Success**: Records processed successfully vs total
- **API Integration**: API calls successful vs total calls made
- **Database Consistency**: Staging records vs production records
- **Error Rates**: Errors by type and frequency
- **Performance**: Processing time and throughput

### Success Thresholds
- **Excellent**: >95% success rate, <5% errors
- **Good**: >90% success rate, <10% errors  
- **Needs Attention**: <90% success rate, >10% errors

## 🚨 Common Pitfalls to Avoid

### ❌ Don't Do This:
1. **Mock data testing** - Always use actual production data
2. **Vague validation** - Define specific numeric criteria
3. **Single-phase tests** - Break complex workflows into phases
4. **No error analysis** - Always check error logs and provide actionable feedback
5. **Manual result checking** - Automate all validation with database queries

### ✅ Do This Instead:
1. **Production data validation** - Query actual tables
2. **Measurable criteria** - Define success as specific percentages/counts
3. **Modular phases** - Each phase tests specific functionality
4. **Comprehensive error handling** - Log, analyze, and report all errors
5. **Automated validation** - Database queries confirm all results

## 🎯 Example Test Implementation

See `tests/end_to_end/test_greyson_po_4755_complete_workflow.py` for a complete implementation following this framework.

This test demonstrates:
- ✅ Modular phase structure
- ✅ Database validation for each step
- ✅ Clear success criteria
- ✅ Comprehensive error analysis
- ✅ Detailed reporting
- ✅ Production data validation
- ✅ Iterative development support
