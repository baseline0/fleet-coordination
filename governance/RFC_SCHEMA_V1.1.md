# RFC: Schema v1.1 — Dependency Tracking & Ownership

**Status:** Proposal (Open for Feedback)  
**Target Release:** Q4 2026 (Nov 1)  
**Migration:** Backward-compatible (optional fields)

---

## Overview

Extend governance schema v1.0 with three optional features:
1. **Dependency tracking** — Explicit repo dependencies
2. **Quality gates** — Required test coverage, checks
3. **Code ownership** — Module-level responsibility

---

## Motivation

**Current gap:** v1.0 captures *what* a repo is. v1.1 adds *how it relates* to other repos.

**Use cases:**
- Service discovery ("what depends on fleet-ops?")
- Dependency validation ("breaking changes require review of downstream repos")
- Ownership clarity ("who owns the auth module?")

---

## Proposed Schema

### `boundaries.yaml` (New Optional Fields)

```yaml
schema_version: "1.1"
name: agent-tooling
# ... existing v1.0 fields ...

# NEW: Track dependencies
dependencies:
  - repo: fleet-base
    version: ">=1.0.0"
    reason: "GovernanceSchemaValidator, EnvSpec"
  - repo: rope-mcp
    version: ">=2.0.0"
    reason: "Code refactoring backend"

# NEW: Quality gates
quality_gates:
  min_test_coverage: 0.80
  required_checks:
    - lint
    - type-check
    - test
  max_response_time_ms: 5000

# NEW: Code ownership
owners:
  - name: "Architecture Team"
    email: "arch@example.com"
    modules:
      - "src/core"
      - "src/orchestrator"
  - name: "Backend Team"
    email: "backend@example.com"
    modules:
      - "src/api"
```

---

## Migration Path

### Adoption Timeline
- **Week 1:** v1.0 still primary (backward compatible)
- **Weeks 2-4:** Encourage adoption of optional fields
- **Week 5+:** Dashboard shows adoption % per field

### Non-Breaking
- All fields **optional**
- v1.0 files remain **valid**
- Validator accepts v1.0 or v1.1
- Gradual adoption encouraged, not forced

### Validator Behavior
```python
# v1.0 file: PASS ✅
schema_version: "1.0"
name: repo

# v1.1 file: PASS ✅
schema_version: "1.1"
name: repo
dependencies: [...]

# Mixed (v1.0 with v1.1 fields): WARN ⚠️
schema_version: "1.0"  # Should be 1.1
dependencies: [...]   # Field won't be validated
```

---

## Implementation

### Validator Changes
```python
# In fleet_base/governance_schema.py
if schema_version == "1.1":
    validate_dependencies(data)
    validate_quality_gates(data)
    validate_owners(data)
elif schema_version == "1.0":
    # Existing v1.0 validation
    pass
```

### Checker Script Updates
```python
# In check_fleet_governance.py
--report-missing-deps    # List repos without dependency tracking
--report-quality-gates   # Repos without quality gates
--report-owners          # Repos without code ownership
```

---

## Benefits

| Feature | Benefit |
|---------|---------|
| **Dependencies** | Prevents breaking changes, enables service discovery |
| **Quality Gates** | Codifies standards, enables compliance reporting |
| **Ownership** | Clarifies responsibility, enables incident response |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Optional fields ignored | Make adoption recommended (not required) |
| Stale dependency info | Quarterly validation + CI checks |
| Ownership conflicts | RFC/vote process before assignment |

---

## Feedback Questions

1. **Should we track version ranges or commits?**
   - Proposal: Semantic versions (>=1.0.0, <2.0.0)
   - Alternative: Git SHAs for strict pinning

2. **Should quality gates be enforced in CI?**
   - Proposal: No (v1.1 is informational)
   - Alternative: Fail builds if gates not met

3. **Should owners be synced to GitHub CODEOWNERS?**
   - Proposal: Manual sync (future automation)
   - Alternative: Auto-sync via CI job

---

## Timeline

| Date | Action |
|------|--------|
| 2026-09-28 | RFC open for feedback (1 week) |
| 2026-10-05 | Community review closes |
| 2026-10-15 | Governance council approves |
| 2026-10-20 | Implementation starts |
| 2026-11-01 | Release candidate (beta) |
| 2026-11-15 | GA release (schema v1.1) |

---

## How to Provide Feedback

1. **Comment here:** Reply with questions/concerns
2. **Slack:** #governance channel (tag @governance-council)
3. **Vote:** Upvote/downvote features you care about most

---

**Next:** Collect feedback, finalize spec, begin implementation.
