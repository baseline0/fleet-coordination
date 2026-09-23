# Checkpoint 2.1: Anomaly Reconciliation & CI Verification

**Purpose:** Resolve three anomalies discovered in Checkpoint 2 inventory before drafting the canonical policy.

**Estimated Time:** 1–2 hours  
**Deliverable:** Reconciliation table with package identities, dependency classifications, and CI status

---

## Task 1: Package Identity Verification (fleet-agents & fleet-spec)

**Issue:** Distribution name ≠ import root in two repos.

### fleet-agents
- **Declared Distribution:** `fleet-agents` (from pyproject.toml `project.name`)
- **Actual Import Root:** `tooling` (scanned from `src/`)
- **Question:** Is `tooling` the intended public import root, or a legacy/internal name?

### fleet-spec
- **Declared Distribution:** `fleet-spec`
- **Actual Import Root:** `fleet_experiment`
- **Question:** Is `fleet_experiment` the intended public import root, or temporary/experiment naming?

### Investigation Steps

Run these commands and capture output:

```bash
# 1. Verify declared distribution names
echo "=== fleet-agents distribution ===" && \
cd /home/mark/projects/fleet-agents && \
grep -A 1 "^name = " pyproject.toml && \
echo "=== fleet-spec distribution ===" && \
cd /home/mark/projects/fleet-spec && \
grep -A 1 "^name = " pyproject.toml

# 2. List all source package roots
echo "=== fleet-agents src/ contents ===" && \
ls -la /home/mark/projects/fleet-agents/src/ && \
echo "=== fleet-spec src/ contents ===" && \
ls -la /home/mark/projects/fleet-spec/src/

# 3. Confirm which package(s) are actually importable
echo "=== Test fleet-agents import ===" && \
cd /home/mark/projects/fleet-agents && \
python3 -c "import tooling; print(f'✅ tooling importable')" 2>&1 || echo "❌ tooling not importable" && \
python3 -c "import fleet_agents; print(f'✅ fleet_agents importable')" 2>&1 || echo "❌ fleet_agents not importable"

echo "=== Test fleet-spec import ===" && \
cd /home/mark/projects/fleet-spec && \
python3 -c "import fleet_experiment; print(f'✅ fleet_experiment importable')" 2>&1 || echo "❌ fleet_experiment not importable" && \
python3 -c "import fleet_spec; print(f'✅ fleet_spec importable')" 2>&1 || echo "❌ fleet_spec not importable"
```

### Deliverable

Fill in this row for the reconciliation table:

| Repository | Distribution (pyproject.toml) | Import Root(s) | Mapping Intentional? | Policy Note |
|---|---|---|---|---|
| fleet-agents | `fleet-agents` | `tooling` | ✅/❓ | e.g., "intentional; tooling is public API, fleet_agents is legacy" |
| fleet-spec | `fleet-spec` | `fleet_experiment` | ✅/❓ | e.g., "experimental; migrate to fleet_spec before v1.0" |

---

## Task 2: fleet-toolbox Dependency Investigation

**Issue:** Declares internal dependencies but scanner finds 0 imports.

### Declared Dependencies
```toml
dependencies = [
    "fleet-base @ file:///home/mark/projects/fleet-base",
    "fleet-agents @ file:///home/mark/projects/fleet-agents",
]
```

### Scanned Result
- Direct static imports: 0
- Potential non-static usage: undetermined

### Investigation Steps

```bash
cd /home/mark/projects/fleet-toolbox

# 1. Search for non-static imports (dynamic, plugin-style)
echo "=== Dynamic/plugin imports ===" && \
rg -n '(import_module|__import__|entry_points|importlib|load_entry_point)' src/ tests/

# 2. Search for fleet package references (by name, not import)
echo "=== References to fleet packages ===" && \
rg -n '(fleet.base|fleet.agents|fleet_base|fleet_agents)' src/ tests/ scripts/ . \
  -g '!uv.lock' -g '!*.egg-info' --type py

# 3. Check pyproject.toml for entry-points or plugin configs
echo "=== Plugin/entry-point configs ===" && \
grep -A 10 '\[project.entry-points\|tool.hatch.build.hooks' pyproject.toml

# 4. Check if dependencies are used in tests or build scripts
echo "=== Test files ===" && \
find tests/ -name "*.py" -type f | xargs grep -l 'fleet' 2>/dev/null | head -5

# 5. Check for optional/extras groups that may use these deps
echo "=== Optional dependencies ===" && \
grep -A 10 '\[project.optional-dependencies\|tool.uv.dependency-groups' pyproject.toml
```

### Deliverable

Classify each declared internal dependency:

| Repository | Dependency | Observed Usage | Classification | Action |
|---|---|---|---|---|
| fleet-toolbox | fleet-base | [output from search] | direct/test-only/plugin/reserved/stale | keep/remove/clarify |
| fleet-toolbox | fleet-agents | [output from search] | direct/test-only/plugin/reserved/stale | keep/remove/clarify |

