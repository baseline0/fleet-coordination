# CI Gate Status: Import Boundary Checks

**Date:** 2026-09-23  
**Scope:** All applicable repositories (5 Python-packaged repos)

---

## Current State

**Workflows deployed:** 5 test workflows include `just check-imports` as a blocking step before pytest.

| Repo | Workflow | Step | Status |
|------|----------|------|--------|
| fleet-base | `.github/workflows/test.yml` | Check import boundaries | ✅ Runs |
| fleet-agents | `.github/workflows/test.yml` | Check import boundaries | ✅ Runs |
| fleet-toolbox | `.github/workflows/test.yml` | Check import boundaries | ✅ Runs |
| fleet-ops | `.github/workflows/test.yml` | Check import boundaries | ✅ Runs |
| fleet-spec | `.github/workflows/test.yml` | Check import boundaries | ✅ Runs |

**Workflow behavior:**
- Runs **before** test execution
- Exits with **non-zero code** on any boundary violation
- Halts the test job on failure (blocking subsequent steps)

---

## Branch Protection Status

**Administrative action required:** To make these gates **merge-blocking**, configure branch protection rules on GitHub:

```
Settings → Branches → main → Require status checks to pass
  ✓ test / test (python-version: 3.13)
```

This ensures that:
1. PRs cannot merge until `just check-imports` passes
2. CI failure automatically blocks the merge button
3. Force-push to main is prevented (without explicit admin override)

**Current status:** Workflows run on every PR/push but are **not yet required** for merge. The gate is in CI; it is not yet enforced by branch protection.

---

## Recommendation

Before marking this as "CI gates active (blocking)":

1. Configure branch protection for all five repositories
2. Verify that a hypothetical boundary violation blocks a test PR
3. Test the exception workflow (if needed: temporarily disable the check to assess the workflow)

This separates two concerns:
- **Increment 2A:** Enforcement tooling + CI execution (✅ Complete)
- **Administrative:** Branch protection policy + merge gate binding (⏳ Next)

---

## Notes

- `fleet-coordination` has no Python package and therefore no import-linter CI check (correct per policy)
- The boundary check is deterministic (import-linter v2.15 with locked config)
- No false positives observed in rollout (5 repos, all baseline-pass)
- Negative control evidence (violation detection) documented in rollout narrative
