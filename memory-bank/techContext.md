# Tech Context

## Technologies and FrameIn summary, the tech context of this project is centered on a Python-based ETL-like process, using web APIs and SQL, configured via external files, and aligned with our existing data engineering frameworks. The choices made keep the solution efficient and maintainable given our team's skill set and the technologies at hand.

## Performance Optimization Context (2025-08-01)

**✅ CRITICAL FIXES COMPLETE:**
- **Batch Processing Validated**: TRUE BATCH PROCESSING confirmed working with proper dropdown configuration handling
- **Dropdown Configuration**: TOML settings properly respected, createLabelsIfMissing working correctly
- **Report Generation**: Customer processing reports generating without database schema errors
- **Code Quality**: Verbose logging cleaned up, essential operation tracking maintained

**NEXT PHASE OPTIMIZATION OPPORTUNITIES:**
- **Default Batch Mode**: Change sync_engine.py default from 'single' to 'batch' mode for production efficiency
- **Logging Optimization**: Convert None value warnings to DEBUG level to reduce I/O overhead
- **Performance Monitoring**: Add timing instrumentation between operations for production monitoring
- **Target Performance**: <1 second per record achievable with optimized default configuration

- **Programming Language:** Python 3.x is used for the pipeline implementation. Python was chosen for its ease of scripting, rich ecosystem (for things like HTTP requests, database access, etc.), and alignment with the rest of our data engineering stack.
- **Database:** The source order data resides in a SQL database (Microsoft SQL Server). We use SQL queries (including complex SQL templated via Jinja2) to interact with the `ORDER_LIST` tables and delta tables. Python’s DB-API (via a library like `pyodbc` or an ORM if any) is used to execute queries.
- **Monday.com GraphQL API:** Communication with Monday.com is done through their GraphQL API. We send HTTP requests (POST) with GraphQL queries/mutations to create items, subitems, and groups on the Monday board. We use **GraphQL query templates** stored as `.graphql` files, loaded and filled in by our Python code. This approach lets us maintain the GraphQL outside of code and easily adjust queries as needed.
- **HTTP Client:** The implementation uses an asynchronous HTTP client (the project references `aiohttp`) to manage API calls to Monday.com efficiently. Async is leveraged so we can perform multiple calls concurrently (up to a safe limit), which is important for throughput given the rate limiting.
- **Config Files:** We use **TOML** (Tom’s Obvious Minimal Language) for configuration (file: `configs/pipelines/sync_order_list.toml`). TOML was selected because it’s human-readable, supports hierarchical config, and is well-supported in Python (via libraries like `toml` or similar). It cleanly separates dev vs prod settings.
- **Jinja2 Templating:** For the earlier part of the pipeline (SQL generation for merging data), we use Jinja2 templates. This templating engine allows us to embed logic in SQL files (like looping through dynamic columns). Jinja2 is a common templating library in Python known for its performance and simplicity.

## Development Environment & Setup

- **Local Development:** Developers can run this pipeline on their local machines by pointing to a development database and a Monday.com dev board. Environment variables or config entries store sensitive info (like Monday.com API tokens, database connection strings) so they are not hard-coded. The code is structured as a Python package (`src/pipelines/sync_order_list`), so running it might involve installing the package or using `python -m src.pipelines.sync_order_list.cli` for the CLI interface.
- **Source Control:** The project is managed in Git (in our internal repository). All changes are tracked, and code reviews are required for merging changes, especially given the critical nature of this integration.
- **Testing Framework:** We rely on **PyTest** for running integration tests and end-to-end tests (the repository has a `tests/sync-order-list-monday/` directory with various test modules). Developers run these tests in a controlled environment (possibly with a test database containing sample data). There’s also mention of an E2E test hitting a Monday dev board with test API keys.
- **CI/CD:** The continuous integration pipeline runs the full test suite on each commit. For deployment, since this is a data pipeline script, it may be deployed as part of a batch job or invoked via an orchestration tool. Deployment likely involves updating the code on our data processing server or container and ensuring the config is set for the target environment.

## Technical Constraints & Considerations

