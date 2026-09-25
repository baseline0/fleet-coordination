# Bounded Remediation Plan: live_dashboard_v2.py

**Target:** Make telemetry extractor failures distinguishable from valid empty results  
**Scope:** 6 exception handlers in fleet-agents `src/tooling/tui/live_dashboard_v2.py`  
**Lines:** 274, 348, 363, 379, 409, 412  
**Priority:** High (operator telemetry reliability)  
**Status:** Planned (awaiting implementation authorization)  
**Repository:** fleet-agents  
**Revision at Planning:** (To be filled at implementation start)

---

## Behavioral Boundary (What This Changes)

**Single objective:**  
Make live-dashboard telemetry extraction report its data-quality state without changing remediation execution, fleet dispatch, dashboard authorization, or unrelated error-handling behavior.

**Operator impact:**  
Dashboard metrics now distinguish "no data found" from "data source failed." Operator can detect incomplete telemetry and investigate root cause.

**Not authorized (scope exclusions):**
- Do not change dispatch behavior or agent execution
- Do not mutate fleet repositories
- Do not expand to enhanced_remediation.py or repo_eval.py
- Do not refactor non-telemetry exception handling
- Do not change dashboard metric definitions except for error-state labeling
- Do not alter historical audit records

---

## Current State (Silent Failures)

| Method | Line | Current Behavior | Problem |
|--------|------|------------------|---------|
| `load_current_run()` | 274 | `except Exception: return False` | Caller can't distinguish error from no data |
| `_load_recent_runs()` | 348 | `except Exception: continue` | File errors silently skipped in loop |
| `_extract_repos()` | 363 | `except Exception: pass` | Returns `[]` on file error; ambiguous |
| `_extract_fixes()` | 379 | `except Exception: pass` | Returns `0` on error; ambiguous |
| `_extract_duration()` | 409 | `except Exception: return 0` | Parse error looks like "no duration"; ambiguous |
| `_extract_duration()` | 412 | `except Exception: pass` | Outer catch; hides all errors |

**Impact:** Dashboard metrics are unreliable when file I/O or JSON parsing fails silently. Operator cannot tell if "0 repos" means "no repos processed" or "file read failed."

---

## Target State (Distinguishable Outcomes)

Use a state-based result type with explicit status enum:

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TelemetryStatus(StrEnum):
    """Status of a telemetry extraction."""
    OK = "ok"  # Extraction succeeded with data
    EMPTY = "empty"  # Extraction succeeded; no matching data in source
    UNAVAILABLE = "unavailable"  # Source file not found or not available
    FAILED = "failed"  # Extraction attempted but failed (parse error, permission, etc.)
    PARTIAL = "partial"  # Some sources succeeded; others failed


@dataclass(frozen=True)
class TelemetryResult:
    """Result of a telemetry extraction operation.
    
    Attributes:
        status: Extraction outcome (ok, empty, unavailable, failed, partial)
        value: Extracted value if status is ok or empty; None otherwise
        error: Error message if status is failed or partial; None otherwise
        source: Data source identifier for debugging (file path, etc.)
    """
    status: TelemetryStatus
    value: Any | None = None
    error: str | None = None
    source: str | None = None
```

**State semantics:**

| Status | Meaning | Operator Display | Example | Caller Action |
|--------|---------|------------------|---------|----|
| `ok` | Extraction completed with usable data | Normal metric | 12 repositories found | Use value |
| `empty` | Extraction succeeded; no matching data | Zero / "none" | No records in time window | Use value (zero/empty) |
| `unavailable` | Source cannot be read or does not exist | "Unavailable" | Optional history file absent | Skip metric or show "N/A" |
| `failed` | Extraction attempted but failed | "Incomplete—error" | Invalid JSON, permission error | Log warning; skip metric |
| `partial` | Some sources succeeded; others failed | "Incomplete—partial" | 4 of 5 files parsed | Log warning; use partial value |

---

## Implementation Steps

### Step 1: Define Result Type
**File:** `src/tooling/tui/live_dashboard_v2.py`

Add at top after imports:

```python
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TelemetryStatus(StrEnum):
    """Status of telemetry extraction."""
    OK = "ok"
    EMPTY = "empty"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass(frozen=True)
