# Week 2 Decisions Record
## Final Decisions with Safe Defaults (Approved)

**Date:** 2026-09-20  
**Status:** Final, documented  
**Authority:** Consultant-approved safe defaults + local code review pending

---

## Summary of 6 Decisions (Safe Defaults)

All decisions use **safe architectural defaults pending actual code-owner review**. No false claims about code intent; all assume internal coupling unless demonstrated otherwise.

---

## Decision 1: fleet_ops.agents.repo_eval (src/todo_generator_cli.py:85)

```yaml
finding_id: BOUNDARY-002-FLEET-OPS-001
current_import: "from fleet_ops.agents.repo_eval import ..."

classification: internal_implementation
treatment: prohibit_and_define_public_api

decision:
  rule: BOUNDARY-002-FLEET-OPS (blocking)
  
  assumption: "fleet_ops.agents.repo_eval is internal implementation, 
              not a documented public API"
  
  verification_required: >
    Code-owner review to confirm:
    - Is this a public API (documented, versioned, tested)?
    - If yes: add to compatibility matrix
    - If no: replace with public interface

  public_api_recommendation: "fleet_ops.RepoEvaluationClient"
  
  remediation:
    action: "Define public API in fleet-ops"
    owner: # NOTE: fleet-ops maintainer
    target_date: "2026-12-15"
    tracking_issue: "# NOTE: create ADR"

status: provisional_awaiting_review
```

---

## Decision 2: code_search_cli.py:24 & lint_fixer.py:25 (fleet_ops.src.mcp_quota_manager)

```yaml
findings:
  - finding_id: BOUNDARY-002-FLEET-OPS-002
    file: "src/code_search_cli.py"
    line: 24
    current_import: "from fleet_ops.src.mcp_quota_manager import ..."
  
  - finding_id: BOUNDARY-002-FLEET-OPS-003
    file: "src/lint_fixer.py"
    line: 25
    current_import: "from fleet_ops.src.mcp_quota_manager import ..."

classification: internal_module_direct_import
treatment: prohibit_and_define_public_api

decision:
  rule: BOUNDARY-002-FLEET-OPS (blocking)
  
  assumption: "fleet_ops.src.mcp_quota_manager is internal; 
              no public quota API exists"
  
  verification_required: >
    Code-owner review to confirm:
    - Quota management scope (fleet-wide? per-workspace?)
    - Who should own quota decisions?
    - What is the proper interface?

  public_api_recommendation: |
    One of:
    - fleet_ops.QuotaPolicy (query quota state)
    - fleet_ops.QuotaClient (request quota)
    - fleet_ops.QuotaManager (if agent-tooling needs to own quotas)
  
  remediation:
    action: "Define public quota API in fleet-ops; replace .src import"
    owner: # NOTE: fleet-ops maintainer
    target_date: "2026-12-15"
    tracking_issue: "# NOTE: create ADR"
    combined: "Can be same ADR as Decision 1 if same root cause"

status: provisional_awaiting_review
```

---

## Decision 3: test_validator.py:18 (fleet_ops.src.audit_logger)

```yaml
finding_id: BOUNDARY-002-FLEET-OPS-004
file: "src/test_validator.py"
line: 18
current_import: "from fleet_ops.src.audit_logger import ..."

classification: audit_validation_coupling
treatment: prohibit_and_clarify_ownership

decision:
  rule: BOUNDARY-002-FLEET-OPS (blocking)
  
  assumption: >
    fleet-ops owns fleet-wide audit validation (authorization, routing, 
    compliance). agent-tooling should not import audit implementation.
  
  verification_required: >
    Code-owner review to confirm:
    - Does test_validator.py validate fleet-level audit semantics?
    - Or does it validate agent-tooling-local event serialization?
    - Where should this validator live?

  options:
    - move_to_fleet_ops: |
        If validator belongs to fleet audit semantics,
        move test_validator.py to fleet-ops
    
    - use_public_api: |
        If validator remains in agent-tooling,
        use public interface: fleet_ops.AuditVerifier
    
    - extract_local_validator: |
        If validator tests agent-tooling-only event format,
        keep in agent-tooling, remove fleet-ops import

  remediation:
    action: "Code-owner decides ownership; implement chosen option"
    owner: # NOTE: agent-tooling + fleet-ops maintainer
    target_date: "2026-12-15"
    tracking_issue: "# NOTE: create ADR"

status: provisional_awaiting_review
```

