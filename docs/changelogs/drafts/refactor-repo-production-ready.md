# 🚀 Repo Restructure Plan: Modern Python Packaging & Project Layout

> **Goal:**
> Migrate to a modern, modular Python repo using `src/` layout, `pyproject.toml`, and explicit, import-safe package structure for scalable data/ETL orchestration.

---

## 🗂️ Final Target Repo Structure
> This is the final structure you will achieve after completing the migration:



```text
repo-root/                       # top‑level Git repo
├─ src/                          # “src layout” → import‑safe after `pip install -e .`  # <—— only Python lives here
│  └─ pipelines/                 # installable namespace package (move all pipelines here)
│     ├─ __init__.py             # empty -> marks package root
│     ├─ utils/
│     │  ├─ __init__.py
│     │  ├─ db.py                # connection helpers
│     │  └─ loader.py            # render_sql(), load_config()
│     ├─ load_order_list/        # specific pipeline module
│     │  ├─ __init__.py
│     │  ├─ etl.py               # extract logic
│     │  ├─ transform.py         # transform/merge logic
│     │  ├─ scripts/             # CLI entry‑points → `python -m ...`
│     │  │  └─ load.py
│     │  └─ resources/           # packaged defaults # “baked-in” defaults
│     │     ├─ sql/
│     │     │  └─ order_list_stage.sql.j2
│     │     └─ config/
│     │        └─ default.toml
│     └─ inventory/              # future pipeline (stub)
│        └─ __init__.py
│
├─ configs/                      # env‑specific overrides (not packaged) # env-specific overrides (NOT packaged)
│   ├─ dev/
│   │  └─ order_list.toml
│   └─ prod/
│      └─ order_list.toml
│
├─ docs/
|
├─ integrations/
|   ├─ graphql                   
|
├─ db/                           # DDL / migrations (Alembic layout) # migrations & seeds @
│   ├─ alembic.ini
│   ├─ env.py
│   └─ versions/
│       └─ *.py
│
├─ workflows/                    # Kestra YAML definitions (move out of pipelines folder) # Kestra YAML
│   ├─ ingest_order_list.yml
│   └─ flow_sync_prod.yml
│
├─ tests/
│   ├─ test_no_path_hacks.py     # CI guard for sys.path inserts
│   └─ test_order_list_etl.py
│
├─ specs/                        # project docs/specs
│   └─ 2025‑07_repo_refactor.md
│
├─ tools/                       # .ps1 scripts, will need to be refactored, as will tasks.json
|
├─ .gitignore                    # standard Python + IDE ignores
├─ .env
├─ .env_encoded                  # base64 for Kestra
├─ requirements.txt
├─ docker-compose.dev.yml        # local Kestra + live reload
├─ dockerfile                    # builds ghcr.io/active-apparel/pipelines
├─ pyproject.toml                # PEP‑621 package + data‑files
├─ .vscode/
│   └─ tasks.json                # “Kestra: validate flows”
└─ README.md


missing from above __legacy/
-- move existing src/ folder here first
-- move /utils from root here
-- move /templates here

```
---

## 📝 Milestones, Checklist, and Key
### **Milestone 1: Create and Confirm Directory Layout**

* [ ] Create `__legacy/`, move selected folders here include `src/`, `utils/`, `templates/`
* [ ] Create new `src/pipelines/`, with subfolders for each pipeline (e.g. `order_list/`, `utils/`)
* [ ] Add empty `__init__.py` to each Python folder

---

### **Milestone 2: Move and Refactor Code**

* [ ] Move all code, helpers, scripts into the correct new locations
* [ ] Refactor all imports to package-style (e.g. `from pipelines.utils.db import ...`)
* [ ] Remove all `sys.path.insert` or path hack code from all files

---

### **Milestone 3: Add and Configure `pyproject.toml`**

* [ ] Create a `pyproject.toml` in the repo root:

  ```toml
  [project]
  name = "pipelines"
  version = "0.1.0"
  description = "AAG Data Orchestration and Engineering"
  authors = [{name = "Chris Kalathas"}]
  requires-python = ">=3.10"
  dependencies = [
    "pandas>=2.0",
    "tomli",
  ]

  [build-system]
  requires = ["setuptools>=64", "wheel"]
  build-backend = "setuptools.build_meta"
  ```
* [ ] (Optional) Add `[tool.setuptools.package-data]` to package SQL/templates with code

---

### **Milestone 4: Install in Editable Mode**

* [ ] In repo root, run:

  ```bash
  python -m pip install -e .
  ```
* [ ] Confirm you can run `python -c "from pipelines.utils.db import ..."` without error

---

### **Milestone 5: Add/Update Tests**

* [ ] Create or update `tests/test_imports.py` to verify key imports:

  ```python
  def test_imports():
      from pipelines.utils import db, loader
      from pipelines.order_list import etl, transform
  ```
* [ ] Add/Update `tests/test_no_path_hacks.py` to ensure no path hacks:

  ```python
  import pkgutil, inspect, re, pipelines
  BAD = re.compile(r"sys\.path\.(insert|append)")
  for mod in pkgutil.walk_packages(pipelines.__path__, "pipelines."):
      src = inspect.getsource(__import__(mod.name, fromlist=["x"]))
      assert not BAD.search(src), f"Path hack in {mod.name}"
  ```
* [ ] Run all tests with `pytest` and confirm pass

---

### **Milestone 6: Update README and Doc Files**

* [ ] Add new structure and install/run instructions to `README.md`
* [ ] Optionally: add a quickstart code sample for “import, run, test”

---

### **Milestone 7: (Optional) Add/Update CI Pipeline**

* [ ] If using GitHub Actions: Add a workflow to run `pytest` on push/PR

---

## ✅ **Completion Criteria**

* [ ] All Python modules are under `src/pipelines/`
* [ ] All imports use package-style (no `sys.path` hacks)
* [ ] Project installs and runs with `pip install -e .`
* [ ] Tests pass
* [ ] README is accurate
* [ ] Ready for modular pipeline expansion, CI, SQL/resource packaging, etc.

---

## 🔬 **Sample Test: `tests/test_imports.py`**

```python
def test_imports():
    from pipelines.utils import db, loader
    from pipelines.order_list import etl, transform
```

## 🚦 **Sample Test: `tests/test_no_path_hacks.py`**

```python
import pkgutil, inspect, re, pipelines
BAD = re.compile(r"sys\.path\.(insert|append)")
for mod in pkgutil.walk_packages(pipelines.__path__, "pipelines."):
    src = inspect.getsource(__import__(mod.name, fromlist=["x"]))
    assert not BAD.search(src), f"Path hack in {mod.name}"
```

---

## 🏁 **Your next actions**

* [ ] Copy and create the directory structure above
* [ ] Move and refactor code
* [ ] Add/init `pyproject.toml`
* [ ] Update imports, install editable, and test
* [ ] Ship and expand

---

**Once these milestones are complete, your repo will be modern, robust, and ready for next-gen ETL/data orchestration.**
Ready for follow-up with ETL modularization, SQL externalization, CI/CD, etc!

Let me know when you want the next phase.
