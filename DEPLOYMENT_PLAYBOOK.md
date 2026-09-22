# Fleet Governance Deployment Playbook

**Target:** 7-day rollout to production  
**Goal:** Pre-commit + CI + Weekly reports live

---

## Day 1-2: Pre-commit Hook Rollout

### Phase A: Test Repos (3 repos)
Start with friendly/low-risk repos:
1. **flashcards** (data team, low churn)
2. **research** (documentation, low conflict)  
3. **toolboxes** (internal tool, controlled)

**For each repo:**
```bash
cd /path/to/repo
curl https://raw.githubusercontent.com/baseline0/fleet-base/main/.pre-commit-hooks.yaml >> .pre-commit-config.yaml
pip install pre-commit
pre-commit install
git commit -m "ci: add fleet governance pre-commit hook"
git push origin main
```

**Validate:**
- Run: `pre-commit run fleet-governance-validate --all-files`
- Expected: ✅ All .fleet/*.yaml pass
- Time: <2 seconds

### Phase B: Rollout to All 19 (if Phase A succeeds)
Repeat for remaining repos. Document any issues in `#governance` Slack.

**Success Criteria:**
- >80% repos have pre-commit installed
- Zero false positives
- No complaints in Slack

---

## Day 2-3: GitHub Actions

### Enable CI Workflow
```bash
cd fleet-coordination
# governance.yml already exists
git push origin main  # Triggers first run on main
```

**Monitor:**
- Visit: Actions tab → Governance Schema Validation
- Expected: ✅ First run passes
- If fails: Check logs, fix issues, commit fix

### Test with PR
```bash
cd fleet-coordination
git checkout -b test/governance
echo "test" >> .fleet/boundaries.yaml
git commit -am "test: trigger governance check"
git push origin test/governance
# Open PR → CI runs → Check results
```

---

## Day 4-5: Weekly Report

### Generate First Report
```bash
cd fleet-coordination
uv run python scripts/check_fleet_governance.py --json > /tmp/report.json
uv run python scripts/generate_weekly_report.py \
  --input /tmp/report.json \
  --output WEEKLY_REPORT_2026-09-28.md
```

### Publish
1. Copy report to `fleet-coordination/`
2. Update `GOVERNANCE_STATUS.md` with latest score
3. Post summary to `#governance` Slack

**Expected:**
```
Score: 100/100 ✅
Compliant: 19/19
Violations: 0
```

---

## Day 6-7: Schema v1.1 Proposal

### Create RFC
File: `fleet-coordination/governance/RFC_SCHEMA_V1.1.md`

**Propose:**
- Optional `dependencies:` field
- Optional `quality_gates:` field
- Optional `owners:` field

**Migration:**
- All fields optional (v1.0 remains valid)
- Gradual adoption over 4 weeks
- No breaking changes

---

## Rollback Plan (If Needed)

**Pre-commit breaks builds:**
```bash
# Remove hook from repo
grep -v fleet-governance .pre-commit-config.yaml > .pre-commit-config.yaml.tmp
mv .pre-commit-config.yaml.tmp .pre-commit-config.yaml
git commit -am "revert: remove governance hook (troubleshooting)"
```

**CI workflow fails:**
```bash
cd fleet-coordination
# Disable workflow temporarily
# .github/workflows/governance.yml → workflow_dispatch only (remove schedule/PR triggers)
```

---

## Success Metrics

| Day | Metric | Target | Status |
|-----|--------|--------|--------|
| 2 | Pre-commit on 3 test repos | ✅ | Monitor |
| 3 | CI first run | ✅ Pass | Monitor |
| 5 | Weekly report generated | ✅ 100/100 | Monitor |
| 7 | v1.1 RFC circulated | ✅ Posted | Monitor |

---

## Slack Announcements

**Day 1:**
```
🚀 Starting fleet governance deployment (7-day rollout)

Today: Pre-commit hook rolling out to 3 test repos
This week: Full deployment of CI + weekly reports

Questions? #governance channel
```

**Day 5:**
```
✅ Weekly governance report is live!

📊 Score: 100/100
✅ Compliant: 19/19 repos

Full report: WEEKLY_REPORT_2026-09-28.md
```

**Day 7:**
```
📝 Schema v1.1 RFC now open for feedback

Proposed additions:
- dependencies tracking
- quality gates
- code ownership

Vote: governance/RFC_SCHEMA_V1.1.md
```

---

**Next:** Execute Day 1-2, monitor, report back.
