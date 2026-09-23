# Increment 2A: Import-Linter Bootstrap & Enforcement Activation

**Status:** Ready to Execute  
**Priority:** High (closes enforcement gap identified in Checkpoint 3)  
**Estimated Time:** 2–3 hours  
**Owner:** Mark Alexiuk  
**Evidence Base:** Checkpoint 2.1 results + fleet-architecture.yaml v0.1.0

---

## Objective

Activate import-linter as a mechanical guardrail across all six fleet repositories. Move from observed conformance (Checkpoints 2–3) to enforced conformance (Increment 2A+).

**Success Criteria:**
- ✅ import-linter installed and pinned in all six repos
- ✅ All legacy .importlinter configs validated or rewritten
- ✅ Explicit zero-dependency contracts added to fleet-coordination and fleet-spec
- ✅ `just check-imports` command works locally in all repos
- ✅ Deliberate test violations are detected
- ✅ GitHub Actions workflows execute checks on PRs
- ✅ Clean mainline passes all checks

---

## Phase 1: Version Selection & Installation (30 min)

### Step 1.1: Select import-linter Version

**Decision:** Which version/release to pin?

**Recommended:** `import-linter>=2.0.0,<3.0.0` (latest stable major version)

**Action:**
```bash
# Check available versions
pip index versions import-linter
# or visit: https://pypi.org/project/import-linter/

# Current recommended: 2.0.1 or later (if available)
```

**Commit this choice** to the Increment 2A plan before proceeding.

### Step 1.2: Add Dependency to All Six Repos

For each repository (fleet-base, fleet-agents, fleet-coordination, fleet-ops, fleet-spec, fleet-toolbox):

```bash
cd /home/mark/projects/REPO

# Add to dev dependencies (not production)
uv add --group dev import-linter>=2.0.0,<3.0.0

# Verify it's in pyproject.toml
grep import-linter pyproject.toml

# Check uv.lock was regenerated
git status uv.lock
```

**Expected Output:**
```
[dependency-groups]
dev = [
    ...existing deps...,
    "import-linter>=2.0.0,<3.0.0",
]
```

### Step 1.3: Verify Installation

```bash
cd /home/mark/projects/REPO

# Test the tool is available
uv run python -m importlinter --version
# Expected: importlinter X.Y.Z

# Check canonical executable name
uv run which lint-imports || echo "Using: python -m importlinter"
```

**Record the canonical invocation** (will be used in justfiles).

---

## Phase 2: Legacy Config Validation (45 min)

### Step 2.1: Validate Existing .importlinter Files

For each repo with an existing `.importlinter` config (fleet-base, fleet-agents, fleet-ops, fleet-toolbox):

```bash
cd /home/mark/projects/REPO

# Run import-linter against the existing config
uv run python -m importlinter

# Expected: Either success, or specific error messages about syntax/rules
```

**Record Results:**
- ✅ Config validates (syntax OK, can run)
- ⚠️ Config has warnings (e.g., deprecated rules)
- ❌ Config fails (syntax error or incompatible version)

**If Validation Fails:**
- Read the error message carefully
- Determine if it's a syntax error or tool incompatibility
- Either fix the config or rewrite it based on policy

### Step 2.2: Rewrite Configs (If Needed)

If any legacy config fails validation, use this template as a starting point:

```ini
[importlinter]
root_package = src.fleet_base  # Example; adjust to your root package

# Layer 0: fleet-base
# Forbidden: Any fleet import (isolation enforced)
[forbidden]
name = Layer 0 isolation
condition = root_package
modules_forbidden_to_import =
    fleet_agents
    fleet_coordination
    fleet_ops
    fleet_spec
    fleet_toolbox
    tooling

# Configuration check (additional invariant)
[forbidden]
name = Configuration via environment, not os.getenv
condition = root_package
modules_forbidden_to_import =
    os -> getenv
    os -> environ
```

**Consult:** The inventory identifies the actual import roots per repo. Adjust `root_package` accordingly.

### Step 2.3: Document Config Status

Create or update a table in fleet-coordination/governance/IMPORT-LINTER-CONFIG-STATUS.md:

| Repository | Config Path | Validation | Status | Notes |
|---|---|---|---|---|
| fleet-base | .importlinter | ✅ Pass | Ready | No changes needed |
| fleet-agents | .importlinter | ✅ Pass | Ready | root_package = src.tooling (non-standard name) |
| fleet-ops | .importlinter | ✅ Pass | Ready | No changes needed |
| fleet-toolbox | .importlinter | ⚠️ Warn | Rewritten | Added explicit [forbidden] rules |

