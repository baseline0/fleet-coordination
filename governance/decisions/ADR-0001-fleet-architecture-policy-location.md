# ADR-0001: Fleet Architecture Policy Location

**Status:** Accepted  
**Decision Date:** 2026-09-23  
**Decider:** Mark Alexiuk  
**Reviewed By:** Architecture Review (wingman)

---

## Decision

The canonical fleet architecture policy is located at:

```
fleet-coordination/governance/fleet-architecture.yaml
```

This is the authoritative, versioned source of truth for cross-repository dependency rules, isolation invariants, and public API surfaces across the six fleet repositories.

---

## Why This Location

**Option B selected over:**
- **Option A (new `fleet-governance` repo):** Avoids introducing a 7th repository; minimizes polyrepo coordination overhead we are intentionally reducing.
- **Option C (fleet-base ownership):** Keeps foundational runtime infrastructure separate from governance policy; prevents accidental coupling of contracts to governance rules.
- **Option D (workspace-root directory):** Preserves a standalone, independently cloneable source of truth; enables CI to fetch the policy at a pinned revision.

**Why fleet-coordination specifically:**
- Already established as the "governance and decision support" layer.
- Existing governance artifacts (`governance-compliance-checker.md`) show precedent.
- Experimental status of fleet-coordination does not affect policy stability (see stability rules below).
- Allows future extraction to a dedicated `fleet-governance` repository without semantic or tooling disruption.

---

## Stability & Governance

### Policy Itself Is Stable

During the boundary-metadata migration (Increment 2), `fleet-coordination`'s v2 `.fleet/boundaries.yaml` will declare this policy as a **stable governance contract**:

```yaml
governance_artifact: fleet-architecture
policy_version: "1.0.0"
status: stable
stability_guarantee: "Policy schema and location are stable; policy content changes require ADR."
```

- Policy schema version changes require a new ADR and backward-compatibility analysis.
- New allowed dependencies require a lightweight ADR.
- Public-module surface changes require ADR + consumer migration plan.
- Invariant changes or removals require explicit stakeholder review.

### Coordination Experimentation Continues Independently

Coordination experiments in fleet-coordination do not affect policy:
- Policy is a data artifact, not a Python import surface.
- Policy has its own versioning (`policy_version: "X.Y.Z"`), independent of package version.
- Fleet validation must not import or depend on fleet-coordination's runtime code.

---

## Access Model

### Local Development

Policy is accessed via explicit file path argument with deterministic precedence:

```bash
# 1. Explicit command-line argument (required in CI, preferred always)
just check-fleet-architecture \
  --policy /home/mark/projects/fleet-coordination/governance/fleet-architecture.yaml \
  --report-only

# 2. Environment variable (local development only)
export FLEET_POLICY_PATH=/home/mark/projects/fleet-coordination/governance/fleet-architecture.yaml
just check-fleet-architecture --report-only

# 3. No implicit filesystem default; fail with clear error if neither is provided
```

Precedence order:
1. `--policy PATH` (command-line, overrides all)
2. `FLEET_POLICY_PATH` (environment, for local convenience)
3. Failure (no implicit defaults)

### CI Integration

CI must pin fleet-coordination revision before fetching policy:

```bash
# CI checkout
git clone https://github.com/user/fleet-coordination /tmp/fc
cd /tmp/fc && git checkout <pinned-sha>

# Policy is then at: /tmp/fc/governance/fleet-architecture.yaml

# Validator called with explicit path
just check-fleet-architecture --policy /tmp/fc/governance/fleet-architecture.yaml
```

Validation run must record:
- `fleet-coordination` Git SHA
- Policy file path
- SHA-256 of policy content
- Policy schema version
- Validator version/SHA
- Python and uv versions
- All target repository SHAs

---

## Validation Modes

### Per-Repository Mode (Local, CI Unit Tests)

Individual repositories validate imports and dependencies *without* checking out the central policy:

```bash
cd fleet-ops
just test              # Unit tests
just lint              # Linting
just check-imports     # Per-repo import-linter only
```

This minimizes dependencies for fast, local feedback.

### Fleet-Integrity Mode (Integration, CI Governance Gate)

Full fleet validation requires all six repositories + central policy:

```bash
# Bootstrap workspace (all six repos cloned)
~/projects/fleet-*/                          # repos at known revisions
~/projects/fleet-coordination/governance/    # canonical policy

just check-fleet-architecture \
  --policy ~/projects/fleet-coordination/governance/fleet-architecture.yaml \
  --report-only
```

This is a CI gate separate from per-repo tests.

---

## Extraction Readiness

The policy directory is designed for future migration to a dedicated governance repository without semantic or tooling changes.

### Self-Containment Rules

- ❌ Policy file must NOT import or depend on `fleet_coordination` Python code.
- ❌ Validator must NOT be embedded in `fleet-coordination` runtime and must NOT be importable by fleet packages.
- ✅ Validator will initially be a standalone fleet-integrity tool. Its permanent location will be decided after policy schema, CLI, and report format stabilize.
- ✅ Policy data format must be stable and self-documenting (JSON schema provided).

### Migration Path

When/if a dedicated `fleet-governance` repository is created:

```bash
# Before (no semantic changes)
fleet-coordination/governance/fleet-architecture.yaml

# After (pure Git/path move to repository root)
fleet-governance/fleet-architecture.yaml
```

No changes to:
- YAML schema or structure
- Policy content or semantics
- Validator interface or output format
- CI invocation or pinning strategy

### Extraction Trigger

Reconsider a dedicated repository if:
- Policy is consumed by external systems (outside the 6-repo fleet).
- Policy release cycle becomes independent of fleet-coordination.
- Coordination experiments destabilize governance delivery.
- Policy grows to require separate access controls.

Until then, keeping policy in fleet-coordination minimizes overhead.

---

## Non-Goals

This decision explicitly does **not**:

- Create a new Python import surface (`fleet_coordination.governance` is not importable).
- Establish a monorepo or consolidate repositories.
- Require import-code generation from policy (generation is optional, validation-first).
- Couple fleet-ops runtime or any consumer to policy data at runtime.
- Dictate a tool (e.g., Tach vs importlinter); policy is tool-agnostic.

---

## Review Cadence

- **Policy schema:** Review annually or when breaking changes are proposed.
- **Policy content:** Review per ADR for significant changes; per PR for corrections.
- **Location and access model:** Review if extraction or consolidation is triggered.

---

## References

- [Checkpoint-based governance plan](../README.md)
- [Fleet architecture schema v2.0](../fleet-architecture.yaml) (to be created)
- [Six-repository inventory](../INVENTORY.md) (Checkpoint 2)