---

## Decision 4: Rope Production Files (3 files, 5 findings)

### 4a. src/refactor_agent.py (lines 34, 41)

```yaml
finding_id: BOUNDARY-001-ROPE-001
file: "src/refactor_agent.py"
current_import: "from rope_mcp_refactor_backend import ..."

classification_provisional: core_logic
treatment: extract_protocol

decision:
  assumption: >
    refactor_agent.py contains core refactoring logic that should depend
    on a RefactoringProvider protocol, not rope_mcp directly
  
  verification_required: >
    Code inspection to confirm:
    - Does this file contain agent logic or rope orchestration?
    - What abstractions exist today?
    - Is rope the only provider or one of many?

  remediation:
    action: "Extract RefactoringProvider protocol; remove direct rope imports"
    option_a:
      name: "protocol_extraction"
      steps:
        1. Define "RefactoringProvider" protocol in agent-tooling
        2. Refactor refactor_agent.py to depend on protocol
        3. Create rope implementation in src/adapters/rope_mcp/
        4. Update fleet-ops to inject rope adapter
    
    option_b:
      name: "keep_as_rope_adapter"
      if: "file is rope-specific adapter, not core logic"
      steps:
        1. Move to src/adapters/rope_mcp/refactor_agent.py
        2. Add to adapter-allowlist.yaml
        3. Create allowlist entry: {path, imports, owner, review_date}

  owner: # NOTE: agent-tooling maintainer
  target_date: "2026-12-15"
  tracking_issue: "# NOTE: create ADR"

status: provisional_awaiting_code_review
```

### 4b. src/rope_backend_orchestration.py (lines 18, 23)

```yaml
finding_id: BOUNDARY-001-ROPE-002
file: "src/rope_backend_orchestration.py"
current_import: "from rope_mcp_diff_capture, rope_mcp_executor import ..."

classification_provisional: outbound_adapter_or_fleet_ops_orchestration
treatment: move_and_classify

decision:
  assumption: >
    This file either orchestrates rope-specific operations (adapter)
    or orchestrates across multiple providers (fleet-ops concern)
  
  verification_required: >
    Code inspection to confirm:
    - Does this file orchestrate ONLY rope_mcp components?
    - Or does it select/route among multiple providers?
    - Is it core agent logic or infrastructure?

  remediation:
    option_a:
      name: "rope_specific_adapter"
      if: "orchestrates rope_mcp only"
      steps:
        1. Move to src/adapters/rope_mcp/orchestration.py
        2. Create RopeOrchestration adapter with protocol
        3. Add to adapter-allowlist.yaml
    
    option_b:
      name: "multi_provider_selection"
      if: "selects among providers or routes by capability"
      steps:
        1. Move orchestration logic to fleet-ops
        2. Keep only rope-specific parts in agent-tooling
        3. Use fleet-ops CapabilityRequest routing

  owner: # NOTE: agent-tooling + fleet-ops maintainer
  target_date: "2026-12-15"
  tracking_issue: "# NOTE: create ADR"

status: provisional_awaiting_code_review
```

### 4c. src/rope_audit.py (line 15)

```yaml
finding_id: BOUNDARY-001-ROPE-003
file: "src/rope_audit.py"
current_import: "from rope_mcp_diff_capture import ..."

classification_provisional: rope_specific_audit_adapter
treatment: move_to_adapter_namespace

decision:
  assumption: >
    rope_audit.py translates rope_mcp audit events to shared AuditEvent
    format. It is a provider-specific adapter, not core logic.
  
  verification_required: >
    Code inspection to confirm:
    - Does this file translate rope events to shared format?
    - Or does it perform fleet-wide audit validation?

  remediation:
    option_a:
      name: "provider_adapter"
      if: "translates rope-specific events to shared format"
      steps:
        1. Move to src/adapters/rope_mcp/audit.py
        2. Create RopeAuditAdapter with AuditEventTranslator protocol
        3. Add to adapter-allowlist.yaml
        4. Core audit logic remains in agent-tooling
    
    option_b:
      name: "shared_audit_interface"
      if: "owns shared audit protocol"
      steps:
        1. Keep audit protocol in agent-tooling
        2. Move rope translation to src/adapters/rope_mcp/audit.py
        3. MCPs emit via shared AuditEvent sink

  owner: # NOTE: agent-tooling maintainer
  target_date: "2026-12-15"
  tracking_issue: "# NOTE: create ADR"

status: provisional_awaiting_code_review
```

