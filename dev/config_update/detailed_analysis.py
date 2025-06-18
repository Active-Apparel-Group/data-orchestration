import json

# Load the audit data
with open('config_audit_data.json', 'r') as f:
    data = json.load(f)

print("🔍 Script Files Analysis")
print("=" * 40)

# Find all script files
script_files = [f for f in data['files'] if 'scripts/' in f['relative_path']]
print(f"📁 Total script files with configs: {len(script_files)}")

if script_files:
    print("\n📝 Script Files by Configuration Count:")
    # Sort by number of hardcoded configs + DB + YAML references
    script_files.sort(key=lambda x: len(x['hardcoded_configs']) + len(x['db_connection_details']) + len(x['yaml_mapping_details']), reverse=True)
    
    for file_data in script_files:
        path = file_data['relative_path']
        priority = file_data['migration_priority']
        configs = len(file_data['hardcoded_configs'])
        db_refs = len(file_data['db_connection_details'])
        yaml_refs = len(file_data['yaml_mapping_details'])
        total_refs = configs + db_refs + yaml_refs
        
        emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "")
        
        print(f"   {emoji} {path}")
        print(f"      📊 {configs} hardcoded | {db_refs} DB | {yaml_refs} YAML | Total: {total_refs}")
        
        # Show some specific patterns found
        if file_data['hardcoded_configs']:
            print(f"      🔧 Hardcoded: {', '.join(file_data['hardcoded_configs'][:3])}...")
        print()

# Check for board IDs specifically
print("\n🎯 Files with Board ID References:")
board_id_files = [f for f in data['files'] if any('BOARD_ID' in config or any(board_id in config for board_id in ['8709134353', '9200517329', '9218090006']) for config in f['hardcoded_configs'])]

if board_id_files:
    for file_data in board_id_files:
        path = file_data['relative_path']
        board_configs = [config for config in file_data['hardcoded_configs'] if 'BOARD_ID' in config or any(board_id in config for board_id in ['8709134353', '9200517329', '9218090006'])]
        print(f"   📌 {path}")
        for config in board_configs[:3]:
            print(f"      - {config}")
        print()
else:
    print("   ✅ No explicit board ID patterns found")

print("\n🗄️ Files with Table Name References:")
table_files = [f for f in data['files'] if any('MON_' in config for config in f['hardcoded_configs'])]

if table_files:
    for file_data in table_files[:5]:  # Show first 5
        path = file_data['relative_path'] 
        table_configs = [config for config in file_data['hardcoded_configs'] if 'MON_' in config]
        print(f"   🗄️ {path}")
        for config in table_configs[:2]:
            print(f"      - {config}")
        print()
else:
    print("   ✅ No table name patterns found")
