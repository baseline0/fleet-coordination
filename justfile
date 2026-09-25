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
