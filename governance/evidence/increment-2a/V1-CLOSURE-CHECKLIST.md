# Architecture Enforcement v1.0 Closure Checklist

**Status:** Ready for merge-protection configuration  
**Date:** 2026-09-23  
**Policy Version:** 1.0.0 (locked)

---

## What's Done

✅ **Enforcement tooling active**
- import-linter 2.15 installed and tested in all 5 Python repos
- `just check-imports` available locally
- CI workflows execute boundary checks on every PR/push
- fleet-coordination static isolation check automated (scripts/check_fleet_isolation.py)

✅ **Policy validated**
- v1.0.0 locked (fleet-architecture.yaml)
- Fleet-wide validation: 0 discrepancies (2026-09-23)
- ADR-0002 documents fleet-toolbox→fleet-agents edge
- ADR-0003 documents v1.0.0 promotion

✅ **Dependencies cleaned**
- Stale fleet-base removed from fleet-toolbox
- All declared deps match policy and observed imports

---

## What Remains: Configure Merge Gates

### For each of 5 Python repositories:
- [ ] fleet-base
- [ ] fleet-agents
- [ ] fleet-toolbox
- [ ] fleet-ops
- [ ] fleet-spec

**Configuration (GitHub Settings → Branches → main):**

1. **Create/Edit Branch Protection Rule**
   - Require pull request reviews before merging: ✓ (any number)
   - Require status checks to pass before merging: ✓
     - **Search for and require:** `test`
     - (This is the exact check name from the workflow job `jobs.test`)
   - Require branches to be up to date before merging: ✓
   - Include administrators: ✓ (uncheck if emergency bypass needed)
   - Restrict who can push to matching branches: ✓ (optional)
   - Dismiss stale PR approvals when new commits are pushed: ✓ (optional)

**The critical line:** Require status check `test` (which runs `just check-imports` as a step).

### For fleet-coordination

- [ ] Configure same branch protection rule
- [ ] Required check: `governance` (the fleet isolation CI job)
- [ ] Same PR + up-to-date + admin settings as Python repos

---

## Verification: One Test PR

After configuring fleet-base as a pilot:

1. **Create a PR** in fleet-base with a deliberate violation:
   ```python
   # Add to src/fleet_base/__init__.py (temporarily)
   from fleet_ops import something  # Should be forbidden
   ```

2. **Observe in GitHub:**
   - PR created
   - CI runs, `test` job executes `just check-imports`
   - Boundary check fails (output shows violation)
   - Merge button is **disabled** (cannot merge without override)

3. **Close the PR without merging**

4. **Record proof:**
   - Repo: fleet-base
   - PR number: (your PR #)
   - Check name: `test`
   - Date: 2026-09-23
   - Merge blocked: YES

5. **Replicate configuration** to fleet-agents, fleet-toolbox, fleet-ops, fleet-spec (same check name `test`)

---

## After Merge Protection Verified

1. Update policy state:
   ```yaml
   enforcement:
     repository_boundary_checks:
       merge_required: true  # ← was: false
   ```

2. Commit: "chore: record merge-protection activation"

3. **Close v1.0 formally:** Architecture Enforcement v1.0 is now complete.
   - Policy: v1.0.0 (locked)
   - Tooling: active (local + CI)
   - Gates: merge-blocking (GitHub branch protection)

---

## Operating v1.0 (Next 30–60 Days)

- Run `fleet_validation.py` on releases and after cross-repo changes (manual, not cron)
- Require ADR for any new cross-repo dependency edge
- Require clean validation report before releases
- Do NOT expand scope (defer public surface, Tach, SLA enforcement)
- Do NOT automate weekly validation until you have: owner, alert destination, response plan

---

## One-line Success Criterion

**Violation in a PR → CI fails → Merge blocked (automatically, by GitHub).**

If that works for the test PR, v1.0 is complete and merge-blocking enforcement is active.
