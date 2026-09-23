# Checkpoint 3: Evidence-to-Policy Mapping Table

**Policy Version:** fleet-architecture.yaml v0.1.0  
**Evidence Base:** Checkpoint 2.1 results  
**Date:** 2026-09-23

---

## Repository Mapping: From Evidence to Policy

Each row maps a fleet repository to its exact identifiers, allowed edges, and evidence status.

| Repository | Repository Path | Distribution Name | Python Import Roots | Declared Fleet Deps | Static Imports Found | Policy: Allowed Deps | Status | Evidence Link |
|---|---|---|---|---|---|---|---|---|
| fleet-base | `fleet-base` | `fleet-base` | `fleet_base` | [] | self only (45) ✅ | [] | production | Checkpoint 2.1: Layer 0 verified; zero deps confirmed |
| fleet-agents | `fleet-agents` | `fleet-agents` | `tooling` | [fleet-base] | fleet_base ✅ | [fleet-base] | production | Checkpoint 2.1: Intentional mapping (distribution ≠ import root); Layer 0.5 verified |
| fleet-toolbox | `fleet-toolbox` | `fleet-toolbox` | `toolboxes` | [base, agents] STALE | 0 | [] | production | Checkpoint 2.1: Stale deps classified; cleanup pending removal proof (Increment 2B) |
| fleet-ops | `fleet-ops` | `fleet-ops` | `fleet_ops` | [base, agents, toolbox] | all 3 ✅ | [base, agents, toolbox] | production | Checkpoint 2.1: Layer 1 verified; all declared deps used |
| fleet-coordination | `fleet-coordination` | `fleet-coordination` | (none) | [] | 0 ✅ | [] | experimental | Checkpoint 2.1: Isolated governance layer; no code packages identified |
| fleet-spec | `fleet-spec` | `fleet-spec` | `fleet_experiment` | [] | 0 ✅ | [] | experimental | Checkpoint 2.1: Intentional mapping (distribution ≠ import root); isolated spec layer |

---

## Semantic Definitions (Policy Fields)

### `repository_path`
The Git directory name within `/home/mark/projects/`. Example: `fleet-base`.

**Source of Truth:** Directory listing from inventory scan.

### `distributions`
The value of `project.name` in `pyproject.toml` (Python package distribution name).

**Source of Truth:** grep from pyproject.toml during Checkpoint 2 inventory.

**Note:** May differ from `repository_path` (e.g., `fleet-agents` repo publishes as `fleet-agents`).

### `python_import_roots`
Top-level Python packages under `src/` that are importable by consumers.

**Source of Truth:** Import test during Checkpoint 2.1 (e.g., `import tooling` succeeds; `import fleet_agents` fails).

**Note:** Distinct from distribution name. Example: fleet-agents publishes as `fleet-agents` but imports as `tooling`.

### `allowed_fleet_dependencies`
List of fleet repositories that this repository may import from (by import root name).

**Policy Meaning:** All other fleet imports are forbidden.

**Enforcement Method:** import-linter rules (planned Increment 2A).

**Example:** fleet-ops may import fleet_base, fleet_agents (via tooling), fleet_toolbox. No other fleet packages.

### `public_surface.enforcement: disabled`
Indicates that public module inventories are not yet enforced.

**Rationale:** Public-module boundaries deferred until enforcement system is active and proven.

**Future:** Will move to `enabled` in v1.0 or later.

### `report_only`
Policy validation reports discrepancies but does not block merges or execution.

**Usage:** Checkpoint 3 draft only. Will change to `blocking` in Increment 2A once enforcement is verified.

---

## Import-Linter Configuration Status

### Current State
- **Configs Exist:** fleet-base, fleet-agents, fleet-ops, fleet-toolbox (4 files)
- **Tool Installed:** ❌ NO (not in any pyproject.toml or uv.lock)
- **CI Enforcement:** ❌ NO (not in workflows or justfiles)
- **Status:** Legacy artifacts; unvalidated; not enforcing

### Planned Activation (Increment 2A)

1. **Version Selection**
   - Pin a compatible `import-linter` release across all six repos.
   - Use uniform major.minor version (e.g., all `import-linter>=2.0.0,<3.0.0`).
   - Add to dev dependency group in each repo.

2. **Validation**
   - Regenerate each `uv.lock` with the new dependency.
   - Run existing legacy configs against real installed tool.
   - Document any syntax or semantic issues.
   - Validate the four legacy configs or rewrite them.

3. **Explicit Contracts for Isolated Repos**
   - Add `.importlinter` configs to fleet-coordination and fleet-spec.
   - Encode zero-fleet-dependency rules explicitly.

4. **Local and CI Activation**
   - Add `just check-imports` to all justfiles.
   - Create GitHub Actions workflow or CI step to run per-repo checks.
   - Make failure a PR blocker (optional; can be report-only initially).

### Test Plan (Increment 2A)
- Inject a deliberately forbidden import into each contract scope (one per layer/isolation level).
- Verify import-linter detects the violation.
- Verify CI gate (if active) blocks the PR.
- Revert the violation.
- Retain evidence of detection.

