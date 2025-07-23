# TASK001 - Modern Template Architecture Implementation

**Status:** Completed  
**Added:** 2025-01-02  
**Updated:** 2025-01-05  

## Original Request
The team needed to refactor the existing SQL merge process to use a modern, flexible template-driven approach. Specifically, the goal was to handle a variable number of “size” columns in the order data without writing separate SQL for each scenario. We wanted a single, maintainable method to merge order data that could adapt to schema changes automatically.

## Thought Process
When this task was initiated, we realized that maintaining raw SQL for merging orders (headers and lines) was error-prone, especially as the number of size columns (representing different product sizes) could change with schema updates. The solution was to introduce a templating system:
- We chose **Jinja2 templates** to generate SQL dynamically. This allows loops and conditionals within the SQL, so we can loop through size columns instead of hardcoding each one.
- We planned to create separate template files for distinct parts of the process (merging headers, unpivoting sizes, merging lines) to keep them manageable and logical.
- A new `SQLTemplateEngine` class or function would be written to load these templates, fill in context (like the list of size columns from the database), and produce the final SQL string to execute.
- We had to ensure that this template engine could be easily integrated with the existing pipeline orchestrator (which executes the SQL merges).
- A major consideration was verifying that the templated SQL outputs exactly matched the expected results of the previous static SQL. This meant we’d need a robust testing approach.

We broke down the task into a series of subtasks focusing on creating templates, implementing the engine, integrating it, and testing:
1. Create Jinja2 template files for merging order headers, unpivoting sizes, and merging lines, parameterizing them for dynamic column handling.
2. Implement the code (`SQLTemplateEngine`) to load templates and substitute actual schema info (like column lists).
3. Replace occurrences of static SQL in the pipeline with calls to this new engine.
4. Add validation steps (like having the engine print or log the SQL it generates) to manually inspect correctness before running it.
5. Develop a comprehensive test plan: unit tests for the template generation logic and integration tests to ensure the new pipeline produces the same results as the old one.

## Implementation Plan
- **Step 1:** Develop Jinja2 template files:
  - `merge_headers.j2` – SQL template for merging order header data (with placeholders for dynamic size columns).
  - `unpivot_sizes.j2` – SQL template to transform wide size columns into a normalized format.
  - `merge_lines.j2` – SQL template for merging order line items.
- **Step 2:** Create a Python utility (e.g., `SQLTemplateEngine` class) to:
  - Load a template file from the filesystem.
  - Gather context data (e.g., list of size columns from the database schema via an information schema query).
  - Render the template with context to produce final SQL.
- **Step 3:** Integrate the template engine into the pipeline:
  - Replace direct SQL strings in `MergeOrchestrator` (or equivalent component) with calls to `SQLTemplateEngine`.
  - Ensure that the order of operations remains correct (headers merge first, then unpivot, then lines merge).
- **Step 4:** Implement template validation:
  - Before executing generated SQL, optionally output it to logs for verification.
  - Possibly run a dry-run of the SQL on a small dataset to ensure syntax is correct.
- **Step 5:** Testing:
  - Write unit tests to check that given a set of dummy columns, the `SQLTemplateEngine` fills the template correctly (e.g., the UNPIVOT clause contains all expected columns).
  - Write integration tests using a known schema (the development database) to execute the generated SQL and verify results (for example, after running the merge, the delta tables have the expected number of records).

## Progress Tracking

**Overall Status:** Completed – 100%

### Subtasks
| ID   | Description                                                | Status    | Updated     | Notes                      |
|------|------------------------------------------------------------|----------|-------------|----------------------------|
| 1.1  | Create Jinja2 template files for headers, sizes, lines     | Complete | 2025-01-03  | Templates `*.j2` created   |
| 1.2  | Implement SQLTemplateEngine for template rendering         | Complete | 2025-01-03  | Engine loads & renders OK  |
| 1.3  | Integrate template engine into pipeline orchestrator       | Complete | 2025-01-04  | Replaced static SQL calls  |
| 1.4  | Add template validation (log or dry-run of generated SQL)  | Complete | 2025-01-04  | Verified SQL syntax        |
| 1.5  | Develop and run tests for template outputs and integration | Complete | 2025-01-05  | All tests passed           |

### Success Gates
- No task is complete until its corresponding test cases pass and all acceptance criteria are met.
- **Success Gate:** All merge operations use generated SQL without errors. The new template-driven process must produce the exact intended data in delta tables (verified by integration tests comparing results to the previous static SQL method).

## Progress Log

### 2025-01-02
- **Initiated Task:** Defined strategy to use Jinja2 for SQL templating. Set up the directory structure for template files and prepared a list of dynamic parts (identified size-related fields as the primary dynamic element).
- **Discussion:** Team agreed on this templating approach and identified where in the pipeline the integration will happen (the Merge Orchestrator module).

### 2025-01-03
- **Templates Created:** Drafted `merge_headers.j2`, `unpivot_sizes.j2`, and `merge_lines.j2` templates. Each template includes loops for size columns. For example, `unpivot_sizes.j2` uses a Jinja loop to list all size columns in the UNPIVOT clause.
- **Engine Implementation:** Wrote the initial version of `SQLTemplateEngine` with methods to load templates from the `sql/` directory and render them. Confirmed that the engine can load a template file and print a rendered SQL when given sample context (list of size columns).
- **Subtask 1.1 & 1.2 Completed:** Verified that the template engine outputs logically correct SQL for a simplified context (e.g., 3 size columns scenario).

### 2025-01-04
- **Integration:** Replaced static SQL strings in our pipeline code with calls to the new template engine. For example, the part of the code that merged headers now calls `SQLTemplateEngine.render('merge_headers.j2', context)` to get the SQL, then executes it.
- **Validation Step:** Added logging to output the generated SQL for one of the sample orders to manually inspect it. The SQL looked correct (it listed all 245 size columns from our dev schema properly in the UNPIVOT).
- **Dry-run Test:** Ran the pipeline in a test mode on a limited dataset. It executed the templated SQL without syntax errors. This was a good initial confirmation.
- **Subtask 1.3 & 1.4 Completed:** The pipeline now fully uses templates, and we have means to validate the output.

### 2025-01-05
- **Testing:** Created a test case in `test_merge_headers.py` to ensure that after running the header merge via the template, the resulting `ORDER_LIST_DELTA` table has the correct data. Similarly, tests for the unpivot and lines merge were written.
- **Test Results:** All tests passed on the first full run. The dynamic columns were handled correctly – for instance, the test confirmed that exactly 245 size columns were unpivoted, matching the actual schema.
- **Completion:** With tests passing and the new system producing expected results, we marked Task001 as completed. The new architecture portion (template-driven SQL) is now in place and functioning as intended.
