#!/usr/bin/env bash
set -euo pipefail

# Configure branch protection for Fleet Architecture v1.0
# Idempotent: safe to re-run; overwrites with desired state
# Requires: GitHub CLI (gh) with admin access to target repositories

: "${GH_OWNER:?Set GH_OWNER to your GitHub user or org (e.g., export GH_OWNER=baseline0)}"

BRANCH="main"
REQUIRED_CHECK="test"

# The six repositories covered by Fleet Architecture v1.0
REPOS=(
  "fleet-base"
  "fleet-agents"
  "fleet-toolbox"
  "fleet-ops"
  "fleet-coordination"
  "fleet-spec"
)

echo "=== Configuring Branch Protection: ${GH_OWNER} ==="
echo "Branch: ${BRANCH}"
echo "Required check: ${REQUIRED_CHECK}"
echo "Mode: Idempotent (safe to re-run)"
echo ""

# Build the GitHub API payload
payload="$(jq -n \
  --arg check "$REQUIRED_CHECK" \
  '{
    required_status_checks: {
      strict: true,
      contexts: [$check]
    },
    enforce_admins: true,
    required_pull_request_reviews: null,
    restrictions: null,
    required_linear_history: false,
    allow_force_pushes: false,
    allow_deletions: false,
    block_creations: false,
    required_conversation_resolution: false,
    lock_branch: false,
    allow_fork_syncing: false
  }'
)"

success_count=0
fail_count=0

for repo in "${REPOS[@]}"; do
  echo "📝 ${repo}..."

  if gh api \
    --method PUT \
    "repos/${GH_OWNER}/${repo}/branches/${BRANCH}/protection" \
    --input - <<<"${payload}" >/dev/null 2>&1; then

    # Verify the configuration was applied
    echo -n "  ✅ Applied. Verifying... "
    if gh api \
      "repos/${GH_OWNER}/${repo}/branches/${BRANCH}/protection/required_status_checks" \
      --jq '.contexts[]' 2>/dev/null | grep -q "^${REQUIRED_CHECK}$"; then
      echo "✅"
      ((success_count++))
    else
      echo "❌ (config applied but verification failed)"
      ((fail_count++))
    fi
  else
    echo "  ❌ Failed (check permissions and repo access)"
    ((fail_count++))
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: ${success_count}/${#REPOS[@]} repos configured"

if [ $fail_count -gt 0 ]; then
  echo "⚠️  ${fail_count} repo(s) failed. Check permissions and try again."
  exit 1
else
  echo "✅ All repositories configured successfully"
  echo ""
  echo "Next steps:"
  echo "1. Create a test PR in fleet-base with a boundary violation"
  echo "2. Verify that merge is blocked by the 'test' check"
  echo "3. Close the PR without merging"
  echo "4. Run: ./audit_branch_protection.sh (to save evidence)"
  echo "5. Update policy state: merge_required: true"
  echo "6. Merge policy update to close v1.0"
  exit 0
fi
