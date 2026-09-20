# fleet-coordination Boundaries

## Role
Layer 1 governance and trial management system for fleet-wide versioned policies, trial profiles, and contract definitions.

## Scope
- **What we own:** Trial governance, profile definitions, release state tracking, capability constraints, audit policy definitions
- **What we don't own:** Enforcement implementation (handled by fleet-ops and runtime systems)
- **What we provide:** Authoritative governance definitions, trial lifecycle management, versioned policy snapshots

## Key Boundaries

### 1. Trial Profile Authority
- fleet-coordination is the source of truth for trial profiles (`trial/trial-profile-*.yaml`)
- Defines capabilities, workspace allowlists, security constraints, resource limits
- fleet-ops and runtime systems enforce profiles; they don't modify them
- Changes require governance review and approval

### 2. Dependency Boundaries
- **Depends on:** fleet-base (for serialization contracts)
- **Does NOT depend on:** fleet-ops, agent-tooling, individual MCPs
- **Used by:** fleet-ops (for policy enforcement), runtime systems (for capability checks), trial management

### 3. Public API Surface
- `trial-profile-*.yaml` — Trial definitions (read-only by downstream systems)
- `governance/` — Versioned governance snapshots
- `contracts/` — Capability and authorization contracts (shared with fleet-base)

### 4. Restricted Operations
- No direct enforcement of policies (that's fleet-ops' responsibility)
- No dependency on implementation details of MCPs or applications
- All profile changes require commit history and audit trail (git-based governance)

## Lifecycle
- **Status:** Approved
- **Layer:** Layer 1 (governance)
- **Maintainer:** Trial lead / Architecture council
- **Last Updated:** 2026-09-20

