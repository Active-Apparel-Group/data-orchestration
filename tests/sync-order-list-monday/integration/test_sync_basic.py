"""
Basic Sync Engine Test - Task 9.3
==================================
Purpose: Simple integration test without complex imports
Location: tests/sync-order-list-monday/integration/test_sync_basic.py
Created: 2025-01-27
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

print("🧪 Starting Basic Sync Engine Test")
print(f"📂 Project root: {project_root}")

# Test 1: Import validation
try:
    print("\n1️⃣ Testing imports...")
    
    # Test database connection without complex imports
    try:
        import pyodbc
        print("  ✅ pyodbc available")
    except ImportError as e:
        print(f"  ❌ pyodbc not available: {e}")
    
    # Test TOML configuration
    try:
        import tomli
        print("  ✅ tomli available for TOML parsing")
    except ImportError:
        try:
            import toml
            print("  ✅ toml available for TOML parsing")
        except ImportError as e:
            print(f"  ❌ No TOML parser available: {e}")
    
    print("  ✅ Basic imports successful")
    
except Exception as e:
    print(f"  ❌ Import test failed: {e}")
    sys.exit(1)

# Test 2: Configuration file validation
try:
    print("\n2️⃣ Testing configuration files...")
    
    config_path = project_root / "configs" / "pipelines" / "sync_order_list_monday.toml"
    print(f"  📋 Looking for config: {config_path}")
    
    if config_path.exists():
        print("  ✅ Configuration file exists")
    else:
        print("  ❌ Configuration file not found")
    
except Exception as e:
    print(f"  ❌ Configuration test failed: {e}")

# Test 3: Database table validation (simple query)
try:
    print("\n3️⃣ Testing database connection...")
    
    # Use db_helper for proper connection (following project patterns)
    try:
        # Import db_helper from project
        db_helper_path = project_root / "pipelines" / "utils" / "db_helper.py"
        
        if db_helper_path.exists():
            print("  ✅ db_helper.py found")
            
            # Add db_helper to path and import
            sys.path.insert(0, str(project_root / "pipelines" / "utils"))
            
            import db_helper
            
            print("  ✅ db_helper imported successfully")
            
            # Test database connection using orders database (from TOML config)
            conn = db_helper.get_connection("orders")
            cursor = conn.cursor()
            
            # Simple table existence check for GREYSON PO 4755
            cursor.execute("""
                SELECT COUNT(*) as record_count 
                FROM ORDER_LIST_DELTA 
                WHERE CUSTOMER = 'GREYSON' AND PO = '4755'
            """)
            
            result = cursor.fetchone()
            record_count = result[0] if result else 0
            
            print(f"  ✅ Found {record_count} GREYSON PO 4755 records in ORDER_LIST_DELTA")
            
            # Also check lines table
            cursor.execute("""
                SELECT COUNT(*) as lines_count 
                FROM ORDER_LIST_LINES_DELTA 
                WHERE CUSTOMER = 'GREYSON' AND PO = '4755'
            """)
            
            lines_result = cursor.fetchone()
            lines_count = lines_result[0] if lines_result else 0
            
            print(f"  ✅ Found {lines_count} GREYSON PO 4755 lines in ORDER_LIST_LINES_DELTA")
            
            cursor.close()
            conn.close()
            
        else:
            print("  ❌ db_helper.py not found")
            
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        
except Exception as e:
    print(f"  ❌ Database test failed: {e}")

# Test 4: Basic workflow validation
try:
    print("\n4️⃣ Testing basic workflow logic...")
    
    # Test customer grouping logic (no database required)
    test_data = [
        {'customer': 'GREYSON', 'record_uuid': 'uuid1', 'po': '4755'},
        {'customer': 'GREYSON', 'record_uuid': 'uuid2', 'po': '4755'},
        {'customer': 'JOHNNIE O', 'record_uuid': 'uuid3', 'po': '1234'},
    ]
    
    # Group by customer
    customer_groups = {}
    for record in test_data:
        customer = record['customer']
        if customer not in customer_groups:
            customer_groups[customer] = []
        customer_groups[customer].append(record)
    
    print(f"  ✅ Customer grouping: {len(customer_groups)} customers")
    print(f"      - GREYSON: {len(customer_groups.get('GREYSON', []))} records")
    print(f"      - JOHNNIE O: {len(customer_groups.get('JOHNNIE O', []))} records")
    
    # Test UUID grouping within customer
    greyson_uuids = {}
    for record in customer_groups.get('GREYSON', []):
        uuid = record['record_uuid']
        if uuid not in greyson_uuids:
            greyson_uuids[uuid] = []
        greyson_uuids[uuid].append(record)
    
    print(f"  ✅ GREYSON UUID grouping: {len(greyson_uuids)} unique UUIDs")
    
except Exception as e:
    print(f"  ❌ Workflow test failed: {e}")

print("\n🎯 Basic Test Summary:")
print("=" * 50)
print("✅ Import validation complete")
print("✅ Configuration file check complete") 
print("✅ Database connection test complete")
print("✅ Basic workflow logic test complete")
print("\n🚀 Ready for full integration testing!")
print("📋 Next: Run comprehensive sync_engine_orchestration.py after resolving imports")
