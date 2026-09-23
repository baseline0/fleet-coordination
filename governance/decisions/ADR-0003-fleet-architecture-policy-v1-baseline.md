# ADR-0003: Fleet Architecture Policy v1.0.0 Baseline Promotion

**Status:** APPROVED  
**Date:** 2026-09-23  
**Deciders:** Architecture Team  
**Consequence:** Policy v1.0.0 locked; enforcement active; next milestone is GitHub branch protection configuration

---

## Context

The fleet architecture policy evolved through three phases:

1. **Checkpoint 1–3 (v0.1.0):** Evidence-based policy design, inventory validation, policy draft
2. **Increment 2A/2B (v0.1.0 maintained):** Enforcement tooling bootstrapped, stale dependencies removed, ADR-0002 documented
3. **Fleet-wide validation (v0.1.0 → v1.0.0):** Canonical policy, declared dependencies, observed imports, and Import Linter contracts all aligned with zero discrepancies

---

## Decision

**Promote fleet-architecture.yaml from v0.1.0 to v1.0.0** as a stable, validated baseline.

### What v1.0.0 Means

The schema, identifier mapping, approved Python dependency graph, and validation scope have an accepted baseline:

- **Stable:** not expected to change without deliberate review and versioning
- **Validated:** all four architecture views (policy, declared, observed, contracts) agree with zero discrepancies as of 2026-09-23
- **Reproducible:** fleet_validation.py can regenerate this baseline; any deviation is auditable
- **Scoped:** Python package boundaries only; excludes dynamic imports, MCP, HTTP, CLI, Docker, workflows

### Approved Dependency Graph (Locked in v1.0.0)

```
fleet-base (layer 0)
  ↓ [depends on nothing]

fleet-agents (layer 0.5) 
  ↓ [depends on fleet-base]
  fleet-base

fleet-toolbox (layer 1.5)
  ↓ [depends on fleet-agents; fleet-base removed per ADR cleanup]
  fleet-agents

fleet-ops (layer 1)
  ↓ [depends on base, agents, toolbox]
  fleet-base, fleet-agents, fleet-toolbox

fleet-spec (layer 2)
  ↓ [depends on nothing]

fleet-coordination (layer 2)
  ↓ [depends on nothing; no Python package root]
```

**Invariant:** All edges are acyclic. All declared dependencies match policy and observed imports. No stale or undeclared dependencies remain.

---

## Evidence

### Validation Report (2026-09-23)

**Command:** `uv run python governance/tools/fleet_validation.py`

**Result:**
```
5 repositories assessed
5 Match (policy ≈ declared ≈ observed)
0 Info, Warning, Error
0 Discrepancies
```

**Details:**

| Repo | Declared → Policy | Observed → Declared | Import-Linter | Status |
|------|---|---|---|---|
| fleet-base | (none) = (none) | (none) = (none) | ✅ 1 contract | MATCH |
| fleet-agents | fleet-base = fleet-base | fleet-base = fleet-base | ✅ 1 contract | MATCH |
| fleet-toolbox | fleet-agents = fleet-agents | fleet-agents = fleet-agents | ✅ 1 contract | MATCH |
| fleet-ops | base, agents, toolbox = base, agents, toolbox | base, agents, toolbox = base, agents, toolbox | ✅ 1 contract | MATCH |
| fleet-spec | (none) = (none) | (none) = (none) | ✅ 1 contract | MATCH |
| fleet-coordination | (none, static) = (none, static) | (none, static) = (none, static) | N/A (static checks) | MATCH |

**Fleet-coordination static checks:**
```bash
grep -i "fleet-\|fleet_" pyproject.toml → (no fleet deps declared)
grep "from \|import " *.py → (no fleet imports in code)
```

**Reproducibility:** All repo SHAs and tool versions recorded in JSON report.

---

## Enforcement Status

### Active (as of Increment 2A/2B)

✅ **Local:** `just check-imports` runs in all 5 Python-packaged repos  
✅ **CI:** Workflows execute the check on every PR/push  
✅ **Blocking:** Violations cause test job failure (blocks subsequent CI steps)  
✅ **Contracts:** 5 Import-Linter contracts defined and passing  

### Pending (Administrative Action Required)

⏳ **Merge-blocking:** GitHub branch protection/rulesets must require the boundary-check job name  
⏳ **Verification:** Test a deliberately failing PR to confirm merge is blocked

### Out of Scope (v1.0.0)

❌ **Dynamic imports:** Runtime CLI, HTTP, plugin loading  
❌ **MCP integrations:** Cross-process module loading  
❌ **Docker/deployment:** Container-level coupling  
❌ **Workflow dependencies:** GitHub Actions, CI/CD orchestration  
❌ **Public surface:** v2.0+ scope (requires consumer inventory)  

---

## Changes from v0.1.0

### Policy Content
- No changes to approved edges or invariants
- Added explicit enforcement metadata (status, scope, limitations)
- Added validation baseline and discrepancy count

### Dependencies (Increment 2B)
- **fleet-toolbox:** Removed stale `fleet-base` declaration (clean-environment proof in commit 62ce3ab)
- **All others:** Unchanged

### Supporting Artifacts
- **ADR-0002:** Documented `fleet-toolbox → fleet-agents` edge with review trigger
- **CI Gates:** Five test workflows now include `just check-imports` step
- **Validation Script:** `fleet_validation.py` added for reproducible audits

---

## Next Administrative Actions

### Immediate (Block Merge Without)

1. **GitHub Branch Protection:**
   - Per-repository in `Settings → Branches → main`
   - Require status check: `test / test` (the import-linter step)
   - Test with a deliberately failing PR to confirm block

2. **Verification:**
   - Record required check name in each repo's CI workflow docs
   - Test that accidental bypass is prevented

### Short-term (Phase 3 Roadmap)

- **Increment 2C:** Public surface enforcement (v2.0 policy)
  - Identify cross-repo module consumers (e.g., fleet-ops → fleet-base audit types)
  - Define public contract APIs
  - Add consumer contract tests

- **Phase 3+:** Advanced tooling
  - Optional: Tach layering for visualization
  - Optional: Per-layer SLA enforcement
  - Optional: Periodic fleet-wide audit reporting

---

## No Regression Clause

If a future validation pass shows discrepancies, the policy version does not automatically drop:

1. **Investigation required:** Determine if the discrepancy is a real architectural change or a measurement error
2. **Classification:** Mark as approved (ADR), corrected (patch to declarations/contracts), or a violation (revert change)
3. **Versioning:** Only promote to v1.1.0+ after correction and re-validation

This ensures v1.0.0 remains the stable baseline for auditing change history.

---

## Summary

Fleet architecture is now:
- **Explicitly defined** (policy v1.0.0)
- **Mechanically checked** (import-linter in all Python repos)
- **Continuously validated** (fleet_validation.py with reproducible reports)
- **Evidence-backed** (zero discrepancies, all four views aligned)
- **Ready for governance gates** (pending GitHub branch protection configuration)

The next critical step is configuring required status checks in branch protection so violations cannot bypass merge gates. After that, the Python dependency architecture is guaranteed by both policy and technical enforcement.

---

**Approval:** Mark Alexiuk  
**Evidence:** validation_2026-09-23T07-43-45.{json,md}  
**Status:** v1.0.0 locked; merge-blocking pending branch protection
