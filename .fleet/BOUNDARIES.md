# Fleet-Coordination Responsibility Boundaries

**Last Updated:** 2026-09-25  
**Owner:** Trial Lead  
**Related:** [fleet-ops boundary declaration](../../fleet-ops/.fleet/BOUNDARIES.md)

---

## Boundary: Policy Authorship vs. Enforcement

### fleet-coordination OWNS (Policy Definition & Evolution)

✅ **Author fleet governance:**
- Define `.fleet/` schema, required fields, and compliance standards (governance/compliance-standard.yaml)
- Maintain fleet-architecture.yaml as canonical policy document
- Manage policy versioning and schema compatibility

✅ **Publish policy decisions:**
- Create ADRs for all governance changes (governance/decisions/)
- Record policy approval and rationale
- Maintain audit trail of policy evolution

✅ **Manage fleet-wide metadata:**
- Own all `.fleet/config.yaml` and `.fleet/catalog-info.yaml` standards
- Approve schema migrations and policy exceptions
- Coordinate cross-repo policy alignment

### fleet-ops OWNS (Runtime Enforcement & Observation)

✅ **Implement enforcement:**
- Execute read-only `.fleet/` compliance checks via GitHub Actions
- Generate actionable diagnostics from policy violations
- Implement advisory CI workflows that surface policy violations to reviewers

✅ **Collect evidence:**
- Measure false-positive rate, remediation time, and contributor adoption
- Run proof-of-control demonstrations
- Maintain observation metrics for policy review checkpoints

---

## Workflow: Policy Change → Enforcement → Evidence

1. **fleet-coordination:** Authors policy via ADR (governance/decisions/)
2. **fleet-coordination:** Updates compliance standards and `.fleet/` schema
3. **fleet-ops:** Consumes updated policy (pins fleet-coordination revision in workflows)
4. **fleet-ops:** Implements GitHub Actions workflows that enforce new policy
5. **fleet-ops:** Runs proof-of-control to verify enforcement works
6. **fleet-ops:** Collects observation evidence over active period (2+ weeks)
7. **fleet-coordination:** Reviews evidence at checkpoint to decide on scope expansion

---

## No Overlap

- fleet-coordination does **NOT** operate runtime compliance checks
- fleet-ops does **NOT** author or change fleet-wide governance policies
- Each repo is read-only consumer of the other's defined output

---

## Active Policy: Metadata Enforcement (2026-09-25 to 2026-10-09)

**Policy authored by:** fleet-coordination (METADATA_ENFORCEMENT_DECISION.md, Option B approved)  
**Enforcement implemented by:** fleet-ops (`validate-metadata.yml` workflows)  
**Review checkpoint:** 2026-10-09  
**Review owner:** fleet-coordination (decision committee)

---

## Reference

**Ops boundary declaration:** `fleet-ops/.fleet/BOUNDARIES.md`  
**Policy repository:** `governance/README.md`  
**Schema version:** 1.0
