# Fleet-Coordination TODO

**Focus:** Compliance infrastructure is at a sustainable stopping point. Returning to Morning Review Phase 2 (thin Typer CLI wiring).

---

## Strategic Review: Fleet Operating Model (20–40 Repo Scale)

**Goal:** Assess and formalize the `.fleet/` folder structure, governance model, and operating cadence for a 20–40 repository portfolio.

**Context:** As the fleet grows beyond a handful of repos, repeatable governance, consistent structure, and automated health checks become critical. This review synthesizes best practices from GitHub, GitLab, and industry guidance on repository portfolio management.

**Scope (comprehensive assessment):**

1. **Portfolio Inventory & Metadata** ([see guidance](pasted_content_686e))
   - [ ] Current `.fleet/` structure and content in each repo
   - [ ] Repository catalog (source of truth: YAML/JSON or internal portal?)
   - [ ] Ownership, lifecycle, business domain, criticality, tier assignments
   - [ ] Dependency and consumer relationships mapped

2. **Repository Contract & Standards**
   - [ ] README template and baseline quality (ownership, lifecycle, runbook, architecture)
   - [ ] CODEOWNERS and code-review enforcement
   - [ ] CONTRIBUTING.md, SECURITY.md, CHANGELOG/release-notes conventions
   - [ ] Architecture decision records (ADRs) or runbook patterns
   - [ ] Consistency of naming (repos, branches, tags, labels, releases)

3. **Governance & Automation**
   - [ ] Branch protection rules (PR requirement, CI gates, review signoff, `CODEOWNERS` integration)
   - [ ] CI/CD patterns (reusable workflows, parallel jobs, caching, artifact handling)
   - [ ] Dependency management (Dependabot/Renovate, patch vs. major update policy)
   - [ ] Secret scanning and vulnerability scanning enabled fleet-wide
   - [ ] Repository provisioning and template pipeline

4. **Operating Cadence & Metrics**
   - [ ] Weekly/biweekly review process (blocked PRs, main-branch health, vulnerabilities, stale branches)
   - [ ] Monthly health report (ownership, CI reliability, dependency freshness, runtime EOL exposure)
   - [ ] Quarterly checkpoints (ownership confirmation, lifecycle re-assessment, access review, boundary review)
   - [ ] Key metrics tracked (build success rate, CI duration, PR lag time, vulnerability age, deployment frequency)

5. **Repository Boundary Decisions**
   - [ ] Polyrepo vs. monorepo rationale documented
   - [ ] Criteria for splitting/consolidating repositories clear
   - [ ] Tightly coupled repos identified (candidates for shared CI, coordinated releases)

**Deliverables:**
- Formalized `.fleet/` schema (config.yaml, catalog-info.yaml, governance.yaml)
- Fleet inventory (repo metadata, ownership, lifecycle state) in YAML or catalog format
- Repository golden-path template with baseline files, labels, CI, and policies
- Operating cadence checklist (weekly, monthly, quarterly review templates)
- Health dashboard or metric collection process (even simple: dashboard.yaml or script)
- Documentation: repo boundaries rationale, ownership model, exception process

**Done when:**
- `.fleet/` structure is consistent across 3+ sample repos
- Fleet inventory (at least 10 repos) is accurate and traceable
- Golden-path template is adopted for next new repo
- One end-to-end operating cadence cycle completed (e.g., first monthly health review)

**Effort:** 6–8 hours (one-time setup; ongoing cadence is ~2 hours/month)

**Acceptance:** A new engineer can open *any* repository in the fleet and within 5 minutes know: what it does, who owns it, how to change it, how it is released, and whether it is healthy.

---

## Compliance Backlog (Non-Blocking)

These are valid tasks but do not block Morning Review:

### Maintenance: Initialize fleet-spec governance
- **Priority:** Next small maintenance task (depends on Strategic Review above for schema decisions)
- **Scope:** Add `.fleet/` directory to fleet-spec with formalized schema
- **Done when:** governance_schema_validation control passes; `.fleet/` files match Strategic Review schema
- **Files:** `.fleet/config.yaml`, `.fleet/catalog-info.yaml`, `.fleet/governance.yaml` (schema TBD from Strategic Review)
- **Effort:** 30 minutes (after Strategic Review defines schema)
- **Related:** Strategic Review (section above) will define `.fleet/` structure, ownership model, and operating cadence

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

### Investigation: AI Testing & Governance Framework Alignment (NIST AI RMF)
- **Priority:** Strategic/governance review
- **Scope:** Document evidence-generating, bounded evaluation approach for AI-assisted development:
  - Explicit evaluation limits (e.g., "Pass@1 ≥ 90%" for delegation decisions)
  - Pre-registered test sets and batch parameters (deterministic acceptance criteria)
  - Safety-decline monitoring (track degradation patterns, not one-time approval)
  - Repeatable evaluation processes (documented metrics, test harness, audit trail)
  - Ongoing monitoring vs. one-time sign-off (continuous governance stance)
  - Alignment with NIST AI RMF: risk management framework for documented oversight
- **Why:** Current agent delegation logic (Ollama vs Claude cost-optimization) uses ad-hoc Pass@1 targets. Formalize as disciplined test strategy with reproducible decision gates.
- **Output:** Governance memo or ADR documenting evaluation framework for fleet AI tooling
- **Effort:** 3-4 hours (research NIST AI RMF + document strategy)

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
