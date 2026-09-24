# Phase 3: Governance Schema Validation

**Date:** 2026-09-24  
**Status:** Control Implementation Complete — Schema Compliance Audited  
**Result:** 5/6 repos compliant; 1 remediation identified

---

## Overview

Phase 3 adds the `governance_schema_validation` control to the compliance audit runner. This deterministic control validates that repository governance metadata (`.fleet/` directory structure) conforms to the v1.0 schema defined in fleet-base.

**Control Goal:** Ensure consistent governance metadata across all fleet repositories.

**Authority:** [fleet-base/.fleet/governance-schema-v1.md](../../fleet-base/.fleet/governance-schema-v1.md)

---

## Audit Results

### Fleet-Wide Governance Compliance

| Repository | Schema Version | Status | Required Files |
|---|---|---|---|
| fleet-agents | 1.0 | ✅ PASS | ✓ boundaries.yaml, catalog-info.yaml, config.yaml |
| fleet-base | 1.0 | ✅ PASS | ✓ boundaries.yaml, catalog-info.yaml, config.yaml |
| fleet-coordination | 1.0 | ✅ PASS | ✓ boundaries.yaml, catalog-info.yaml, config.yaml |
| fleet-ops | 1.0 | ✅ PASS | ✓ boundaries.yaml, catalog-info.yaml, config.yaml |
| fleet-toolbox | 1.0 | ✅ PASS | ✓ boundaries.yaml, catalog-info.yaml, config.yaml |
| **fleet-spec** | **none** | ❌ **FAIL** | **Missing: .fleet/ directory** |

**Compliance Rate:** 5/6 (83%)

---

## Schema Requirements

### Required Files
All three files must exist and contain `schema_version: "1.0"`:

1. **boundaries.yaml** — Repository boundaries and scope
   - Fields: name, title, description, layer, owner, status

2. **catalog-info.yaml** — Backstage component metadata
   - Follows backstage.io/v1alpha1 format
   - Must include schema_version: "1.0"

3. **config.yaml** — Fleet configuration
   - Fields: type, language, standards, testing, governance
   - Must include schema_version: "1.0"

### Optional Files
- roadmap.yaml — Milestone tracking
- standards.md — Repository-specific standards
- maintenance.md — Maintenance procedures
- onboarding.md — Contributor onboarding

### Constraints
- All filenames must be **lowercase**
- No unexpected files (governance checker warns on unknown files)

---

## Remediation: fleet-spec

**Finding:** Missing `.fleet/` directory

**Required Action:** Initialize `.fleet/` with three required files

**Template:**
```yaml
# .fleet/boundaries.yaml
schema_version: "1.0"
name: fleet-spec
title: Fleet Specification
description: <description of fleet-spec role>
layer: "0"
owner: <owner>
status: approved
```

```yaml
# .fleet/catalog-info.yaml
schema_version: "1.0"
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: fleet-spec
  title: Fleet Specification
  description: <description>
spec:
  type: service
  lifecycle: production
  owner: <owner>
```

```yaml
# .fleet/config.yaml
schema_version: "1.0"
type: infrastructure
language: python
standards:
  type_hints: required
  docstrings: google-style
testing:
  test_command: pytest tests/
```

**Effort:** ~30 minutes

**Done When:** `governance_schema_validation` control returns PASS for fleet-spec

---

## Summary

The audit runner now supports **six controls**; five are deterministic or schema-based, while `error_boundary_review` has discovery and a classification rubric but awaits reviewed handler classifications.

**Deterministic controls (Phase 1B & 3):**
- repository_metadata
- test_execution
- package_install
- import_boundary_check
- governance_schema_validation

**Qualitative control (Phase 2):**
- error_boundary_review (pending classification)

All six controls committed and operational. Fleet-wide governance status is known with one concrete, low-ambiguity remediation identified.

---

**Next:** Return to Morning Review Phase 2 (thin Typer CLI wiring). Compliance backlog captured in TODO.md.
