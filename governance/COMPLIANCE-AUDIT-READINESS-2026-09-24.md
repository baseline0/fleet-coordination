# Fleet Compliance Audit Readiness Design
## Reconciliation & Recurring Audit Plan

**Date:** 2026-09-24  
**Status:** Design (pre-implementation)  
**Objective:** Design recurring compliance audit task dispatcher based on existing canonical standard and pilot evidence.

---

## Current State Summary

### Canonical Authority (Existing)
- **Location:** `fleet-coordination/governance/`
- **compliance-standard.yaml** (v0.1.0, 2026-09-23): 7 controls, 4 repository roles, deterministic evidence criteria
- **compliance-audit-agent.md** (v0.1.0, 2026-09-23): Read-only audit contract, output schema, classification rules
- **fleet-architecture.yaml** (v1.0.0): 6 repositories, 4 layers, import-boundary enforcement active

### Pilot Evidence (Completed)
- **fleet-agents** audited 2026-09-23: test_execution (pass), error_boundary_review (partial)
- **Audit results:** YAML evidence records + Markdown summaries in `compliance-audit-results/`
- **Post-pilot status:** Standard produces specific, fair findings; ready for fleet-wide rollout

### Standards Reference
- **fleet-base/docs/STANDARDS.md** (1390 lines): Human-oriented engineering reference
  - Agentic governance framework (layers, personas, constraints)
  - Code-as-docs philosophy
  - Python patterns, testing strategy, periodic-agent model

---

## Repository Compliance Inventory

### Control Applicability Matrix

| Repository | Role | Applicable Controls | Audit Status |
|---|---|---|---|
| fleet-base | foundation | package_install, test_execution, import_boundary_check, repository_metadata, governance_schema_validation | *Pending* |
| fleet-coordination | foundation | package_install, test_execution, import_boundary_check, repository_metadata, governance_schema_validation | *Not yet scoped* |
| fleet-ops | orchestration | package_install, test_execution, import_boundary_check, repository_metadata, error_boundary_review | *Not yet scoped* |
| fleet-agents | agent_library | package_install, test_execution, import_boundary_check, error_boundary_review | **Audited 2026-09-23** |
| fleet-toolbox | agent_library | package_install, test_execution, import_boundary_check, error_boundary_review | *Not yet scoped* |
| fleet-spec | standards | package_install, repository_metadata, standards_validation | *Not yet scoped* |

### Known Findings

#### fleet-base (Not Yet Audited)

**Governance Format Mismatch**
- **Status:** Migration candidate (not noncompliance)
- **Finding:** Document-only `.fleet/` structure vs. structured YAML in other repos
- **Context:** fleet-base is Layer 0 foundational; may have valid exception for governance format
- **Evidence Needed:** Explicit standard language defining acceptable governance representations for Layer 0

**Proposed Resolution**
- Classify fleet-base structure as valid exception (Layer 0 may use documentation-primary format)
- OR: Migrate to structured `.fleet/` format matching other repos
- **Decision Gate:** Requires explicit standard amendment if exception is valid

#### fleet-agents (Pilot Complete)

**test_execution:** ✅ Pass
- Tests exist, organized by marker (unit/integration)
- Declared test command available and executable
- CI executes tests per commit
- Coverage known

**error_boundary_review:** ⚠️ Partial (Post-Remediation)
- **Total handlers classified:** 89 (pre-remediation discovery universe)
- **Classification breakdown (pre-remediation):**
  - 20 identified as silent-failure risks
  - 48 classified as acceptable boundaries
  - 21 classified as best-effort
- **Post-remediation status:** Focused remediation on 6 highest-consequence handlers completed; 14 deferred for later investigation
- **Evidence:** See `compliance-audit-results/fleet-agents-2026-09-23-FINAL-post-remediation.yaml` and `.md` for full classification record
- **Status:** Pilot validation complete; ready to expand handler classification to fleet-ops and fleet-toolbox

---

## Control Readiness Assessment

### Control Evidence Resolution (Command Discovery Required)

Commands are **not** assumed fleet-wide. Each repository declares its control evidence method in `.fleet/` governance metadata or CLAUDE.md.

**Evidence Resolution Rule:**
```yaml
evidence_resolution:
  process:
    1. Query repository's declared control command (e.g., .fleetconfig.yaml)
    2. If not found, query CLAUDE.md for project-specific execution
    3. If not found, control result is UNKNOWN with limitation
  outcome: pass | fail | unknown | not_applicable
```

### Ready for Phase 1A Pilot (Narrow Scope)

**✅ repository_metadata** (High Confidence, Deterministic)
- Evidence: Repository listed in governance/fleet-architecture.yaml with current role and valid entry
- Evidence Resolution: Query fleet-architecture.yaml; validate required fields present
- Result: pass/fail/unknown
- Confidence: high
- Automation: Deterministic YAML schema check

