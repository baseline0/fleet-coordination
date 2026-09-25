# P1-002 Migration Inventory: Legacy Identifier Mapping

**Date:** 2026-09-25  
**Scope:** Canonical naming for fleet-coordination governance  
**Status:** Inventory phase (no replacements authorized yet)

---

## Summary

| Legacy ID | Canonical | Active References | Role Classification | Decision Required |
|-----------|-----------|-------------------|---------------------|-------------------|
| agent-tooling | fleet-agents | 50 | Mixed (repo ID + component ref) | YES* |
| rope-mcp | mcp-rope | 38 | Mixed (provider ID + repo ref) | YES* |
| vscode-workspace-mcp | mcp-vscode | 32 | Mixed (provider ID + repo ref) | NO |

**\* Decision required:** `agent-tooling` and `rope-mcp` appear as both repository identifiers AND logical component/provider names. Confirm they should all map to canonical repo names.

---

## AGENT-TOOLING → FLEET-AGENTS

### Active Governance Files (50 occurrences)

**fleet.yaml (9 occurrences)**
- Line 18: `fleet_scope.core` list → **REPO_IDENTIFIER** → fleet-agents
- Line 180: `dependencies[agent-tooling]` → **COMPONENT_REFERENCE** → DECISION_REQUIRED
- Line 184: `agent-tooling:` (key) → **COMPONENT_REFERENCE** → DECISION_REQUIRED
- Line 186-187, 193-195, 200: dependency refs → **COMPONENT_REFERENCE** → DECISION_REQUIRED
- Line 237: `source: "../agent-tooling"` → **SOURCE_PATH** → DECISION_REQUIRED (path may be planned structure)

**README.md (2 occurrences)**
- Line 45: prose description → **USER_FACING_PROSE** → fleet-agents
- Line 92: test example → **EXAMPLE_CODE** → DECISION_REQUIRED

**governance/repository-lifecycle.yaml (6 occurrences)**
- Lines 11, 26, 49, 90, 103, 120: lifecycle refs → **GOVERNANCE_POLICY** → DECISION_REQUIRED

**governance/boundary-rules.yaml (13 occurrences)**
- Repository enforcement policies → **BOUNDARY_POLICY** → DECISION_REQUIRED (affects contract interpretation)

**governance/repository-manifest.yaml (7 occurrences)**
- Repository definitions, ownership → **MANIFEST_ENTRY** → DECISION_REQUIRED

**compatibility/compatibility-matrix.yaml (12 occurrences)**
- Compatibility definitions → **COMPAT_DEFINITION** → DECISION_REQUIRED

**.fleet/governance-compliance-checker.md (1 occurrence)**
- Documentation → **DOCUMENTATION** → fleet-agents

### Historical Files (PRESERVE AS-IS)

- `contracts/WEEK_2_DECISIONS_RECORD.md` (17) — ADR completed, dated 2026-09-20
- `contracts/CORRECTED_ARCHITECTURE_CONTRACTS.md` (11) — Contract specification, dated
- `contracts/contract-bundle.yaml` (7) — Contract artifacts
- `governance/boundary-remediations.yaml` (22) — Remediation history
- `docs/CONTRACT_VERIFICATION_0_1_0.md` (2) — Test specifications
- `governance/FINDING-dashboard-execution-decoupling-2026-09-24.md` (2) — Finding report
- `governance/RFC_SCHEMA_V1.1.md` (1) — Old RFC
- `governance/PILOT-CLOSURE-2026-09-23.md` (1) — Pilot closure record
- `TEST_HEALTH_BACKLOG.md` (1) — Backlog item

---

## ROPE-MCP AND VSCODE-WORKSPACE-MCP (Similar structure)

Same pattern as agent-tooling: mixed repository identifiers + provider/component names.

**rope-mcp → mcp-rope:** 38 active occurrences  
**vscode-workspace-mcp → mcp-vscode:** 32 active occurrences

---

## KEY DECISIONS REQUIRED

1. **Component vs. Repository:** Are `agent-tooling`, `rope-mcp`, `vscode-workspace-mcp` distinct logical components that happen to share names with repos, or are they pure repo references?
   - If distinct components → separate naming needed (e.g., `fleet-agents` repo owns `agent-tooling` component)
   - If pure repo refs → direct 1:1 replacement across all active files

2. **Source paths:** Does `../agent-tooling` in fleet.yaml represent an expected directory structure that differs from `../fleet-agents`?
   - If yes → may require symlink or path mapping, not simple name replacement

3. **Contracts and policies:** Boundary rules, lifecycle guidance, and compatibility matrices reference these names explicitly. Confirm they should adopt canonical repo names without affecting policy semantics.

---

## VALIDATION PLAN

Once decision made, validate with:

```bash
# Schema validation
fleet-schema-validator fleet.yaml

# Reference scan (ensure no broken refs)
rg "agent-tooling|rope-mcp|vscode-workspace-mcp" governance/ --type yaml

# Boundary rule validation
boundary-rules-validator governance/boundary-rules.yaml

# Active scan (should find 0 legacy IDs in enforced files)
rg "agent-tooling|rope-mcp|vscode-workspace-mcp" \
  --include="{fleet.yaml,governance/,compatibility/,trial/}" \
  --type yaml --type markdown
```

---

**Next:** Bring inventory back with answers to key decisions → authorize bounded migration slice.

