# Fleet Architecture v1.0: Closure Status & Path Forward

**Date:** 2026-09-23  
**Status:** Implementation complete; branch protection configuration pending  
**Blocker:** Private repositories require GitHub Pro/Team/Enterprise for branch protection

---

## ✅ Implementation Complete

### Enforcement Tooling
- ✅ import-linter 2.15 active in five Python repositories + fleet-coordination
- ✅ `just check-imports` available locally in all repos
- ✅ CI workflows (test.yml) execute boundary checks before tests
- ✅ Violations block test execution (but not merge yet—that requires branch protection)

### Policy & Validation
- ✅ fleet-architecture.yaml v1.0.0 locked
- ✅ Fleet-wide validation: 0 discrepancies (policy = declared = observed)
- ✅ ADR-0002 documents fleet-toolbox→fleet-agents edge with review trigger
- ✅ ADR-0003 documents v1.0.0 promotion evidence

### Infrastructure
- ✅ Workflows standardized (redundant fleet-test.yml removed)
- ✅ fleet-coordination static isolation check automated (governance.yml)
- ✅ Stale dependencies removed from fleet-toolbox
- ✅ Idempotent configuration scripts ready (UI and CLI/API paths)

---

## ⏳ Pending: Branch Protection Configuration

### The Constraint

**Branch protection is available for:**
- ✅ **Public repositories** on any GitHub plan (Free, Pro, Team, Enterprise)
- ✅ **Private repositories** on GitHub Pro (personal), Team, or Enterprise
- ❌ **Private repositories** on GitHub Free

This constraint applies regardless of configuration method (UI or API). The GitHub Free plan simply does not support branch protection for private repositories, period.

**Status:** Your fleet repositories are private, and the account is on GitHub Free. Branch protection requires upgrading to GitHub Pro (personal) or GitHub Team/Enterprise (organization).

### Path Forward

**Three options:**

1. **Upgrade GitHub Account**
   - Personal: Upgrade to GitHub Pro ($4/month)
   - Organization: Upgrade to GitHub Team ($21/month/seat)
   - Then configure protection via UI or automation scripts

2. **Make Repositories Public**
   - Branch protection becomes available immediately on GitHub Free
   - Suitable if the fleet repos can be open-source
   - Then configure protection via UI or automation scripts

3. **Configure in Future**
   - Complete v1.0 closure when plan/visibility changes
   - All technical work is done; branch protection is the final gate
   - Can proceed with operating model (validation, ADR requirements) without the merge gate

---

## Ready-to-Use Assets

| Asset | Purpose | Status |
|---|---|---|
| `scripts/configure_branch_protection.sh` | Idempotent API configuration | ✅ Ready (blocked by plan) |
| `scripts/audit_branch_protection.sh` | Read-only state audit | ✅ Ready (blocked by plan) |
| `BRANCH-PROTECTION-SETUP.md` | Manual UI configuration | ✅ Ready (blocked by visibility) |
| `V1-CLOSURE-CHECKLIST.md` | Final tasks and verification | ✅ Ready |
| `SUMMARY.md` | Architecture reference | ✅ Ready |

---

## If Branch Protection Cannot Be Configured Now

**Operating model remains valid without the automated merge gate:**

- Policy v1.0.0 is locked and validated
- Enforcement tooling is active (tests fail, CI blocks)
- Validation script (fleet_validation.py) is runnable
- ADR process is in place for new edges

**What's missing:**
- GitHub's automated merge blocker (requires plan upgrade or public repos)
- One-click enforcement; violating PRs would need manual review before merge

**Recommendation:** Proceed with operating model; defer the GitHub branch-protection step until plan/visibility allows. The v1.0 engineering work is complete and durable.

---

## Exact Closure Criterion (When Plan/Visibility Changes)

All six repositories' `main` branches have protection enabled requiring the `test` status check:

1. ✅ Configure: `scripts/configure_branch_protection.sh` (via API) or `BRANCH-PROTECTION-SETUP.md` (via UI)
2. ✅ Verify: One test PR in fleet-base with boundary violation → merge blocked → PR closed without merging
3. ✅ Record: `audit_branch_protection.sh` output as evidence
4. ✅ Update policy: `merge_required: true`
5. ✅ Merge final policy update

Then v1.0 is formally closed with merge-blocking enforcement active.

---

## Summary

**Technical v1.0 is complete.** The final governance gate (GitHub branch protection) requires one of:
- GitHub Pro personal plan upgrade
- GitHub Team/Enterprise plan upgrade
- Make repositories public

Choose a path forward; then closure takes ~10 minutes (UI) or ~1 minute (scripts).
