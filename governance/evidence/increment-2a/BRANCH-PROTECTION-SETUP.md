# Branch Protection Setup: Closing v1.0

**Goal:** Make architectural boundary violations unmergeable by requiring the `test` status check.

**Time:** ~10 minutes for 6 repos  
**Prerequisite:** Admin access to each repo

---

## Quick Reference

For each repo, go to **Settings → Branches → Add rule**:

```
Branch name pattern: main
✅ Require pull request reviews before merging: 1 approval
✅ Require status checks to pass: test
✅ Require branches to be up to date before merging
✅ Include administrators
```

---

## Per-Repository Instructions

### Step 1: fleet-base

1. Go to https://github.com/baseline0/fleet-base/settings/branches
2. Click **"Add rule"**
3. Branch name pattern: `main`
4. Check:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Search for: `test` (click to select)
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators
5. **Save changes**

### Step 2–6: Repeat for other 5 repos

- https://github.com/baseline0/fleet-agents/settings/branches
- https://github.com/baseline0/fleet-toolbox/settings/branches
- https://github.com/baseline0/fleet-ops/settings/branches
- https://github.com/baseline0/fleet-spec/settings/branches
- https://github.com/baseline0/fleet-coordination/settings/branches

**Same config for each:**
- Branch: `main`
- Required check: `test` (for Python repos) OR `governance` (for fleet-coordination)

---

## Verification: One Test PR (After All Repos Configured)

Once fleet-base is protected, create a test PR:

```bash
cd /home/mark/projects/fleet-base
git checkout -b test/boundary-violation
echo "from fleet_ops import x  # VIOLATES BOUNDARY" >> src/fleet_base/__init__.py
git add src/fleet_base/__init__.py
git commit -m "test: deliberate boundary violation (will be blocked)"
git push origin test/boundary-violation
```

Then on GitHub:
1. Create PR from `test/boundary-violation` to `main`
2. **Expected:** CI runs, `test` job fails on boundary check
3. **Expected:** Merge button is **disabled** with message "Required status check did not pass: test"
4. **Close PR without merging** (don't approve or merge)

This confirms the gate works. Then replicate the same branch-protection config to other 5 repos—no additional verification needed, config is identical.

---

## After Protection is Verified

Once all 6 repos have protection configured and verified (test PR confirms the block):

```bash
cd /home/mark/projects/fleet-coordination
git checkout -b feat/v1-closure-update-policy
# Edit governance/fleet-architecture.yaml
# Change: merge_required: false → merge_required: true
git add governance/fleet-architecture.yaml
git commit -m "chore: record merge-protection activation (v1.0 closure)"
git push origin feat/v1-closure-update-policy
```

Then create a PR, merge it. **Architecture Enforcement v1.0 is now closed.**

---

## Checklist

- [ ] Configure fleet-base (Settings → Branches → Add rule)
- [ ] Configure fleet-agents
- [ ] Configure fleet-toolbox
- [ ] Configure fleet-ops
- [ ] Configure fleet-spec
- [ ] Configure fleet-coordination
- [ ] Create test PR in fleet-base, confirm merge is blocked
- [ ] Close test PR without merging
- [ ] Update policy state: `merge_required: true`
- [ ] Merge policy update
- **v1.0 Closed** ✅

---

## Success Criterion

**Merge blocked automatically when `test` job fails** (no manual override needed for ordinary users).

If that works, v1.0 enforcement is complete and active.