---

## Decision 5: Integration Test Location & Classification

```yaml
test_files:
  - file: "tests/test_rope_mcp_integration.py"
    current_line: 19
    classification_current: "misleadingly named (has 'integration' but in tests/ not tests/integration/)"

finding_id: BOUNDARY-001-UNIT-001
current_scope: "unit tests directory"
desired_scope: "integration tests directory"

decision:
  assumption: >
    This test file exercises real provider behavior, despite misleading name.
    Reclassify and move to tests/integration/ for proper scoping.
  
  verification_required: >
    Code inspection to confirm:
    - Does test exercise real rope_mcp behavior?
    - Or does it test local agent logic with mock?

  remediation:
    action: "Move to tests/integration/test_rope_mcp_integration.py"
    rule: "BOUNDARY-001-INTEGRATION (report-only)"
    
    if_actually_unit_test: |
      Rename to test_rope_mcp_unit.py and:
      1. Replace direct rope_mcp import with mock/fake
      2. Keep in tests/test_*.py location
      3. Add unit test fixture library

  owner: # NOTE: integration-test maintainer
  target_date: "2026-09-30"
  tracking_issue: "# NOTE: code review issue"

status: provisional_awaiting_content_review
```

---

## Decision 6: Unit Test Remediation

```yaml
findings: 4
test_files:
  - "tests/test_rope_mcp_executor_unit.py:18"
  - "tests/test_rope_mcp_diff_capture.py:11"
  - "tests/test_rope_backend_orchestration.py:21"
  (+ the reclassified tests/test_rope_mcp_integration.py if it is unit)

decision:
  rule: "BOUNDARY-001-UNIT (blocking)"
  
  treatment: "remediate_with_mocks"
  
  remediation:
    action: "Replace direct rope_mcp imports with test fixtures"
    
    steps:
      1. Create test fixtures (mocks/fakes) for rope_mcp components
      2. Update all 4 test files to use fixtures
      3. Document fixture library
      4. Add CI check for unit-test rope imports
    
    deliverables:
      - tests/fixtures/rope_mcp_mock.py (fixture library)
      - Updated test files (no direct rope imports)
      - CI rule blocking new unit-test rope imports
    
    timeline:
      start: immediate (unblocked)
      target: 2026-12-31

  owner: # NOTE: agent-tooling test maintainer
  tracking_issue: "# NOTE: create refactoring issue"

status: ready_for_implementation
```

---

## Provisional Ownership Assignments

All pending **actual named people** (use these only as accountability until named):

```yaml
accountable_owners:
  production_findings_3:
    title: "agent-tooling production code owner"
    responsibility: "Decide core vs. adapter classification for 3 rope files"
    placeholder: "# NOTE: assign"
  
  public_apis_2:
    title: "fleet-ops maintainer"
    responsibility: "Define public quota API, repo-eval API, audit API"
    placeholder: "# NOTE: assign"
  
  unit_tests:
    title: "agent-tooling test maintainer"
    responsibility: "Create fixture library, remediate 4 test files"
    placeholder: "# NOTE: assign"
  
  integration_tests:
    title: "integration-suite maintainer"
    responsibility: "Reclassify, move integration tests, maintain suite"
    placeholder: "# NOTE: assign"
  
  architecture_lead:
    title: "architecture council representative"
    responsibility: "Review decisions, approve ADRs, gate enforcement"
    placeholder: "# NOTE: assign"
  
  observability:
    title: "runtime-observability owner"
    responsibility: "Implement metrics, dashboard, correlation tests"
    placeholder: "# NOTE: assign"
```

---

## Final Rules (Approved)

See BOUNDARY_RULES_FINAL.yaml for corrected rule definitions.

---

## Status

- **6 decisions: Documented with safe defaults**
- **All awaiting: Code-owner review and actual named ownership**
- **Ready to proceed: Trial on Track A + implementation on Track B in parallel**
- **Strict enforcement: Still blocked until full remediation tracking**

---

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
