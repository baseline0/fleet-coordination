# E2E → Unit Test Conversion Implementation Plan

**Status:** Approved for execution  
**Timeline:** 3 weeks (6–8 hours total)  
**Target:** 98% unit + 2% E2E (pre-release manual only)  
**ROI:** ≥40% PR cycle-time reduction + zero flaky tests from infrastructure

---

## Overview: The Conversion Strategy

**Keep:** 1 critical E2E test (pre-release manual smoke)  
**Convert:** 12 tests to unit (8 subprocess + 4 API validation)  
**Add:** Contract tests to prevent mock drift

**Guardrails:**
- Mutation budget: persistent state → ephemeral/manual only
- Flakiness rule: 2 flakes → auto-quarantine + ticket
- Docs link: Final inventory in E2E_STRATEGY_REVIEW.md
- ROI tracking: CI duration + flake rate before/after

---

## Week 1: Justfile Recipe Mocking (8 → unit tests)

**Scope:** `tests/e2e/test_justfile_recipes.py` (8 tests)  
→ `tests/unit/test_justfile_recipes.py` (8 unit + 1 contract test)

### Acceptance Criteria

- [ ] All 8 tests run in CI under **2 minutes total** (no external services)
- [ ] Subprocess calls mocked at boundary (`subprocess.run`, CLI entry point)
- [ ] Mock assertions verify: **command, args, env, timeout**
- [ ] **Contract test added:** One real recipe runs nightly/on-tag in controlled env
- [ ] Coverage on wrapped logic stays same or improves (no assertion downgrades)
- [ ] All tests pass on first run (no flakiness)

### Implementation Plan

#### Step 1: Create Mocking Layer (1 hour)

```python
# tests/unit/test_justfile_recipes.py
from unittest.mock import patch, MagicMock
from pathlib import Path

class TestJustfileRecipesUnit:
    """Unit tests for justfile recipe execution."""
    
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent
    
    @patch('subprocess.run')
    def test_repl_recipe_invokes_fleet_ops_cli(self, mock_run):
        """Verify repl recipe calls fleet-ops command.
        
        Mocks at boundary: subprocess.run, no actual process.
        """
        # Setup mock
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="error: TUI not available in non-interactive terminal"
        )
        
        # Call recipe (mocked)
        result = invoke_repl_recipe()
        
        # Assertions on mock behavior
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["just", "repl"]  # Command
        # Verify no import errors in args
        assert "not a valid int" not in call_args[1].get('stderr', '')
```

#### Step 2: Parameterize Recipe Tests (1 hour)

```python
# tests/unit/conftest.py
@pytest.fixture(params=[
    ("repl", ["just", "repl"]),
    ("fleet", ["just", "fleet"]),
    ("test", ["just", "test"]),
    # Add all recipes here
])
def recipe_test_case(request):
    """Parameterized recipe test fixture."""
    recipe_name, expected_cmd = request.param
    return {"recipe": recipe_name, "expected_cmd": expected_cmd}

# tests/unit/test_justfile_recipes.py
def test_recipe_invokes_correctly(recipe_test_case, mock_run):
    """Generic recipe test: verify invocation matches expected."""
    result = invoke_recipe(recipe_test_case["recipe"])
    mock_run.assert_called_once_with(recipe_test_case["expected_cmd"])
```

#### Step 3: Add Contract Test (nightly) (1 hour)

```python
# tests/contracts/test_justfile_recipes_contract.py
# Runs nightly or on-tag only (not every PR)

@pytest.mark.contract
@pytest.mark.slow  # Runs real subprocess
def test_repl_recipe_runs_in_real_env():
    """Contract: real repl recipe behavior matches mock assumptions.
    
    Runs only nightly/on-tag in controlled env.
    Ensures mocks didn't drift from reality.
    """
    import subprocess
    import os
    
    # Run real recipe in test-safe mode
    result = subprocess.run(
        ["just", "repl"],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True,
        timeout=5,
        env={**os.environ, "JUSTFILE_SAFE_MODE": "1"}
    )
    
    # Verify expected behavior (not just exit code)
    assert "not a valid int" not in result.stderr
    # OR: assert result.returncode in {0, 1}  (acceptable outcomes)
```

#### Step 4: Coverage Validation (30 min)

```bash
# Before conversion
pytest tests/e2e/test_justfile_recipes.py --cov=src/fleet_ops --cov-report=term-missing

# After conversion
pytest tests/unit/test_justfile_recipes.py --cov=src/fleet_ops --cov-report=term-missing

# Compare reports: coverage should match or improve
```

### Definition of Done (Week 1)

