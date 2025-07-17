# 📋 Create Script Mappings Runbook

## 🎯 Overview

The `create_script_mappings.py` script transforms Monday.com board metadata JSON files into either enhanced JSON with script mappings or TOML configuration files for the OPUS Universal Monday.com Update system.

**Script Location**: `pipelines/codegen/create_script_mappings.py`

## 🚨 Common Issues & Solutions

### Issue 1: "No such file or directory" Error
**Problem**: Running script from wrong directory
```powershell
# ❌ WRONG - Running from project root
python create_script_mappings.py board_8709134353_metadata.json
# Error: can't open file 'create_script_mappings.py': [Errno 2] No such file or directory
```

**Solutions**:

#### Option A: Run from correct directory
```powershell
# ✅ CORRECT - Change to codegen directory
cd pipelines\codegen
python create_script_mappings.py ..\..\configs\boards\board_8709134353_metadata.json
```

#### Option B: Use full path from project root
```powershell
# ✅ CORRECT - Full path from project root
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json
```

#### Option C: Use VS Code Tasks (Recommended)
Use the predefined VS Code task:
- Press `Ctrl+Shift+P` → "Tasks: Run Task" → "Dev: Monday Boards Dynamic Generator"

## 📁 File Locations

### Input Files (Board Metadata)
Board metadata JSON files are located in:
```
configs/boards/board_{board_id}_metadata.json
```

**Available boards**:
- `configs/boards/board_8709134353_metadata.json` (Customer Master Schedule)

### Output Files

#### Enhanced JSON (Default)
- **Location**: Same as input file (overwrites)
- **Purpose**: Adds `script_mappings` field to original JSON

#### TOML Configuration (--toml flag)
- **Default Location**: `configs/updates/templates/{board_name}_update.toml`
- **Custom Location**: Use `-o` flag to specify path
- **Purpose**: Creates OPUS Universal Monday.com Update configuration

## 🔧 Usage Patterns

### Pattern 1: Enhanced JSON Generation (Original Functionality)
```powershell
# From project root
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json

# From codegen directory
cd pipelines\codegen
python create_script_mappings.py ..\..\configs\boards\board_8709134353_metadata.json
```

**Output**: Adds `script_mappings` field to the original JSON file.

### Pattern 2: TOML Configuration Generation
```powershell
# Generate TOML with default name
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json --toml

# Generate TOML with custom output path
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json --toml -o configs\updates\planning_update_fob.toml
```

**Output**: Creates TOML configuration file in `configs/updates/templates/` or specified path.

## 📊 Script Functionality

### Enhanced JSON Mode (Default)
1. **Loads** board metadata JSON
2. **Extracts** column mappings from `columns` array
3. **Generates** `script_mappings` object: `{monday_id: sql_column}`
4. **Injects** `script_mappings` into top-level JSON
5. **Overwrites** original file with enhanced version

### TOML Configuration Mode (--toml)
1. **Loads** board metadata JSON
2. **Extracts** board information (ID, name, table, database)
3. **Generates** TOML sections:
   - `[metadata]`: Board identification and configuration
   - `[query_config]`: SQL query template and item ID mapping
   - `[column_mapping]`: Monday column ID to SQL column mappings
4. **Creates** TOML file with proper structure for OPUS updates

## 🎯 Step-by-Step Examples

### Example 1: Working with Customer Master Schedule Board

#### Step 1: Verify board metadata exists
```powershell
# Check if file exists
ls configs\boards\board_8709134353_metadata.json
```

#### Step 2: Generate enhanced JSON
```powershell
# From project root
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json
```

#### Step 3: Generate TOML configuration
```powershell
# Generate TOML for OPUS updates
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json --toml -o configs\updates\customer_master_schedule_update.toml
```

### Example 2: Using VS Code Tasks (Recommended)

#### Step 1: Open Command Palette
- Press `Ctrl+Shift+P`

#### Step 2: Run Task
- Type "Tasks: Run Task"
- Select "Dev: Monday Boards Dynamic Generator"
- Enter board ID when prompted: `8709134353`

## 🛠️ Configuration Management