class TelemetryResult:
    """Result of telemetry extraction with status indicator.
    
    Attributes:
        status: Extraction outcome
        value: Extracted data if status is ok/empty; None for failed/partial
        error: Error message if status is failed; description if partial
        source: Data source for debugging (file path, component name)
    """
    status: TelemetryStatus
    value: Any | None = None
    error: str | None = None
    source: str | None = None
```

### Step 2: Refactor load_current_run()
**Lines:** 274–275

Replace `except Exception: return False` with specific exception handling:

```python
except FileNotFoundError:
    # Run log doesn't exist yet (expected at startup)
    self.current_run = None
    self.start_time = None
    return False
except OSError as e:
    logger.warning(f"Failed to read run log (OS error): {e}")
    return False
except json.JSONDecodeError as e:
    logger.warning(f"Corrupted run log entry: {e}")
    return False
except Exception as e:
    logger.error(f"Unexpected error reading run log: {e}")
    return False
```

**Why:** Distinguish file-not-found (expected at startup) from OS/permission errors vs. JSON corruption. Enables debugging.

### Step 3: Refactor _load_recent_runs()
**Lines:** 348–349

Replace `except Exception: continue` with:

```python
except FileNotFoundError:
    continue
except json.JSONDecodeError as e:
    logger.warning(f"Corrupted run file {run_file}: {e}; skipping")
    continue
except OSError as e:
    logger.warning(f"Cannot read run file {run_file}: {e}; skipping")
    continue
except Exception as e:
    logger.error(f"Unexpected error processing {run_file}: {e}; skipping")
    continue
```

### Step 4: Refactor _extract_repos()
**Lines:** 363–364

Refactor return type and exception handling:

```python
def _extract_repos(self, run_file: Path) -> TelemetryResult:
    """Extract unique repos from run file.
    
    Returns:
        TelemetryResult with status indicating success/failure
    """
    repos = set()
    try:
        with open(run_file) as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if "repo" in event:
                        repos.add(event["repo"])
                except json.JSONDecodeError:
                    continue
        
        if not repos:
            return TelemetryResult(status=TelemetryStatus.EMPTY, value=[])
        return TelemetryResult(status=TelemetryStatus.OK, value=list(repos))
    
    except FileNotFoundError:
        return TelemetryResult(
            status=TelemetryStatus.UNAVAILABLE,
            value=[],
            source=str(run_file),
        )
    except OSError as e:
        return TelemetryResult(
            status=TelemetryStatus.FAILED,
            value=[],
            error=f"Cannot read {run_file.name}: {e}",
            source=str(run_file),
        )
    except Exception as e:
        return TelemetryResult(
            status=TelemetryStatus.FAILED,
            value=[],
            error=f"Unexpected error extracting repos: {e}",
            source=str(run_file),
        )
```

### Step 5: Refactor _extract_fixes()
**Lines:** 379–380

Similar structure to _extract_repos:

```python
def _extract_fixes(self, run_file: Path) -> TelemetryResult:
    """Extract total fixes from run file."""
    total = 0
    try:
        with open(run_file) as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if "fixes_applied" in event:
                        total += event["fixes_applied"]
                except json.JSONDecodeError:
                    continue
        
        if total == 0:
            return TelemetryResult(status=TelemetryStatus.EMPTY, value=0)
        return TelemetryResult(status=TelemetryStatus.OK, value=total)
    
    except FileNotFoundError:
        return TelemetryResult(
            status=TelemetryStatus.UNAVAILABLE,
            value=0,
            source=str(run_file),
        )
    except OSError as e:
        return TelemetryResult(
            status=TelemetryStatus.FAILED,
            value=0,
            error=f"Cannot read {run_file.name}: {e}",
            source=str(run_file),
        )
    except Exception as e:
        return TelemetryResult(
            status=TelemetryStatus.FAILED,
            value=0,
            error=f"Unexpected error extracting fixes: {e}",
            source=str(run_file),
        )
