# fleet-push Safety Policy

## Policy

Fleet-wide push operations are gated by promotion status and scope. Dry-run operations are always safe and provide visibility into what would happen.

### Dry-Run (Always Safe)

```bash
just fleet-push --dry-run --scope core
```

**Allowed:** `promotion_eligible` can be true OR false  
**Output:** Shows selected/excluded repositories, dependency order, current/target refs, dirty worktrees, blocked conditions  
**Mutations:** ZERO (guaranteed read-only)
- No repository refs changed
- No branches created/deleted
- No manifests modified
- No remote state changed
- No commits pushed
**Gates:** None (informational only)  
**Invariant:** Dry-run is safe to run at any time, on any branch state

### Non-Dry-Run (Requires Promotion)

```bash
just fleet-push --apply --scope core
```

**Allowed:** Only if `promotion_eligible == true`  
**Blocked:** If `status == "candidate"` or `status == "invalid"`  

**Explicit Requirements (all required):**
- `--scope` flag must be explicit (core, managed, trial, or --repos list)
- `--apply` flag must be explicit (no defaults/inference)
- `promotion_eligible == true` (fresh fleet-check required)
- Dependency order resolved and acyclic
- Working tree clean or explicitly overridden with --force
- Remote identity verified (git remote matches manifest)
- Preview approved (reviewed --dry-run output)
- Partial-failure behavior defined

**Re-Validation Invariant:**
- Before any mutation, re-run fleet-check immediately
- Use fresh validation result, not cached
- If state changed since approval, refuse and require re-approval

**Default behavior:** Refuse everything unless explicit
- No `just fleet-push` (infers scope)
- No `just fleet-push --scope core` (missing --apply)
- No apply without fresh validation

**Mutation Safety:** All operations logged with audit trail  
**Idempotency:** Each run re-validates; safe to retry after partial failure

---

## Scope-Specific Policies

### Core Scope

```
promotion_eligible: true only when:
  - All 7 repositories reachable (paths exist)
  - All refs valid (40-char hex, git-verified)
  - All boundary files present
  - Contracts verified (pending → pass)
  - Trial profile enabled

When promotion_eligible == false:
  - Dry-run allowed → shows blockers
  - Apply blocked → lists missing gates
```

### Managed Scope

```
Not part of core release candidate. Refs not required for core verification.

promotion_eligible: false (currently)
  - Managed repos remain "registered" status
  - Health checks enabled
  - Evaluation enabled
  - No fleet-wide push until individually promoted
```

### Trial Scope

```
Separate from fleet manifest promotion. Governed by trial profile.

fleet-check --scope trial:
  - Validates trial participants (3 repos)
  - Checks trial profile requirements
  - Not gated by fleet promotion

fleet-push --scope trial:
  - Requires separate trial authorization
  - Not blocked by core candidate status
```

---

## Pre-Push Checklist

Before non-dry-run push, verify:

```text
[ ] Scope is explicit (--scope core, not ambiguous)
[ ] promotion_eligible == true in fleet-check output
[ ] Dependency graph is acyclic and documented
[ ] Working trees are clean (git status per repo)
[ ] Remote URLs verified (git remote -v)
[ ] Dry-run preview reviewed (fleet-push --dry-run --scope ...)
[ ] Partial-failure plan defined (which repos can fail independently)
[ ] Rollback procedure rehearsed
[ ] Audit trail enabled (all mutations logged)
```

---

## Blocked Conditions

Non-dry-run push is refused if:

1. **Promotion gates not met:**
   - promotion_eligible == false
   - fleet-check has errors or blocking warnings

2. **Scope not explicit:**
   - No --scope flag
   - Ambiguous repository selection

3. **Dependency order not resolved:**
   - Circular dependencies detected
   - Consumer pushed before provider

4. **Working tree policy not satisfied:**
   - Dirty worktrees without explicit --force
   - Uncommitted changes in selected repos

5. **Remote identity not verified:**
   - Mismatched remote URLs
   - Unresolved remote configuration

---

## Example Workflows

### Verify Core Readiness

```bash
# Check status (JSON for automation)
just fleet-check --scope core --json

# If promotion_eligible == true, core is ready for push
# If promotion_eligible == false, dry-run shows what's blocking
```

### Prepare for Push (Dry-Run First)

```bash
# Inspect what would happen
just fleet-push --dry-run --scope core

# Output includes:
#   - Selected repositories (7)
#   - Excluded repositories (7) and reasons
#   - Dependency order
#   - Current refs vs. target refs
#   - Any dirty worktrees
#   - Blocked conditions (if any)
```

### Execute Push (After Dry-Run Review)

```bash
# Only if promotion_eligible == true
just fleet-push --apply --scope core

# Mutation occurs:
#   - Per-repository commits pushed
#   - Audit trail recorded
#   - Partial failures reported
```

### Rollback After Failed Push

```bash
# If some repos succeeded and some failed:
just fleet-push --rollback --scope core
# (not yet implemented; documented for readiness)
```

---

## Implementation Status

- ✅ Dry-run visibility (informational)
- ✅ Scope requirements (core/managed/trial)
- ✅ promotion_eligible deterministic flag
- ⏳ Non-dry-run gate enforcement (TODO)
- ⏳ Dependency order validation (TODO)
- ⏳ Working tree policy (TODO)
- ⏳ Partial-failure rollback (TODO)

See `governance/TODOs.md` for implementation roadmap.

