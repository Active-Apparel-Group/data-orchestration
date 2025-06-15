# Tests Directory Structure

This directory contains all tests for the data orchestration project, organized by pipeline and test type.

## Structure

```
tests/
├── __init__.py
└── audit_pipeline/              # Tests for audit pipeline
    ├── __init__.py
    ├── unit/                    # Unit tests
    ├── integration/             # Integration tests  
    ├── performance/             # Performance tests
    ├── test_*.py               # Main test files
    ├── debug_*.py              # Debug utilities
    ├── check_*.py              # Check utilities
    └── simple_*.py             # Simple test utilities
```

## Test Categories

### Unit Tests (`unit/`)
- Fast, isolated tests
- Mock external dependencies
- Test individual functions/classes

### Integration Tests (`integration/`)
- Test component interactions
- Use real databases/services
- End-to-end workflow testing

### Performance Tests (`performance/`)
- Load testing
- Performance benchmarks
- Memory usage tests

## Running Tests

```bash
# All tests
pytest

# Specific pipeline tests
pytest tests/audit_pipeline/

# Specific test types
pytest tests/audit_pipeline/unit/
pytest tests/audit_pipeline/integration/
pytest tests/audit_pipeline/performance/

# Specific test file
pytest tests/audit_pipeline/test_matching.py
```

## Configuration

Tests are configured via `pytest.ini` in the project root:
- `testpaths = tests` - Look for tests in the tests/ directory
- Coverage reports for `src/audit_pipeline`
- Standard test discovery patterns (`test_*.py`)
