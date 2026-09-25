# Compliance Audit: fleet-agents

**Date:** 2026-09-23  
**Repository:** fleet-agents  
**Role:** agent_library  
**Standard Version:** fleet-engineering-compliance 0.1.0  
**Pilot:** Yes — First audit using evidence-based control framework

---

## Executive Summary

| Control | Result | Confidence | Status |
|---------|--------|------------|--------|
| test_execution | Pass | High | No action required |
| error_boundary_review | Partial | Medium | Bounded investigation recommended |

**Key Finding:** Fleet-agents test infrastructure is solid. Exception handling at execution boundaries has localized silent-failure risks (20/97 handlers) concentrated in three areas. Risk is operational: failures are invisible to callers, making debugging difficult.

---

## Control 1: test_execution

**Result:** ✓ Pass  
**Confidence:** High

### Evidence

- **Test Suite:** 642 tests organized by markers (unit, integration, live)
- **Test Command:** `just test` runs and passes
- **CI Validation:** Tests run on every commit via GitHub Actions
- **Tested Behaviors:** Agent lifecycle, execution bounds, escape testing, exception paths

### Tested Behaviors

- ExecutionBounds declaration and threading through agent lifecycle ✓
- Filesystem boundary enforcement and escape blocking ✓
- Audit trail recording and event correlation ✓
- Agent execution dispatch and error handling ✓
- MCP coordinator fallback strategies ✓
- Refactoring operations and error recovery ✓

### Known Untested Modules

- Some optional features (graceful degradation paths)
- Live dashboard rendering edge cases
- Some CLI decorators

### Operational Consequence

Regressions in core agent behaviors are detected. Fleet-agents is validated before each deployment.

---

## Control 2: error_boundary_review

**Result:** ⚠ Partial  
**Confidence:** Medium

### Findings

**Total Handlers Reviewed:** 97 generic exception handlers (`except Exception` and `except BaseException`)

**Classification:**
- 48 (49%) **Acceptable Boundaries** — logged, lifecycle recorded, error returned to caller ✓
- 21 (22%) **Acceptable Best-Effort** — optional features, graceful degradation ✓
- 8 (8%) **Needs Focused Review** — unclear intent, insufficient context
- 20 (21%) **Silent-Failure Risks** — swallowed exceptions, no logging, no error indication ⚠

### Operational Risk Areas

**High Consequence: `live_dashboard_v2.py`** (6 handlers)
- Lines: 274, 348, 363, 379, 409, 412
- Issue: Telemetry extractors silently hide file I/O and JSON parse errors
- Impact: Operator metrics become inaccurate; operator cannot tell if data is incomplete
- Example: `_extract_repos()` returns empty list on parse failure; caller assumes "no repos" (valid) not "file read failed" (error)

**Medium Consequence: `enhanced_remediation.py`** (4 handlers)
- Lines: 177, 269, 354, 392
- Issue: Suggestion helpers catch all exceptions and return `None` or `{}`
- Impact: Callers cannot tell if parsing succeeded with no suggestions vs. parsing failed
- Examples: `suggest_circular_dependency_fix()` returns `None` on AST parse error

**Medium Consequence: `repo_eval.py`** (3 handlers)
- Lines: 387, 397, 487
- Issue: AST parsing failures hidden in loops; incomplete analysis returned as complete
- Impact: Analysis results may be partial or invalid without caller awareness

### Evidence: Handler Classification

Full classification details: `/tmp/fleet-agents-exception-boundary-review-2026-09-23.md` (97 handlers, evidence per handler)

Sample classification:

```
live_dashboard_v2.py:274 — load_current_run()
  Operation: File I/O + JSON parse
  Handler: except Exception: return False
  Issue: File permission error looks like "not found" to caller
  Caller cannot distinguish "run not found" from "file read failed"
  Classification: Silent-failure risk
```

### Operational Consequence

Live dashboard metrics may be unreliable. If file I/O fails silently:
- `runs_processed` count is inaccurate
- `total_fixes` metric is incomplete
- Operator believes dashboard is complete when it's incomplete

Debugging is difficult: failure is hidden; operator sees "0 repos" without knowing why.

### Limitations

- Handler classification is qualitative (requires code inspection)
- Handler intent varies by context (graceful degradation vs. error hiding)
- Some silent failures are intentional; others represent bugs
- Full assessment requires deeper investigation of high-consequence areas

### Confidence Assessment

**Medium** because:
- Classification is evidence-based (code inspection, caller analysis, test coverage)
- But intent varies by context and requires human judgment
- Bounded investigation needed to distinguish "intentional graceful degradation" from "hidden bugs"

---

## Recommendations

### Immediate Next Step

**Bounded Remediation: `live_dashboard_v2.py`**

**Why this area first:**
- Highest operational consequence (operator telemetry reliability)
- Smallest scope (6 handlers in one file)
- Clear remediation path (distinguish error from valid result)

**Approach:**
1. Refactor telemetry extractors to distinguish outcomes:
   - `success: T` — parsing succeeded, value is reliable
   - `error: str` — operation failed, reason provided
   - `unavailable: true` — feature/file not available
2. Caller checks result type before using value
3. Dashboard shows error indicator if data is incomplete

**Example refactor:**
```python
# Before: returns False on parse error
def load_current_run() -> bool:
    try:
        ...
    except Exception:
        return False  # Caller can't tell why

# After: distinguishable result type
class RunResult(TypedDict, total=False):
    run: Run
    error: str
    unavailable: bool

def load_current_run() -> RunResult:
    try:
        ...
    except OSError as e:
        return {"error": f"File read failed: {e}"}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}
```

**Success Criteria:**
- Telemetry extractors return distinguishable results
- Caller can detect incomplete data
- Dashboard shows error state (e.g., "metrics incomplete due to file read error")
- Regression tests validate error paths

**Stop After This:**
Do NOT attempt to fix all 20 handlers. Fix this one area, test it, then re-audit to validate the approach.

---

## Pilot Learnings

This is the first audit using the evidence-based compliance standard. The standard:

- ✓ Produces specific findings per control (not generic scores)
- ✓ Distinguishes high-consequence from low-consequence issues
- ✓ Provides evidence-based next steps
- ✓ Avoids synthetic numeric scoring

Changes to standard based on this pilot: none yet. Standard is working as intended.

---

## Earlier Audit (Exploratory, Not Authoritative)

The earlier fleet-wide compliance report (`/tmp/compliance-audit-2026-09-23.md`) was an exploratory heuristic inventory using synthetic numeric scoring (6.5/10, 8.0/10, etc.). **That report is not authoritative** and should not guide remediation decisions.

**Why it was unreliable:**
- Used metrics (exception count, logger count) as compliance findings
- Assigned numeric scores without role differentiation
- Recommended sweeping changes without evidence
- Did not classify handlers individually

**This audit (2026-09-23) is authoritative** because it:
- Uses role-based control applicability
- Classifies exceptions individually with evidence
- Specifies operational consequences
- Recommends bounded next steps

---

## Next Audit

After remediation of live_dashboard_v2.py:

1. **Re-audit fleet-agents** (same controls) to validate remediation
2. **Pilot fleet-spec** with standards_validation control
3. Decide whether to expand to other repos based on lessons learned

---

**Report Generated:** 2026-09-23  
**Auditor:** Compliance Audit Agent  
**Evidence Location:** `/tmp/fleet-agents-exception-boundary-review-2026-09-23.md`  
**Standard Location:** `governance/compliance-standard.yaml`  
**Agent Contract:** `governance/compliance-audit-agent.md`
