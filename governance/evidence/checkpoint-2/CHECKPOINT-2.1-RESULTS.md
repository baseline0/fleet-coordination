# Checkpoint 2.1 Results: Reconciliation & Findings

**Execution Date:** 2026-09-23  
**Investigator:** Claude (fleet-ops assistant)  
**Status:** ✅ All three tasks complete

---

## Task 1: Package Identity Verification

### Finding: Intentional Distribution/Import-Root Mismatch

**fleet-agents:**
```
Distribution:     fleet-agents (from pyproject.toml project.name)
Import Root:      tooling (actual public import package in src/)
Mapping:          INTENTIONAL ✅
Result:           ✅ tooling is importable
                  ❌ fleet_agents is NOT importable (doesn't exist)
```

**fleet-spec:**
```
Distribution:     fleet-spec (from pyproject.toml project.name)
Import Root:      fleet_experiment (actual public import package in src/)
Mapping:          INTENTIONAL ✅
Result:           ✅ fleet_experiment is importable
                  ❌ fleet_spec is NOT importable (doesn't exist)
```

### Classification

| Repository | Distribution | Import Roots | Mapping Intentional? | Policy Note |
|---|---|---|---|---|
| fleet-agents | fleet-agents | tooling | ✅ Intentional | Public API is `tooling`; distribution name is for packaging |
| fleet-spec | fleet-spec | fleet_experiment | ✅ Intentional | Public API is `fleet_experiment`; distribution name is for packaging |

**Action for Policy:** Policy YAML must normalize this mapping. Do NOT rename packages; the current separation is intentional.

---

## Task 2: fleet-toolbox Dependency Investigation

### Finding: Declared But Completely Unused

**Declared Dependencies:**
```toml
dependencies = [
    "fleet-base @ file:///home/mark/projects/fleet-base",
    "fleet-agents @ file:///home/mark/projects/fleet-agents",
]
```

**Investigation Results:**
- ✅ Static imports searched: 0 found
- ✅ Dynamic imports searched (`importlib`, `__import__`, etc.): 0 found
- ✅ Plugin/entry-point configs: None
- ✅ Test files checked: No fleet imports
- ✅ Fleet package references in docstrings: Only in "fleet-toolbox" (name, not imports)

### Classification

| Repository | Dependency | Usage Evidence | Classification | Recommendation |
|---|---|---|---|---|
| fleet-toolbox | fleet-base | None found (0 static, 0 dynamic, 0 tests) | **STALE** ❌ | REMOVE from dependencies |
| fleet-toolbox | fleet-agents | None found (0 static, 0 dynamic, 0 tests) | **STALE** ❌ | REMOVE from dependencies |

**Why These Were Declared:** Unknown. Possible explanations:
- Reserved for planned future use (no longer planned)
- Legacy dependency from refactoring (forgotten removal)
- Accidentally added and never used

**Action for Policy:** 
1. Remove both stale dependencies from fleet-toolbox/pyproject.toml
2. Update policy to reflect that fleet-toolbox has zero fleet dependencies (currently lists base + agents)
3. Add to Increment 2 cleanup work

---

## Task 3: import-linter CI Verification

### Finding: Configs Exist But Tool Is NOT Installed or Enforced

**Current State:**
```
✅ .importlinter config files exist:
   - fleet-base/.importlinter
   - fleet-agents/.importlinter
   - fleet-ops/.importlinter
   - fleet-toolbox/.importlinter

❌ import-linter tool NOT installed:
   - NOT declared in any pyproject.toml
   - NOT in any uv.lock
   - Not runnable via `python -m importlinter`

❌ NOT enforced in CI:
   - No GitHub Actions workflows execute import-linter
   - No justfile commands for import-linter
   - No CI gates or enforcement

❌ Isolated repos (fleet-coordination, fleet-spec):
   - No .importlinter configs
   - Isolation is implicit, not enforced
```

### Detailed Verification Results

| Repository | .importlinter Exists | GitHub Actions | justfile Commands | Local Test Result | Enforcement Status |
|---|---|---|---|---|---|
| fleet-base | ✅ Yes | ❌ None | ❌ None | ❌ Module not found | **DORMANT** |
| fleet-agents | ✅ Yes | ❌ None | ❌ None | ❌ Module not found | **DORMANT** |
| fleet-ops | ✅ Yes | ❌ None | ❌ None | ❌ Module not found | **DORMANT** |
| fleet-toolbox | ✅ Yes | ❌ None | ❌ None | ❌ Module not found | **DORMANT** |
| fleet-coordination | ❌ No | ❌ None | ❌ None | N/A | **NO ENFORCEMENT** |
| fleet-spec | ❌ No | ❌ None | ❌ None | N/A | **NO ENFORCEMENT** |

