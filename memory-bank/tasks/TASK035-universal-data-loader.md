# TASK035 - Universal Data Loader Script

**Status:** Pending  
**Added:** 2025-08-08  
**Updated:** 2025-08-08

## Original Request
Create a universal script, based on the ORDER_LIST pipeline architecture, that:
- Given variables:
  - source folder path
  - file search criteria (optional)
  - blob storage container
  - blob storage CSV container
  - staging table name
  - target table name
- Loads CSV data into staging table (with predefined schema)
- Executes INSERT INTO (target) SELECT * FROM {source}

The script should be configurable, reusable, and follow the established project patterns from the ORDER_LIST pipeline.

## Thought Process
After analyzing the ORDER_LIST pipeline (`order_list_extract.py`, `order_list_pipeline.py`), I can see the following key patterns that should be incorporated into a universal data loader:

1. **Configuration-Driven Architecture**: All parameters should be configurable via TOML files, following the project's pattern of keeping configuration separate from code.

2. **Robust Error Handling**: The ORDER_LIST extract script has excellent retry logic with exponential backoff, file validation, and comprehensive error reporting.

3. **Blob Storage Integration**: The existing pattern uses Azure Blob Storage for intermediate CSV files with external data sources for BULK INSERT operations.

4. **Schema Management**: The project uses `schema_helper` for dynamic table creation and SQL conversion, which should be leveraged.

5. **Logging and Monitoring**: Comprehensive logging with metrics tracking, performance monitoring, and detailed progress reporting.

6. **Multi-Stage Pipeline Architecture**: Clear separation between extract, transform, and load stages with independent validation.

The universal loader should be a generalized version of the ORDER_LIST extract logic, but configurable for any source/target combination.

## Definition of Done

- All code implementation tasks have a corresponding test/validation sub-task (integration testing is the default, unit tests by exception).
- No implementation task is marked complete until the relevant test(s) pass and explicit success criteria (acceptance criteria) are met.
- Business or user outcomes are validated with production-like data whenever feasible.
- Every task and sub-task is cross-linked to the corresponding file and test for traceability.
- All tests must pass in CI/CD prior to merging to main.
- **All business-critical paths must be covered by integration tests.**

## Implementation Plan

1. **Create Universal Loader Configuration Schema** - Design TOML configuration structure that supports multiple source types and target configurations
2. **Develop Core Universal Loader Module** - Build the main loader class with configurable parameters
3. **Implement Blob Storage Integration** - Extend blob storage handling for multiple containers and file types
4. **Add Schema Discovery and Management** - Build dynamic schema detection and table creation logic
5. **Create Data Validation Framework** - Implement configurable data quality checks and validation rules
6. **Build Pipeline Orchestration** - Create orchestrator that handles the complete load process
7. **Add CLI Interface** - Build command-line interface for easy execution with parameter overrides
8. **Create Configuration Templates** - Build template configurations for common use cases
9. **Comprehensive Testing Suite** - Integration tests with real data and validation scenarios
10. **Documentation and Examples** - Usage documentation with practical examples

## Progress Tracking

**Overall Status:** Not Started - 0% Complete

### Subtasks
| ID | Description | Status | Updated | Notes |
|----|-------------|--------|---------|-------|
| 1.1 | Design TOML configuration schema for universal loader | Not Started | 2025-08-08 | Support multiple source types, blob containers, schema options |
| 1.2 | Create UniversalDataLoader core class | Not Started | 2025-08-08 | Based on ORDER_LIST extract patterns with configurable parameters |
| 1.3 | Implement blob storage file discovery and processing | Not Started | 2025-08-08 | Support custom file search criteria and multiple containers |
| 1.4 | Add dynamic schema detection and table creation | Not Started | 2025-08-08 | Leverage existing schema_helper with enhancements |
| 1.5 | Build data validation and quality checks framework | Not Started | 2025-08-08 | Configurable validation rules with pass/fail criteria |
| 1.6 | Create pipeline orchestration with staging → target flow | Not Started | 2025-08-08 | Atomic operations with rollback capabilities |
| 1.7 | Develop CLI interface with parameter overrides | Not Started | 2025-08-08 | Similar to ORDER_LIST pipeline CLI pattern |
| 1.8 | Create configuration templates for common patterns | Not Started | 2025-08-08 | Excel→SQL, CSV→SQL, Blob→SQL templates |
| 1.9 | Build comprehensive integration test suite | Not Started | 2025-08-08 | Test all load patterns with validation metrics |
| 1.10 | Create documentation and usage examples | Not Started | 2025-08-08 | Complete user guide with practical examples |

## Relevant Files

- `pipelines/scripts/load_order_list/order_list_extract.py` - Base pattern for blob storage and Excel processing
- `pipelines/scripts/load_order_list/order_list_pipeline.py` - Orchestration and CLI pattern reference
- `pipelines/utils/schema_helper.py` - Schema detection and table creation utilities
- `pipelines/utils/db_helper.py` - Database operations and connection management
- `pipelines/utils/logger_helper.py` - Logging framework
- `configs/extracts/` - Configuration pattern examples

## Test Coverage Mapping

| Implementation Task                | Test File                                             | Outcome Validated                                |
|------------------------------------|-------------------------------------------------------|--------------------------------------------------|
| UniversalDataLoader core class     | tests/universal_loader/integration/test_core_loader.py | Configuration loading, parameter validation      |
| Blob storage file processing       | tests/universal_loader/integration/test_blob_processing.py | File discovery, download, validation             |
| Schema detection and table creation| tests/universal_loader/integration/test_schema_management.py | Dynamic schema creation, type conversion        |
| Data validation framework          | tests/universal_loader/integration/test_data_validation.py | Quality checks, validation rules                |
| Pipeline orchestration            | tests/universal_loader/integration/test_pipeline_orchestration.py | Complete load process, error handling           |
| CLI interface                      | tests/universal_loader/integration/test_cli_interface.py | Command-line parameter processing              |
| End-to-end load scenarios          | tests/universal_loader/e2e/test_complete_load_scenarios.py | Full load workflows with various data types    |

## Progress Log
### 2025-08-08
- Created task for universal data loader based on ORDER_LIST pipeline analysis
- Analyzed existing patterns in order_list_extract.py and order_list_pipeline.py
- Identified key architectural patterns: configuration-driven, robust error handling, blob storage integration
- Planned 10-step implementation with comprehensive testing requirements
- Ready for implementation phase once prioritized