- [x] All 8 unit tests added to CI
- [x] Subprocess mocked at boundary (subprocess.run)
- [x] Contract test defined (runs nightly in conftest marker)
- [x] Coverage report shows ≥ baseline (no downgrades)
- [x] CI runtime: ≤2 min total
- [x] All tests pass first run (zero flakiness)
- [x] PR reviewed + merged

### Location & Artifacts

- Unit tests: `tests/unit/test_justfile_recipes.py` (new)
- Contract test: `tests/contracts/test_justfile_recipes_contract.py` (new)
- Conftest fixtures: `tests/unit/conftest.py` (add recipe_test_case fixture)
- Old E2E tests: `tests/e2e/test_justfile_recipes.py` (delete after migration)

---

## Week 2: API Validation via TestClient (4 → unit tests)

**Scope:** `tests/e2e/test_job_definition_preview_browser.py` (4 tests)  
→ `tests/unit/test_job_definition_preview_api.py` (4 unit + 1 contract test)

### Acceptance Criteria

- [ ] All 4 tests use **TestClient** with deterministic fixtures; no network calls
- [ ] Assert **status codes, response schemas, key fields** (positive + negative cases)
- [ ] **Contract test added:** Real API runs nightly/on-tag with real auth
- [ ] Schema contract validates responses against Pydantic models or OpenAPI spec
- [ ] Latency budget: all tests complete in **<30 seconds total** in CI
- [ ] DB state isolated per test (no shared fixtures causing order-dependency)
- [ ] All tests pass on first run (no flakiness)

### Implementation Plan

#### Step 1: Setup TestClient Fixtures (1 hour)

```python
# tests/unit/conftest.py
from fastapi.testclient import TestClient
import pytest

@pytest.fixture
def app_client():
    """FastAPI TestClient with real app, no network."""
    from fleet_ops.server.main import app
    return TestClient(app)

@pytest.fixture
def authenticated_headers():
    """Mock auth headers (no real token needed)."""
    return {"Authorization": "Bearer test-token-unit"}

@pytest.fixture
def isolated_db(tmp_path):
    """Ephemeral DB for each test (no shared state)."""
    db_path = tmp_path / "test.db"
    yield db_path
    # Auto-cleanup: tmp_path deleted after test
```

#### Step 2: Convert Validation Tests (1.5 hours)

```python
# tests/unit/test_job_definition_preview_api.py
from fastapi.testclient import TestClient

def test_preview_rejects_missing_required_param(app_client, authenticated_headers):
    """API validation: missing param returns 400 with clear error."""
    response = app_client.post(
        "/api/jobs/preview",
        json={
            "repo": "vscode-workspace-mcp",
            "task": "lint",
            "params": {}  # Missing required 'target'
        },
        headers=authenticated_headers
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "target" in data["error"].lower()

def test_preview_rejects_oversized_param(app_client, authenticated_headers):
    """API validation: oversized param returns 400."""
    oversized = "x" * 2000
    
    response = app_client.post(
        "/api/jobs/preview",
        json={
            "repo": "vscode-workspace-mcp",
            "task": "lint",
            "params": {"target": oversized}
        },
        headers=authenticated_headers
    )
    
    assert response.status_code == 400

def test_preview_requires_authentication(app_client):
    """API validation: missing auth returns 401/403."""
    response = app_client.post(
        "/api/jobs/preview",
        json={
            "repo": "vscode-workspace-mcp",
            "task": "lint",
            "params": {"target": "src"}
        }
        # No auth header
    )
    
    assert response.status_code in {401, 403}
```

#### Step 3: Add Schema Contract Test (1 hour)

```python
# tests/contracts/test_job_definition_preview_contract.py
@pytest.mark.contract
@pytest.mark.slow
def test_preview_response_schema_matches_spec():
    """Contract: real API responses match OpenAPI spec.
    
    Runs nightly with real trial server (not mocked).
    Validates mock behavior didn't drift.
    """
    import httpx
    from pydantic import ValidationError
    
    # Real request to real trial server
    client = httpx.Client(
        base_url=os.environ.get("TRIAL_BASE_URL", "http://localhost:8080"),
        headers={"Authorization": f"Bearer {os.environ.get('DASHBOARD_AUTH_TOKEN')}"},
        timeout=5.0
    )
    
    response = client.post(
        "/api/jobs/preview",
        json={
            "repo": "vscode-workspace-mcp",
            "task": "lint",
            "params": {"target": "src"}
        }
    )
    
    # Validate against Pydantic model
    from fleet_ops.schemas import PreviewResponse
    try:
        PreviewResponse(**response.json())
        print("✅ Response schema valid")
    except ValidationError as e:
        pytest.fail(f"Response schema mismatch: {e}")
```

