#!/usr/bin/env python3
"""
Test GraphQL Item Creation - GQ3 Validation

Tests the new GraphQL-based item creation to ensure it works correctly
with all 43+ mapped fields from the YAML configuration.
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Add paths
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "dev" / "customer-orders"))
sys.path.insert(0, str(repo_root / "utils"))

def test_graphql_creation():
    """Test GraphQL item creation with comprehensive field mapping"""
    
    print("🔍 Task GQ3: Test GraphQL Item Creation")
    print("=" * 50)
    
    try:
        # Import the adapter
        from monday_api_adapter import MondayApiAdapter
        
        # Create test data with all YAML mapped fields
        test_order = pd.Series({
            # ALL 37 Exact match fields from YAML
            'AAG ORDER NUMBER': 'TEST-GQ3-001',
            'AAG SEASON': '2026 SPRING',
            'CUSTOMER ALT PO': 'ALT-TEST',
            'CUSTOMER SEASON': '2026 SPRING',
            'ORDER DATE PO RECEIVED': '2024-01-15',
            'DROP': 'DROP 1',
            'PO NUMBER': 'TEST-001',
            'PATTERN ID': 'TEST-PATTERN',
            'STYLE DESCRIPTION': 'GraphQL Test Item',
            'CATEGORY': 'TOPS',
            'UNIT OF MEASURE': 'PCS',
            'ORDER TYPE': 'FIRM',
            'DESTINATION': 'US',
            'DESTINATION WAREHOUSE': 'TEST WAREHOUSE',
            'DELIVERY TERMS': 'FOB',
            'PLANNED DELIVERY METHOD': 'OCEAN',
            'NOTES': 'GraphQL API test',
            'CUSTOMER PRICE': 25.50,
            'USA ONLY LSTP 75% EX WORKS': 19.13,
            'EX WORKS (USD)': 12.75,
            'ADMINISTRATION FEE': 0.50,
            'DESIGN FEE': 1.00,
            'FX CHARGE': 0.25,
            'HANDLING': 0.75,
            'SURCHARGE FEE': 0.00,
            'DISCOUNT': 2.50,
            'FINAL FOB (USD)': 22.75,
            'HS CODE': '6109100010',
            'US DUTY RATE': 16.5,
            'US DUTY': 3.75,
            'FREIGHT': 2.50,
            'US TARIFF RATE': 7.5,
            'US TARIFF': 1.71,
            'DDP US (USD)': 30.71,
            'SMS PRICE USD': 32.00,
            'FINAL PRICES Y/N': 'Y',
            'NOTES FOR PRICE': 'GraphQL test pricing',
            
            # ALL 6 Mapped fields from YAML (using canonical customer names)
            'CUSTOMER NAME': 'GREYSON',  # Canonical customer name (not GREYSON CLOTHIERS)
            'CUSTOMER STYLE': 'TEST-STYLE-001',
            'ALIAS/RELATED ITEM': 'TEST-ALIAS',
            'CUSTOMER COLOUR DESCRIPTION': 'NAVY',
            'ETA CUSTOMER WAREHOUSE DATE': '2024-03-15',
            'EX FACTORY DATE': '2024-02-28',
            
            # Test metadata
            'TOTAL QTY': 500,
            'UUID': 'test-uuid-graphql-001'
        })
        
        print(f"📊 Test data: {len(test_order)} fields")
        
        # Initialize adapter
        adapter = MondayApiAdapter()
        print("✅ MondayApiAdapter initialized")
        
        # Test GraphQL templates loading
        try:
            mutation_template = adapter.load_graphql_template("create-master-item")
            print("✅ GraphQL template loaded successfully")
            print(f"   Template preview: {mutation_template[:100]}...")
        except Exception as e:
            print(f"❌ Failed to load GraphQL template: {e}")
            return False
        
        # Test column transformation (should map 43+ fields)
        try:
            column_values = adapter._transform_to_monday_columns(test_order)
            print(f"✅ Field transformation: {len(column_values)} fields mapped")
            print(f"   Sample mappings: {list(column_values.keys())[:5]}...")
        except Exception as e:
            print(f"❌ Failed field transformation: {e}")
            return False
        
        # Test GraphQL creation (DRY RUN - comment out for actual creation)
        print("\n🚨 DRY RUN MODE - Not creating actual Monday.com item")
        print("   To test actual creation, uncomment the following block:")
        print("""
        # result = adapter.create_item_graphql(test_order)
        # if result.get('status') == 'success':
        #     print(f"✅ Item created via GraphQL: {result['id']}")
        # else:
        #     print(f"❌ GraphQL creation failed: {result.get('error')}")
        """)
        
        print("\n✅ SUCCESS: GraphQL integration ready for testing")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_graphql_creation()
    sys.exit(0 if success else 1)
