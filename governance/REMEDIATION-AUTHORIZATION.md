# Remediation Authorization: live_dashboard_v2.py Telemetry Extraction

**Date:** 2026-09-23  
**Authority:** Compliance Audit Pilot (error_boundary_review control)  
**Status:** AUTHORIZED FOR IMPLEMENTATION  
**Revision:** fleet-agents@8682c91d21bc96dc719b2a8ff4c1addd827fccc2

---

## Authorization Statement

Implement one bounded remediation to make live-dashboard telemetry extraction failures distinguishable from valid empty results. This is the **only** remediation authorized from the pilot audit findings. Do not extend to other modules or exception categories.

---

## Target Behavior

**Objective:**  
Refactor `live_dashboard_v2.py` telemetry extractors (`_extract_repos`, `_extract_fixes`, `_extract_duration`) to return a structured `TelemetryResult` that explicitly signals:
- `ok` — Extraction succeeded with data
- `empty` — Extraction succeeded; no matching data
- `unavailable` — Source file not found or not available
- `failed` — Extraction attempted but failed (parse error, permission, etc.)

**Operator impact:**  
Dashboard can now detect and display incomplete or unreliable metrics. Operator can distinguish "no data found" from "data source failed."

---

## Allowed Changes

- [x] Define `TelemetryResult` dataclass and `TelemetryStatus` enum
- [x] Refactor 6 exception handlers in `live_dashboard_v2.py` (lines 274, 348, 363, 379, 409, 412)
- [x] Update direct callers within `live_dashboard_v2.py` to check result status
- [x] Add dashboard logic to display error indicators ("⚠️ Incomplete")
- [x] Add focused regression tests for exception paths (8+ tests covering all status outcomes)
- [x] Run full repository test suite to verify no regressions

---

## Forbidden Changes

- [ ] Do **not** change dispatch behavior, fleet mutation, or orchestration logic
- [ ] Do **not** modify exception handling in other modules (enhanced_remediation.py, repo_eval.py, lint_fixer.py)
- [ ] Do **not** extend this change to other exception handlers in live_dashboard_v2.py
- [ ] Do **not** refactor non-telemetry exception handling
- [ ] Do **not** change dashboard metric definitions except for error-state labeling
- [ ] Do **not** alter or rewrite historical audit records
- [ ] Do **not** scope-creep into related improvements (logging, caching, performance)

---

## Implementation Contract

### Required Acceptance Criteria (Behavior-Based)

- [x] Every targeted telemetry extraction method returns a `TelemetryResult`
- [x] `TelemetryResult.status` is one of: ok, empty, unavailable, failed
- [x] Valid empty data (e.g., no repos in time window) returns **empty**, not error
- [x] Missing optional source returns **unavailable**, not failed
- [x] Malformed or parse-failed source returns **failed** with error message
- [x] Callers check `result.status` before using `result.value`
- [x] Dashboard displays "⚠️ Incomplete" when status is failed or unavailable
- [x] Targeted exception paths have focused regression tests
- [x] All existing tests continue to pass
- [x] No changes to dispatch logic or fleet mutation
- [x] No changes to dashboard metric definitions except for error-state labeling

### Required Artifacts

1. **Code changes:** live_dashboard_v2.py
   - TelemetryResult type definition
   - Refactored methods: load_current_run, _load_recent_runs, _extract_repos, _extract_fixes, _extract_duration
   - Updated callers in _load_recent_runs
   - Dashboard error-state indicator logic

2. **Tests:** tests/integration/test_live_dashboard_v2.py
   - 8+ regression tests covering: ok, empty, unavailable, failed status
   - Exception path tests (file not found, permission error, parse error, invalid timestamp)
   - Existing test compatibility verified

3. **Verification:**
   - `just test` passes (full test suite)
   - Post-remediation audit: re-assess error_boundary_review control
   - Record outcome change (if any) from Partial status

---

## Post-Remediation Reassessment

After implementation is complete and tests pass:

1. **Re-audit** `error_boundary_review` control against the post-change revision
2. **Update** `fleet-agents-2026-09-23.yaml` with new revision hash
3. **Record** control outcome:
   - Did status improve from **Partial**?
   - What limitations remain?
   - What confidence level?
4. **Document** findings in audit record
5. **Decide** whether to pilot live_dashboard_v2 remediation on other high-risk areas (enhanced_remediation, repo_eval)

---

## Scope Boundaries

### What This Controls

**Only:** Telemetry extraction error-state distinction in live_dashboard_v2.py

### What This Does NOT Control

- Fleet orchestration or dispatch behavior (remains unchanged)
- Exception handling in other modules (deferred to future audits)
- Test execution or validation infrastructure (unchanged)
- Repository mutation or CI behavior (unchanged)

---

## Execution Authority

**Implementation:** Claude agent or human developer  
**Audit Mode:** Subagent (read-only exception classification already complete)  
**Testing:** Existing test infrastructure (pytest, markers)  
**Review:** Post-implementation audit update required

---

## Timeline & Effort

- **Implementation:** 2–3 hours
- **Testing:** 1–2 hours
- **Verification & post-remediation audit:** 1 hour
- **Total:** 4–5 hours

---

## Termination Clause

If implementation encounters:
- **Unexpected breakage** in unrelated components → Halt, investigate, rollback
- **Scope creep temptation** (e.g., "while we're here, let's fix X") → Decline; add to future audit
- **Requests to expand scope** (e.g., "fix enhanced_remediation too") → Redirect to future audit

This is a one-behavior-change remediation. Stop when telemetry extraction is distinguishable. Then reassess.

---

## Related Documents

- **Pilot Audit:** `governance/compliance-audit-results/fleet-agents-2026-09-23.yaml` (evidence record, revision pinned)
- **Remediation Plan:** `governance/remediation-plans/fleet-agents-live-dashboard-v2-error-boundary-2026-09-23.md` (detailed implementation steps)
- **Compliance Standard:** `governance/compliance-standard.yaml` (error_boundary_review control definition)
- **Audit History:** `governance/AUDIT-HISTORY.md` (lifecycle tracking)

---

**Authorization Date:** 2026-09-23  
**Authorized by:** Compliance Audit Pilot Governance  
**Status:** ✅ READY FOR IMPLEMENTATION  
**Next Step:** Execute implementation; update audit record with post-remediation result