**Classifications:**
- **Direct:** Source import exists; essential to package
- **Test-only:** Used only in `tests/`; not part of runtime
- **Plugin/MCP:** Used via entry-point, plugin discovery, or MCP interface registration
- **Reserved:** Intentionally declared but unused; needs documented owner and review date
- **Stale:** No usage found; should be removed in separate cleanup

---

## Task 3: import-linter CI Verification

**Issue:** 4/6 repos have `.importlinter` config; unclear if they're actually running in CI.

### Repos with Configs (Status Unknown)
- `fleet-base/.importlinter`
- `fleet-agents/.importlinter`
- `fleet-ops/.importlinter`
- `fleet-toolbox/.importlinter`

### Repos without Configs (Isolated)
- `fleet-coordination` (no .importlinter; zero fleet deps intended)
- `fleet-spec` (no .importlinter; zero fleet deps intended)

### Investigation Steps

```bash
# 1. Check GitHub Actions workflows for import-linter execution
echo "=== GitHub Actions workflows ===" && \
find /home/mark/projects/fleet-*/\
  .github/workflows/*.yml \
  -exec grep -l 'importlinter\|import.linter\|python.*-m.*importlinter' {} \; 2>/dev/null

# 2. Show the actual CI commands
for repo in fleet-base fleet-agents fleet-ops fleet-toolbox; do
  echo "=== $repo CI workflows ===" && \
  find /home/mark/projects/$repo/.github/workflows -name "*.yml" -type f -exec basename {} \; 2>/dev/null | sort || echo "(no workflows)"
done

# 3. Test each repo's .importlinter locally (clean environment)
for repo in fleet-base fleet-agents fleet-ops fleet-toolbox; do
  echo "=== Testing $repo locally ===" && \
  cd /home/mark/projects/$repo && \
  uv run python -m importlinter || echo "FAILED"
done

# 4. Check justfile for import-linter commands
echo "=== justfile commands containing 'import' or 'lint' ===" && \
for repo in fleet-*; do
  echo "--- $repo ---" && \
  grep -E 'lint|import' /home/mark/projects/$repo/justfile 2>/dev/null | head -3 || echo "(none)"
done
```

### Deliverable

Fill in this table for each repo with a `.importlinter` config:

| Repository | .importlinter Path | GitHub Workflow | CI Command | Local Test Result | Status |
|---|---|---|---|---|---|
| fleet-base | .importlinter | [workflow name] | `uv run python -m importlinter` | ✅/❌ | enforced/report-only/unknown |
| fleet-agents | .importlinter | [workflow name] | `uv run python -m importlinter` | ✅/❌ | enforced/report-only/unknown |
| fleet-ops | .importlinter | [workflow name] | `uv run python -m importlinter` | ✅/❌ | enforced/report-only/unknown |
| fleet-toolbox | .importlinter | [workflow name] | `uv run python -m importlinter` | ✅/❌ | enforced/report-only/unknown |

**Status Options:**
- **Enforced:** CI workflow explicitly runs import-linter on PRs/pushes; failure blocks merge
- **Report-only:** CI runs it but doesn't block; runs locally but not in CI
- **Unknown:** No evidence of CI execution; config exists but enforcement unclear

---

## Summary Deliverable: Reconciliation Table

Once all three tasks are complete, produce a summary table:

```markdown
| Repository | Distribution | Import Roots | Declared Fleet Deps | Import-Linter CI | Reconciliation Note |
|---|---|---|---|---|---|
| fleet-base | fleet-base | fleet_base | [] | ✅ enforced | Layer 0 isolation verified |
| fleet-agents | fleet-agents | tooling | [fleet-base] | ✅ enforced | Intentional: tooling is public API |
| fleet-coordination | fleet-coordination | (none) | [] | ❌ missing | Isolated; add .importlinter for explicit zero-dep rule |
| fleet-ops | fleet-ops | fleet_ops | [base, agents, toolbox] | ✅ enforced | Layer 1 deps verified |
| fleet-spec | fleet-spec | fleet_experiment | [] | ❌ missing | Isolated; naming TBD before 1.0; add .importlinter |
| fleet-toolbox | fleet-toolbox | toolboxes | [base, agents] | ✅ enforced | [Classification of toolbox deps from Task 2] |
```

---

## Next Steps

After Checkpoint 2.1 is complete:

1. **Policy Draft (Checkpoint 3):** Use reconciliation table as ground truth for `fleet-architecture.yaml` v0.1.0
2. **import-linter Decisions:** Add configs to fleet-coordination and fleet-spec (Increment 2)
3. **Package Naming:** If fleet-agents/fleet-spec mappings are intentional, document in policy; if not, plan a separate naming cleanup
4. **Dependency Cleanup:** If fleet-toolbox dependencies are stale, remove them in a separate PR

---

## Instructions for Submission

When complete, reply with:

1. **Task 1 Output:** Package identity verification results (distribution/import-root confirmation)
2. **Task 2 Output:** fleet-toolbox dependency investigation and classification
3. **Task 3 Output:** import-linter CI verification and enforcement status
4. **Summary Table:** Reconciliation table ready for policy draft

Format as markdown blocks or code blocks for easy copy-paste into Checkpoint 3 planning.
