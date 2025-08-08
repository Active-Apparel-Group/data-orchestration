# TASK037 - Integrate MondayConfig Into Sync Order List Pipeline (Rate Limits + CLI)

**Status:** Pending  
**Added:** 2025-08-08  
**Updated:** 2025-08-08

## Original Request
Analyse the sync_order_list pipeline and Memory Bank for recent TOML-driven API concurrency and Monday.com API controls to maximize throughput under rate limits. Apply the centralized MondayConfig model to this pipeline. PLAN MODE – create a task for this activity and report back.

## Thought Process
- Centralized Monday rate limit management (TASK033) provides board-specific optimal batch sizes, concurrency, and unified retry/backoff honoring retry_in_seconds. This is integrated across ingestion/update scripts but not yet in sync_order_list.
- sync_order_list currently uses local TOML rate_limits (item_batch_size, group_batch_size, delay_between_batches, max_concurrent_batches) and true batch processing with aiohttp, plus conservative async semaphore and backoffs embedded in monday_api_client.py.
- Gaps to close:
  - Replace/augment ad-hoc client delays/semaphore logic with centralized MondayConfig parameters and retry_in_seconds handling.
  - Ensure SyncEngine passes the correct board context and respects centralized settings (with TOML as fallback for overrides).
  - Complete CLI command execution in cli.py (sync/retry/report/status), default to batch mode, keep flags for sequential and skip-subitems, and generate structured reports.
  - Add measurable throughput, backoff logging, and success metrics per test standards.

## Definition of Done
- MondayConfig is applied to sync_order_list end-to-end:
  - monday_api_client.py consumes MondayConfig for board-specific batch size, max concurrency, timeouts, and backoff using retry_in_seconds.
  - sync_engine.py loads MondayConfig and passes relevant parameters to the client; TOML values remain as explicit overrides where configured.
- CLI wiring completed in cli.py for sync, retry, report, and status commands:
  - Batch mode is the default; flags remain for sequential, skip-subitems, dry-run/execute, and report generation.
  - Output includes an executive summary, customer-level reports, and a run folder under reports/sync/{sync_id}.
- Logging/metrics:
  - Logs include rate-limit backoff events, effective throughput (items/sec), batch success counts, and error categorization.
- Tests (integration-first) cover:
  - Basic end-to-end sync in dry-run with centralized rate limits enabled.
  - Retry/backoff behavior honoring retry_in_seconds.
  - CLI command paths: sync and report generation.
- Documentation updated:
  - Memory Bank progress entries; brief runbook note in docs/pipelines (or existing sync docs) for new flags/behavior.

## Implementation Plan
1. Discovery and Wiring
   - Identify the centralized MondayConfig interfaces (from TASK033) and how board settings are retrieved.
   - Add MondayConfig loading to sync_order_list config path and ensure environment awareness.
2. Client Integration
   - Update monday_api_client.py to consume MondayConfig for:
     - request timeout, batch sizes, max concurrency, and delay strategies
     - retry/backoff using retry_in_seconds when returned by API
   - Maintain TOML overrides if present.
3. Engine Integration
   - Update sync_engine.py to initialize MondayConfig and pass configuration/context to MondayAPIClient.
   - Ensure group creation batch behavior aligns with centralized group settings.
4. CLI Completion
   - Implement sync, retry, report, and status command handlers in cli.py.
   - Default to batch; keep flags for sequential and skip-subitems; ensure report artifacts are generated consistently.
5. Instrumentation & Reporting
   - Add structured logs for backoff events and throughput; include in executive summaries where useful.
6. Tests & Validation
   - Create integration tests exercising dry-run sync with MondayConfig and verify measurable metrics (e.g., success rate ≥ 95%; no unhandled rate-limit errors).
   - Add a report generation validation test.
7. Docs
   - Update Memory Bank progress and a short usage note under docs/pipelines (or existing sync docs).

## Progress Tracking
**Overall Status:** Not Started - 0%

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 1.1 | Load and access MondayConfig in sync_order_list | Not Started | 2025-08-08 | Use board-specific settings; honor env |
| 1.2 | Apply MondayConfig to monday_api_client.py | Not Started | 2025-08-08 | Replace ad-hoc semaphore/delays; keep overrides |
| 1.3 | Wire SyncEngine to pass centralized settings | Not Started | 2025-08-08 | Fallback to TOML when explicitly set |
| 1.4 | Implement CLI command handlers in cli.py | Not Started | 2025-08-08 | sync/retry/report/status; default batch |
| 1.5 | Add instrumentation (throughput/backoff metrics) | Not Started | 2025-08-08 | Log + summary inclusion |
| 1.6 | Integration tests: rate-limit + CLI | Not Started | 2025-08-08 | Dry-run E2E, retry_in_seconds honor |
| 1.7 | Documentation updates | Not Started | 2025-08-08 | Memory Bank + short runbook note |

## Relevant Files
- `src/pipelines/sync_order_list/cli.py` – CLI command wiring (sync/retry/report/status)
- `src/pipelines/sync_order_list/config_parser.py` – Existing TOML config, environment-aware; maintain overrides
- `src/pipelines/sync_order_list/sync_engine.py` – Orchestration; pass centralized settings; preserve true batch processing
- `src/pipelines/sync_order_list/monday_api_client.py` – Apply centralized concurrency, timeouts, and retry/backoff
- `src/pipelines/sync_order_list/merge_orchestrator.py` – Ensure group batch creation aligns with centralized settings
- Centralized MondayConfig system from TASK033 (board registry + rate limits) – consumed by the above

## Test Coverage Mapping
| Implementation Task | Test File | Outcome Validated |
|---------------------|----------|-------------------|
| MondayConfig applied to client | tests/sync_order_list/integration/test_rate_limit_integration.py | retry_in_seconds honored; no unhandled rate-limit errors |
| Engine uses centralized settings | tests/sync_order_list/integration/test_engine_centralized_config.py | Batch sizes and concurrency match board config |
| CLI sync + report | tests/sync_order_list/integration/test_cli_sync_and_report.py | Dry-run E2E runs; summary and customer reports generated |

## Progress Log
### 2025-08-08
- Task created with scope, DoD, and plan. Pending implementation kickoff.
