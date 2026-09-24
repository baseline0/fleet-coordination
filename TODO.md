# Fleet-Coordination TODO

**Focus:** Compliance infrastructure is at a sustainable stopping point. Returning to Morning Review Phase 2 (thin Typer CLI wiring).

---

## Compliance Backlog (Non-Blocking)

These are valid tasks but do not block Morning Review:

### Maintenance: Initialize fleet-spec governance
- **Priority:** Next small maintenance task
- **Scope:** Add `.fleet/` directory to fleet-spec
- **Done when:** governance_schema_validation control passes
- **Files:** `.fleet/config.yaml`, `.fleet/catalog-info.yaml`, `.fleet/boundaries.yaml` (v1.0 schema)
- **Effort:** 30 minutes

### Review: Classify fleet-toolbox handlers
- **Priority:** Next focused review task
- **Scope:** Manually review and classify 10 exception handlers (already collected in Phase 2)
- **Rubric:** Handler classification guide with examples in `/tmp/handler-classification-guide.md`
- **Done when:** All 10 handlers classified with high confidence; examples document created
- **Effort:** 45 minutes

### Batch: Bulk-classify fleet-ops handlers
- **Priority:** Subsequent batch task
- **Scope:** Classify 160 exception handlers using fleet-toolbox rubric as reference
- **Strategy:** Auto-classify with high confidence rules; spot-check 10-15 results; manually review risk/unknown cases
- **Done when:** All 160 handlers classified; flagged risks reviewed and documented
- **Effort:** 2-3 hours (mostly automated with spot-checks)

### Housekeeping: Normalize audit output directory naming
- **Priority:** Cleanup
- **Scope:** Rename `/tmp/compliance-audit-results-phase-1a/` to use timestamp-based naming
- **Done when:** Results use format like `fleet-ops-2026-09-24T1415CDT.yaml` instead of phase names
- **Effort:** 15 minutes

---

## Morning Review (ACTIVE)

### Phase 2: Thin Typer CLI wiring and compatibility checks

**Goal:** Wire report generation to CLI command with JSON + text output modes.

**Scope (keep narrow):**
1. ✅ Existing report generation path (morning_review.py)
2. ✅ Existing Typer CLI scaffold (api_commands.py)
3. ⏳ Test JSON output mode (deterministic, all data always present)
4. ⏳ Test text output mode (human-readable, scope-filtered)
5. ⏳ Verify exit codes (0 on success, even if optional domains unavailable)
6. ⏳ Verify optional domains treated as `unknown` with explicit limitations

**Avoid in this slice:**
- Endpoint work
- Dispatcher integration
- TUI implementation
- Source mutations or auto-remediation
- CI integration

**Files:**
- `src/fleet_ops/services/morning_review.py` — existing service
- `src/fleet_ops/cli/api_commands.py` — existing CLI command
- `tests/unit/test_morning_review_cli.py` — existing tests (verify deterministic fixtures)

---

## Known Audit Findings

### fleet-ops: Test execution fails
- **Audit Control:** test_execution
- **Finding:** Unawaited coroutines in test cleanup
- **Status:** Documented in `TODO-AUDIT-2026-09-24.md`
- **Action:** Separate remediation task (not blocking compliance audit)

### fleet-spec: No governance metadata
- **Audit Control:** governance_schema_validation
- **Finding:** `.fleet/` directory missing
- **Status:** Known gap, remediation scoped
- **Action:** Initialize `.fleet/` (backlog item above)

---

## Archive

- Phase 1B: Deterministic controls (repository_metadata, test_execution, package_install, import_boundary_check) — **COMPLETE**
- Phase 2: Error boundary review (handler collection + classification rubric) — **COMPLETE**
- Phase 3: Governance schema validation — **COMPLETE**

Audit results: `/tmp/compliance-audit-results-phase-1a/` (ephemeral)
