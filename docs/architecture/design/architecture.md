# 📐 Audit Platform – End-to-End Architecture (v2025-Q2)

> **Author:** Chris Kalathas | Director of Digital Innovation
> **Status:** Draft ✅ (PR # …)  
> **Last Updated:** 2025-06-01

---

## 1. Big-Picture Diagram

```mermaid
flowchart LR
    subgraph Source Systems
        A[WMS Packed v_packed_products.sql]
        B[WMS Shipped v_shipped.sql]
        C[MOL Orders v_master_order_list.sql]
    end

    subgraph Kestra Orchestrator
        D[Flows YAML<br/>ingestion/*] -->|Extract| E[Python ETL<br/>src/audit_pipeline/etl.py]
        E -->|Load Staging| F[(Azure SQL<br/>stg_* tables)]
        F -->|Transform| G[Python Matching<br/>src/audit_pipeline/matching.py]
        G -->|Write| H[(Azure SQL<br/>reconciled tables)]
        G -->|Excel| I[Excel Report<br/>outputs/*.xlsx]
        G -->|Notify| J[Monday.com<br/>adapters/monday.py]
    end

    A --> D
    B --> D
    C --> D
````



*Legend:*

* White boxes = code we own (in `src/`).
* Rounded boxes = data stores.
* **Kestra** drives every arrow; failures auto-retry, logs stored in Postgres metadata DB.

--- 

## 2. Component Overview

| Layer             | Tech                                           | Responsibility                                                               |
| ----------------- | ---------------------------------------------- | ---------------------------------------------------------------------------- |
| **Orchestration** | **Kestra** (`infra/docker-compose.kestra.yml`) | Scheduling, dependency graph, retries, secrets via `.env` ➜ KeyVault (prod). |
| **Transform**     | Python 3.11 (`pandas`, `rapidfuzz`)            | ETL, matching, variance calc, Excel export.                                  |
| **Storage**       | Azure SQL Database                             | Raw staging, reconciled fact tables, analytical views.                       |
| **Metadata**      | Postgres (inside Kestra stack)                 | Flow & execution state; file storage in `kestra-data` volume.                |
| **Event Bus**     | Apache Pulsar (Kestra default)                 | Task queue → horizontal scale.                                               |
| **Notification**  | Monday.com GraphQL                             | Status updates on pipeline success/failure.                                  |
| **CI/CD**         | GitHub Actions                                 | Lint → pytest → sqlfluff → build Docker image → deploy flows via API.        |

---

## 3. Data Flow Steps (MVP)

1. **Extract**
   *Kestra* triggers `ingestion/ingest_orders.yaml` (and packed/shipped equivalents).
   SQL views pull source data → saved as CSV/DF in task workspace.

2. **Standardise** (`etl.py`)

   * Wide → long melt (order sizes).
   * Upper-case, alias mapping, canonical customer column.

3. **Load → Staging**
   Bulk-insert into `stg_orders`, `stg_packed`, `stg_shipped`.

4. **Match & Reconcile** (`matching.py`)

   * Vectorised exact merge.
   * RapidFuzz fuzzy fallback.
   * Qty variance + quality flag fields.

5. **Persist**
   Upsert into `fact_order_recon`.

6. **Report** (`report.py`)
   Generate Excel with SUMMARY + ≤255 tabs; push to blob storage (future).

7. **Notify** (`monday.py`)
   Patch board item: status = Success/Fail, attach run log link.

---

## 4. Runtime Environments

| Env           | URL                              | Secrets Source              | Notes                              |
| ------------- | -------------------------------- | --------------------------- | ---------------------------------- |
| **Dev-local** | `http://localhost:8080`          | `.env` (git-ignored)        | Docker Compose stack.              |
| **Staging**   | `https://kestra-stg.company.com` | Azure Key Vault (`kv-stg`)  | Deployed via GH Actions on `main`. |
| **Prod**      | `https://kestra.company.com`     | Azure Key Vault (`kv-prod`) | Blue/green DB release pattern.     |

---

## 5. Security & Compliance

* All DB creds & API tokens referenced in flows via `{{ secret('…') }}`.
* Execution logs scrub secrets automatically (Kestra feature).
* Database network traffic limited to private subnet; bastion for manual SQL only.
* GDPR: raw source CSVs purged from task workspace after flow success (`cleanup` task).

---

## 6. Open Questions / Next ADR

1. Do we adopt Terraform provider [https://registry.terraform.io/providers/kestra-io/kestra](https://registry.terraform.io/providers/kestra-io/kestra) for flow promotion? *(ADR-0002 pending)*
2. Decide between container-image per flow vs. requirements-install at runtime once scale > 30 flows.
3. Long-term storage of Excel artefacts – Azure Blob vs SharePoint.

---

## 7. Changelog

| Date       | Author    | Change                               |
| ---------- | --------- | ------------------------------------ |
| 2025-06-01 | SDA & CDM | Initial draft architecture document. |

---

````

### 🚀 Next doc to create

`docs/design/adr-0001-kestra.md` – the Architecture Decision Record explaining **why** we chose Kestra over Airflow/Azure Data Factory.  (Ping me when you’re ready and I’ll draft it.)

---

### 🛠️  Batch script snippet to add new doc

Append to `add_docs_structure.bat`:

```bat
echo Adding architecture.md ...
type nul > docs\design\architecture.md
````

(Or rerun script if the file doesn’t exist yet.)
