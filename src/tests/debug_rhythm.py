#!/usr/bin/env python3
"""Debug script to test Rhythm customer configuration"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pandas as pd
from audit_pipeline.config import get_customer_matching_config
from audit_pipeline.matching import get_style_value_and_source, add_match_keys

# Test data for Rhythm
rhythm_row = {
    'Canonical_Customer': 'RHYTHM',
    'Style': '',
    'Pattern_ID': '',
    'ALIAS/RELATED ITEM': 'RHY-TEST-ITEM'
}

print("=== Testing Rhythm Customer Configuration ===")

# Test config loading
config = get_customer_matching_config('RHYTHM')
print(f"Rhythm config: {config}")

# Test get_style_value_and_source directly
style_value, style_source = get_style_value_and_source(rhythm_row, 'RHYTHM')
print(f"Direct test - Style value: '{style_value}', Style source: '{style_source}'")

# Test with dataframe
df = pd.DataFrame([rhythm_row])
print(f"Input DataFrame:\n{df}")

df_with_keys = add_match_keys(df)
print(f"Output DataFrame columns: {list(df_with_keys.columns)}")
print(f"Output DataFrame with keys:\n{df_with_keys[['Canonical_Customer', 'Style_Source']]}")

style_source_from_df = df_with_keys['Style_Source'].iloc[0]
print(f"DataFrame test - Style_Source: '{style_source_from_df}'")

if style_source_from_df == 'ALIAS/RELATED ITEM':
    print("✅ SUCCESS: Rhythm customer correctly uses ALIAS/RELATED ITEM")
else:
    print(f"❌ FAILURE: Expected 'ALIAS/RELATED ITEM', got '{style_source_from_df}'")