### Root Cause Analysis

The `.importlinter` config files are **legacy artifacts**:
- They were created with a policy-draft intention
- The tool was never integrated as a dependency or CI gate
- They are syntactically correct but operationally inert

### Action Items

**Immediate (Checkpoint 3):**
1. Policy should NOT assume import-linter is enforced (it is not)
2. Document in policy: "import-linter configs are present but currently dormant"

**Increment 2 (Enable import-linter):**
1. Add `import-linter` to dev dependencies in all six repos
2. Create or update GitHub Actions workflows to run import-linter on PRs
3. Add `just check-imports` command to all justfiles
4. Promote to CI blocking gates for repos with `.importlinter` configs
5. Add explicit zero-dependency contracts for fleet-coordination and fleet-spec

**Increment 2 Parallel (Cleanup):**
1. Remove stale fleet dependencies from fleet-toolbox
2. Decide whether to keep or remove the .importlinter configs (if specs are final)

---

## Summary Reconciliation Table (All Findings)

| Repository | Distribution | Import Roots | Declared Fleet Deps | Static Imports | import-linter Config | CI Enforced? | Policy Implication |
|---|---|---|---|---|---|---|---|
| **fleet-base** | fleet-base | fleet_base | [] | 45 (self) | ✅ (dormant) | ❌ No | Layer 0: Zero fleet deps verified; add CI gate |
| **fleet-agents** | fleet-agents | tooling | [fleet-base] | fleet_base ✅ | ✅ (dormant) | ❌ No | Intentional mapping; Layer 0.5 verified; add CI gate |
| **fleet-coordination** | fleet-coordination | (none) | [] | 0 | ❌ | ❌ No | Isolated; add explicit .importlinter + CI gate |
| **fleet-ops** | fleet-ops | fleet_ops | [base, agents, toolbox] | All 3 ✅ | ✅ (dormant) | ❌ No | Layer 1 verified; add CI gate |
| **fleet-spec** | fleet-spec | fleet_experiment | [] | 0 | ❌ | ❌ No | Isolated; add explicit .importlinter + CI gate |
| **fleet-toolbox** | fleet-toolbox | toolboxes | [base, agents] ❌ STALE | 0 | ✅ (dormant) | ❌ No | Remove stale deps; zero fleet deps verified; add CI gate |

---

## Critical Discoveries

### 1. Boundary Enforcement is Dormant (High Priority)

**Problem:** All `.importlinter` configs exist but the tool is not installed or enforced in CI. The layer model is correct in practice but not mechanically enforced.

**Risk:** Someone could accidentally introduce a boundary violation and it would not be caught.

**Solution:** Wire up import-linter as a CI gate (Increment 2).

### 2. fleet-toolbox Has Stale Dependencies (Medium Priority)

**Problem:** Declares fleet-base and fleet-agents but doesn't use them.

**Risk:** False indication of dependency coupling; adds installation bloat; confuses policy.

**Solution:** Remove stale deps from fleet-toolbox (Increment 2 cleanup).

### 3. Isolated Repos Lack Explicit Contracts (Medium Priority)

**Problem:** fleet-coordination and fleet-spec are isolated (zero fleet imports) but have no `.importlinter` contracts to enforce it.

**Risk:** Isolation is implicit; could drift if someone adds a dependency later.

**Solution:** Create zero-dependency `.importlinter` configs for both (Increment 2).

### 4. Distribution/Import-Root Mismatch Is Intentional (Low Priority)

**Problem:** fleet-agents and fleet-spec use different names for distribution vs. import root.

**Risk:** None currently; it's intentional and works correctly.

**Action:** Document in policy; do NOT rename packages.

---

## Next Checkpoints

### Checkpoint 3: Policy Draft
Use this reconciliation table to populate `fleet-architecture.yaml` v0.1.0 with:
- Correct distribution/import-root mappings
- Actual dependency graph (without stale fleet-toolbox deps)
- Note that import-linter is currently dormant

### Increment 2: Enforcement & Cleanup
1. Install and wire import-linter in CI (all repos)
2. Remove stale fleet-toolbox dependencies
3. Add explicit isolation configs for fleet-coordination and fleet-spec
4. Make CI gates required before merge

---

## Files

- **This file:** Reconciliation results and root cause analysis
- **CHECKPOINT-2.1-TASKS.md:** Original task definitions and methods
- **inventory.json:** Raw Checkpoint 2 inventory
- **inventory-summary.md:** Checkpoint 2 analysis
- **MANIFEST.md:** Checkpoint 2 metadata and evidence chain

---

## Approval Status

✅ **Checkpoint 2.1 COMPLETE**

All three investigations finished. Ready for Checkpoint 3: Policy Draft.