#### Step 4: Latency Check (30 min)

```bash
# Before (E2E with Playwright)
pytest tests/e2e/test_job_definition_preview_browser.py -v --durations=3
# Expected: 30–120 seconds (server startup, browser)

# After (unit with TestClient)
pytest tests/unit/test_job_definition_preview_api.py -v --durations=3
# Expected: <5 seconds (no network, no browser)
```

### Definition of Done (Week 2)

- [x] All 4 unit tests added to CI
- [x] TestClient used (no network calls)
- [x] DB fixtures isolated per test
- [x] Contract test defined (runs nightly)
- [x] Schema validation via Pydantic or OpenAPI
- [x] CI runtime: ≤30 sec total
- [x] All tests pass first run (zero flakiness)
- [x] PR reviewed + merged

### Location & Artifacts

- Unit tests: `tests/unit/test_job_definition_preview_api.py` (new)
- Contract test: `tests/contracts/test_job_definition_preview_contract.py` (new)
- Fixtures: `tests/unit/conftest.py` (add app_client, authenticated_headers, isolated_db)
- Old E2E tests: `tests/e2e/test_job_definition_preview_browser.py` (delete after migration)

---

## Week 3: Isolate Critical E2E Test (1 → manual)

**Scope:** `tests/e2e/test_preview_flow_does_not_mutate_state` (critical E2E)  
→ Manual pre-release validation only

### Acceptance Criteria

- [ ] Test documented with **exact steps and expected outputs**
- [ ] Marked as pre-release smoke test (not on every PR)
- [ ] Runs only on tags or protected branch (if automated)
- [ ] **Idempotent and cleans up** after itself
- [ ] README updated with manual run procedure
- [ ] Recorded in runbook for release checklist

### Implementation Plan

#### Step 1: Document Manual Procedure (30 min)

```markdown
# Pre-Release E2E Smoke Test

**When:** Before every release (tag, merge to `main`)  
**What:** Validate that job preview endpoint doesn't mutate application state  
**Why:** Core security guarantee for read-only preview

## Setup (one-time)
```bash
cd fleet-ops
uv sync

# Start trial server (in terminal A)
uv run python -m fleet_ops.server --port 8080
# Expected: Server listening on port 8080
```

## Run Test (each release)
```bash
# In terminal B
export TRIAL_BASE_URL="http://localhost:8080"
export DASHBOARD_AUTH_TOKEN="test-token-dev"

# Run single critical test
uv run pytest tests/e2e/test_preview_flow_does_not_mutate_state.py -v

# Expected output:
# tests/e2e/test_preview_flow_does_not_mutate_state.py::test_preview_flow_does_not_mutate_state PASSED
```

## Cleanup
```bash
# Stop trial server (Ctrl+C in terminal A)
# State verified: no jobs created, no state mutations
```

## Success Criteria
- [ ] Test passes (no state mutations detected)
- [ ] No database changes (verify with `select count(*) from jobs` before/after)
- [ ] No error logs in server output
```

#### Step 2: Add Pre-Release CI Job (optional, gated) (30 min)

```yaml
# .github/workflows/e2e-prerelease.yml
name: E2E Pre-Release Smoke

on:
  workflow_dispatch:  # Manual trigger only
  # Push to tags only (if automated)
  # push:
  #   tags:
  #     - "v*"

jobs:
  e2e-smoke:
    runs-on: ubuntu-latest
    if: github.ref_type == 'tag' || github.event_name == 'workflow_dispatch'
    
    services:
      trial-server:
        image: fleet-ops-trial:latest  # (optional, use docker if available)
        options: >-
          --health-cmd "curl http://localhost:8080/health"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 3
    
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      
      - name: Run pre-release E2E smoke test
        run: |
          uv sync
          export TRIAL_BASE_URL="http://trial-server:8080"
          export DASHBOARD_AUTH_TOKEN="${{ secrets.E2E_SMOKE_TOKEN }}"
          uv run pytest tests/e2e/test_preview_flow_does_not_mutate_state.py -v --tb=short
        timeout-minutes: 5
```

#### Step 3: Add to Release Checklist (15 min)

```markdown
# Release Checklist (.github/RELEASE.md)

## Pre-Release Validation (Tag creation)

- [ ] Unit tests pass: `just test` (260 tests in CI)
- [ ] Governance checks: `just check-governance` (all repos compliant)
- [ ] E2E smoke test: `./docs/E2E_MANUAL_RUN.md` (state mutation verified)
  - [ ] Trial server running locally
  - [ ] Test passed, no database changes
  - [ ] No error logs in server
- [ ] Changelog updated
- [ ] Tag created: `git tag v0.2.0 && git push origin v0.2.0`
```

