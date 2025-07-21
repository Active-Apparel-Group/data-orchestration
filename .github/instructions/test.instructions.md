---
applyTo: '**'
---

# 🟦 Test Instructions – Data Orchestration (Unified Standards)

## 🎯 Overview

**Integration testing is the default.**  
Unit tests are only written by exception for complex or isolated logic.  
All tests must use production-like data, have measurable outcomes, and link directly to requirements.

---

## 1. Test Folder Structure

tests/
    <feature-or-pipeline>/
        integration/     # Multi-component, business flow, and system tests (default)
        unit/            # Rare, for isolated logic only (must be justified)
        e2e/             # End-to-end, user-facing workflow tests (optional)
        debug/           # For development/debug scripts only


- Folder and test file names must match the feature/component.
- Each test must include a docstring linking to the relevant requirement or user story.

---

## 2. Test Generation & Agent Workflow

- **Default:** Create an integration test for each new feature or business-critical change.
- **Exception:** Unit tests only if logic is critical, complex, or needs strict isolation (must be justified and flagged).
- For each implementation, generate:
    - [ ] An integration test validating the outcome.
    - [ ] An explicit, measurable success gate (e.g., “>95% successful processing”).
    - [ ] Cross-link tests to requirements in docstrings.
- **CI/CD Blocker:** No code is merged until all required tests pass and success gates are met.

---

## 3. Success Criteria & Measurables

- **All tests must define clear, numeric acceptance criteria** (e.g., “success rate ≥ 95%”).
- **Standard metrics:**
    - Data availability/completeness
    - Processing and transformation success rates
    - API/database consistency
    - Error frequency and type
- **Quality gates:**
    - Excellent: >95% success, <5% errors
    - Good: >90% success, <10% errors
    - Needs attention: <90% success, >10% errors

---

## 4. Anti-Patterns to Avoid

❌ Mock data tests – always validate against actual data  
❌ Vague pass/fail – always use measurable thresholds  
❌ “Big bang” single-phase tests – break into logical phases  
❌ No error breakdown – always report & categorize errors  
❌ Manual review – automate all validation in code

---

## 5. Best Practices Checklist

✅ Integration-first (default to integration tests)  
✅ Test with real/production-like data  
✅ Measurable numeric outcomes  
✅ One-to-one mapping: implementation → test → requirement  
✅ Modular, phase-based validation  
✅ CI/CD must pass all tests before merging

---

## 📊 Example

Reference:  
`tests/sync_order_list_monday/integration/test_merge_headers.py`  
`tests/sync_order_list_monday/e2e/test_order_list_complete_pipeline.py`

---

> **In summary:**  
Integration testing is the default standard. Every code change must be validated by a measurable, requirement-linked integration test, using real data and enforced in CI/CD. Unit tests are only permitted by clear exception.

