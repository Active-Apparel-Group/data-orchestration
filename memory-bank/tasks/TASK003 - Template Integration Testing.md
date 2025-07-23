# TASK003 - Template Integration Testing

**Status:** Completed  
**Added:** 2025-01-07  
**Updated:** 2025-01-09  

## Original Request
After implementing the template-driven architecture for SQL (Tasks 1 and 2), we needed to rigorously test each part of the template integration to ensure that the output and behavior match expectations. The request was to create a battery of **integration tests** targeting the newly introduced Jinja2 templates (headers merge, size unpivot, lines merge) and their corresponding Python integration, to catch any issues early and guarantee correctness.

## Thought Process
The shift to dynamic SQL generation introduced a lot of flexibility, but also the risk of subtle errors (like missing a column in the template, or misordering things). We determined that targeted tests were necessary:
- Each template should be tested in isolation with a controlled environment, to verify it produces the correct SQL and that executing that SQL yields expected results.
- We planned to use a subset of real data or known test fixtures for these tests. Possibly, create a temporary table or use a small portion of `ORDER_LIST_V2` for predictable results.
- We identified three critical areas for testing:
  1. **Header Merge Template (`merge_headers.j2`)** – does it correctly bring together all header fields (including any aggregated fields) into `ORDER_LIST_DELTA`?
  2. **Size Unpivot Template (`unpivot_sizes.j2`)** – does it convert wide size columns to rows properly? This one is particularly tricky due to the large number of columns.
  3. **Lines Merge Template (`merge_lines.j2`)** – does it correctly associate line items with order headers and populate `ORDER_LIST_LINES_DELTA`?

We also wanted to simulate the pipeline running end-to-end in a test environment (though that overlaps with Task005, which is a full pipeline test, at this stage we focus on individual parts).
The approach:
- Use the config with dynamic columns from Task002 to feed the templates in tests (ensuring we test with the real set of columns).
- Pre-load some test data into a known state (maybe use an existing small order example).
- Run the SQL produced by each template in the test database (within a transaction or a test schema) and verify the outputs.

## Implementation Plan
- **Step 1:** Create an **integration test for header merge**:
  - Setup: Ensure `swp_ORDER_LIST_V2` (or a copy) has at least one known new order. Possibly use the GREYSON CLOTHIERS test PO data (with 69 new orders) or a smaller subset.
  - Action: Invoke the `merge_headers.j2` via the pipeline code (or directly call template engine with context) to merge into `ORDER_LIST_DELTA` table.
  - Assert: After execution, check that `ORDER_LIST_DELTA` has the expected number of records (e.g., 69 if that’s the number of new orders) and key fields (like record_uuid, order number, etc.) are correctly populated.
- **Step 2:** Create an **integration test for unpivot sizes**:
  - Setup: Run the header merge first so that we have a context of data with wide columns, or isolate this by creating a temp table that mimics a single order’s size columns.
  - Action: Execute the `unpivot_sizes.j2` template which should output a normalized table or intermediate result.
  - Assert: Verify that the result contains one row per size per order, and that the total number of rows equals the sum of quantities or entries in the wide format. Essentially, ensure no sizes are lost or duplicated.
- **Step 3:** Create an **integration test for lines merge**:
  - Setup: Assume header merge and unpivot have provided needed intermediate data.
  - Action: Run the `merge_lines.j2` template to populate `ORDER_LIST_LINES_DELTA`.
  - Assert: Check that each line item is present in `ORDER_LIST_LINES_DELTA` with correct foreign keys (record_uuid matching the header, and line identifiers).
- **Step 4:** Possibly combine the above into one larger test scenario:
  - End-to-end integration (though that’s Task005, some overlap might occur if we test sequence of templates here as well).
- **Step 5:** Use real data for validation:
  - For example, after running all templates, the count of records in delta tables should match known criteria (like the known number of new orders, etc.).
  - Cross-verify a sample: pick one order and ensure its fields in `ORDER_LIST_DELTA` match source, and that all its line items appear in `ORDER_LIST_LINES_DELTA`.

## Progress Tracking

**Overall Status:** Completed – 100%

