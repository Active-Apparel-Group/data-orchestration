# Project Brief

The **Data Orchestration Repo** is a data integration project designed to automatically synchronize order data from our internal systems like Excel and various scattered databases to a Monday.com board. This project was initiated to streamline order tracking by bridging our internal order database with the Monday.com platform, ensuring that our operations team can visualize and manage order statuses in real-time on Monday.com.  This project will also serve up key business data to internal stakeholders and customers.

## Core Requirements and Goals

- **End-to-End Order Synchronization:** Automatically transfer new orders and their line items (sizes, quantities, etc.) from the internal `ORDER_LIST` database tables to a designated Monday.com board. Each order should appear as an item on the board, and each order’s line items should appear as subitems under the respective order item.

- **Ultra-Lightweight Architecture:** Keep the solution as simple and maintainable as possible. The target architecture uses only two core Python modules (`sync_engine.py` and `monday_api_client.py`) for the sync logic, rather than a complex multi-module system. This significantly reduces code complexity and improves maintainability.

- **Configuration-Driven Setup:** All environment-specific details (like database table names, field mappings to Monday.com columns, etc.) must be defined in configuration files (e.g., a TOML config). This allows the pipeline to run in different environments (development, production) without code changes and makes it easy to update mappings or settings.

- **Robust Error Handling & Logging:** The sync process should be fault-tolerant. Any failures (e.g., API rate limits, network issues, data errors) must be handled gracefully, with clear logging and without stopping the entire pipeline. Partial failures (like one order failing to sync) should not block others; such records should be retried or flagged for review.

- **Traceability and Auditability:** Every synchronized record should be traceable. The system updates the main tables (ORDER_LIST_V2, ORDER_LIST_LINES) directly with the Monday.com item IDs and subitem IDs, along with sync status flags. This provides an audit trail so we know which orders have been synced, which are pending, and if any failed. **DELTA complexity eliminated** in Task 19.0 architectural simplification.

- **Testability and Quality Assurance:** The project scope includes creating comprehensive integration tests. Each implementation task is paired with tests that must pass before the task is considered done. **No code change is complete until its corresponding test passes all success criteria.** Business-critical paths (e.g. creating orders and subitems on Monday.com) are to be covered by integration or end-to-end tests using production-like data.

## Project Scope

This pipeline covers **Step 4** of our order processing workflow. Steps 0–3 handle data ingestion and preparation (including merging headers, unpivoting size columns, and merging lines into main tables). **Step 4 (this project)** takes the prepared main table data and syncs it directly to Monday.com. **Revolutionary simplification achieved** - DELTA tables eliminated in Task 19.0, system now operates with direct main table operations (ORDER_LIST_V2, ORDER_LIST_LINES). The scope includes building the sync mechanism, ensuring data integrity throughout the sync, and verifying that the Monday.com board accurately reflects the content of our internal order list.

Out of scope for this project are the prior data preparation steps and any two-way sync (updates from Monday.com back to the database). The sync is currently one-directional: internal system → Monday.com. Also out of scope is long-term data archival; completed sync records will remain in the database (with a synced status) until separate housekeeping tasks remove or archive old data.

## Success Criteria

This project will be considered successful when:
- **Automatic Sync:** New orders appear on the Monday.com board with all relevant details without manual intervention.
- **Data Integrity:** Every order’s data on Monday.com matches the source data (including all line items and correct customer grouping) with no loss or duplication.
- **Performance:** The sync runs within acceptable time limits (e.g., able to process on the order of hundreds of records per minute) and respects Monday.com API rate limits (no throttling errors in normal operation).
- **Reliability:** The system can recover from common issues (network glitches, temporary API failures) by retrying or skipping and logging problem records, and it does not crash on single-record errors.
- **Maintainability:** The codebase is easy to understand and modify. Adding a new field to sync or changing a mapping should be achievable by updating configuration rather than altering code. New developers (or the AI agent assistant) should be able to pick up the project by reading the memory bank documentation and quickly get up to speed.
- **Full Test Pass:** All integration and end-to-end tests associated with the pipeline pass on the CI/CD pipeline, demonstrating that the implementation meets the expected behavior under various scenarios (happy path, error injection, large batch sizes, etc.).
