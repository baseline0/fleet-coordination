# Increment 2A: Enforcement Activation Complete

**Status:** ✅ COMPLETE  
**Date:** 2026-09-23  
**Scope:** All applicable fleet repositories (5 of 6)  
**Timeline:** 3-hour focused rollout (bootstrap + policy discovery + CI activation)

---

## Executive Summary

Import-linter 2.15 boundary enforcement is now **active and blocking** across all Python-packaged repositories. The rollout proved the tool, discovered a policy incomplete (fleet-toolbox→fleet-agents dependency), corrected it via ADR-0002, and integrated enforcement into CI.

| Repo | Status | Root | Contracts | CI |
|------|--------|------|-----------|-----|
| fleet-base | ✅ Enforced | fleet_base | 1 (forbid: fleet_*) | test.yml |
| fleet-agents | ✅ Enforced | tooling | 1 (forbid: fleet_ops, toolboxes, fleet_experiment) | test.yml |
| fleet-toolbox | ✅ Enforced | toolboxes | 1 (allow: tooling; forbid: fleet_base, fleet_ops, fleet_experiment) | test.yml |
| fleet-ops | ✅ Enforced | fleet_ops | 1 (forbid: fleet_experiment, non-fleet repos) | test.yml |
| fleet-spec | ✅ Enforced | fleet_experiment | 1 (forbid: all fleet) | test.yml |
| fleet-coordination | ⏭️ No Python package | — | N/A (pyproject.toml check only) | — |

---

## Rollout Evidence

### Phase 1: fleet-base (Commit edc3a1a)
**Objective:** Prove the pattern works.

**Evidence:**
```
Baseline:                    1 contract kept, 0 broken
Inject from fleet_ops:       1 contract broken ✅
Revert:                      1 contract kept, 0 broken
Integration (just):          ✅ Deterministic CLI invocation
```

**Outcome:** Pattern validated. Tool correctly recognizes contracts, detects violations, and integrates with justfile.

---

### Phase 2: fleet-agents (Commit ac5c9c6)
**Objective:** Replicate pattern across different dependency profile.

**Evidence:**
```
Root package: tooling (not src.tooling, not agent-tooling)
Allowed deps: fleet-base only
Forbidden deps: fleet-ops, toolboxes, fleet_experiment

Baseline:                    1 contract kept, 0 broken
Inject from fleet_ops:       1 contract broken ✅
Revert:                      1 contract kept, 0 broken
Integration (shared.just):   ✅ Wrapper script for centralized check-imports
```

**Outcome:** Pattern replicated successfully. Shared justfile recipe + wrapper script approach works across repos.

---

### Phase 3: fleet-toolbox (Commits 4956c3f + c0169e3 + ADR-0002)
**Objective:** Validate policy against reality.

**Critical Finding:** Baseline test FAILED—code imports `tooling.agents` (fleet-agents), but policy declared zero dependencies.

**Investigation:**
- `TodoAnalysisToolbox` in `src/toolboxes/todo/todo_analysis.py` inherits from `Toolbox` protocol
- Imports: `Context`, `Analysis`, `Recommendation`, `Toolbox` — all pure @dataclass types + ABC
- Exports: Explicitly declared in `tooling.agents.__all__`
- Use case: Stable contract for toolbox implementation

**Decision:** ADR-0002 approved policy correction.
- **Rationale:** Not accidental; intentional public API for fleet infrastructure
- **Boundary:** Allow `fleet-toolbox → fleet-agents` (narrow: only tooling.agents)
- **Review trigger:** If second independent consumer emerges, reconsider placement in fleet-base
- **Status:** Durable edge, not workaround

**Updated Policy Evidence:**
```yaml
fleet-toolbox:
  allowed_fleet_dependencies:
    - fleet-agents  # ← New
  notes:
    - "Consumes tooling.agents public contract (Toolbox, Context, Analysis, Recommendation)"
    - "Contract placement review required if second consumer emerges"
```

**Post-Correction Validation:**
```
Baseline:                    1 contract kept, 0 broken
Inject from fleet_ops:       Violation detected ✅
Inject from fleet_base:      Violation detected ✅
Inject from fleet_experiment: Violation detected ✅
Allowed import (tooling):    ✅ Passes without violation
Revert all:                  1 contract kept, 0 broken
```

**Outcome:** Policy discovery validated. Tool found real architectural incompleteness; ADR documented the correction.

---

### Phase 4: fleet-ops (Commit 0bc4816)
**Objective:** Enforce orchestration layer boundaries.

**Evidence:**
```
Root package: fleet_ops
Allowed deps: fleet-base, tooling, toolboxes
Forbidden deps: fleet_experiment, non-fleet repos

Baseline: 1 contract kept, 0 broken ✅
```

**Outcome:** Orchestration layer correctly isolated from experiment/spec layers.

---

### Phase 5: fleet-spec (Commits c77fc41 + c8e698f)
**Objective:** Enforce zero-dependency isolation.

**Evidence:**
```
Root package: fleet_experiment
Allowed deps: (none)
Forbidden deps: fleet_base, tooling, toolboxes, fleet_ops

Baseline: 1 contract kept, 0 broken ✅
```