---

## Phase 3: Explicit Contracts for Isolated Repos (30 min)

### Step 3.1: Create .importlinter for fleet-coordination

File: `/home/mark/projects/fleet-coordination/.importlinter`

```ini
[importlinter]
root_package = src.fleet_coordination

# Isolation contract: zero fleet imports
[forbidden]
name = Isolation: no fleet imports
condition = root_package
modules_forbidden_to_import =
    fleet_base
    fleet_agents
    fleet_ops
    fleet_spec
    fleet_toolbox
    tooling
    agent_adapters
    agents_cli
```

### Step 3.2: Create .importlinter for fleet-spec

File: `/home/mark/projects/fleet-spec/.importlinter`

```ini
[importlinter]
root_package = src.fleet_experiment

# Isolation contract: zero fleet imports
[forbidden]
name = Isolation: no fleet imports
condition = root_package
modules_forbidden_to_import =
    fleet_base
    fleet_agents
    fleet_ops
    fleet_coordination
    fleet_toolbox
    tooling
```

### Step 3.3: Validate New Configs

```bash
cd /home/mark/projects/fleet-coordination
uv run python -m importlinter
# Expected: No violations (or informational only)

cd /home/mark/projects/fleet-spec
uv run python -m importlinter
# Expected: No violations
```

---

## Phase 4: Local Commands & Justfile Integration (30 min)

### Step 4.1: Add `just check-imports` to All Justfiles

For each repository, add this recipe to the justfile:

```justfile
[group('quality')]
check-imports:
    @echo "🔍 Checking import boundaries..."
    uv run python -m importlinter
```

### Step 4.2: Test Locally

```bash
cd /home/mark/projects/REPO
just check-imports
```

**Expected:** Clean run with no violations (or pass the existing check status).

### Step 4.3: Verify in All Six Repos

```bash
for repo in fleet-base fleet-agents fleet-coordination fleet-ops fleet-spec fleet-toolbox; do
  echo "=== $repo ==="
  cd /home/mark/projects/$repo
  just check-imports || echo "FAILED"
done
```

---

## Phase 5: Test Violations (Deliberate Detection) (30 min)

### Step 5.1: Inject Forbidden Import (Layer 0 Test)

In `fleet-base/src/fleet_base/test_boundary.py` (temporary file):

```python
# This should be FORBIDDEN in Layer 0
from fleet_ops.cli import cli  # DELIBERATELY FORBIDDEN

def test_violation():
    pass
```

### Step 5.2: Run Check & Verify Detection

```bash
cd /home/mark/projects/fleet-base
just check-imports
# Expected: FAIL with message about forbidden import
```

**Capture the output** — this is proof of detection.

### Step 5.3: Revert Violation

```bash
rm fleet-base/src/fleet_base/test_boundary.py
just check-imports
# Expected: PASS
```

### Step 5.4: Test Isolated Repo Contract

In `fleet-coordination/src/fleet_coordination/test_boundary.py` (temporary):

```python
# This should be FORBIDDEN (isolation)
from fleet_ops.cli import cli  # DELIBERATELY FORBIDDEN

def test_violation():
    pass
```

### Step 5.5: Verify Detection & Revert

```bash
cd /home/mark/projects/fleet-coordination
just check-imports
# Expected: FAIL

rm src/fleet_coordination/test_boundary.py
just check-imports
# Expected: PASS
```

**Document:** Violations were detected successfully.

---

## Phase 6: CI Integration (30 min)

### Step 6.1: Add GitHub Actions Workflow (Per Repo)

For each repository, add or update `.github/workflows/lint.yml` (or similar):

```yaml
name: Import Boundaries

on: [push, pull_request]

jobs:
  import-linter:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v2
      - run: uv run python -m importlinter
```

### Step 6.2: Test Workflow

Push a branch with the temporary test violation to trigger the workflow. Verify CI catches it.

### Step 6.3: Promote to Required Check (Optional)

In GitHub repository settings, add `import-linter` as a required status check for PRs. For now, keep it report-only (informational) — promote to blocking after one full clean mainline cycle.

---

## Phase 7: Mainline Validation & Evidence (15 min)

### Step 7.1: Clean Mainline Run

Ensure all six repos are on main with clean working trees:

```bash
for repo in fleet-base fleet-agents fleet-coordination fleet-ops fleet-spec fleet-toolbox; do
  cd /home/mark/projects/$repo
  git checkout main
  git pull
  just check-imports
  echo "✅ $repo clean"
done
```