```

### Step 6: Refactor _extract_duration()
**Lines:** 409–410, 412–413

```python
def _extract_duration(self, run_file: Path) -> TelemetryResult:
    """Calculate run duration from first and last event timestamps."""
    try:
        with open(run_file) as f:
            lines = f.readlines()

        if len(lines) < 2:
            return TelemetryResult(
                status=TelemetryStatus.UNAVAILABLE,
                value=0.0,
                source=str(run_file),
            )

        first_event = None
        last_event = None

        for line in lines:
            try:
                event = json.loads(line.strip())
                if not first_event:
                    first_event = event
                last_event = event
            except json.JSONDecodeError:
                continue

        if not first_event or not last_event:
            return TelemetryResult(
                status=TelemetryStatus.UNAVAILABLE,
                value=0.0,
                source=str(run_file),
            )

        try:
            t1 = datetime.fromisoformat(first_event.get("timestamp", "").replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(last_event.get("timestamp", "").replace("Z", "+00:00"))
            duration = (t2 - t1).total_seconds()
            return TelemetryResult(status=TelemetryStatus.OK, value=duration)
        except (ValueError, TypeError) as e:
            return TelemetryResult(
                status=TelemetryStatus.FAILED,
                value=0.0,
                error=f"Invalid timestamps: {e}",
                source=str(run_file),
            )
    
    except FileNotFoundError:
        return TelemetryResult(
            status=TelemetryStatus.UNAVAILABLE,
            value=0.0,
            source=str(run_file),
        )
    except OSError as e:
        return TelemetryResult(
            status=TelemetryStatus.FAILED,
            value=0.0,
            error=f"Cannot read {run_file.name}: {e}",
            source=str(run_file),
        )
    except Exception as e:
        return TelemetryResult(
            status=TelemetryStatus.FAILED,
            value=0.0,
            error=f"Unexpected error extracting duration: {e}",
            source=str(run_file),
        )
```

### Step 7: Update Callers
**In `_load_recent_runs()`**

```python
repos_result = self._extract_repos(run_file)
fixes_result = self._extract_fixes(run_file)
duration_result = self._extract_duration(run_file)

run_summary = {
    "run_id": run_file.name,
    "timestamp": last_line.get("timestamp", ""),
    "status": last_line.get("status", "unknown"),
    "repos": repos_result,  # Store full result
    "fixes": fixes_result,  # Store full result
    "duration": duration_result,  # Store full result
}

# Detect if any extraction failed
errors = [
    r.error for r in [repos_result, fixes_result, duration_result]
    if r.status == TelemetryStatus.FAILED
]
if errors:
    run_summary["data_quality_issues"] = errors
```

### Step 8: Add Regression Tests
**File:** `tests/integration/test_live_dashboard_v2.py`

Behavior-based test suite:

```python
@pytest.mark.unit
def test_extract_repos_ok_returns_ok_status():
    """Valid extraction returns ok status with data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text('{"repo": "foo"}\n{"repo": "bar"}\n')
        
        dashboard = LiveDashboardV2()
        result = dashboard._extract_repos(run_file)
        assert result.status == TelemetryStatus.OK
        assert set(result.value) == {"foo", "bar"}

@pytest.mark.unit
def test_extract_repos_empty_returns_empty_status():
    """File with no repos returns empty status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text('{"step": "lint"}\n{"agent": "fixer"}\n')
        
        dashboard = LiveDashboardV2()
        result = dashboard._extract_repos(run_file)
        assert result.status == TelemetryStatus.EMPTY
        assert result.value == []

@pytest.mark.unit
def test_extract_repos_missing_file_returns_unavailable():
    """Missing file returns unavailable status."""
    dashboard = LiveDashboardV2()
    result = dashboard._extract_repos(Path("/nonexistent/run.jsonl"))
    assert result.status == TelemetryStatus.UNAVAILABLE
    assert result.value == []

@pytest.mark.unit
def test_extract_repos_permission_error_returns_failed():
    """Permission error returns failed status with error message."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text('{"repo": "foo"}\n')
        run_file.chmod(0o000)  # Remove read permissions
        
        try:
            dashboard = LiveDashboardV2()
            result = dashboard._extract_repos(run_file)
            assert result.status == TelemetryStatus.FAILED
            assert result.error is not None
            assert result.value == []
        finally:
            run_file.chmod(0o644)  # Restore permissions for cleanup

@pytest.mark.unit
def test_extract_duration_ok_returns_ok_status():
    """Valid duration extraction returns ok status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text(
            '{"timestamp": "2026-09-23T10:00:00Z"}\n'
            '{"timestamp": "2026-09-23T10:05:00Z"}\n'
        )
        
        dashboard = LiveDashboardV2()
        result = dashboard._extract_duration(run_file)
        assert result.status == TelemetryStatus.OK
        assert result.value == 300.0  # 5 minutes

@pytest.mark.unit
def test_extract_duration_invalid_timestamps_returns_failed():
    """Invalid timestamp format returns failed status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text(
            '{"timestamp": "not-a-timestamp"}\n'
            '{"timestamp": "also-invalid"}\n'
        )
        
        dashboard = LiveDashboardV2()
        result = dashboard._extract_duration(run_file)
        assert result.status == TelemetryStatus.FAILED
        assert result.error is not None
        assert result.value == 0.0

@pytest.mark.unit
def test_extract_fixes_ok_returns_ok_status():
    """Valid fixes extraction returns ok status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text('{"fixes_applied": 3}\n{"fixes_applied": 2}\n')
        
        dashboard = LiveDashboardV2()
        result = dashboard._extract_fixes(run_file)
        assert result.status == TelemetryStatus.OK
        assert result.value == 5

@pytest.mark.unit
def test_extract_fixes_empty_returns_empty_status():
    """File with no fixes returns empty status."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_file = Path(tmpdir) / "run.jsonl"
        run_file.write_text('{"step": "verify"}\n{"agent": "checker"}\n')
        
        dashboard = LiveDashboardV2()
        result = dashboard._extract_fixes(run_file)
        assert result.status == TelemetryStatus.EMPTY
        assert result.value == 0
```

---

## Acceptance Criteria

**Behavior-Based Contract:**

- [ ] Every targeted telemetry extraction method returns a TelemetryResult
- [ ] TelemetryResult.status is one of: ok, empty, unavailable, failed, partial
- [ ] Valid empty data (e.g., no repos in time window) returns **empty** status, not error
- [ ] Missing optional source (e.g., file not found) returns **unavailable** status, not failed
- [ ] Malformed, unreadable, or parse-failed source returns **failed** status with error message
- [ ] Callers check result.status before using result.value
- [ ] Dashboard displays data-quality indicators: "⚠️ Incomplete" when status is failed/partial
- [ ] Targeted exception paths have regression tests (8+ tests covering ok, empty, unavailable, failed, partial)
- [ ] Existing dashboard functionality remains compatible for ok/empty status values
- [ ] All existing tests continue to pass
- [ ] No changes to dispatch logic, fleet mutation, or other exception handling
- [ ] Post-remediation audit records the outcome with evidence

---

## Rollback Plan

If remediation causes regression:
1. Revert methods to previous implementation
2. Restore original return types (bare list/int/float)
3. Re-run full test suite
4. Report findings to audit

---

## Expected Effort

- **Implementation:** 2–3 hours (refactor 6 methods, update result types)
- **Testing:** 1–2 hours (add 8+ focused regression tests)
- **Verification:** 30 minutes (run full suite, manual dashboard test)
- **Post-remediation audit:** 30 minutes (re-assess error_boundary_review control)
- **Total:** 4–5.5 hours

---

## After Completion

1. ✓ Implement and test
2. ✓ Verify full test suite passes
3. ✓ Run manual dashboard test
4. ✓ Re-audit live_dashboard_v2.py with error_boundary_review control
5. **Do NOT** attempt enhanced_remediation.py or repo_eval.py yet
6. Review whether remediation was effective
7. Document findings and decide next steps

---

## Related Governance Artifacts

- **Evidence Record:** `fleet-agents-2026-09-23.yaml` (pilot audit)
- **Compliance Standard:** `compliance-standard.yaml` (error_boundary_review control)
- **Audit History:** `AUDIT-HISTORY.md` (transition from scorecard to evidence-based controls)
- **Post-Remediation Reassessment:** (To be recorded after implementation)

---

**Plan Created:** 2026-09-23  
**Authorized by:** Compliance Audit (pilot phase)  
**Status:** Ready for implementation authorization  
**Assessment Mode:** Subagent (not fleet-ops dispatch)  
**Durable Location:** fleet-coordination/governance/remediation-plans/
