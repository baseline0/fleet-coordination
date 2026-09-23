# Fleet Governance & Architecture Policy

**Status:** Established location; policy draft pending Checkpoint 3  
**Owner:** Mark Alexiuk  
**Last Updated:** 2026-09-23

This directory contains the canonical fleet architecture policy and governance metadata for the six-repository fleet.

---

## Files

### `fleet-architecture.yaml` (Checkpoint 3)
Canonical cross-repository dependency policy, public API surfaces, and invariants.

**Not yet created.** Draft in progress; see [ADR-0001](decisions/ADR-0001-fleet-architecture-policy-location.md).

### `schema/fleet-architecture-v2.schema.json` (Checkpoint 3)
JSON Schema for validating `fleet-architecture.yaml`.

### `decisions/`
Architecture decision records (ADRs) for policy changes.

- [ADR-0001: Policy Location](decisions/ADR-0001-fleet-architecture-policy-location.md) — Approved

---

## Access

### Local Development

```bash
# Check fleet architecture (report-only mode)
just check-fleet-architecture \
  --policy ~/projects/fleet-coordination/governance/fleet-architecture.yaml \
  --report-only
```

### CI Integration

CI must pin `fleet-coordination` revision before accessing policy:

```bash
git clone https://github.com/user/fleet-coordination /tmp/fc
cd /tmp/fc && git checkout <pinned-sha>
```

See [ADR-0001](decisions/ADR-0001-fleet-architecture-policy-location.md) for full CI model.

---

## Roadmap

**Checkpoint 1 (This Week):** ✅ ADR-0001 approved; location established  
**Checkpoint 2 (Complete):** ✅ Six-repository inventory collected and classified  
**Checkpoint 2.1 (Next):** 📋 Reconcile anomalies; verify import-linter CI  
**Checkpoint 3 (Week 2):** 📋 First policy draft (`fleet-architecture.yaml` v0.1.0)  
**Checkpoint 4:** 📋 Validator design and proof-of-detection  
**Checkpoint 5:** 📋 Pilot boundary migration (fleet-base)  
**Checkpoint 6:** 📋 Fleet-wide report-only validation pass  
**Checkpoint 7:** 📋 CI promotion decision  
**Checkpoint 8:** 📋 Dependency portability plan  
**Checkpoint 9:** 📋 TEST-003 evidence review & periodic-agent approval gate  

---

## Related Documents

- `fleet-ops/docs/PHASE-2E-DISPATCH-AUDIT-IMPLEMENTATION.md` — Phase 2E dispatch audit trail implementation
- `fleet-base/docs/BOUNDARIES-FRAMEWORK.md` — Fleet boundary framework (if present)
- `fleet-base/.fleet/governance-schema-v1.md` — Governance schema v1.0 (current fleet standard)

---

## Notes

- This directory is a **stable governance artifact**, independent of fleet-coordination runtime code.
- Policy changes require an ADR; see [decisions/](decisions/).
- Policy schema versioning is separate from package versioning.
- Validator is not imported by fleet packages; it is a fleet-integrity tool only.