### Step 7.2: Commit Results

Create an evidence file documenting the bootstrap:

File: `fleet-coordination/governance/evidence/increment-2a/IMPORT-LINTER-BOOTSTRAP-EVIDENCE.md`

```markdown
# Increment 2A: Import-Linter Bootstrap Evidence

**Date:** 2026-09-23  
**Tool Version:** import-linter 2.0.1  
**Status:** Activated across all six repos

## Per-Repository Status

| Repository | Config | Validation | Test Violation | CI Workflow | Status |
|---|---|---|---|---|---|
| fleet-base | ✅ | ✅ Pass | ✅ Detected | ✅ Active | Ready |
| fleet-agents | ✅ | ✅ Pass | ✅ Detected | ✅ Active | Ready |
| fleet-coordination | ✅ | ✅ Pass | ✅ Detected | ✅ Active | Ready |
| fleet-ops | ✅ | ✅ Pass | ✅ Detected | ✅ Active | Ready |
| fleet-spec | ✅ | ✅ Pass | ✅ Detected | ✅ Active | Ready |
| fleet-toolbox | ✅ | ✅ Pass | ✅ Detected | ✅ Active | Ready |

## Evidence

- All six repos updated with import-linter>=2.0.0,<3.0.0
- uv.lock regenerated and committed
- Legacy configs validated or rewritten
- Explicit isolation contracts added
- Deliberate test violations caught and reverted
- CI workflows activated
- Mainline passes all checks

## Success Criteria Met

✅ Tool installed and pinned  
✅ All configs validated  
✅ Violations detected  
✅ CI workflows running  
✅ Mainline clean  

## Next Phase

Increment 2B: Stale dependency cleanup + CI gate promotion
```

---

## Checklist

Run through this checklist to confirm completion:

- [ ] Phase 1: import-linter version selected and pinned
- [ ] Phase 1: Dependency added to all six repos
- [ ] Phase 1: Installation verified (uv run python -m importlinter works)
- [ ] Phase 2: Legacy configs validated or rewritten
- [ ] Phase 3: Isolation contracts created for fleet-coordination and fleet-spec
- [ ] Phase 3: New configs validated
- [ ] Phase 4: `just check-imports` added to all justfiles
- [ ] Phase 4: Local checks pass
- [ ] Phase 5: Test violations injected and detected in Layer 0
- [ ] Phase 5: Test violations injected and detected in isolated repo
- [ ] Phase 5: Violations reverted; mainline clean
- [ ] Phase 6: CI workflows added/updated
- [ ] Phase 6: CI catches violations on test branches
- [ ] Phase 7: Mainline validation successful
- [ ] Phase 7: Evidence documented in governance/evidence/increment-2a/
- [ ] All changes committed to main

---

## Time Estimate Breakdown

| Phase | Task | Time |
|---|---|---|
| 1 | Version selection + installation (all repos) | 30 min |
| 2 | Legacy config validation/rewrite | 45 min |
| 3 | Isolation contracts + validation | 30 min |
| 4 | Justfile integration | 30 min |
| 5 | Test violations + detection | 30 min |
| 6 | CI workflows | 30 min |
| 7 | Mainline validation + evidence | 15 min |
| **Total** | | **3 hours** |

---

## Rollback Plan

If import-linter causes unexpected issues:

1. Revert dependency additions from all pyproject.toml files
2. Regenerate uv.lock files
3. Remove justfile `check-imports` commands
4. Remove/revert CI workflow changes
5. Document the issue for Checkpoint 4 (tool evaluation)

---

## Next: Increment 2B (After 2A Success)

Once 2A is complete and validated:

1. Remove stale dependencies from fleet-toolbox (clean-environment proof required)
2. Regenerate fleet-toolbox/uv.lock
3. Promote import-linter CI checks to required/blocking
4. Update policy to v0.2.0 reflecting zero stale dependencies
5. Document completion in evidence archive

---

## Notes

- Keep import-linter as a development/testing tool, not a production dependency
- Version must be consistent across all repos (use same major.minor)
- Test violations are temporary — revert immediately after detection is proven
- CI workflows can stay report-only initially; promote to blocking after 1–2 clean cycles
- Update fleet-architecture.yaml status from "planned" to "active" once this phase completes

---

**Ready to Execute?** ✅  
Start with Phase 1. Proceed sequentially. Commit results after each phase completes.