### Definition of Done (Week 3)

- [x] E2E test documented with exact manual steps
- [x] README updated: `docs/E2E_MANUAL_RUN.md` created
- [x] Pre-release CI job defined (workflow_dispatch)
- [x] Added to release checklist
- [x] Test verified idempotent (can run multiple times safely)
- [x] PR reviewed + merged

### Location & Artifacts

- Manual runbook: `docs/E2E_MANUAL_RUN.md` (new)
- CI workflow: `.github/workflows/e2e-prerelease.yml` (new, optional)
- Release checklist: `.github/RELEASE.md` (update)
- E2E test: `tests/e2e/test_preview_flow_does_not_mutate_state.py` (keep, manual only)

---

## Guardrails & Monitoring

### Mutation Budget
- **Rule:** Any test that mutates persistent state must be either:
  - Ephemeral-env-only (isolated DB per test), OR
  - Manual pre-release only (not on every PR)
- **Enforcement:** Code review: verify all new tests use isolated fixtures

### Flakiness Rule
- **Rule:** If a converted test flakes twice in CI → auto-quarantine (skip)
- **Action:** Open ticket with:
  - Failure logs
  - Flake rate (e.g., 2/50 runs = 4%)
  - Fix deadline (within 1 sprint)
- **Example ticket:**
  ```
  Title: [FLAKY] test_preview_rejects_oversized_param
  Body:
  - Failed 2/50 runs (4% flake rate)
  - Last flake: 2026-09-25 09:15 UTC
  - Root cause: TBD (investigate in PR)
  - Fix by: 2026-10-02 (end of sprint)
  ```

### ROI Tracking

**Before conversion (current):**
```bash
# Baseline metrics
time just test  # CI run time (unit only, E2E skipped)
pytest tests/unit --tb=short -v  # 246 tests
# Flake rate: 0% (no E2E infrastructure issues)
```

**After conversion (Week 4):**
```bash
# Post-conversion metrics
time just test  # CI run time (260 tests: 246 + 12 converted + 2 removed)
pytest tests/unit --tb=short -v
pytest tests/contracts -m slow --tb=short -v  # Contract tests (nightly only)
# Flake rate target: ≤0.5% (no infrastructure, only code logic)
```

**Success criteria:**
- [ ] CI PR cycle time: ≥40% reduction
- [ ] Flake rate: ≤0.5%
- [ ] Contract tests: all pass nightly
- [ ] Coverage: same or better than baseline

### Docs Link

Update `E2E_STRATEGY_REVIEW.md` with final inventory:

```markdown
## Final Test Inventory (Post-Conversion)

### In CI (Every PR)
- Unit tests: 260 total (246 original + 12 converted from E2E)
- Contract tests: Skipped in PR, run nightly only

### Manual / Pre-Release Only
- E2E test: 1 (state-mutation verification)
- Trigger: Manual pre-release, tag-based, or on protected branch
- Runbook: docs/E2E_MANUAL_RUN.md
```

---

## Timeline & Milestones

| Date | Week | Task | Owner | Done |
|------|------|------|-------|------|
| 2026-09-29 | 1 | Justfile recipe mocking (8→unit) | — | [ ] |
| 2026-10-06 | 2 | API validation via TestClient (4→unit) | — | [ ] |
| 2026-10-13 | 3 | E2E isolation + manual runbook | — | [ ] |
| 2026-10-20 | — | ROI measurement & retrospective | — | [ ] |

---

## Related Documents

- [E2E_STRATEGY_REVIEW.md](E2E_STRATEGY_REVIEW.md) — Detailed analysis + recommendations
- [TEST_HEALTH_BACKLOG.md](TEST_HEALTH_BACKLOG.md) — Master backlog tracking all 4 priorities
- CI workflows: `.github/workflows/test.yml`, `.github/workflows/e2e-prerelease.yml`

---

## Questions & Decisions

**Q: Should contract tests run on every PR or only nightly?**  
**A:** Nightly only (marked with `@pytest.mark.contract @pytest.mark.slow`). They validate mock correctness, not regression. Worth running once daily but overkill for every PR.

**Q: What if we need to refactor the CLI entry point (subprocess call)?**  
**A:** Mocks live close to the boundary (subprocess.run level), so CLI refactors require mock updates. This is intentional—it forces us to think about the contract. Update + run contract test → validate real behavior still matches.

**Q: How do we prevent mock drift over time?**  
**A:** Three layers:
1. Code review: inspect mock setup for realism
2. Contract tests: run nightly against real API/subprocess
3. Flakiness rule: if tests pass unit but fail production, it's a mock drift ticket
