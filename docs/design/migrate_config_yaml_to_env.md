
Below is a **migration play-book** that shows exactly **how to turn your old `config.yaml`** into environment-variable–based secrets for Kestra **and** how to wire them into the Docker Compose stack.
A short **batch helper** (`yaml2env.bat`) is included to speed up the conversion for dev use.

---

## 1. Naming & Encoding strategy

| What                                                | Rule                                                                                                          | Example                                             |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **Sensitive values** (passwords, full JDBC strings) | Store in `.env` with prefix **`SECRET_`** and **Base64-encode the value** (Kestra loads those automatically). | `SECRET_DMS_PWD=bWFnaWNQYXNzIQ==`                   |
| **Non-secret values** (host, port, DB name)         | Plain env vars — no prefix, human-readable.                                                                   | `DB_DMS_HOST=ross-db-srv-test.database.windows.net` |
| **Variable casing**                                 | All env vars **UPPER\_SNAKE\_CASE**.                                                                          | `DB_DMS_USERNAME=admin_ross`                        |
| **Multi-word keys**                                 | Chain with `_` not dots.                                                                                      | `DB_DMS_ITEM_DATABASE=DMS_ITEM`                     |

### Why Base64 for passwords?

Kestra’s secret loader reads any env var that starts with `SECRET_`, decodes Base64, and puts it in its encrypted secret store.
At flow runtime you call it with:

```yaml
password: "{{ secret('DMS_PWD') }}"
```

*(note: drop the prefix).*

---

## 2. `.env.example` template (snippet)

```dotenv
#############  DMS  #############
DB_DMS_HOST=ross-db-srv-test.database.windows.net
DB_DMS_PORT=1433
DB_DMS_DATABASE=DMS
DB_DMS_USERNAME=admin_ross
SECRET_DMS_PWD=QWN0aXZlQElUMjAyMw==   # <-- Base64("Active@IT2023")

#############  INFOR 13.2 #############
DB_INFOR_132_HOST=192.168.30.7
DB_INFOR_132_PORT=1433
DB_INFOR_132_DATABASE=M3FDBPRD
DB_INFOR_132_USERNAME=sa
SECRET_INFOR_132_PWD=SW5mb3IxMjM=      # <-- "Infor123"
DB_INFOR_132_ENCRYPT=no
DB_INFOR_132_TRUSTSERVERCERTIFICATE=yes
```

*(repeat for every entry in old YAML).*

Keep this file in Git; real `.env` (with prod secrets) is **git-ignored**.

---

## 3. Update `infra/docker-compose.kestra.yml`

```yaml
services:
  kestra:
    image: kestra/kestra:latest-full
    env_file:
      - ../.env           # <── loads all DB_* and SECRET_* vars
    environment:
      # Add Kestra-specific overrides below if needed
      KESTRA_LOGGER_LEVEL: INFO
```

*(Postgres & Pulsar services don’t need DB\_* variables, so keep env\_file only on `kestra`.)\*

---

## 4. Refactor `config.py` (already stubbed)

```python
import os

def _env(key, default=None):
    val = os.getenv(key, default)
    if val is None:
        raise RuntimeError(f"Missing env var: {key}")
    return val

def get_db_config(name: str) -> dict:
    """
    Reconstruct DB config dict from env variables.
    name = 'dms' -> DB_DMS_HOST, DB_DMS_PORT, ...
    """
    prefix = f"DB_{name.upper()}_"
    cfg = {
        'host': _env(prefix + 'HOST'),
        'port': int(_env(prefix + 'PORT', 1433)),
        'database': _env(prefix + 'DATABASE'),
        'username': _env(prefix + 'USERNAME'),
        'password': os.getenv(f"SECRET_{name.upper()}_PWD")  # fetched later via secret()
    }
    # optional flags
    cfg['encrypt'] = os.getenv(prefix + 'ENCRYPT', 'yes')
    cfg['trustServerCertificate'] = os.getenv(prefix + 'TRUSTSERVERCERTIFICATE', 'no')
    return cfg
```

Inside a **Kestra** flow you’d reference secrets like:

```yaml
- id: load-dms
  type: io.kestra.plugin.jdbc.mssql.Query
  url: "jdbc:sqlserver://{{ env('DB_DMS_HOST') }}:{{ env('DB_DMS_PORT') }};database={{ env('DB_DMS_DATABASE') }};encrypt={{ env('DB_DMS_ENCRYPT') }};trustServerCertificate={{ env('DB_DMS_TRUSTSERVERCERTIFICATE') }}"
  username: "{{ env('DB_DMS_USERNAME') }}"
  password: "{{ secret('DMS_PWD') }}"
  sql: "SELECT 1"
```

---

## 5. One-time helper script — **`yaml2env.bat`**

For devs who still have the old `config.yaml`, this converts passwords to base64 and prints `.env` lines.
*(Run in a prompt with Python available.)*

```bat
@echo off
REM  yaml2env.bat  path\to\config.yaml  > .env
python - <<PY
import sys, yaml, base64, re
cfg = yaml.safe_load(open(sys.argv[1]))
for name, db in cfg['databases'].items():
    upper = name.upper()
    print(f"DB_{upper}_HOST={db['host']}")
    print(f"DB_{upper}_PORT={db.get('port',1433)}")
    print(f"DB_{upper}_DATABASE={db['database']}")
    print(f"DB_{upper}_USERNAME={db['username']}")
    pw = base64.b64encode(db['password'].encode()).decode()
    print(f"SECRET_{upper}_PWD={pw}")
    for opt in ['encrypt','trustServerCertificate']:
        if opt in db:
            key = opt.upper().replace('TRUSTSERVERCERTIFICATE','TRUSTSERVERCERTIFICATE')
            print(f"DB_{upper}_{key}={db[opt]}")
    print()
PY %*
```

---

## 6. Migration checklist (add to `phase01_mvp.md`)

```markdown
### 🔑  Secrets migration
- [ ] Convert old `config.yaml` to `.env` via `yaml2env.bat`; commit **only** `.env.example`.
- [ ] Refactor `config.py` to pull creds from env.
- [ ] Update Kestra docker-compose with `env_file: ../.env`.
- [ ] Test SQL connection using `python -c "from audit_pipeline.config import get_db_config, get_connection; print(get_connection('dms'))"`.
```

---

### Summary

* **Sensitive fields** → `SECRET_XXX` Base64 in `.env`
* **Non-secret fields** → plain `DB_XXX` vars
* **Kestra** auto-ingests secrets; code reads env for non-secret parts
* Batch helper eases one-time migration from legacy YAML

Move these instructions into `docs/runbooks/migrate_yaml_to_env.md` for future reference, then continue ticking items in **Phase-01 MVP**.
