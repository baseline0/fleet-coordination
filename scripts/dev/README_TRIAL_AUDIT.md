# Trial Posture Audit — Phase A (Static)

## Overview

The trial posture audit is a **read-only compliance checker** that validates the fleet-ops internal trial environment remains within the approved security posture.

**Phase A** (this version) performs static checks:
- Trial profile validity and expiry
- Repository declarations in manifest
- Boundary file presence
- Ownership assignments

**Future phases** (B–E) will add:
- Phase B: Test evidence validation
- Phase C: Runtime binding inspection
- Phase D: Behavioral probes
- Phase E: Scheduled reporting

## Installation

Requirements: `ruamel.yaml>=0.19.0` (installed in fleet-coordination)

```bash
cd fleet-coordination
uv sync  # Install dependencies
```

## Usage

### Basic run

```bash
uv run python scripts/dev/trial_posture_audit.py \
  --config scripts/dev/trial-audit.yaml \
  --json-out results/trial-posture.json \
  --text-out results/trial-posture.txt
```

### With custom project root

```bash
uv run python scripts/dev/trial_posture_audit.py \
  --project-root /home/mark/projects \
  --config scripts/dev/trial-audit.yaml
```

## Exit Codes

```
0: Pass or warnings only (safe to proceed)
1: Policy failures detected (trial unsafe)
2: Audit tool or configuration error
```

## Configuration

Edit `scripts/dev/trial-audit.yaml` to customize:

```yaml
scope:
  name: internal-readonly-poc
  repositories:
    - fleet-coordination
    - fleet-ops
    - mcp-vscode

trial_profile:
  path: "trial-profile-readonly-poc.yaml"

checks:
  # Enable/disable individual Phase A checks
  profile_exists: true
  profile_parses: true
  profile_unexpired: true
  # ... more checks
```

## Phase A Checks

| Check ID | Category | What it validates |
|----------|----------|-------------------|
| **PROFILE-001** | profile | Trial profile file exists |
| **PROFILE-002** | profile | Trial profile parses as valid YAML |
| **PROFILE-003** | profile | Trial profile has not expired |
| **PROFILE-004** | profile | Read-only enforcement configured |
| **PROFILE-005** | profile | Provider allowlist non-empty |
| **PROFILE-006** | profile | Workspace allowlist non-empty |
| **REPO-001** | repository | Trial repositories declared in manifest |
| **REPO-003** | repository | Boundary files present for all trial repos |
| **REPO-004** | repository | Contract version matches expected |
| **OWN-001** | ownership | Trial lead assigned |
| **OWN-002** | ownership | Security owner assigned |
| **OWN-003** | ownership | Rollback owner assigned |

## Output Format

### JSON (`--json-out results/trial-posture.json`)

```json
{
  "audit_version": "0.1.0",
  "scope": "internal-readonly-poc",
  "checked_at": "2026-09-20T20:34:18Z",
  "status": "fail",
  "promotion_eligible": false,
  "checks": [
    {
      "id": "PROFILE-001",
      "category": "profile",
      "status": "pass",
      "message": "Trial profile file exists",
      "evidence": ["trial-profile-readonly-poc.yaml"],
      "remediation": null,
      "owner": null
    },
    // ... more checks
  ],
  "summary": {
    "pass": 10,
    "warn": 0,
    "fail": 1,
    "pending": 0,
    "error": 0
  }
}
```

### Text (`--text-out results/trial-posture.txt`)

Human-readable report with all findings, evidence, and remediation steps.

## Common Issues

### Trial Profile Parse Error

**Problem:** `Found undefined alias '*Profile'`

**Cause:** The trial profile mixes Markdown headers (`**Profile ID:**`) with YAML, which YAML interprets as anchor syntax.

**Solution:** The trial profile must be pure YAML. Markdown comments should be in YAML comment format:

```yaml
# GOOD: YAML comment
profile_id: internal-readonly-poc-v1

# BAD: Markdown header (breaks YAML)
**Profile ID:** internal-readonly-poc-v1
```

### Missing Repository in Manifest

**Problem:** `Missing repositories in manifest: ['fleet-coordination']`

**Cause:** A trial repository is not declared in `repository-manifest.yaml`

**Solution:** Add the repository to `repository-manifest.yaml`:

```yaml
repositories:
  fleet-coordination:
    boundary_file: "BOUNDARIES.md"
    ci_checks: [...]
```

### Missing Ownership

**Problem:** `trial_lead not assigned in profile`

**Cause:** The trial profile metadata has placeholder values like `# NOTE: assign`

**Solution:** Replace with actual names/emails:

```yaml
metadata:
  trial_lead: "alice@example.com"
  security_owner: "bob@example.com"
  rollback_owner: "charlie@example.com"
```

## Interpreting Results

### Promotion Eligible?

The system is eligible for promotion if:
- ✅ All Phase A checks pass
- ✅ No failures
- ✅ No errors
- ✅ No pending required checks

### Green Light Threshold

For the internal trial:

```
required checks: all pass
warnings: allowed if explicitly accepted
failures: zero
pending: zero
errors: zero
```

## Next Steps

After Phase A passes:

1. **Phase B (Test Evidence):** Add security test validation
2. **Phase C (Runtime):** Check bind addresses, process state
3. **Phase D (Probes):** Run behavioral safety checks
4. **Phase E (Scheduled):** Run daily during trial, store timestamped results

## Development

### Running tests

```bash
uv run pytest tests/ -v
```

### Adding a new check

1. Create a `_check_SOMETHING()` method in `TrialPostureAudit` class
2. Append an `AuditCheck` result
3. Update `trial-audit.yaml` to enable/disable it

### Debugging

Enable verbose output:

```bash
uv run python scripts/dev/trial_posture_audit.py \
  --config scripts/dev/trial-audit.yaml \
  --json-out /tmp/debug.json \
  --text-out /tmp/debug.txt
cat /tmp/debug.txt
```

---

**Maintainers:** Trial lead, security owner  
**Last updated:** 2026-09-20