---

## Dependency Edge Verification

### Confirmed Edges (Checkpoint 2.1)

| Source | Target | Evidence | Status |
|---|---|---|---|
| fleet-agents | fleet-base | Static imports found (fleet_base) | ✅ Verified |
| fleet-ops | fleet-base | Static imports found (fleet_base) | ✅ Verified |
| fleet-ops | fleet-agents | Static imports found (tooling) | ✅ Verified |
| fleet-ops | fleet-toolbox | Static imports found (fleet_toolbox) | ✅ Verified |

### Zero-Dependency Verifications (Checkpoint 2.1)

| Repository | Evidence | Status |
|---|---|---|
| fleet-base | Zero fleet imports (self-imports only) | ✅ Verified |
| fleet-coordination | Zero fleet imports found | ✅ Verified |
| fleet-spec | Zero fleet imports found | ✅ Verified |
| fleet-toolbox | Zero fleet imports found (despite stale declarations) | ✅ Verified |

### Graph Properties

- **Acyclic:** ✅ Yes (no cycles detected)
- **Conformant to Policy:** ✅ Yes (observed graph matches intended graph, except stale fleet-toolbox deps)
- **Mechanically Enforced:** ❌ No (import-linter not running)

---

## Stale Dependency Cleanup (fleet-toolbox)

### Classification (Checkpoint 2.1)
Both declared dependencies are **STALE**:

**fleet-base:**
- Status: Declared in pyproject.toml
- Static imports: 0 found
- Dynamic imports: 0 found
- Plugin/entry-points: 0 found
- Test imports: 0 found
- Classification: STALE (unused)

**fleet-agents:**
- Status: Declared in pyproject.toml
- Static imports: 0 found
- Dynamic imports: 0 found
- Plugin/entry-points: 0 found
- Test imports: 0 found
- Classification: STALE (unused)

### Removal Plan (Increment 2B)

**Prerequisites:**
- Completion and success of Increment 2A (import-linter activated)
- Clean-environment removal proof:
  ```bash
  cd fleet-toolbox
  git stash
  rm -rf .venv
  
  # Remove from pyproject.toml:
  # "fleet-base @ file://...",
  # "fleet-agents @ file://...",
  
  uv sync
  uv run pytest
  uv run python -c "import toolboxes; print(toolboxes.__file__)"
  uv build
  ```

**Evidence Required:**
- Before/after diff of pyproject.toml
- uv.lock regeneration successful
- All tests pass
- Package imports work
- Build succeeds

**After Cleanup:**
- Policy v0.2.0 updated to reflect zero dependencies
- Inventory re-run documents the change
- PR references the removal proof

---

## Next Steps: Increment 2A (Enforcement Bootstrap)

### Scope
Activate import-linter across all six repositories as a local per-repo check.

### Sequence
1. Select import-linter version (e.g., `import-linter>=2.0.0,<3.0.0`)
2. Add to dev dependencies in all six repos
3. Regenerate uv.lock files
4. Validate legacy .importlinter configs with real tool
5. Create .importlinter configs for fleet-coordination and fleet-spec
6. Add `just check-imports` command to all justfiles
7. Test with deliberate violations (create, detect, revert)
8. Add GitHub Actions job to run check-imports per repo
9. Run clean mainline cycle with enforcement enabled
10. Document version, configuration, and test results

**Success Criteria:**
- All six repos can run `just check-imports` locally
- Tool runs in CI without errors
- Deliberate violations are detected
- Clean code passes all checks
- No false positives or false negatives in test suite

---

## Next Steps: Increment 2B (Cleanup & CI Promotion)

### Scope
Complete stale dependency removal and promote import-linter to required CI gate.

### Sequence
1. Run clean-environment removal proof for fleet-toolbox
2. Remove stale dependencies from pyproject.toml
3. Regenerate uv.lock and validate
4. Update policy v0.2.0 to reflect change
5. Promote import-linter CI checks to required/blocking
6. Run a full fleet-wide report-only validation pass
7. Document all changes in evidence archive

**Success Criteria:**
- fleet-toolbox has zero fleet dependencies
- All tests pass after removal
- CI gates are active and passing
- No boundary violations in entire fleet
- Evidence chain complete and auditable

---

## Evidence Files

This mapping references:

- `inventory.json` — Raw Checkpoint 2 inventory data
- `inventory-summary.md` — Checkpoint 2 analysis
- `CHECKPOINT-2.1-RESULTS.md` — Full reconciliation findings
- `CHECKPOINT-2.1-TASKS.md` — Task definitions and methods
- `MANIFEST.md` — Evidence metadata and collection details
- `fleet-architecture.yaml` — This policy (v0.1.0)

All files are located in:
```
fleet-coordination/governance/evidence/checkpoint-2/
fleet-coordination/governance/fleet-architecture.yaml
```

---

## Sign-Off

✅ **Checkpoint 3 Draft: Evidence-to-Policy Mapping Complete**

Policy is grounded in Checkpoint 2.1 evidence. Ready for wingman review and approval.
