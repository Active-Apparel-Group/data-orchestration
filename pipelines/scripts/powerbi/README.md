# Power BI Operations - Organized Structure

**Location:** `pipelines/scripts/powerbi/`  
**Purpose:** Clean, organized Power BI operations domain  
**Status:** ✅ Organized and Production Ready

---

## 📁 Directory Structure

### **🏗️ `/core/` - Production Core Files**
```
core/
└── powerbi_manager.py          # Universal Power BI manager (CLI + functions)
```

**Usage:**
```bash
# Universal manager operations
python pipelines/scripts/powerbi/core/powerbi_manager.py load-tokens
python pipelines/scripts/powerbi/core/powerbi_manager.py refresh-dataflow --dataflow order_list_dataflow
```

### **⚙️ `/operations/` - Specific Operations**
```
operations/
├── refresh_dataflow.py         # Simple dataflow refresh operations
└── generate_admin_consent_url.py # Admin consent URL generator
```

**Usage:**
```bash
# Simple dataflow refresh
python pipelines/scripts/powerbi/operations/refresh_dataflow.py

# Generate admin consent URL
python pipelines/scripts/powerbi/operations/generate_admin_consent_url.py
```

---

## 🧪 Test & Debug Files

**Location:** `tests/powerbi/`  
- **`debug/`** - Active development and testing files
- **`archive/`** - Obsolete files kept for reference

All experimental implementations, test scripts, and debug utilities have been moved to the tests directory to keep production code clean.

---

## 🎯 Key Production Files

1. **Universal Manager:** `core/powerbi_manager.py`  
   - Primary entry point for all Power BI operations
   - CLI interface + importable functions
   - Kestra-compatible logging and error handling

2. **Simple Operations:** `operations/refresh_dataflow.py`  
   - Lightweight dataflow refresh
   - Perfect for simple automation scenarios

3. **Admin Utilities:** `operations/generate_admin_consent_url.py`  
   - Generate admin consent URLs for service principal setup

---

## 🔗 Integration Points

- **Kestra Workflows:** All scripts use `logger_helper` for consistent logging
- **Database Operations:** Leverage `db_helper` for configuration and connections  
- **Authentication:** Use centralized `pipelines/scripts/auth/` domain
- **Configuration:** Shared `pipelines/utils/powerbi_config.yaml`

---

*This organization ensures clean separation between production code and development/testing files while maintaining full backward compatibility.*
