# ADR-0002: fleet-toolbox Dependency on fleet-agents Public Contracts

**Status:** APPROVED  
**Date:** 2026-09-23  
**Deciders:** Architecture Review (Policy Checkpoint 3)  
**Affected parties:** fleet-toolbox, fleet-agents, future toolbox implementations

---

## Context

During Increment 2A enforcement bootstrap (import-linter activation on fleet-toolbox), a discrepancy was discovered between the canonical architecture policy and source code:

- **Policy stated:** fleet-toolbox has zero fleet dependencies.
- **Code showed:** `src/toolboxes/todo/todo_analysis.py` imports `Toolbox`, `Context`, `Analysis`, `Recommendation` from `tooling.agents` (fleet-agents).

Checkpoint 2.1 investigation had reported zero imports of fleet-agents, but this was an observation limitation: the static scanner did not find the todo_analysis.py imports. The policy was incomplete, not the source code.

---

## Decision

**Allow `fleet-toolbox → fleet-agents` as a deliberate, durable architectural edge.**

### Basis

1. **Intentional public API:** The four symbols are explicitly declared in `tooling.agents.__all__`:
   - `Toolbox` (ABC protocol)
   - `Context`, `Analysis`, `Recommendation` (@dataclass pure data contracts)
   
2. **Role-focused:** These are stable abstractions, not implementation details. They define the core contract for how all fleet tools/agents work.

3. **Currently necessary:** `TodoAnalysisToolbox` and any future toolbox implementations depend on these contracts to implement the protocol.

4. **Clean dependency:** The import is narrow (four symbols) and the types are zero-behavior data/protocol.

### Policy change

Update `fleet-architecture.yaml`:

```yaml
fleet-toolbox:
  allowed_fleet_dependencies:
    - fleet-agents  # ← New
```

Update `fleet-toolbox/.importlinter`:

```ini
[importlinter:contract:fleet-boundary]
forbidden_modules =
    fleet_base      # Still forbidden
    fleet_ops       # Still forbidden
    fleet_experiment # Still forbidden
    # Note: tooling (fleet-agents) is now ALLOWED; omitted from forbidden list
```

---

## Contract Placement Review Trigger

This decision does **not** resolve a longer-term architectural question:

> **Should `Context`, `Analysis`, `Recommendation`, and the `Toolbox` protocol be owned by `fleet-agents` (Layer 0.5 agent infrastructure) or extracted to `fleet-base.contracts` (Layer 0 foundation)?**

Currently, only agent/toolbox implementations consume these types. If a second independent consumer emerges outside the agent/toolbox domain—such as:

- `fleet-ops` audit events or job result types
- `fleet-spec` task outcome schemas
- External MCP adapters needing a stable schema
- Cross-fleet API contracts

Then dependency inversion principles suggest reconsidering the placement. Moving a dependency-free contract to the foundation layer would reduce coupling and clarify the abstraction boundary.

### Review trigger

**When:** A second independent non-agent/toolbox component requires these types or the `Toolbox` protocol for a non-toolbox use case.

**Action:** Convene an architecture review to consider:
1. Whether the types are agent-specific or genuinely multi-use abstractions
2. Whether extracting a narrow `fleet-base.contracts` module would clarify the architecture
3. The cost of migration vs. the benefit of reduced coupling

**Until trigger:** Keep the contracts in `fleet-agents`. No refactor is warranted while the dependency is single-domain and intentional.

---

## Implications

### For enforcement

- `fleet-toolbox/.importlinter` now allows `tooling` (removes it from forbidden list)
- Baseline test should pass; violation tests still work for other forbidden imports
- No workarounds or exceptions needed; this is deliberate policy, not a bypass

### For dependencies

- `fleet-toolbox/pyproject.toml` currently declares `fleet-agents` as a production dependency
- This declaration is now **confirmed required** (not stale)
- Keep it in place; do not remove during cleanup (Increment 2B)
- Historical `fleet-base` declaration remains stale; removal can proceed after clean-environment proof

### For documentation

- Fleet architecture policy is updated to reflect the actual dependency
- Public surface declaration (future: v1.0 policy) will need to define `tooling.agents` as a stable public module

---

## Lessons

1. **Enforcement bootstrap is policy discovery.** The guardrail found an incomplete policy, not a code error.
2. **Deliberate edges are not failures.** Some cross-repo dependencies are intentional; the policy tool's job is to separate intended from accidental, not to forbid all.
3. **Review triggers prevent architectural drift.** Approving this edge today with a future review condition ensures the decision remains deliberate if conditions change.

---

## Next steps

1. Update `fleet-architecture.yaml` v0.1.0 with allowed edge ✓
2. Update `fleet-toolbox/.importlinter` to allow `tooling` ✓
3. Re-run fleet-toolbox pilot: baseline pass → violation detect → revert → pass
4. Document evidence in governance/evidence/increment-2a/
5. Continue rollout with fleet-ops, fleet-spec, fleet-coordination (no policy changes needed for those)
