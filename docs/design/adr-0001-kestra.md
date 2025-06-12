# ADR-0001 — Choose Kestra for Data Orchestration

| Status | Accepted |
|--------|----------|
| Date   | 2025-06-01 |
| Author | Chris Kalathas | Director of Digital Innovation |

---

## 1. Context

We must orchestrate ~10 daily ETL pipelines (soon 30+) that:

* extract data from WMS, TMS, ERP (SQL Server / CSV dumps)  
* transform & reconcile them in Python (pandas + rapidfuzz)  
* write back to Azure SQL and notify Monday.com  
* scale to 1 M+ tasks / month with reliable retries & lineage  
* run locally by devs and deploy the same config to staging & prod.

We evaluated **Apache Airflow**, **Azure Data Factory**, and **Kestra**.

## 2. Decision

Adopt **Kestra** (open-source, event-driven, YAML-as-code) as the single orchestration engine across all environments.

## 3. Options & Trade-offs

| Criteria | Airflow | Azure Data Factory | **Kestra (Chosen)** |
|----------|---------|--------------------|---------------------|
| Git-based flow definitions | DAG Python files | UI-driven (JSON export) | **YAML in repo — ✔** |
| Local-dev parity | Needs full Airflow stack | Impossible (cloud only) | **Docker Compose one-liner** |
| Plugin ecosystem | Huge | MSFT native only | 600+ plugins (JDBC, HTTP, Slack…) |
| Event throughput | High (Celery/K8s) | Good | **High (Pulsar) — millions/day** |
| Learning curve for analysts | Steep (Python DAG) | Low | **Low (YAML + UI)** |
| Cost | Self-host infra | Pay-per-activity | Self-host (VM) |
| Secrets | Env / Vault | Azure Key Vault | Env today ➜ Key Vault plugin |
| UI observability | Good | Good | **Excellent (topology + Gantt)** |

Kestra best fits our *mono-repo / GitOps* philosophy and gives non-Python users a friendlier YAML entry point, while still letting us embed full Python when needed.

## 4. Consequences

* **Infrastructure** — We will run the “full” Kestra image behind Nginx; Postgres metadata and Pulsar broker must be provisioned (already in `docker-compose.kestra.yml`).  
* **Developer Workflow** — All pipelines live under `flows/`; PR review required for any schedule change.  
* **CI/CD** — GitHub Actions workflow will lint YAML, run tests, then `PUT` flows to Kestra via API (CD pipeline).  
* **Future Migration Risk** — If project scope balloons to 1000+ flows we must benchmark Pulsar cluster and consider managed Kestra cloud.  
* **Fallback** — If Kestra proves unfit, Airflow remains Plan B; YAML flows are convertible to Python DAG generators with moderate effort.

## 5. Follow-ups

1. ADR-0002 — “Use Terraform provider for multi-env promotion?”  
2. ADR-0003 — “Baked Docker image vs `requirements:` installs per task”.  
3. Update onboarding docs with Kestra UI & CLI cheat-sheet.

---
