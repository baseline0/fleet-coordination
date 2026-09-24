# Phase 2: Error Boundary Review (Exception Handler Classification)

**Date:** 2026-09-24  
**Status:** Control Implementation Complete — Handler Discovery Done  
**Next Step:** Manual Classification (Pilot Model: fleet-agents)

---

## Overview

Phase 2 introduces the `error_boundary_review` control to the compliance audit runner. This qualitative control differs from Phase 1's deterministic checks (test_execution, import_boundary_check, etc.) because handler classification requires code review.

**Control Goal:** Identify exception handlers that silently swallow errors without indicating failure to the caller.

**Pilot Model:** fleet-agents (89 handlers classified into: 20 silent-failure risks, 48 acceptable boundaries, 21 best-effort)

---

## Discovery Results

### Fleet-Ops (Scope: orchestration_and_control_plane)

**Handlers Found:** 160  
**Control Result:** unknown (pending classification)  
**Confidence:** medium (grep finds locations; classification awaits review)

**Handler Breakdown (by pattern):**
- `except Exception as e:` — 96 handlers (mostly logging + error handling)
- `except Exception:` — 57 handlers (mostly silent swallow + pass patterns)
- `except BaseException:` — 4 handlers (rare; higher severity)
- `except HTTPException:` — 3 handlers (library-specific; lower risk)

**High-Risk Candidates (Silent-Failure Patterns):**
- 17 handlers in `src/fleet_ops/services/work_queue_service.py` (4 except Exception: patterns on lines 157, 218, 283, 362)
- 10 handlers in `src/fleet_ops/local_agents/vscode_mcp_refactor_backend.py` (line 498: bare except Exception)
- 6 handlers in `src/fleet_ops/tui/components/sortable_table.py` (lines 296, 319: bare except Exception)

**Evidence Location:** `/tmp/compliance-audit-results-phase-1a/fleet-ops-2026-09-24.md` (full handler list with line numbers)

---

### Fleet-Toolbox (Scope: domain_tooling)

**Handlers Found:** 10  
**Control Result:** unknown (pending classification)  
**Confidence:** medium (smaller scope; easier to classify)

**Handler Breakdown:**
- `except Exception as e:` — 9 handlers (mostly in scrapers/todo analysis)
- `except Exception:` — 1 handler (todo_analysis.py)

**Specific Locations:**
- 2 handlers: `arxiv_scraper.py` (lines 131, 164)
- 2 handlers: `etf_finder.py` (lines 128, 155)
- 1 handler: `base.py` (line 93)
- 4 handlers: `todo_analysis.py` (lines 47, 126, 199, 309, 312 — 5 total)

**Evidence Location:** `/tmp/compliance-audit-results-phase-1a/fleet-toolbox-2026-09-24.md`

---

## Classification Task

### Categories

Each handler is classified as ONE of:

1. **Acceptable Boundary** — Handler logs the error and returns a clear error result to the caller
   - Caller can detect that an operation failed
   - Error signal is explicit (exception, return value, sentinel, or status enum)
   - Example: `except Exception as e: logger.error(f"Failed: {e}"); return None`

2. **Acceptable Best-Effort** — Handler is for an optional feature; failure is degradation, not fatal
   - Feature is optional or graceful-degradation scenario
   - Caller doesn't require success signal for the core operation
   - Example: `except Exception: pass  # Optional cache refresh; no-op if fails`

3. **Silent-Failure Risk** — Handler swallows exception with no indication to caller
   - Caller has no way to know operation failed
   - Could mask bugs or operational issues
   - Example: `except Exception: pass  # Return implicitly None; caller can't tell if succeeded`

### Classification Process (Pilot Model: fleet-agents)

For each handler:

1. **Read the handler code** (line number + surrounding context)
2. **Identify what caller receives** (return value, side effect, or exception-free exit)
3. **Determine if caller can detect failure** (yes → boundary or best-effort; no → risk)
4. **Record classification** in YAML with evidence quote

**Example Classification Entry:**

```yaml
- handler_id: fleet_agents_live_dashboard_v2_274
  file: src/tooling/tui/live_dashboard_v2.py
  line: 274
  pattern: "except Exception: return False"
  classification: acceptable_boundary
  rationale: "Caller gets explicit False return; can detect failure"
  evidence: "load_current_run() returning False allows caller to branch on error"
```

---

## Next Steps

### Immediate (This Session)

1. ✅ **Phase 2 control implemented** — error_boundary_review audit runner complete
2. ✅ **Handler discovery complete** — 160 fleet-ops, 10 fleet-toolbox handlers collected
3. ⏳ **Classification task ahead** — Structured review of each handler

### Classification Roadmap

**Option A: Subagent-Assisted Classification**
- Spawn subagent with fleet-agents pilot model as reference
- Provide handler grep output + code excerpts
- Subagent classifies handlers with rationale
- Human review and spot-check results

**Option B: Manual Incremental Review**
- Start with fleet-toolbox (10 handlers, quicker)
- Use fleet-agents pilot classifications as reference guide
- Build handler classification docs
- Expand to fleet-ops (160 handlers) in phases

**Option C: Hybrid (Recommended)**
- Start manual on fleet-toolbox to establish classification precedent
- Use that to build a classification guide/examples
- Then scale to fleet-ops via subagent with examples in context

### Post-Classification

1. Generate remediation plans for silent-failure risks (like fleet-agents pilot)
2. Create bounded tasks for high-risk handlers
3. Track handler classification changes over time
4. Re-audit quarterly to track improvement

---

## Constraint & Limitation

**This control is qualitative and requires judgment.**

- Grep finds handler locations; classification requires code reading
- Classification confidence is medium, not high
- No automated way to verify classification; peer review recommended
- Handlers may be intentional best-effort; context is everything

---

## Audit Evidence

**Fleet-ops audit record:**  
`/tmp/compliance-audit-results-phase-1a/fleet-ops-2026-09-24.{yaml,md}`

**Fleet-toolbox audit record:**  
`/tmp/compliance-audit-results-phase-1a/fleet-toolbox-2026-09-24.{yaml,md}`

**Pilot reference (fleet-agents):**  
`/home/mark/projects/fleet-coordination/governance/remediation-plans/fleet-agents-live-dashboard-v2-error-boundary-2026-09-23.md`

---

**Status:** Phase 2 control ready for classification task. User decision required on approach (subagent-assisted, manual, or hybrid).
