# Checkpoint 2 Evidence Manifest

**Collection Date:** 2026-09-23T11:48:41Z  
**Collector:** Claude (fleet-ops assistant)  
**Collection Tool:** collect_inventory.py (v0.1.0)

---

## Repository State at Collection Time

| Repository | Git SHA | Working State |
|---|---|---|
| fleet-base | bd6b4b31982a2869d86079d52f798264db6f3634 | Dirty (modified) |
| fleet-agents | dc6bf28ba45e61b4d32dba045ce82968eafa984c | Dirty (modified) |
| fleet-coordination | 392424180b5f4f06f54686f07741c31b7ab8ff3f | Dirty (modified + 4 untracked) |
| fleet-ops | bcd0d4fc4d9f151a1ff642ddd02997a08b7ddbe1 | Clean |
| fleet-spec | 849e0e8e76c519b4657033aea2afca0dfa8973d2 | Dirty (modified + 1 untracked) |
| fleet-toolbox | af960fc6fabb3d3677847177bec61b661ba2cf12 | Clean |

**Timestamp:** 2026-09-23T11:48:41Z UTC

---

## Evidence Files

### `inventory.json`
Raw machine-readable inventory output from `collect_inventory.py`.

**Structure:**
- Collection timestamp
- Per-repository metadata:
  - Git revision and working state
  - Package distribution name
  - Python import roots
  - `.fleet/` metadata file locations
  - Import-linter config presence
  - Declared fleet dependencies
  - Actual fleet imports (scanned)
  - CI entry points (workflows, justfile commands)

**Generation Command:**
```bash
python3 collect_inventory.py > inventory.json 2>&1
```

### `inventory-summary.md`
Human-readable analysis and classification of the raw inventory.

**Sections:**
- Quick facts table
- Key observations (distribution/import-root mismatch, import patterns, gaps)
- Evidence classification (no violations detected, metadata gaps, anomalies)
- Policy draft data extraction
- Checkpoint 2 approval questions

---

## Known Limitations & Observations

### Inventory Anomalies Requiring Reconciliation (Checkpoint 2.1)

1. **Distribution ≠ Import Root (fleet-agents, fleet-spec)**
   - `fleet-agents`: distributes as `fleet-agents`, imports from `tooling`
   - `fleet-spec`: distributes as `fleet-spec`, imports from `fleet_experiment`
   - Action: Verify intentionality; policy must normalize mapping

2. **fleet-toolbox: Declared Dependencies, Zero Imports**
   - Declares `fleet-base`, `fleet-agents`
   - Scanner finds 0 imports
   - Action: Investigate (dynamic imports, plugins, tests, CLI, or stale declaration)

3. **import-linter Coverage**
   - 4/6 repos have `.importlinter` config
   - fleet-coordination, fleet-spec lack enforcement
   - Action: Verify CI execution; decide on enforcement for isolated repos

### Scanner Limitations

- **Dynamic imports not detected** (e.g., `importlib.import_module()`)
- **Plugin/entry-point usage not detected** (consumed via registration, not import)
- **CLI/MCP/non-Python edges not scanned** (these are out of scope for import analysis)
- **Test-only and build-script imports** may be included or excluded depending on source root filtering

---

## Reconciliation Tasks (Checkpoint 2.1)

Before the policy draft, complete:

1. **Package Identity Verification**
   ```bash
   # For fleet-agents and fleet-spec: confirm distribution name and all import roots
   grep -A 2 "^name = " fleet-agents/pyproject.toml fleet-spec/pyproject.toml
   ls -la fleet-agents/src/ fleet-spec/src/
   ```

2. **fleet-toolbox Dependency Investigation**
   ```bash
   # Search for non-static import usage
   rg -n '(import_module|__import__|entry_points|importlib)' fleet-toolbox/src/
   rg -n '(fleet.base|fleet.agents)' fleet-toolbox/{src,tests,scripts,}/**/*.py
   ```

3. **import-linter CI Verification**
   - Check GitHub Actions workflows for import-linter execution
   - Run `python -m importlinter` locally per repo
   - Document per-repo CI command and pass/fail state

---

## Files in This Checkpoint

```
governance/evidence/checkpoint-2/
├── MANIFEST.md                    (this file)
├── inventory.json                 (350 lines, machine-readable)
├── inventory-summary.md           (analysis & classification)
└── (generated policy schema ref, once drafted)

governance/tools/
└── collect_inventory.py           (collection script, v0.1.0)
```

---

## Reproducibility

To re-run the inventory collection:

```bash
cd /home/mark/projects
python3 fleet-coordination/governance/tools/collect_inventory.py > \
  fleet-coordination/governance/evidence/checkpoint-2/inventory-latest.json
```

Then compare with the baseline `inventory.json` to detect drift.

---

## Next Checkpoint

**Checkpoint 2.1:** Anomaly reconciliation and import-linter CI verification.  
**Expected Output:** Reconciliation table with package identities, dependency classifications, and CI status per repo.

---

## Sign-Off

✅ **Checkpoint 2 Complete**  
Evidence collected, classified, and preserved durably.  
Ready for Checkpoint 2.1 reconciliation.
