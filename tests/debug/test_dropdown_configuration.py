#!/usr/bin/env python3
"""
Test Dropdown Configuration - Task 19.15.2 Validation
Test the TOML-driven dropdown configuration implementation
"""

import sys
from pathlib import Path

repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))

from pipelines.utils import db, logger
from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
from src.pipelines.sync_order_list.monday_api_client import MondayAPIClient

logger = logger.get_logger(__name__)

def main():
    print("🧪 Testing Dropdown Configuration Implementation...")
    
    # Config FIRST
    config_path = str(repo_root / "configs" / "pipelines" / "sync_order_list.toml")
    config = DeltaSyncConfig.from_toml(config_path)
    
    # Initialize Monday API client
    monday_client = MondayAPIClient(config_path)
    
    # Test 1: Verify TOML configuration loading
    print("\n📋 Test 1: TOML Configuration Loading")
    environment = monday_client._get_environment()
    print(f"Environment: {environment}")
    
    # Test dropdown configuration reading
    headers_dropdown_config = monday_client._get_dropdown_config("headers")
    lines_dropdown_config = monday_client._get_dropdown_config("lines")
    
    print(f"Headers dropdown config: {headers_dropdown_config}")
    print(f"Lines dropdown config: {lines_dropdown_config}")
    
    # Test 2: Verify specific column configuration
    print("\n🎯 Test 2: Critical Dropdown Columns")
    
    # AAG SEASON column
    aag_season_enabled = monday_client._should_create_labels_for_column("dropdown_mkr58de6", "headers")
    print(f"AAG SEASON (dropdown_mkr58de6) auto-create: {aag_season_enabled}")
    
    # CUSTOMER SEASON column  
    customer_season_enabled = monday_client._should_create_labels_for_column("dropdown_mkr5rgs6", "headers")
    print(f"CUSTOMER SEASON (dropdown_mkr5rgs6) auto-create: {customer_season_enabled}")
    
    # Size code column for subitems
    size_code_enabled = monday_client._should_create_labels_for_column("dropdown_mkrak7qp", "lines")
    print(f"Size Code (dropdown_mkrak7qp) auto-create: {size_code_enabled}")
    
    # Test 3: Test with sample GREYSON records
    print("\n📊 Test 3: Sample Record Analysis")
    
    # Create sample records similar to GREYSON PO 4755
    sample_header_record = {
        "AAG ORDER NUMBER": "3001234",
        "CUSTOMER NAME": "GREYSON",
        "AAG SEASON": "FALL 2025",  # This should trigger auto-creation
        "CUSTOMER SEASON": "F25",   # This should trigger auto-creation
        "PO NUMBER": "4755"
    }
    
    sample_line_record = {
        "size_code": "L",  # This should trigger auto-creation
        "qty": "5",
        "parent_item_id": "123456"
    }
    
    # Test if records trigger label creation
    headers_needs_labels = monday_client._determine_create_labels_for_records([sample_header_record], "headers")
    lines_needs_labels = monday_client._determine_create_labels_for_records([sample_line_record], "lines")
    
    print(f"Headers record needs label creation: {headers_needs_labels}")
    print(f"Lines record needs label creation: {lines_needs_labels}")
    
    # Test 4: Validation Summary
    print("\n✅ Test 4: Validation Summary")
    print("=" * 50)
    
    critical_tests = [
        ("AAG SEASON auto-create enabled", aag_season_enabled),
        ("CUSTOMER SEASON auto-create enabled", customer_season_enabled), 
        ("Size Code auto-create enabled", size_code_enabled),
        ("Headers trigger label creation", headers_needs_labels),
        ("Lines trigger label creation", lines_needs_labels)
    ]
    
    all_passed = True
    for test_name, result in critical_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Dropdown configuration is working correctly.")
        print("📊 Expected Impact: AAG SEASON and CUSTOMER SEASON should now populate in Monday.com")
    else:
        print("⚠️  Some tests failed. Check TOML configuration.")
    
    print(f"\n🔧 Next Step: Run actual Monday.com sync test to validate API integration")

if __name__ == "__main__":
    main()
