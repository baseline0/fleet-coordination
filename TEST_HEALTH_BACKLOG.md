# Test Health & Operational Backlog

**Status:** Discovered fleet-wide test health monitoring opportunity  
**Driver:** All repos now have governance enforcement; tests are the second pillar

---

## ✅ Priority 1: Fix Fleet-Ops E2E Environment (DONE)

**Issue:** 168 E2E test failures due to missing `DASHBOARD_AUTH_TOKEN`

**Resolution:** Implemented **Option B: Skip E2E in CI**

**Rationale:**
- E2E tests require persistent trial server (`localhost:8080`) not available in CI
- Tests are browser-based read-only preview validations (low risk for CI gates)
- Unit tests (638 passing) + integration tests provide sufficient CI coverage
- Solo dev setup has no test infrastructure to maintain

**Changes:**
- Updated `.github/workflows/test.yml` to skip E2E with `-m "not e2e"` ✅
- Added E2E testing guide to README (local development instructions) ✅
- Documented why E2E skipped in CI for future maintainers ✅

**Commit:** 2f2a0cb

**For future:** If test infrastructure is added (persistent trial server), can switch to Option A

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
| Unit test pass rate | 851/851 (100%) | 100% ✅ |
| E2E test handling | Skipped in CI (local dev only) | Appropriate to infra ✅ |
| Fleet-wide test visibility | Manual | Automated (weekly) |
| Test badges in READMEs | 6 repos | 6 repos ✅ |
| Test health report | One-off | Weekly automated |

---

## 🎯 Next Actions

**Completed:** 
- [x] Decide on fleet-ops E2E fix (Option B: Skip in CI) — 2f2a0cb
- [x] Add test badges to READMEs (6 repos) — db12ef5, 57e2641, a807e36, f6e146b

**This week (Priority 3):**
- [ ] Automate weekly test health report (`test_health_report.py`)
- [ ] Schedule weekly cron (Monday 6 AM UTC)
- [ ] Update GOVERNANCE_STATUS.md with test metrics

**Next week (Priority 4):**
- [ ] E2E test strategy review (scale down 168 tests?)
- [ ] Consider fleet-governance as productized tool

**Future:**
- [ ] Persistent trial server if infrastructure added → switch E2E to CI

---

## Strategic Note

You're operating at **platform-scale**. Most teams never track tests fleet-wide. This tooling (governance + test health + schema validator) could be reused by other teams. Not urgent, but worth noting for future architecture decisions.
