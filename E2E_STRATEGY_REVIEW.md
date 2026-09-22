# E2E Test Strategy Review

**Date:** 2026-09-22  
**Current State:** 13 E2E tests (skipped in CI, local development only)  
**Question:** Which tests are critical vs. optional? Which can be converted to unit tests?

---

## Current E2E Test Suite Analysis

### File 1: `test_job_definition_preview_browser.py` (5 tests)

These use Playwright for browser-based HTTP testing against a trial server.

| Test | Type | Current Setup | Can Convert? | Recommendation |
|------|------|----------------|--------------|-----------------|
| `test_preview_flow_does_not_mutate_state` | **CRITICAL** | Playwright + server | ⚠️ Keep as E2E | Read-only guarantees require state verification |
| `test_preview_rejects_unknown_repo_safely` | Important | Playwright + server | ✅ Easy | Mock API, unit test error handling |
| `test_preview_rejects_missing_required_param` | Important | Playwright + server | ✅ Easy | Mock API, unit test validation |
| `test_preview_rejects_oversized_param` | Nice-to-have | Playwright + server | ✅ Easy | Mock API, unit test size limits |
| `test_preview_requires_authentication` | Important | Playwright + server | ✅ Medium | Mock auth, unit test 401/403 response |

**Summary:** 1 critical (requires E2E), 4 convertible to unit tests (mock API)

---

### File 2: `test_justfile_recipes.py` (8 tests)

These use subprocess to execute justfile recipes—not true browser E2E. Can all be unit tests or integration tests.

| Test | Type | Current Setup | Can Convert? | Recommendation |
|------|------|----------------|--------------|-----------------|
| `test_repl_recipe_exists` | Nice-to-have | subprocess → justfile | ✅ Easy | Unit test: check justfile content |
| `test_repl_recipe_invokes_fleet_ops_cli` | Nice-to-have | subprocess → justfile | ✅ Easy | Unit test: mock subprocess, check args |
| `test_fleet_recipe_works` | Nice-to-have | subprocess → justfile | ✅ Easy | Unit test: mock subprocess, check exit |
| `test_<recipe>_*` (5+ more) | Nice-to-have | subprocess → justfile | ✅ Easy | Unit tests: all can mock subprocess |

**Summary:** 0 critical, 8 all convertible to unit tests (mock subprocess)

---

## Proposed E2E Reduction Strategy

### Target: 80% Unit Tests, 20% E2E

**Current:**
- E2E tests: 13 (100% E2E)
- Unit tests: 246 (all other repos)
- Ratio: 5% E2E, 95% unit

**Proposed:**
- E2E tests: 1–2 (critical read-only state verification)
- Unit tests: 20 (converted from E2E)
- Ratio: 5–10% E2E, 90–95% unit

**Reduction:** 85–90% fewer E2E tests (from 13 → 1–2)

---

## Conversion Plan: E2E → Unit Tests

### Phase 1: Justfile Recipe Tests (8 tests → 8 unit tests)

**Current:** Subprocess-based E2E execution  
**Proposal:** Mock subprocess, test recipe logic in isolation

```python
# Before (E2E):
def test_repl_recipe_invokes_fleet_ops_cli(self):
    result = self.run_recipe("repl", timeout=5)
    assert "not a valid int" not in result.stderr

# After (Unit):
@patch('subprocess.run')
def test_repl_recipe_invokes_fleet_ops_cli(mock_run):
    mock_run.return_value = CompletedProcess(args=["fleet-ops", ...])
    invoke_repl_recipe()
    mock_run.assert_called_once_with("fleet-ops", ...)
```

**Benefits:**
- No subprocess overhead (faster CI)
- Deterministic (no environment variance)
- Can test error paths easily (mock failures)
- Runs in CI without justfile binary

**Effort:** 2–3 hours (refactor 8 tests)

---

### Phase 2: API Validation Tests (4 tests → 4 unit tests)

**Current:** Playwright + trial server (error handling, validation)  
**Proposal:** Mock FastAPI app, test endpoints directly