### Subtasks
| ID   | Description                                   | Status   | Updated     | Notes                                                   |
|------|-----------------------------------------------|----------|-------------|---------------------------------------------------------|
| 3.1  | Write integration test for merge_headers.j2    | Complete | 2025-01-08  | Verified header delta population (69 records as expected) |
| 3.2  | Write integration test for unpivot_sizes.j2    | Complete | 2025-01-08  | Verified unpivot of all size columns, correct row count |
| 3.3  | Write integration test for merge_lines.j2      | Complete | 2025-01-09  | Verified lines delta population and foreign key linking |
| 3.4  | Run combined sequence tests (headers → lines)  | Complete | 2025-01-09  | Full sequence validated via tests (overlap with Task005)|
| 3.5  | Review test results and adjust templates       | Complete | 2025-01-09  | Minor tweaks done, all tests passing                    |

### Success Gates
- No task is complete until all its related tests pass successfully.
- **Success Gate:** Each template’s integration test passes:
  - Headers merge test should confirm correct number of records and accurate data in `ORDER_LIST_DELTA`.
  - Sizes unpivot test should confirm that every size field is transformed into a row and no data loss occurs.
  - Lines merge test should confirm `ORDER_LIST_LINES_DELTA` has the expected records linked to the correct headers.
  Additionally, the **combined test** (headers + lines sequence) should run without issues, indicating that all templates work together in order.

## Progress Log

### 2025-01-08
- **Test 3.1 (Headers Merge):** Created `test_merge_headers.py`. Loaded the config (with dynamic columns from Task002). Before running the template, inserted a known scenario into the source (took a snapshot of the dev DB’s current new orders for consistency). Ran the merge via our pipeline function (or directly executing the rendered SQL). The test checked that `ORDER_LIST_DELTA` had exactly 69 records (since we knew 69 orders were marked NEW for GREYSON CLOTHIERS in dev data). The test also sampled a couple of records to ensure fields like `AAG_ORDER_NUMBER`, `CUSTOMER_NAME` were correctly carried over. The test passed initially, which was a great sign.
- **Test 3.2 (Sizes Unpivot):** Created `test_unpivot_sizes.py`. This test is a bit more involved because the unpivot is usually part of the header merge process in our pipeline. However, to test it in isolation, we configured the environment such that after header merge, a temp table (or a CTE inside the template) provided a wide format. We executed the unpivot query on one of the new orders. We expected, for example, if one order had values in 5 different size columns, that the unpivot would produce 5 rows for that order. The test counted the rows output for a couple of orders and compared them to the sum of non-zero sizes in the source – they matched. One specific check: if an order had a total quantity of X distributed among sizes, the unpivot should produce exactly X subitem entries (with each entry corresponding to one unit or one style-size combination depending on design). This alignment was confirmed. Test passed.
- **Subtask 3.1 & 3.2 Completed:** Both template-specific tests green on first run.

### 2025-01-09
- **Test 3.3 (Lines Merge):** Created `test_merge_lines.py`. After running the header merge (which also calls unpivot internally in our actual pipeline design), we then ran the lines merge template. This populates the `ORDER_LIST_LINES_DELTA` table. The test verified that:
  - The number of records in `ORDER_LIST_LINES_DELTA` equals the number of unpivoted size records for the new orders (in our test scenario, for GREYSON’s PO, it was 317 lines expected, and the table had 317 records).
  - Each line in the lines delta has a `record_uuid` that matches one of the headers in `ORDER_LIST_DELTA`.
  - No lines from other orders were included (we filtered by `record_uuid` in test to double-check isolation).
  The test initially failed because we found that `record_uuid` was not being selected in one of our queries, meaning lines didn’t have a way to link to headers (this was the bug discovered). We quickly fixed the template (and SyncEngine code) to include `record_uuid` where needed. After that fix, the test passed.
- **Combined Test (Optional but done):** We ran a full sequence in `test_complete_pipeline.py` (which is essentially Task005’s domain, but we kicked it off here). This test simply invoked the entire pipeline end-to-end on the dev data (in a controlled way) and then checked the final outputs (e.g., `ORDER_LIST_DELTA` has 69 records, `ORDER_LIST_LINES_DELTA` has 317, and some known aggregate totals match). It passed, confirming that all templates work together in context.
- **Bug Fix:** Notably, this testing task uncovered the missing `record_uuid` in our pipeline logic, which we fixed. This shows the value of these integration tests in catching a critical issue that would have broken the linking of items to subitems.
- **Completion:** With all tests passing and the minor fixes applied, Task003 was completed. The template integration is now validated, giving us confidence to move forward with the next phases of development.