**✅ test_execution** (High Confidence, Executor + Review)
- Evidence: Declared test command executes successfully and produces exit code 0
- Evidence Resolution: Query repository's .fleet/config.yaml or CLAUDE.md for test_command
- Result: pass/fail/unknown/not_applicable
- Confidence: high (execution itself), medium (coverage/adequacy assessment)
- Automation: Deterministic command resolution and subprocess execution; **coverage assessment is post-audit review**
- Limitation: "This control confirms declared test-command execution only; it does not assess test adequacy, coverage sufficiency, or architectural correctness."

### NOT Ready Yet (Require Further Evidence)

**⏳ package_install** (Candidate, Command Discovery Needed)
- Issue: `just check` is ambiguous; not equivalent to reproducible installation
- Evidence Needed: Each repo's declared installation command (e.g., `uv sync --locked`)
- Status: Defer to Phase 1B after test-execution evidence model validated

**⏳ import_boundary_check** (Candidate, Command Discovery Needed)
- Issue: `just check-imports` is not universal; single-module and non-Python repos have no boundary checks
- Evidence Needed: Declare per-repo via metadata or CLAUDE.md
- Status: Defer to Phase 1B; focus on `repository_metadata` first

**⏳ governance_schema_validation** (Foundation Only, Command Discovery Needed)
- Issue: Applies to foundation repos only; validation command must be discovered
- Status: Defer to Phase 1B; not needed for Phase 1A pilot

### Ready for Recurring Audit (Requires Review)

**⚠️ error_boundary_review** (Medium Confidence)
- Evidence: Individual handler classification (qualitative)
- Automation: Partial — grep for patterns, classify by context
- Limitation: Handler intent varies; requires code review
- Status: Pilot complete; ready for fleet-agents expansion; other repos TBD

**⚠️ standards_validation** (Medium Confidence, Spec-Only)
- Evidence: Standards documented, examples provided, standards repo complies
- Automation: Partial — can verify documentation exists; compliance assessment requires review
- Limitation: Subjective evaluation of "clarity" and "completeness"
- Status: Applies to fleet-spec only; not yet audited

---

## Control Crosswalk (Standards.md → Automation Readiness)

| STANDARDS.md Section | Control(s) | Automation Status | Notes |
|---|---|---|---|
| Agentic Governance Framework (layers, personas) | repository_metadata | ✅ Automated | Registry check |
| Code-as-Docs Philosophy | standards_validation | ⚠️ Partial | Applies to fleet-spec |
| Package Structure (src-layout) | package_install, governance_schema_validation | ✅ Automated | Validation tests exist |
| CLI & Justfile Pattern | test_execution | ✅ Automated | Test command deterministic |
| Python Version & Modern Patterns | test_execution | ✅ Automated | Ruff enforcement in CI |
| Pre-Commit Hooks | test_execution | ✅ Automated | Tests validate pre-commit |
| Testing Standards | test_execution | ✅ Automated | Marker validation deterministic |
| Periodic-Agent Operating Model | ❌ Not a control | — | Narrative governance guidance |
| Error Handling | error_boundary_review | ⚠️ Partial | Handler classification qualitative |
| Type Hints (Mandatory) | ❌ Not a control | — | Enforced by ruff in CI |
| Docstring Standards | ❌ Not a control | — | Code review + ruff |

---

## Standards Gaps & Conflicts

### Gap 1: Justfile Recipe Validation

**STANDARDS.md Requirement (CLI & Justfile Pattern):**
> "Requirement: If repo uses Typer, it must use fleet-base for auto-generation."

**Current Standard:** No control for justfile auto-gen validation  
**Applicability:** Typer-based repos (fleet-ops, fleet-agents, possibly others)  
**Severity:** Medium (enforcement exists in code, not in compliance standard)  
**Resolution Options:**
- Add `justfile_autogen_validation` control to standard
- OR: Add as sub-criterion to `test_execution` (tests validate auto-gen)
- OR: Remain narrative-only (STANDARDS.md governs; no recurring audit)

### Gap 2: Type Hints Coverage

**STANDARDS.md Requirement:**
> "Use type hints for Python functions (PEP 484)."
> "Ruff Configuration: select UP, RUF, SIM"

**Current Standard:** No quantitative control for type-hint coverage  
**Applicability:** All Python repositories  
**Enforcement:** Ruff linting in CI (not measured as compliance control)  
**Resolution Options:**
- Add `type_hints_coverage` control (% of functions typed)
- OR: Remain CI-enforced via ruff (no separate audit control)
- Recommendation: Remain CI-enforced (ruff is the authority)

### Gap 3: Pre-Commit Hook Configuration

**STANDARDS.md Requirement:**
> "Master Config (Each repo should have)"
> "Ruff format, ruff check, pytest, trailing-whitespace, end-of-file-fixer"

