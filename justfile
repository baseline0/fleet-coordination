import "../fleet-agents/just/shared.just"

@default:
  @just --list

# Fleet governance compliance — check all repos
check-governance:
  uv run python scripts/check_fleet_governance.py

# Check specific repo (e.g., just check-governance-repo flashcards)
check-governance-repo REPO:
  uv run python scripts/check_fleet_governance.py --repo {{ REPO }}

# Check with strict mode (warnings = failures)
check-governance-strict:
  uv run python scripts/check_fleet_governance.py --strict

# Export governance status as JSON
check-governance-json:
  uv run python scripts/check_fleet_governance.py --json

# ============================================================================
# GOVERNANCE CADENCE: Weekly, Monthly, Quarterly Reviews
# ============================================================================

# Weekly governance review: what changed this week?
governance-review-weekly:
  #!/usr/bin/env bash
  set -euo pipefail
  REPORT_DIR="reports/governance/weekly"
  mkdir -p "$REPORT_DIR"
  WEEK=$(date +%Y-W%V)
  REPORT="$REPORT_DIR/$WEEK.md"

  {
    echo "# Weekly Governance Review — Week $WEEK"
    echo ""
    echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    echo "## Summary"
    echo ""
    echo "Checking governance across fleet..."
    echo ""

    # Run compliance check
    echo "## Compliance Status"
    echo ""
    uv run python scripts/check_fleet_governance.py 2>&1 | grep -E "Compliant|Non-Compliant|COMPLIANT|NON-COMPLIANT" || echo "No issues detected"
    echo ""

    # Steward audit if available
    echo "## Layer Boundary Audit (LAYER-001)"
    echo ""
    if [ -d "../fleet-ops" ]; then
      echo "Running: \`just steward-audit\` (sample repos)"
      echo ""
      echo '```'
      (cd ../fleet-ops && just steward-audit 2>&1 | head -20) || echo "No LAYER-001 audit available"
      echo '```'
    fi
    echo ""

    echo "## Actions Required"
    echo ""
    echo "- [ ] Review any new governance warnings above"
    echo "- [ ] Check fleet-manifest.yaml is up-to-date"
    echo "- [ ] Note any new repos or ownership changes"

  } > "$REPORT"

  echo "✅ Weekly review saved to: $REPORT"
  cat "$REPORT"

# Monthly governance report: aggregate status, fleet-wide summary
governance-report-monthly:
  #!/usr/bin/env bash
  set -euo pipefail
  REPORT_DIR="reports/governance/monthly"
  mkdir -p "$REPORT_DIR"
  MONTH=$(date +%Y-%m)
  REPORT="$REPORT_DIR/$MONTH.md"

  {
    echo "# Monthly Governance Report — $MONTH"
    echo ""
    echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    echo "## Fleet-Wide Summary"
    echo ""

    # Count repos by status
    echo "### Compliance Status"
    echo ""
    uv run python scripts/check_fleet_governance.py --json 2>&1 | grep -E "Compliant|errors|warnings" || echo "Run check-governance for status"
    echo ""

    echo "### Observed Patterns"
    echo ""
    echo "- Number of repos: $(cd .. && find . -maxdepth 2 -name .fleet -type d | wc -l) active governance records"
    echo "- Review: Check for tightly coupled repos, ownership gaps, deprecated repos"
    echo ""

    echo "## Structural Notes"
    echo ""
    echo "- Review fleet-manifest.yaml for emerging coupling patterns"
    echo "- Any repos that should be merged, split, or deprecated?"
    echo "- Owner assignments current and clear?"
    echo ""

    echo "## Next Steps"
    echo ""
    echo "- [ ] Aggregate prior weekly reviews"
    echo "- [ ] Update fleet-inventory if ownership changed"
    echo "- [ ] Note any structural concerns for quarterly review"

  } > "$REPORT"

  echo "✅ Monthly report saved to: $REPORT"
  cat "$REPORT"

# Quarterly governance checkpoint: ownership, boundaries, criticality review
governance-checkpoint-quarterly:
  #!/usr/bin/env bash
  set -euo pipefail
  REPORT_DIR="reports/governance/quarterly"
  mkdir -p "$REPORT_DIR"
  MONTH=$(date +%m | sed 's/^0//')  # Remove leading zero
  QUARTER=$(date +%Y-Q$(( (MONTH - 1) / 3 + 1 )))
  REPORT="$REPORT_DIR/$QUARTER.md"

  {
    echo "# Quarterly Governance Checkpoint — $QUARTER"
    echo ""
    echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    echo "## Governance Health Assessment"
    echo ""

    echo "### Compliance & Boundaries"
    echo ""
    uv run python scripts/check_fleet_governance.py 2>&1 | tail -10 || echo "Run check-governance for full status"
    echo ""

    echo "### Ownership Review"
    echo ""
    echo "- [ ] Confirm owner assignments in fleet-manifest.yaml still accurate"
    echo "- [ ] Any repos without clear ownership or backup owner?"
    echo "- [ ] Any teams that own >50% of repos? (concentration risk)"
    echo ""

    echo "### Boundary Assessment"
    echo ""
    echo "- [ ] Layer violations or attempted L2→L1 imports? (indicates boundary pressure)"
    echo "- [ ] Tightly coupled repos? Consider merge/shared infrastructure."
    echo "- [ ] Under-coupled repos? Are they truly independent or just orphaned?"
    echo ""

    echo "### Criticality Tiers"
    echo ""
    echo "- [ ] Core tier repos have <2h incident response time? (verify SLO alignment)"
    echo "- [ ] Supporting tier: quarterly deprecation review"
    echo "- [ ] Experimental: deprecate or graduate to supporting tier?"
    echo ""

    echo "## Recommendations"
    echo ""
    echo "- [ ] Revisit polyrepo / monorepo boundaries based on coupling signals"
    echo "- [ ] Any repos that should change criticality tier?"
    echo "- [ ] Opportunities for shared infrastructure (stdlib, test fixtures, CI patterns)?"
    echo ""

    echo "## Follow-Up Actions"
    echo ""
    echo "Record any decisions and revisit in the next quarterly checkpoint"

  } > "$REPORT"

  echo "✅ Quarterly checkpoint saved to: $REPORT"
  cat "$REPORT"
