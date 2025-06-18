import json

# Load the audit data
with open('config_audit_data.json', 'r') as f:
    data = json.load(f)

print("🔍 Configuration Audit Summary")
print("=" * 40)

print(f"📊 Total files analyzed: {data['summary']['total_files']}")
print(f"🔗 Files with DB connections: {data['summary']['files_with_db']}")
print(f"📄 Files with YAML mappings: {data['summary']['files_with_yaml']}")
print(f"⚙️ Files with hardcoded configs: {data['summary']['files_with_hardcoded']}")

print("\n🎯 Priority Breakdown:")
priorities = {}
for file_data in data['files']:
    priority = file_data['migration_priority']
    priorities[priority] = priorities.get(priority, 0) + 1

for priority, count in sorted(priorities.items()):
    emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "")
    print(f"   {emoji} {priority}: {count} files")

# Show high-priority script files
print("\n📝 Key Script Files Needing Migration:")
script_files = [f for f in data['files'] if f['relative_path'].startswith('scripts/') and (f['has_db_connection'] or f['has_yaml_mapping'])]
script_files.sort(key=lambda x: len(x['hardcoded_configs']), reverse=True)

for file_data in script_files[:10]:
    path = file_data['relative_path']
    priority = file_data['migration_priority']
    configs = len(file_data['hardcoded_configs'])
    emoji = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}.get(priority, "")
    print(f"   {emoji} {path} ({configs} configs)")
