# Test Health & Operational Backlog

**Status:** Discovered fleet-wide test health monitoring opportunity  
**Driver:** All repos now have governance enforcement; tests are the second pillar

---

## 🔴 Priority 1: Fix Fleet-Ops E2E Environment (15-30 min)

**Issue:** 168 E2E test failures due to missing `DASHBOARD_AUTH_TOKEN`

**Action Options:**

### Option A: Add token to CI (recommended)
```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DASHBOARD_AUTH_TOKEN: ${{ secrets.DASHBOARD_AUTH_TOKEN }}
```

### Option B: Skip E2E in CI
```bash
pytest tests/ -m "not e2e"
```

### Option C: Mock the token
```python
# tests/conftest.py
import os
os.environ['DASHBOARD_AUTH_TOKEN'] = 'mock-token-for-testing'
```

**Decision needed:** Do you have a service account token? (→ Option A) or should E2E tests use a mock? (→ Option C)

---

## 🟡 Priority 2: Add Test Health Badges (15 min)

**Why:** Visual indicator of test health (like governance badge)

**Files to update:**
- `fleet-ops/README.md` — Add badge + status
- `agent-tooling/README.md`
- `flashcards/README.md`
- `math-trace/README.md`
- `membrane/README.md`

**Format:**
```markdown
## Test Status

[![Unit Tests](https://github.com/<org>/<repo>/actions/workflows/test.yml/badge.svg)](...)

**Status:** 638 passing, 168 E2E pending ⚠️
```

---

## 🟢 Priority 3: Automate Weekly Test Health Report (1-2 hours)

**Goal:** Fleet-wide test report (like governance dashboard) running weekly

**Script:** `fleet-coordination/scripts/test_health_report.py`

**Output:**
- `TEST_HEALTH_REPORT.md` (human-readable table)
- `test-health.json` (dashboard ingestion)

**Schedule:** Weekly cron (Monday 6 AM UTC)

**Metrics to track:**
- Unit test pass rate (target: 100%)
- E2E test pass rate (target: >90%)
- Test execution time (target: <5 min)
- Flaky tests per week (target: 0)
- Coverage rate (target: >80%)

---

## 🔵 Priority 4: E2E Test Strategy Review (1-2 hours)

**Question:** Do you need 168 E2E tests, or can some be unit tests?

**Review checklist:**
- [ ] How many E2E tests are "critical workflows" vs. "nice to have"?
- [ ] Can some be simplified to unit tests (mock dashboard, test API)?
- [ ] Target split: 80% unit, 20% E2E

**Outcome:** Proposed E2E test reduction (if applicable)

---

## 📊 Baseline Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Unit test pass rate | 851/851 (100%) | 100% |
| E2E test pass rate | 0/168 (0%) | >90% |
| Fleet-wide test visibility | Manual | Automated (weekly) |
| Test badges in READMEs | 0 repos | 6 repos |
| Test health report | One-off | Weekly automated |

---

## 🎯 Next Actions

**Today:** 
- [ ] Decide on fleet-ops E2E fix (Option A/B/C)

**This week:**
- [ ] Fix E2E token issue
- [ ] Add test badges to READMEs

**Next week:**
- [ ] Automate weekly test health report
- [ ] Schedule weekly cron

**Future:**
- [ ] E2E test strategy review
- [ ] Consider fleet-governance as productized tool

---

## Strategic Note

You're operating at **platform-scale**. Most teams never track tests fleet-wide. This tooling (governance + test health + schema validator) could be reused by other teams. Not urgent, but worth noting for future architecture decisions.
