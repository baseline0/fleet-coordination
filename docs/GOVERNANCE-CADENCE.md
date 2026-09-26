# Fleet Governance Cadence

**Status:** Production-ready | **Version:** 1.0 | **Updated:** 2026-09-26

Operating rhythm for 20–40 repository fleet: weekly compliance checks, monthly fleet-wide summary, quarterly strategic review.

---

## Quick Start

```bash
# Weekly: Monday morning (5 min)
just governance-review-weekly

# Monthly: End of month (5 min)
just governance-report-monthly

# Quarterly: End of quarter (5 min)
just governance-checkpoint-quarterly
```

Reports are saved to `reports/governance/{weekly,monthly,quarterly}/` and printed to terminal.

---

## Three-Level Rhythm

### 🔵 Weekly: Compliance & Changes

**When:** Monday morning (or start of week)  
**Time:** ~5 minutes  
**Output:** `reports/governance/weekly/YYYY-Www.md`

**What it shows:**
- Governance compliance status (compliant vs. non-compliant repos)
- Layer boundary audit results (LAYER-001-NO-L2-IMPORTS)
- Checklist: review warnings, check fleet-manifest, note ownership changes

**How to use:**
- Skim the "Compliance Status" section
- If any repos show errors/warnings, investigate
- Verify fleet-manifest is up-to-date
- Update it if you've added/removed/ownership-changed any repos

**Adjust if:** You find yourself always skipping a section, or wishing for a new signal.

---

### 📊 Monthly: Fleet-Wide Health

**When:** End of month (any day)  
**Time:** ~5 minutes  
**Output:** `reports/governance/monthly/YYYY-MM.md`

**What it shows:**
- Compliance status aggregate
- Number of active `.fleet/` records
- Structural notes: coupling patterns, deprecation candidates
- Checklist: update fleet-inventory, note concerns for quarterly review

**How to use:**
- Review the "Compliance Status" snapshot
- Note any emerging patterns (e.g., "clusters of related repos")
- Flag candidates for merge/split/deprecation
- Update `fleet-ops/fleet-manifest.yaml` if ownership or lifecycle changed

**Integrate with:** Your monthly planning or team sync.

---

### 📈 Quarterly: Strategic Review

**When:** End of quarter  
**Time:** ~5 minutes (generates checklist; review discussion takes ~30 min)  
**Output:** `reports/governance/quarterly/YYYY-Qq.md`

**What it shows:**
- Governance compliance health
- Ownership review checklist
- Boundary assessment (layer violations, coupling)
- Criticality tier alignment
- Recommendations: merge/split/deprecate, restructure, SLO adjustments

**How to use:**
- Use the generated checklist as your review agenda
- Walk through each section with stakeholders
- Make explicit decisions:
  - Are boundaries still right?
  - Should any repos change tier or ownership?
  - Which repos are candidates for action (merge/deprecate/restructure)?
- Record decisions in a follow-up note for next quarter

**Output:** Short decision doc, not exhaustive audit. Record "here's what we're changing and why."

---

## Schema Reference

**Three required files (all repos):**
- `.fleet/config.yaml` — type, owner, language, standards, testing
- `.fleet/catalog-info.yaml` — Backstage metadata (dependencies, APIs, lifecycle)
- `.fleet/boundaries.yaml` — layer invariants and verification status

**Two recommended optional files:**
- `.fleet/health.yaml` — CI dashboard, coverage, alert channel, last health check
- `.fleet/release-strategy.yaml` — versioning, cadence, deployment target

See: `fleet-coordination/docs/.fleet-schema.md` for full details.

---

## Golden-Path Repos

**Template reference:** `fleet-base/.fleet/`  
- Minimal required structure  
- Well-formed config.yaml, catalog-info.yaml, boundaries.yaml

**Full example:** `fleet-ops/.fleet/`  
- Includes health.yaml and release-strategy.yaml
- Boundary audit trail and layer verification
- Use as reference for repos with complex deployments

---

## Debugging & Adjustments

### "Weekly report is too verbose / too terse"

Edit `justfile` recipe `governance-review-weekly`:
- Add/remove sections
- Change grep filters
- Adjust output format

Commit and iterate: `git commit -am "adjust(cadence): weekly output format"`

### "I need a signal that's not in the templates"

Small additions to weekly/monthly/quarterly recipes:
- Add new check (e.g., `just steward-audit` for multiple repos)
- Add new section (e.g., "Dependency updates" from Dependabot)
- Filter existing output differently

Example: Add runtime EOL check to quarterly:

```bash
echo "### Runtime End-of-Life"
echo "- [ ] Any repos running Python <3.11? (check pyproject.toml)"
echo "- [ ] Any repos on deprecated Node LTS? (check .node-version)"
```

### "The reports aren't being used"

1. Check: Are you actually running the recipes each period?
2. Ask: Which sections get skipped? (remove them)
3. Adjust: Make the report shorter or more targeted

After 2–4 weeks of real use, you'll know what's signal and what's noise.

---

## Future: Phase 2b (init-fleet-repo.sh)

Once manual `.fleet/` setup becomes repetitive (you onboard 2–3 new repos):

Build `scripts/init-fleet-repo.sh`:
- Copy template `.fleet/` files from fleet-base
- Prompt for repo name, owner, type, description
- Run `just check-governance-repo` as sanity check
- ~30 lines of shell script

Until then: copy fleet-base/.fleet/, edit the placeholders, done.

---

## Notes

- **Governance is read-only during stabilization.** These recipes report, not enforce. No automated fixes, no CI gates blocking merges.
- **Reports are immutable.** Store them in version control. Future analysis will benefit from the archive.
- **Adjust cadence if needed.** If you run weekly but it's always "all green," try biweekly. If you run monthly and miss signals, try weekly + monthly.
- **This is not a dashboard.** No live UI, no automations. Text files, human review. Scales to 40+ repos with minimal overhead.

---

## Commands Reference

```bash
# One-time compliance check
just check-governance                   # All repos
just check-governance-repo REPO         # Single repo
just check-governance-strict            # Fail on warnings
just check-governance-json              # JSON output

# Cadence (produces reports + terminal output)
just governance-review-weekly           # Monday: what changed?
just governance-report-monthly          # Month-end: health snapshot
just governance-checkpoint-quarterly    # Quarter-end: strategy review
```

---

**Questions?** See `fleet-coordination/docs/.fleet-schema.md` for schema details.
