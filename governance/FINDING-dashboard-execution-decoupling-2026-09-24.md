# Architectural Finding: Dashboard Execution Decoupling

**Date:** 2026-09-24  
**Discovery:** Pilot observation phase investigation  
**Status:** Deferred (separate initiative required for remediation)

---

## Finding

The live dashboard's telemetry source contract is not met by the observed production execution path.

## Observed State

| Component | Location | Behavior | Status |
|---|---|---|---|
| Dashboard telemetry reader | `src/tooling/tui/live_dashboard_v2.py:264, 372` | Reads per-run `run_*.jsonl` files from `~/.cache/agent-tooling/runs/` | **Files not produced by execution path** |
| Dashboard extraction functions | `src/tooling/tui/live_dashboard_v2.py:428–591` | Extract repos, fixes, duration by parsing JSONL | **No execution context available** |
| Telemetry logger | `src/run_logger.py:71–87` | `RunLogger.log_run()` writes to `runs.jsonl` | **Manual/CLI invocation only** |
| Execution dispatcher | `src/task_orchestrator.py:173–223` | `TaskOrchestrator.execute_pending_tasks()` calls `dispatcher.dispatch()` | **Does NOT call RunLogger** |
| Run identity propagation | `src/agent_dispatcher.py` vs `src/run_logger.py` | ExecutionResult has `run_id` (UUID); FleetRunLog accepts `run_id` (string) | **No data flow exists** |

## Evidence Chain

1. **No per-run writer exists:**
   - Searched `fleet-agents/src/` for `run_*.jsonl` writers
   - Found only test fixtures creating `run_*.jsonl` (test_live_dashboard_v2.py)
   - Filesystem inspection: `~/.cache/agent-tooling/runs/` contains only `runs.jsonl` and `dashboard.html`
   - Result: Dashboard expects files that are never produced

2. **Dashboard metrics are unconnected to dispatch:**
   - `TaskOrchestrator.execute_pending_tasks()` calls `dispatcher.dispatch()` (line 198)
   - Returns `ExecutionResult` with `run_id` and execution status
   - No subsequent call to `RunLogger.log_run()`
   - Result: Execution outcomes are not recorded to any log

3. **Manual `runs.jsonl` exists but separately:**
   - `RunLogger` writes to `runs.jsonl` via manual CLI commands (runs_cli.py, phase5e_tripwire.py)
   - Records have `run_id` field (schema supports it)
   - But values are created outside dispatch path
   - Result: `runs.jsonl` records are not causally linked to dispatched tasks

4. **No shared identifier across the gap:**
   - Dispatcher creates: `ExecutionResult(run_id=UUID('...'))`
   - Dashboard reads: `run_*.jsonl` (files that don't exist) or derives from filename
   - Manual logger records: `FleetRunLog(run_id="2026-09-16-0200")` (manual invocation)
   - Result: No way to correlate execution to telemetry

## Impact Assessment

| Scenario | Impact |
|---|---|
| Viewing dashboard metrics | Likely empty, stale, or only from manually-logged records |
| Correlating execution to metrics | Not possible; no shared identifier or causal path |
| Building operational efficacy evidence | Not possible; cannot establish which execution produced which telemetry |
| Dashboard as audit authority | Not safe; records lack provenance to dispatched execution |

## Confidence Level

**High** for the inspected source paths and filesystem state.

**Limited to** the repository/source scope examined; external dashboards or manual telemetry sources not investigated.

## Not Established

- Whether dispatcher was intentionally designed separate from dashboard
- Whether earlier (pre-v2) implementations had different architecture
- Whether dashboard is actively used or a legacy component
- Whether manual `runs.jsonl` records are sufficient for current operational needs

## Disposition

**Deferred.** Any repair requires:

1. An explicitly authorized initiative (separate from this remediation)
2. A clear problem statement: "Should dispatched agent execution produce a canonical run record that the dashboard consumes?"
3. Evidence collection: Is dashboard output operationally important? How often used?
4. Product/operational decision: Is the integration worth the implementation cost?
5. Acceptance criteria: What constitutes "correct" linking?
6. Migration plan: What happens to existing manual `runs.jsonl` records?
7. Integration tests: Prove execution → telemetry correlation works end-to-end

## Related Records

- **Pilot Closure:** `PILOT-CLOSURE-2026-09-23.md` (observation phase marked not instrumentable)
- **Remediation (Complete):** `compliance-audit-results/fleet-agents-2026-09-23-FINAL-post-remediation.md` (error boundary fix remains valid)
- **Dashboard Code (Reviewed):** `src/tooling/tui/live_dashboard_v2.py` (readers, not writers)
- **Telemetry Logger:** `src/run_logger.py` (manual invocation only)

## Future Initiative Template

If this finding becomes a priority, open a separate scoped initiative with this decision tree:

```text
Decision: Should dispatched agent execution produce a canonical run record
that the dashboard consumes, with one shared run_id and an explicit
ownership model?

If YES:
  1. Determine who owns the execution record (dispatcher? orchestrator? task boundary?)
  2. Design the run record schema and identity propagation
  3. Decide: TaskOrchestrator calls RunLogger, or new writer?
  4. Plan migration for manual runs.jsonl records
  5. Add integration tests (dispatch → execution → telemetry → dashboard)
  6. Update dashboard to read from authoritative source
  7. Retire/archive manual CLI runs logging

If NO:
  1. Clearly document why dashboard and execution are separate systems
  2. Update dashboard docs: what data sources are available, when
  3. Remove or deactivate the per-run file reader (run_*.jsonl lookup)
  4. Recommend dashboard users: use runs.jsonl or external telemetry
```

---

**This finding documents an architectural gap discovered during bounded pilot investigation. It does not authorize implementation or schedule work. Any response requires a separate decision and scoped initiative.**