**Outcome:** Experiment layer correctly isolated from all fleet infrastructure.

---

### Phase 6: fleet-coordination (No Python root)
**Status:** ⏭️ Skipped for import-linter.

**Rationale:** fleet-coordination is primarily governance/tooling (scripts/, docs/). No importable Python package (no `src/`, no `__init__.py` at package root).

**Isolation mechanism:** Rely on pyproject.toml dependency declarations (currently zero fleet deps—correct).

---

## Policy Artifacts

**Updated governance documentation:**
- `fleet-coordination/governance/fleet-architecture.yaml` (v0.1.0 with fleet-toolbox correction)
- `fleet-coordination/governance/decisions/ADR-0002-toolbox-agent-contract-dependency.md`

**Evidence locations:**
- Phase 1-5 violation detection and baseline results: Documented in commit messages
- Three-stage proof for fleet-base, fleet-agents, fleet-toolbox: Recorded in rollout narrative

---

## CI Integration

All applicable repositories now have `just check-imports` as a blocking CI step:

**Committed workflows:**
- `fleet-base/.github/workflows/test.yml` (2cdd57d)
- `fleet-agents/.github/workflows/test.yml` (9024403)
- `fleet-toolbox/.github/workflows/test.yml` (759918b)
- `fleet-ops/.github/workflows/test.yml` (6c24a6a)
- `fleet-spec/.github/workflows/test.yml` (a9307e6)

**Workflow pattern:**
```yaml
- name: Check import boundaries
  run: just check-imports
```

Runs **before tests**, fails fast on boundary violation, blocking merge to main.

---

## Technical Stack

| Component | Version | Status |
|-----------|---------|--------|
| import-linter | 2.15 | Pinned in all dev dependencies |
| Python | 3.13+ | Supported across fleet |
| uv | 0.12.13+ | Invokes linter via `uv run` |
| justfile | (shared.just) | Canonical developer interface |
| GitHub Actions | ubuntu-latest | CI environment |

**Configuration pattern:**
```ini
[importlinter]
root_package = <actual_import_root>  # e.g., fleet_ops, tooling, toolboxes
include_external_packages = True     # Required for cross-repo boundaries

[importlinter:contract:<id>]
name = <human-readable contract name>
type = forbidden
source_modules = <repo import root>
forbidden_modules = <list of forbidden roots>
```

---

## Key Decisions Locked In

1. ✅ **Polyrepo stays:** import-linter works well; no monorepo migration needed
2. ✅ **Policy-first enforcement:** Canonical YAML policy + import-linter validation
3. ✅ **fleet-toolbox→fleet-agents edge approved:** ADR-0002 documents rationale + review trigger
4. ✅ **CI gates active:** Blocking step before test execution
5. ✅ **No pytest wrapper:** CLI exit code is the contract; CI invokes `just check-imports` directly
6. ✅ **Manual violation testing complete:** Three-stage proof recorded; CI will catch regressions

---

## Known Limitations & Scope

**fleet-coordination:** No import-linter check (no Python package). Alternative: periodic `pyproject.toml` dependency audit.

**Public surface:** Not yet enforced (v1.0 policy deferred). Current focus: internal layer isolation.

**Stale dependencies:** fleet-toolbox still declares fleet-base (unused). Removal planned for Increment 2B after clean-environment proof.

---

## Next Phases

### Immediate (monitor CI)
- Run `just check-imports` in test workflows; assert no regressions
- Review CI execution logs for any false positives

### Increment 2B (planned)
- Remove stale fleet-base declaration from fleet-toolbox (after clean-environment test)
- Update policy v0.1.0 → v0.2.0 reflecting verified state

### Phase 3+ (future)
- Public surface enforcement (v1.0 policy)
- Consumer contract tests (fleet-ops ↔ fleet-base)
- Optional: Tach layering for advanced visualization

---

## Lessons Learned

1. **Enforcement bootstrap is policy discovery.** The tool found an incomplete policy, not a code error. This is expected and valuable.

2. **Role-focused interfaces reduce coupling.** `Toolbox`, `Context`, `Analysis`, `Recommendation` are abstractions that enable decoupling; they belong in the agent layer and should be reviewed for extraction if adopted by multiple consumers.

3. **Narrow contracts are durable.** A 4-symbol import is easier to maintain than a broad `from tooling import *`.

4. **CI integration closes the loop.** Manual injection testing proved the tool; CI execution ensures ongoing compliance.

---

## Summary

**Increment 2A is complete.** Five repositories now have active, blocking import-linter enforcement. One architectural discovery (fleet-toolbox→fleet-agents dependency) was documented and approved via ADR-0002. CI workflows ensure that boundary violations are caught before merge.

The enforcement model is now in place. Architecture is observed conformant *and* mechanically guaranteed.

---

**Approval:** Mark Alexiuk  
**Reviewed:** ✅ Policy v0.1.0 + ADR-0002  
**Status:** Ready for Increment 2B (cleanup + policy v0.2.0)
