# Contract Verification Scope — Fleet 0.1.0

## Scope: Initial Read-Only Path Only

Contract verification for fleet 0.1.0 focuses on a single, narrow path:

```
fleet-coordination → fleet-ops → agent-tooling → vscode-workspace-mcp
```

This is the **read-only trial path**. Do not verify contracts for:
- rope-mcp refactoring path (separate, later)
- managed repositories (registered, not release-managed)
- trial profile application semantics (separate from contract verification)

---

## Contracts to Verify (7 types)

These are the contracts needed by the read-only path:

### 1. OperationContext
- **Definition:** Immutable context passed from fleet-coordination → fleet-ops → provider
- **Verification:**
  - Schema is valid (can be serialized/deserialized)
  - All required fields present (run_id, operation_id, workspace_id, user, timestamp)
  - Preserved through the call chain without mutation

### 2. AuditEvent
- **Definition:** Immutable audit trail entry
- **Verification:**
  - Schema is valid
  - All required fields present (event_id, timestamp, operation_id, status, result_digest)
  - Audit sink can append events
  - Round-trip serialization preserves hash

### 3. CapabilityRequest
- **Definition:** Request from fleet-ops to provider (e.g., find-files)
- **Verification:**
  - Schema matches provider's expected input
  - All required fields present (capability, args, workspace scope)
  - Constraints enforced (max files, timeout, scope validation)

### 4. CapabilityDecision
- **Definition:** Response from fleet-ops to fleet-coordination
- **Verification:**
  - Schema is valid
  - Explicit reason codes (permitted, denied_quota, denied_policy, denied_scope, error)
  - Never generic rejections
  - Result digest included (not raw result)

### 5. ProviderReference
- **Definition:** Metadata about a provider (name, version, status)
- **Verification:**
  - Schema valid
  - Version field matches fleet manifest
  - Status field (available, unavailable, deprecated)

### 6. ProviderInvoker
- **Definition:** Interface for calling a provider
- **Verification:**
  - Can instantiate vscode-workspace-mcp invoker
  - Preserves OperationContext through call
  - Maps provider result to CapabilityResult

### 7. Trial Profile
- **Definition:** Runtime policy for trial scope
- **Verification:**
  - Schema valid
  - Required fields present (profile_id, status, capabilities, providers, workspaces, limits, security)
  - Capabilities match vscode-workspace-mcp capabilities
  - Workspace allowlist is non-empty
  - Read-only flag is true

---

## Five Practical Checks

### Check 1: Schema / Serialization Round-Trip
```
Input:  OperationContext(run_id="...", operation_id="...", workspace_id="...", ...)
→ Serialize to JSON
→ Deserialize back
→ Verify hash matches
```

**Pass condition:** All 7 contract types pass round-trip without data loss.

### Check 2: Fleet-Ops Creates Valid Decision
```
fleet-ops receives CapabilityRequest(capability="find-files", ...)
→ Checks constraints (max 100 files, timeout 30s)
→ Creates CapabilityDecision(reason_code="permitted", result_digest="...")
```

**Pass condition:** Decision has valid reason_code and result_digest, never null/generic reason.

### Check 3: vscode-workspace-mcp Preserves Context
```
OperationContext passed in
→ vscode-workspace-mcp processes request
→ Returns CapabilityResult with operation_id preserved
```

**Pass condition:** operation_id in result matches input context.

### Check 4: Provider Result Maps to Capability Result
```
vscode-workspace-mcp finds files (internal success)
→ Maps to CapabilityResult(status="success", matches=[...])
→ fleet-ops creates CapabilityDecision from result
```

**Pass condition:** Status flows correctly, no data loss in mapping.

### Check 5: Audit Event Chain Is Complete
```
OperationContext created (event_id="op-1")
→ Request dispatched (event_id="op-2")
→ Result received (event_id="op-3")
→ Decision made (event_id="op-4")
→ Audit events form a chain
```

**Pass condition:** All 4 events present, linked by operation_id, in correct order.

---

## Implementation Path

### Step 1: Contract Artifact Verification
```
Verify the contract-bundle.yaml exists and is valid YAML
```
**Status:** Ready (artifact exists)

### Step 2: Schema Validation
```
Load each contract schema
Verify it parses as valid JSON Schema
Test a valid instance against schema
```
**Status:** To do (15 min)

### Step 3: Round-Trip Tests
```
Test (1): OperationContext serializes/deserializes correctly
Test (2): AuditEvent hash round-trips
Test (3): CapabilityRequest validates constraints
Test (4): CapabilityDecision has valid reason_code
Test (5): ProviderReference has version
Test (6): ProviderInvoker can be instantiated
Test (7): Trial profile is valid
```
**Status:** To do (1 hour, reuse fleet-base tests)

### Step 4: Integration Path Test
```
Simulate: fleet-coordination → fleet-ops → agent-tooling → vscode-workspace-mcp
Verify the 5 practical checks pass for the full path
```
**Status:** To do (2 hours)

### Step 5: Update Promotion Gate
```
When all checks pass:
  contracts: "pass"
  promotion_eligible: true (if no other blockers)
```
**Status:** To do (after tests pass)

---

## What NOT to Verify (0.1.0)

❌ **Do not** implement generalized contract compatibility matrix  
❌ **Do not** verify rope-mcp mutation contracts  
❌ **Do not** verify managed repository contracts  
❌ **Do not** build a contract versioning system  
❌ **Do not** test all provider/consumer combinations  

These are **future work** (0.2.0+).

---

## Effort Estimate

- Schema validation: **15 min**
- Round-trip tests: **1 hour** (reuse fleet-base serialization tests)
- Integration path test: **2 hours**
- Update promotion gate: **30 min**
- **Total: ~4 hours**

---

## Success Criteria

```
fleet-check --scope core --json
→ checks.contracts: "pass"
→ promotion_eligible: true
→ ready for trial execution
```

When all 5 practical checks pass, core 0.1.0 is promoted to **verified**.

