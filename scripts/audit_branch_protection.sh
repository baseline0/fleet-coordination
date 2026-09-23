#!/usr/bin/env bash
set -u

# Audit current branch protection state across the six protected repositories
# Run before applying configuration to see what's already in place

: "${GH_OWNER:?Set GH_OWNER to your GitHub user or org (e.g., export GH_OWNER=baseline0)}"

BRANCH="main"

# The six repositories covered by Fleet Architecture v1.0
REPOS=(
  "fleet-base"
  "fleet-agents"
  "fleet-toolbox"
  "fleet-ops"
  "fleet-coordination"
  "fleet-spec"
)

echo "=== Branch Protection Audit: ${GH_OWNER} ==="
echo "Branch: ${BRANCH}"
echo ""

for repo in "${REPOS[@]}"; do
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📁 ${GH_OWNER}/${repo}"
  echo ""

  if gh api "repos/${GH_OWNER}/${repo}/branches/${BRANCH}/protection" \
    --jq '{
      required_status_checks: .required_status_checks.contexts,
      strict: .required_status_checks.strict,
      enforce_admins: .enforce_admins.enabled,
      force_pushes_allowed: .allow_force_pushes.enabled,
      deletions_allowed: .allow_deletions.enabled,
      allow_fork_syncing: .allow_fork_syncing.enabled
    }' 2>/dev/null; then
    echo ""
  else
    echo "❌ No branch protection configured (or insufficient permissions)"
    echo ""
  fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Audit complete"
