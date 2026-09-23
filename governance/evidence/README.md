# Fleet Governance Evidence Archive

This directory contains reproducible evidence collected during governance policy development.

---

## Checkpoints

### Checkpoint 2: Repository Inventory
**Location:** `checkpoint-2/`  
**Status:** ✅ Complete (2026-09-23)  
**Manifest:** `checkpoint-2/MANIFEST.md`

Raw inventory of all six fleet repositories with:
- Git state (revision, working-tree status)
- Package metadata (distribution name, import roots)
- Governance metadata (.fleet/ files)
- Dependency declarations (pyproject.toml)
- Actual imports (scanned from source)
- CI entry points (workflows, justfile commands)

**Key Finding:** No policy violations detected. Dependency graph is acyclic and follows intended layer structure.

**Pending:** Checkpoint 2.1 reconciliation of anomalies (fleet-agents/fleet-spec naming, fleet-toolbox imports, import-linter CI verification).

---

## Reproducibility

Each checkpoint includes:
- **Raw output** — Machine-readable evidence (JSON)
- **Analysis** — Human-readable summary and classification
- **Manifest** — Metadata (collection time, repository SHAs, tool versions, limitations)
- **Collection tool** — Script/command to re-run the checkpoint

To re-run a checkpoint:

```bash
cd /home/mark/projects

# Checkpoint 2: Re-inventory all repos
python3 fleet-coordination/governance/tools/collect_inventory.py
```

---

## Preserved State

Each checkpoint freezes:
- Repository Git SHAs at collection time
- Tool versions and configuration
- Scan scope and limitations
- Timestamp and collection metadata

This allows:
- Comparison with current state (drift detection)
- Reproducible evidence for decisions
- Audit trail of when facts were established
- Rollback/reconciliation if later findings contradict

---

## Related Decisions

- **ADR-0001:** Policy location and access model
- **Checkpoint 3:** First policy draft (using this evidence as ground truth)
- **Increment 2:** Boundary metadata migration (v2.0 `.fleet/` files per repo)

---

## For Future Contributors

When re-running a checkpoint or creating a new one:

1. Record exact collection command and output location
2. Capture repository SHAs and working-tree status
3. Save tool version/SHA (e.g., `collect_inventory.py` hash)
4. Include timestamp in UTC
5. Preserve both raw and summary outputs
6. Document any deviations from prior checkpoint methodology
7. Create a manifest with metadata and reproducibility instructions
