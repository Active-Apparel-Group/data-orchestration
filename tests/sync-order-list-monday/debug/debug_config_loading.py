"""
Debug config loading issue
"""
import sys
from pathlib import Path
import toml

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

print('🔍 Debugging config loading issue...')

# Test 1: Direct TOML loading
try:
    config_path = 'configs/pipelines/sync_order_list.toml'
    print(f'📂 Loading TOML file: {config_path}')
    
    config_data = toml.load(config_path)
    print(f'✅ TOML loaded successfully')
    print(f'📋 Top-level sections found: {list(config_data.keys())}')
    
    # Check specific sections
    if 'phase' in config_data:
        print(f'✅ phase section found: {config_data["phase"]}')
    else:
        print('❌ phase section NOT found')
        
    if 'environment' in config_data:
        print(f'✅ environment section found with keys: {list(config_data["environment"].keys())}')
    else:
        print('❌ environment section NOT found')
        
except Exception as e:
    print(f'❌ Error loading TOML directly: {e}')
    import traceback
    traceback.print_exc()

print('\n' + '='*50)

# Test 2: Config parser loading
try:
    from src.pipelines.sync_order_list.config_parser import DeltaSyncConfig
    
    print('🔍 Testing config parser internal loading...')
    
    # Let's peek into what the parser actually loads
    test_config = DeltaSyncConfig.__new__(DeltaSyncConfig)  # Create without __init__
    test_config._config_path = config_path
    test_config._environment = 'development'
    
    # Load the config manually like the parser does
    with open(config_path, 'r', encoding='utf-8') as f:
        parser_config = toml.load(f)
    
    print(f'📋 Parser loaded sections: {list(parser_config.keys())}')
    
    # Check what validation is looking for
    required_sections = ['phase', 'environment']
    missing_sections = [section for section in required_sections 
                      if section not in parser_config]
    
    if missing_sections:
        print(f'❌ Parser validation would fail: Missing {missing_sections}')
    else:
        print('✅ Parser validation should pass')
        
except Exception as e:
    print(f'❌ Error testing parser: {e}')
    import traceback
    traceback.print_exc()
