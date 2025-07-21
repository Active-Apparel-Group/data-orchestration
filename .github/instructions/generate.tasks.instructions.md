# Rule: Generating a Task List from a PRD

## Goal

To guide an AI assistant in creating a detailed, step-by-step task list in Markdown format based on an existing Product Requirements Document (PRD). The task list should guide a developer through implementation, ensure robust testing, and define clear, outcome-based success gates.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-[prd-file-name].md` (e.g., `tasks-prd-user-profile-editing.md`)

## Definition of Done

- All code implementation tasks have a corresponding test/validation sub-task (integration testing is the default, unit tests by exception - but acceptable, the agent or developer should make this call and flag for review, e2e for end-to-end flows).
- No implementation task is marked complete until the relevant test(s) pass and explicit success criteria (acceptance criteria) are met.
- Business or user outcomes are validated with production-like data whenever feasible.
- Every task and sub-task is cross-linked to the corresponding file and test for traceability.
- All tests must pass in CI/CD prior to merging to main.
- **All business-critical paths must be covered by integration tests.**

## Test Type Selection: Integration vs Unit Testing

- **Default:**  
  - Generate **integration tests** for all new features, pipelines, or business flows.
- **Exception:**  
  - Only generate **unit tests** for logic that is critical, complex, or best validated in isolation.
  - The agent or developer should make this call and, if in doubt, flag for review.
- **Integration tests are always run before progressing to e2e or production testing.**
- **Unit tests are rare and must be explicitly justified.**

## File and Folder Naming and Structure

- Tests for each feature or pipeline must be placed in `/tests/<task-name>/<test-type>/`, where:
  - `<task-name>` matches the feature, pipeline, or task (e.g., `order_list_delta_sync`)
  - `<test-type>` is one of: `integration`, `unit`, `e2e`, `debug`
- Test file names must match the logic or component being tested (e.g., `test_merge_headers.py` for `merge_headers.j2`).
- Task names and test folder names must be consistent for easy traceability.
- Any shared test helpers should be placed at the root `/tests/` only if they are used by multiple features.

## Process

1.  **Receive PRD Reference:** The user points the AI to a specific PRD file.
2.  **Analyze PRD:** The AI reads and analyzes the functional requirements, user stories, and other sections of the specified PRD.
3.  **Phase 1: Generate Parent Tasks:** Based on the PRD analysis, create the file and generate the main, high-level tasks required to implement the feature. Use your judgement on how many high-level tasks to use. It's likely to be about 5. Present these tasks to the user in the specified format (without sub-tasks yet). Inform the user: "I have generated the high-level tasks based on the PRD. Ready to generate the sub-tasks? Respond with 'Go' to proceed."
4.  **Wait for Confirmation:** Pause and wait for the user to respond with "Go".
5.  **Phase 2: Generate Sub-Tasks:** Once the user confirms, break down each parent task into smaller, actionable sub-tasks necessary to complete the parent task. Ensure sub-tasks logically follow from the parent task and cover the implementation details implied by the PRD. For every implementation sub-task, generate a corresponding test sub-task and a specific success gate/acceptance criteria.  
6.  **Identify Relevant Files:** Based on the tasks and PRD, identify potential files that will need to be created or modified. List these under the `Relevant Files` section, including corresponding test files and their locations under the `/tests/<task-name>/<test-type>/` structure.
7.  **Test Coverage Mapping:** Create a table mapping each implementation task to its test file(s) and the outcome being validated.
8.  **Generate Final Output:** Combine the parent tasks, sub-tasks, relevant files, test coverage mapping, and notes into the final Markdown structure.
9.  **Save Task List:** Save the generated document in the `/tasks/` directory with the filename `tasks-[prd-file-name].md`, where `[prd-file-name]` matches the base name of the input PRD file (e.g., if the input was `prd-user-profile-editing.md`, the output is `tasks-prd-user-profile-editing.md`).

## Output Format

The generated task list _must_ follow this structure:

```markdown
## Relevant Files

- `src/feature/file.py` - Brief description of why this file is relevant.
- `tests/<task-name>/integration/test_feature.py` - Integration test for the main logic.
- `tests/<task-name>/unit/test_component.py` - Unit test for isolated logic.
- `tests/<task-name>/e2e/test_end_to_end.py` - End-to-end test for full flow.

### Notes

- Unit tests should typically be placed in the `unit/` subfolder under their feature’s test directory.
- All test and implementation files must be cross-referenced in the task list for traceability.
- No task is complete until its corresponding test task passes and the success gate is met.

## Test Coverage Mapping

| Implementation Task                | Test File                                             | Outcome Validated                                |
|------------------------------------|-------------------------------------------------------|--------------------------------------------------|
| merge_headers.j2                   | tests/order_list_delta_sync/integration/test_merge_headers.py | Dynamic size detection, SQL syntax               |
| unpivot_sizes.j2                   | tests/order_list_delta_sync/integration/test_unpivot_sizes.py | All size columns unpivoted                       |
| merge_lines.j2                     | tests/order_list_delta_sync/integration/test_merge_lines.py   | Delta output and business keys                   |
| New Order Detection                | tests/order_list_delta_sync/integration/test_new_order_detection.py | New/existing order accuracy               |

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 Implementation sub-task
  - [ ] 1.2 **Test:** Corresponding test file (integration/unit/e2e as appropriate)
  - [ ] 1.3 **Success Gate:** Explicit outcome or acceptance criteria (must pass test, validate business logic, etc.)
- [ ] 2.0 Next Parent Task
  - [ ] 2.1 Implementation sub-task
  - [ ] 2.2 **Test:** Corresponding test file
  - [ ] 2.3 **Success Gate:** Acceptance criteria

...

## Interaction Model

The process explicitly requires a pause after generating parent tasks to get user confirmation ("Go") before proceeding to generate the detailed sub-tasks. This ensures the high-level plan aligns with user expectations before diving into details.

## Target Audience

Assume the primary reader of the task list is a **junior developer** who will implement the feature.
