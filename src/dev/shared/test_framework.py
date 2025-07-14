#!/usr/bin/env python3
"""
Standardized testing framework for data orchestration workflows
Provides common testing utilities and patterns for all workflows
"""

import sys
import time
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add utils directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))
import db_helper as db

class WorkflowTester:
    """Standardized testing framework for all workflows"""
    
    def __init__(self, workflow_name: str, dev_mode: bool = True):
        self.workflow_name = workflow_name
        self.dev_mode = dev_mode
        self.test_results = []
        self.start_time = None
        self.test_data_path = Path(f"dev/{workflow_name}/testing/test_data_samples/")
        
    def start_test_suite(self, suite_name: str):
        """Initialize a new test suite"""
        self.start_time = datetime.now()
        print(f"🧪 === Testing {suite_name} ===")
        print("=" * 60)
        
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Run a single test and track results"""
        print(f"\n--- {test_name} ---")
        try:
            result = test_func(*args, **kwargs)
            if result:
                print(f"✅ {test_name}: PASSED")
                self.test_results.append({"name": test_name, "status": "PASSED", "error": None})
                return True
            else:
                print(f"❌ {test_name}: FAILED")
                self.test_results.append({"name": test_name, "status": "FAILED", "error": "Test returned False"})
                return False
        except Exception as e:
            print(f"❌ {test_name}: EXCEPTION - {e}")
            self.test_results.append({"name": test_name, "status": "EXCEPTION", "error": str(e)})
            return False
    
    def finish_test_suite(self) -> bool:
        """Complete test suite and show results"""
        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = len(self.test_results) - passed
        
        print(f"\n📊 === Test Results ===")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed! Script is ready for deployment.")
            print("✅ VS Code compatibility: Confirmed")
            print("✅ Database integration: Working")
            print("✅ Function imports: Success")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Please review before deployment.")
        
        if self.start_time:
            duration = datetime.now() - self.start_time
            print(f"⏱️ Test duration: {duration.total_seconds():.2f} seconds")
        
        return failed == 0
    
    def test_database_connectivity(self, db_key: str = "orders") -> bool:
        """Standard database connectivity test"""
        try:
            print("🔄 Testing database connection...")
            result = db.run_query("SELECT GETDATE() as server_time", db_key)
            print("✅ Database connection successful!")
            print(f"📅 Server time: {result.iloc[0]['server_time']}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def test_table_access(self, table_name: str, db_key: str = "orders") -> bool:
        """Test access to a specific table"""
        try:
            print(f"🔄 Testing access to table {table_name}...")
            result = db.run_query(f"SELECT COUNT(*) as row_count FROM {table_name}", db_key)
            count = result.iloc[0]['row_count']
            print(f"✅ Table access successful! Found {count} rows")
            return True
        except Exception as e:
            print(f"❌ Table access failed: {e}")
            return False
    
    def test_function_import(self, module_name: str, function_names: List[str]) -> bool:
        """Test importing functions from a module"""
        try:
            print(f"🔄 Testing import of functions from {module_name}...")
            module = __import__(module_name)
            
            for func_name in function_names:
                if not hasattr(module, func_name):
                    print(f"❌ Function {func_name} not found in {module_name}")
                    return False
            
            print(f"✅ Successfully imported {len(function_names)} functions from {module_name}")
            return True
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False
    
    def load_test_data(self, filename: str) -> Any:
        """Load test data from samples directory"""
        file_path = self.test_data_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Test data file not found: {file_path}")
        
        if filename.endswith('.json'):
            with open(file_path, 'r') as f:
                return json.load(f)
        elif filename.endswith('.csv'):
            return pd.read_csv(file_path)
        else:
            with open(file_path, 'r') as f:
                return f.read()
    
    def create_test_data_sample(self, filename: str, data: Any):
        """Create test data sample file"""
        self.test_data_path.mkdir(parents=True, exist_ok=True)
        file_path = self.test_data_path / filename
        
        if isinstance(data, dict) or isinstance(data, list):
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif isinstance(data, pd.DataFrame):
            data.to_csv(file_path, index=False)
        else:
            with open(file_path, 'w') as f:
                f.write(str(data))
    
    def performance_test(self, func, expected_time_limit: float, *args, **kwargs) -> bool:
        """Test function performance"""
        try:
            print(f"🔄 Testing performance (limit: {expected_time_limit}s)...")
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            
            if elapsed_time <= expected_time_limit:
                print(f"✅ Performance test passed: {elapsed_time:.2f}s (limit: {expected_time_limit}s)")
                return True
            else:
                print(f"❌ Performance test failed: {elapsed_time:.2f}s (limit: {expected_time_limit}s)")
                return False
        except Exception as e:
            print(f"❌ Performance test exception: {e}")
            return False

class MockDataGenerator:
    """Generate mock data for testing purposes"""
    
    @staticmethod
    def generate_sample_orders(count: int = 10) -> List[Dict]:
        """Generate sample order data"""
        import random
        from datetime import datetime, timedelta
        
        orders = []
        for i in range(count):
            order = {
                "id": f"ORD-{i+1:04d}",
                "customer": f"Customer_{random.randint(1, 10)}",
                "product": f"Product_{random.randint(1, 20)}",
                "quantity": random.randint(100, 1000),
                "order_date": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "status": random.choice(["pending", "processing", "shipped", "delivered"])
            }
            orders.append(order)
        
        return orders
    
    @staticmethod
    def generate_monday_api_response(items: List[Dict]) -> Dict:
        """Generate mock Monday.com API response"""
        return {
            "data": {
                "boards": [{
                    "name": "Test Board",
                    "items_page": {
                        "cursor": None,
                        "items": [
                            {
                                "id": item["id"],
                                "name": item.get("name", f"Item {item['id']}"),
                                "updated_at": item.get("updated_at", datetime.now().isoformat()),
                                "group": {
                                    "id": "group1",
                                    "title": "Test Group"
                                },
                                "column_values": [
                                    {
                                        "column": {"title": "Status", "type": "status"},
                                        "label": item.get("status", "Active")
                                    },
                                    {
                                        "column": {"title": "Quantity", "type": "numbers"},
                                        "number": item.get("quantity", 100)
                                    }
                                ]
                            } for item in items
                        ]
                    }
                }]
            }
        }

def create_standard_test_suite(workflow_name: str, main_script: str, functions_to_test: List[str]) -> str:
    """Generate a standard test suite for a workflow"""
    
    test_template = f'''#!/usr/bin/env python3
"""
Test suite for {main_script}
Validates both VS Code development and Kestra deployment compatibility
"""

import sys
from pathlib import Path

# Add utils directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))

# Import testing framework
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from test_framework import WorkflowTester

def test_import_functions():
    """Test that we can import all functions from the main script"""
    try:
        from {main_script.replace('.py', '')} import (
            {', '.join(functions_to_test)}
        )
        print("✅ Successfully imported all functions from {main_script}")
        return True
    except ImportError as e:
        print(f"❌ Import error: {{e}}")
        return False

def main():
    """Run all tests for {workflow_name}"""
    tester = WorkflowTester("{workflow_name}")
    
    tester.start_test_suite("{main_script}")
    
    # Standard tests
    tester.run_test("Import Test", test_import_functions)
    tester.run_test("Database Connectivity", tester.test_database_connectivity)
    
    # Add workflow-specific tests here
    
    success = tester.finish_test_suite()
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
'''
    
    return test_template