### TOML Output Structure
```toml
# OPUS Universal Monday.com Update Configuration
[metadata]
board_id = 8709134353
board_name = "Customer Master Schedule"
table_name = "CUSTOMER_MASTER_SCHEDULE"
database = "dms"
update_type = "batch_item_updates"

[query_config]
query = """
# TODO: Add your SQL query here
SELECT
    [Item ID] as monday_item_id,
    -- Add your columns here
FROM your_table
WHERE your_conditions
"""
item_id_column = "monday_item_id"

[column_mapping]
# Monday.com column_id -> SQL query column mapping
"status" = "STATUS_COLUMN"
"text" = "TEXT_COLUMN"
# ... additional mappings
```

### Enhanced JSON Structure
```json
{
  "board_id": 8709134353,
  "board_name": "Customer Master Schedule",
  "columns": [...],
  "script_mappings": {
    "status": "STATUS_COLUMN",
    "text": "TEXT_COLUMN"
  }
}
```

## 🔍 Troubleshooting

### Issue: Path Resolution Errors
**Symptoms**: 
- `FileNotFoundError: Could not find repository root`
- Import errors for `logger_helper`

**Solution**: Ensure running from correct directory structure
```powershell
# Verify you're in the project root
pwd
# Should show: ...\data-orchestration\data-orchestration

# Verify pipelines structure exists
ls pipelines\utils\logger_helper.py
```

### Issue: Board Metadata File Not Found
**Symptoms**: 
- `FileNotFoundError` when loading JSON

**Solution**: Verify board metadata exists
```powershell
# Check available board metadata files
ls configs\boards\*.json

# If missing, extract metadata first using board extraction tools
```

### Issue: TOML Generation Fails
**Symptoms**: 
- Missing `[column_mapping]` section
- Empty or malformed TOML

**Solution**: Verify board metadata structure
```powershell
# Check JSON structure
python -c "import json; print(json.load(open('configs/boards/board_8709134353_metadata.json'))['columns'][:2])"
```

## 📚 Integration with OPUS Pipeline

### Generated TOML Usage
1. **Place TOML** in `configs/updates/` directory
2. **Configure SQL query** in `[query_config]` section
3. **Verify column mappings** in `[column_mapping]` section
4. **Run OPUS update** using the TOML configuration:
   ```powershell
   python pipelines\scripts\update\update_boards.py --config configs\updates\your_config.toml --dry_run
   ```

### Integration Workflow
1. **Extract board metadata** → `configs/boards/board_{id}_metadata.json`
2. **Generate TOML config** → `configs/updates/{board_name}_update.toml`
3. **Configure SQL query** → Edit `[query_config]` section
4. **Test with dry run** → Validate updates before execution
5. **Execute live updates** → Run with `--execute` flag

## 🎯 Best Practices

### File Organization
- Keep board metadata in `configs/boards/`
- Store TOML configs in `configs/updates/`
- Use descriptive filenames: `{board_name}_update.toml`

### Configuration Management
- **Always test** with `--dry_run` first
- **Verify column mappings** against actual data
- **Document custom queries** with comments
- **Version control** all configuration files

### Workflow Integration
- Use VS Code tasks for consistency
- Generate TOML configs for new boards
- Keep enhanced JSON for reference
- Test configurations before deployment

## 📞 Support

### Common Commands Reference
```powershell
# Generate enhanced JSON
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json

# Generate TOML configuration
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json --toml

# Custom TOML output path
python pipelines\codegen\create_script_mappings.py configs\boards\board_8709134353_metadata.json --toml -o configs\updates\my_config.toml

# Using VS Code task (recommended)
Ctrl+Shift+P → "Tasks: Run Task" → "Dev: Monday Boards Dynamic Generator"
```

### Related Documentation
- `docs/patterns/monday-board-configuration.md` - Board configuration patterns
- `docs/pipelines/opus-universal-updates.md` - OPUS update system documentation
- `configs/updates/README.md` - Update configuration guide

---

📝 **Last Updated**: July 15, 2025  
🔄 **Review Frequency**: Monthly  
👥 **Maintainer**: Data Orchestration Team