**Current Standard:** No control validating pre-commit hook presence  
**Applicability:** All Python repositories  
**Enforcement:** CI validates behavior (hooks' effects); not their presence  
**Resolution:** Remain narrative (STANDARDS.md); CI validates outcomes

### Conflict 1: fleet-base Governance Format

**Standard Language (repository_metadata):**
> "Repository is listed in governance/fleet-architecture.yaml with declared role."

**Interpretation:** fleet-base IS listed; role is "foundational_infrastructure"  
**Observed:** fleet-base has document-only `.fleet/` structure vs. structured YAML in other repos  
**Status:** Needs explicit amendment to standard clarifying Layer 0 format expectations

---

## fleet-base Disposition Decision

### Current Situation
- ✅ Listed in fleet-architecture.yaml with correct role
- ✅ Has .fleet/ directory with config.yaml, boundaries.md, catalog-info.yaml
- ⚠️ Uses markdown-primary structure; other repos use YAML-primary + markdown
- ✅ Passes package_install (uv sync works)
- ✅ Passes test_execution (just test runs, CI executes)
- ✅ Passes import_boundary_check (no Python package root, static checks used)
- ✅ Passes governance_schema_validation (governance module + tests exist)

### Decision Options

**Option A: Representation-Neutral Governance (Recommended)**
- Define the repository_metadata control as format-agnostic: "Governance declaration is present and machine-extractable."
- Acceptance Criteria: A repository satisfies the repository_metadata control when:
  - A valid role entry exists in governance/fleet-architecture.yaml (machine-readable authority)
  - A boundary/scope declaration is present (Markdown or YAML, extractable)
  - A catalog metadata entry exists (catalog-info.yaml per governance schema)
- Rationale: The control validates **semantic governance presence**, not artifact format uniformity
- Action: Amend compliance-standard.yaml to clarify format-neutral acceptance criteria
- Status: fleet-base compliant as-is (role declared, catalog valid)

**Option B: Uniform Structured Format**
- Migrate fleet-base to structured YAML-primary `.fleet/` governance
- Rationale: Uniformity simplifies tooling and discovery
- Action: Refactor .fleet/ artifacts in fleet-base to YAML-primary format
- Status: Requires implementation; currently uses Markdown-primary

**Recommendation:** Option A (Representation-Neutral)  
**Rationale:** The control must verify **semantic equivalence** (role declared, boundary declared, catalog present), not artifact format. This is testable, maintainable, and allows each repository to choose representation without compliance consequences.

---

## Phase 1A: Narrow Pilot Audit (Manual Only)

### Scope

**Repositories:** 2 (fleet-agents, fleet-ops)  
**Controls:** 2 (repository_metadata, test_execution)  
**Execution:** Manual invocation only (no scheduler)  
**Output:** Review-only (scratch/local results pending review)

**Why this scope:**
- **fleet-agents:** Existing pilot context; test-bearing repository
- **fleet-ops:** Orchestration role; likely different validation shape than agents
- **repository_metadata:** Validates role declaration and governance registry logic
- **test_execution:** Validates command resolution, subprocess execution, result capture, and evidence reporting

### Execution Model

1. **Resolve Control Evidence Per Repository**
   - Query `.fleet/config.yaml` or CLAUDE.md for declared commands
   - If not found, result is UNKNOWN (not failure)
   - Example: `test_execution` → look for `testing.test_command` in config.yaml

2. **Run Deterministic Checks**
   - Execute declared command in repository context
   - Capture exit code, stdout, stderr, execution timestamp
   - Record exact command, environment revision (git SHA)

3. **Render Evidence Record**
   - YAML structure: control_id, repository, role, applicable, result, confidence, evidence, limitations, next_step
   - Markdown summary: human-readable findings
   - Store locally (scratch) pending review

4. **No Mutations, No Scheduler**
   - Read-only audit only
   - Manual dispatch; do not write recurring schedule
   - Operator reviews output before any other action

### Output Schema (Per Control)

```yaml
control_id: test_execution
repository: fleet-ops
role: orchestration
applicable: true
result: pass | fail | unknown | not_applicable
confidence: high | medium | low
evidence:
  - source: ".fleet/config.yaml"
    output: "test_command: pytest tests/"
  - source: "command execution"
    output: "exit_code: 0, duration: 23s"
    timestamp: "2026-09-24T14:30:00Z"
    revision: "abc123def456"
limitations:
  - "Test execution result only; does not assess test adequacy or coverage sufficiency"
next_step: "review output and compare across two repositories"
```

### Phase 1A Success Criteria

After two manual audits (fleet-agents, fleet-ops):

- [ ] Commands resolve correctly from repository metadata
- [ ] Execution output is captured reliably
- [ ] False positives identified and root-caused
- [ ] Unknown/not_applicable outcomes handled correctly
- [ ] Evidence is machine-readable and human-reviewable
- [ ] No unexpected timeout or cancellation issues
- [ ] Operator can understand findings without prompting

---

## Phase 1B, 1C, 2+ (Deferred)

**Do not authorize until Phase 1A audit output is reviewed:**

- **Phase 1B:** Add 3 more controls (package_install, import_boundary_check, governance_schema_validation) after command resolution evidence validated
- **Phase 1C:** Write reviewed canonical audit records (durable storage)
- **Phase 2:** Error_boundary_review narrative handler classification
- **Phase 3+:** Recurring schedule, dashboard, or CI policy (requires real run history and explicit decision)

---

## Implementation Roadmap (Phase 1A)

### Phase 1A: Narrow Audit Runner (Manual Invocation)

**Increment 1: Command Resolution & Execution**
- Implement audit runner: parse `.fleet/config.yaml` for declared test_command
- Resolver fallback: CLAUDE.md project-specific settings
- Execute declared command, capture exit code/output/timestamp
- Output: local YAML evidence record + Markdown summary

**Increment 2: Operator Review & Adjustment**
- Run 1 (manual): Audit fleet-agents (existing context)
- Review output: Are commands resolving? Is evidence clear?
- Adjust evidence schema or resolver logic if needed
- Run 2 (manual): Audit fleet-ops
- Compare outputs; identify patterns and missing evidence

**Increment 3: Design Amendment**
- Incorporate findings into compliance-standard.yaml (if needed)
- Update control semantics (e.g., clarify test_execution scope)
- Document resolved evidence queries (YAML paths, fallbacks)

### Phase 1B (Deferred)

**After Phase 1A success:**
- Add 3 more controls (package_install, import_boundary, schema validation)
- Prove command resolution and evidence collection across these
- Do not combine 5 controls in initial implementation

### Phase 2+ (Deferred)

- Error boundary review narrative classification
- Recurring schedule (only after real audit history)
- Dashboard/TUI integration (not before)

---

## Standards Amendment Checklist (Phase 1A)

**Before Phase 1A Implementation:**

- [ ] Amend `compliance-standard.yaml` to clarify repository_metadata control as representation-neutral (YAML or Markdown acceptable if semantically complete)
- [ ] Clarify test_execution control scope: "execution result only; does not assess test adequacy"
- [ ] Document evidence resolution process: declared command → fallback to CLAUDE.md → UNKNOWN (not failure)

**After Phase 1A Review (Pre-Phase 1B):**

- [ ] Amend controls for package_install and import_boundary_check based on command-resolution evidence
- [ ] Add explicit evidence paths for each control (YAML queries, grep patterns)
- [ ] Document not_applicable vs. unknown semantics per control

**Optional (Later Phases):**

- [ ] Add error_boundary_review handler classification guidance
- [ ] Add standards-validation assessment rubric for fleet-spec
- [ ] Document promotion criteria for controls from report-only to CI-enforced (after recurring audit history)

---

## Output: Phase 1A Audit Runner (Manual Invocation)

```python
# Pseudocode: Phase 1A audit execution

audit(
    repositories=["fleet-agents", "fleet-ops"],
    controls=["repository_metadata", "test_execution"],
    output_format="local-scratch",  # YAML + Markdown
    output_dir="/tmp/compliance-audit-results",  # Pending review
    execution_mode="manual",  # No scheduler
    mutations_allowed=False,  # Read-only only
)
```

## Green-Light Conditions (Phase 1A Approval)

Before implementation, confirm:

- [ ] A per-repository control-command resolution rule exists (declared command → fallback → UNKNOWN)
- [ ] Control semantics corrected: environment installation separate from test execution
- [ ] No unsupported universal `just` command assumptions
- [ ] fleet-agents handler counts reconciled and pre/post-remediation evidence linked
- [ ] A representation-neutral, field-based fleet-base governance rule (semantic equivalence, not format)
- [ ] No scheduler or cancellation/timeout experiment in Phase 1A
- [ ] Manual two-repo/two-control pilot as the only authorized scope
- [ ] `unknown` and `not_applicable` outcomes for unavailable/non-applicable evidence (not inferred failure)

---

## Next Steps (Sequential)

1. **Approve Phase 1A Design** — Confirm corrections, narrow scope, manual-only execution
2. **Amend Canonical Standard** — Update compliance-standard.yaml (representation-neutral repository_metadata, test_execution scope clarification)
3. **Implement Phase 1A Runner** — Command resolver, executor, evidence formatters
4. **Execute Phase 1A Audits** — Manual runs on fleet-agents, fleet-ops
5. **Review Phase 1A Output** — Validate evidence, identify false positives, adjust semantics
6. **Propose Phase 1B** — Only after Phase 1A audit output reviewed

---

**Phase 1A ready for implementation approval?**
