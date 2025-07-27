#!/usr/bin/env python3
"""
Task FY2 Debug: Test YAML field mapping in _transform_to_monday_columns
This will test why only 1 field is being returned instead of 30+
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to Python path
def find_repo_root():
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "utils").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find repository root")

repo_root = find_repo_root()
sys.path.insert(0, str(repo_root / "utils"))
sys.path.insert(0, str(repo_root))

# Import after path setup
sys.path.append(str(repo_root / "dev" / "customer-orders"))
from monday_api_adapter import MondayApiAdapter

def main():
    print("🔍 Task FY2 Debug: Test YAML field mapping")
    print("-" * 50)
    
    # Create comprehensive test data with ALL 44 YAML source fields
    test_order = pd.Series({
        # ALL 37 Exact match fields from YAML
        'AAG ORDER NUMBER': 'GRE-04972',
        'AAG SEASON': '2026 SPRING',
        'CUSTOMER ALT PO': 'ALT-4755',
        'CUSTOMER SEASON': '2026 SPRING',
        'ORDER DATE PO RECEIVED': '2024-01-15',
        'DROP': 'DROP 1',
        'PO NUMBER': '4755',
        'PATTERN ID': 'JWHD100120',
        'STYLE DESCRIPTION': 'Cotton Jersey Polo',
        'CATEGORY': 'TOPS',
        'UNIT OF MEASURE': 'PCS',
        'ORDER TYPE': 'FIRM',
        'DESTINATION': 'US',
        'DESTINATION WAREHOUSE': 'NJ WAREHOUSE',
        'DELIVERY TERMS': 'FOB',
        'PLANNED DELIVERY METHOD': 'OCEAN',
        'NOTES': 'Rush order for spring season',
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
        'NOTES FOR PRICE': 'Confirmed pricing',
        
        # ALL 6 Mapped fields from YAML (source -> target)
        'CUSTOMER NAME': 'GREYSON',                      # -> CUSTOMER (canonical name)
        'CUSTOMER STYLE': 'JWHD100120',              # -> STYLE
        'ALIAS/RELATED ITEM': 'POLO-001',            # -> ALIAS RELATED ITEM
        'CUSTOMER COLOUR DESCRIPTION': 'WHITE',      # -> COLOR
        'ETA CUSTOMER WAREHOUSE DATE': '2024-03-15', # -> CUSTOMER REQ IN DC DATE
        'EX FACTORY DATE': '2024-02-28',             # -> CUSTOMER EX FACTORY DATE
        
        # Additional test fields
        'TOTAL QTY': 720,
        'Title': 'Test Item'
    })
    
    print(f"📊 Test data has {len(test_order)} fields (covering ALL 44 YAML mappings)")
    print(f"   Expected to map ALL available fields from YAML")
    
    # Create adapter and test transformation
    try:
        adapter = MondayApiAdapter()
        print(f"✅ MondayApiAdapter created successfully")
        
        # Test the transformation
        column_values = adapter._transform_to_monday_columns(test_order)
        
        print(f"\n📊 RESULTS:")
        print(f"   Fields returned: {len(column_values)}")
        print(f"   Expected: 30+ fields")
        
        if len(column_values) > 0:
            print(f"\n📋 Sample column mappings:")
            for i, (key, value) in enumerate(column_values.items()):
                if i < 10:  # Show first 10
                    print(f"      {key}: {value}")
                elif i == 10:
                    print(f"      ... and {len(column_values) - 10} more")
                    break
        else:
            print("❌ NO COLUMN VALUES RETURNED!")
            
        # Check if this meets success criteria
        if len(column_values) >= 30:
            print(f"\n✅ SUCCESS: {len(column_values)} fields mapped (meets 30+ requirement)")
            return True
        else:
            print(f"\n❌ FAILED: Only {len(column_values)} fields mapped (need 30+)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