```python
# Before (E2E):
def test_preview_rejects_missing_required_param(authenticated_page, trial_base_url):
    response = authenticated_page.request.post(...)
    assert response.status == 400

# After (Unit):
def test_preview_rejects_missing_required_param():
    client = TestClient(app)  # FastAPI test client
    response = client.post(
        "/api/jobs/preview",
        json={"repo": "...", "task": "...", "params": {}}
    )
    assert response.status_code == 400
    assert "target" in response.json()["error"]
```

**Benefits:**
- Test app logic without server/browser setup
- Faster (no Playwright overhead)
- Easier to test error paths
- CI-compatible (no infrastructure needed)

**Effort:** 3–4 hours (refactor 4 tests, add TestClient mocking)

---

### Phase 3: Critical State Verification (1 test → 1 E2E test)

**Current:** Playwright E2E (state mutation verification)  
**Proposal:** Keep as E2E (essential for read-only guarantees)

**Rationale:**
- This is the **core security guarantee** for fleet-ops
- Proves that preview endpoints don't mutate state
- Can only be validated with a real server + real API calls
- Unit mocking would invalidate the test's purpose

**Recommendation:** Keep this one E2E test, run it:
- **Locally:** Before shipping (developer validation)
- **In CI:** Only on demand (`workflow_dispatch`) or gated environment
- **Frequency:** Weekly manual run + part of release checklist

---

## Implementation Roadmap

### Week 1: Refactor Justfile Tests (8 → Unit)
- Migrate `test_justfile_recipes.py` to `tests/unit/test_justfile_recipes.py`
- Add subprocess mocking with `unittest.mock.patch`
- Verify all 8 tests pass (should be same assertions, just mocked)
- **Outcome:** 8 tests in CI at 0.5s execution time

### Week 2: Refactor API Validation Tests (4 → Unit)
- Convert 4 validation tests to use FastAPI `TestClient`
- Add fixtures for mock authenticated client
- Verify all 4 tests pass in CI
- **Outcome:** 4 tests in CI at 1.0s execution time

### Week 3: Isolate Critical E2E Test (1 → Manual)
- Keep 1 state-mutation test in `tests/e2e/`
- Document manual run procedure (requires trial server)
- Add to pre-release checklist
- **Outcome:** 1 E2E test available for manual validation only

### Outcome
- **CI:** 246 unit tests (current) + 12 converted tests = **258 unit tests**
- **CI Time:** No increase (unit tests fast; E2E removed)
- **Local:** 1 E2E test available for manual pre-release validation
- **Ratio:** 98% unit, 2% E2E (both running in CI: 260 tests)

---

## Cost/Benefit Analysis

### Costs
- **Effort:** 6–8 hours of refactoring
- **Learning:** Subprocess mocking, TestClient patterns
- **Maintenance:** Keep mocks in sync with actual APIs

### Benefits
- **CI Speed:** E2E removed, unit tests 50% faster
- **Reliability:** No trial server dependency → no flaky tests
- **Coverage:** Same assertions, faster feedback
- **Scalability:** Unit tests easier to expand
- **Debugging:** Failures point to code logic, not infrastructure

### ROI
- **Break-even:** ~3 weeks (saved CI time pays back refactoring cost)
- **Long-term:** Sustainable test suite for fleet operations

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Mocks diverge from real API | Keep 1 E2E test as regression check; review mocks quarterly |
| Lost critical test coverage | Test state mutation manually before releases; document procedure |
| Unit tests miss environment issues | Keep local E2E test for pre-release validation |

---

## Recommendation

✅ **Proceed with conversion**

**Rationale:**
1. **13 tests is excessive** for a solo dev project without persistent infrastructure
2. **8/13 can be unit tests** (no true browser testing needed)
3. **1/13 is critical** but can be manual (pre-release validation)
4. **4/13 are validation** (better as unit tests closer to code)
5. **CI will be cleaner:** No E2E failures from infrastructure, only code logic

**Next Steps:**
1. Approve strategy
2. Schedule 6–8 hour refactoring sprint
3. Migrate tests per 3-week roadmap
4. Update CI to include converted unit tests

---

**Questions for review:**
- Is the state-mutation test (currently E2E) important enough for pre-release validation?
- Are justfile recipe tests mission-critical, or can they be simplified?
- Should converted tests be run in CI, or kept as local development checks?