- **API Rate Limits:** Monday.com’s API has a rate limit (~10 requests per second by default and complexity limits per query). This was a major constraint that influenced design. The solution must batch requests and throttle itself to avoid hitting these limits. We’ve implemented a conservative approach (limiting concurrency and adding slight delays) to respect this constraint.
- **Data Volume:** Each run may sync tens or hundreds of orders (with their line items). The design assumes possibly up to a few hundred orders in a batch (based on test data of ~69 new orders with 317 line items). Performance considerations include making sure the solution can scale if those numbers grow (for example, processing 500+ orders with thousands of line items in a reasonable time frame). The lightweight design and use of batch APIs is meant to allow scaling, but if volumes grow significantly, we might need to revisit concurrency and batching logic.
- **Transactional Integrity:** The database operations (moving orders from NEW to SYNCED state, etc.) ideally should be atomic per order or batch. We’ve considered using transactions for updating the status after a successful sync. It’s important that if a sync fails mid-way, we don’t incorrectly mark records as synced. The current approach updates states only after confirming success from the API.
- **Idempotency:** The pipeline is designed to be safe to re-run. Because of the sync state flags and the presence of Monday.com item IDs after a sync, if the pipeline runs again it should ideally detect already-synced records and skip or handle them appropriately. This means we need to either filter those out in SQL queries or have logic to not duplicate items on Monday (which might involve checking if an item already exists for a given record). We rely on our delta tables filtering (`sync_state != 'SYNCED'`) to achieve this.
- **Dependencies:** Besides the Python standard library, this project likely depends on:
  - `aiohttp` (for async HTTP calls),
  - `pandas` or `pyodbc`/`sqlalchemy` for database interactions (not explicitly stated, but common in our pipelines),
  - `jinja2` for templating,
  - Possibly a config library for TOML (like `pytoml` or `toml`).
  All these dependencies are managed in the project’s environment (e.g., specified in a requirements file or pipenv).
- **Security:** The Monday.com API token is a sensitive credential. It’s stored securely (not in the code or repo). Likely fetched from an environment variable or a secure store by the pipeline at runtime. We ensure not to log this token or expose it. Also, any data being sent (order details) isn’t extremely sensitive (mostly order meta-data), but it’s still internal info, so we treat the pipeline and logs with appropriate confidentiality.
- **Logging & Monitoring:** We have a logging utility (`src/pipelines/utils/logger.py`) integrated. The pipeline logs key events (like “Created 20 items on Monday.com successfully” or errors from the API). For production, we plan to monitor these logs and possibly set up alerts if a sync fails or if there are records stuck in `PENDING` for too long. The design anticipates adding more monitoring in Task 10 (Monitoring and Maintenance).
- **Development vs Production Config:** The TOML config has separate sections for development and production. In dev, for example, the Monday board ID might be a sandbox board (ID `9609317401` as noted in documentation), whereas in production it’s the real board (ID `8709134353`). Similarly, dev might use a test database/schema. The code reads a flag or environment to decide which config section to use. This separation ensures we can test safely in an isolated environment before pointing the pipeline at live data.

## Dependencies Within Codebase

This project doesn’t operate in isolation; it integrates with our existing codebase:
- Upstream, it relies on outputs of previous pipeline steps (which populate the delta tables). Those are implemented as SQL merge scripts and possibly Python orchestrators (like `merge_orchestrator.py` used for earlier steps).
- It uses shared utilities in `src/pipelines/utils/` (like `db.py` for database connections and `logger.py` for consistent logging).
- It also uses the shared `graphql_loader.py` in `src/pipelines/integrations/monday/`, which means other Monday integrations or utilities exist in the codebase. Our pipeline leverages that instead of duplicating GraphQL file loading logic.

Being aware of these helps when setting up the dev environment (ensuring the whole package is installed or PYTHONPATH is set so that `src.pipelines.utils` and `src.pipelines.integrations.monday` are available to our modules).

In summary, the tech context of this project is centered on a Python-based ETL-like process, using web APIs and SQL, configured via external files, and aligned with our existing data engineering frameworks. The choices made keep the solution efficient and maintainable given our team’s skill set and the technologies at hand.