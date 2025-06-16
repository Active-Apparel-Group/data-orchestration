# 🏗️ KESTRA PROJECT ORGANIZATION RULES

## 📁 **CLEAN PROJECT STRUCTURE**

### ✅ **ROOT LEVEL - KEEP MINIMAL:**
```
kestra-start/
├── 📋 *.yml                    (ONLY production workflows)
├── 🐳 docker-compose.yml       (Infrastructure)
├── 🐳 dockerfile               (Infrastructure)
├── ⚙️ .env, .env_encoded       (Configuration)
├── 📄 requirements.txt         (Dependencies)
├── 🛠️ makefile                 (Build automation)
├── 📚 README.md                (Main documentation)
└── 📁 Organized folders/       (Everything else organized)
```

### 📁 **ORGANIZED FOLDER STRUCTURE:**

```
├── 📁 workflows/               (Production workflows)
│   ├── test-sql-with-variables.yml
│   ├── test-enhanced-sql-script.yml
│   └── *.yml
│
├── 📁 scripts/                 (Python scripts for Kestra)
│   ├── test_sql_with_env.py
│   ├── test_sql_enhanced.py
│   └── *.py
│
├── 📁 queries/                 (SQL queries for Kestra)
│   ├── v_master_order_list.sql
│   └── *.sql
│
├── 📁 tools/                   (Helper scripts & utilities)
│   ├── deploy-workflows.ps1
│   ├── kestra-helper.ps1
│   └── *.ps1
│
├── 📁 docs/                    (Documentation)
│   ├── KESTRA-SETUP-NOTES.md
│   ├── DEPLOYMENT-COMPLETE.md
│   └── *.md
│
├── 📁 .github/                 (CI/CD)
│   └── workflows/
│
├── 📁 tests/                   (Test files & experiments)
│   ├── simple-deployment-test.ps1
│   ├── test-*.ps1
│   └── experiments/
│
└── 📁 _backup/                 (Archive old files)
    └── (old files)
```

## 🚨 **GROUND RULES:**

### ✅ **DO:**
1. **Keep root clean** - Only essential files
2. **Use folders** - Organize by purpose
3. **Name clearly** - Descriptive file names
4. **Document changes** - Update README when adding files
5. **Clean as you go** - Move test files immediately

### ❌ **DON'T:**
1. **Dump test files in root** - Use tests/ folder
2. **Keep multiple versions** - Use git, not file copies
3. **Leave experiments around** - Clean up or move to tests/
4. **Mix production and test** - Separate clearly
5. **Create files without purpose** - Every file should have a reason

## 🎯 **FILE NAMING CONVENTIONS:**

- **Workflows**: `kebab-case.yml` (e.g., `database-connection-test.yml`)
- **Scripts**: `snake_case.py` (e.g., `test_sql_with_env.py`)
- **Tools**: `kebab-case.ps1` (e.g., `deploy-workflows.ps1`)
- **Docs**: `UPPER-CASE.md` (e.g., `SETUP-NOTES.md`)
- **Tests**: `test-*.ps1` or `*-test.ps1`

## 🧹 **CLEANUP PROCESS:**

1. **Identify file purpose** - What is this file for?
2. **Move to correct folder** - Based on purpose
3. **Remove duplicates** - Keep only working versions
4. **Update references** - Fix any broken paths
5. **Document structure** - Update README

---

**Remember: A clean project is a maintainable project! 🏆**
