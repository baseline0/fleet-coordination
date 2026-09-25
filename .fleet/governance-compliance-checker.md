# Fleet Governance Compliance Checker

**Location:** `scripts/check_fleet_governance.py`  
**Status:** Active  
**Version:** 1.0  
**Last Updated:** 2026-09-21

---

## Overview

Automated compliance checker for fleet governance schema v1.0. Validates that all repos have:

✅ `.fleet/` directory  
✅ Required files (boundaries.yaml, catalog-info.yaml, config.yaml)  
✅ All YAML files with `schema_version: "1.0"`  
✅ Lowercase filenames  
✅ No unexpected files  

---

## Quick Start

### Check All Repos
```bash
just check-governance
# or
uv run python scripts/check_fleet_governance.py
```

### Check Single Repo
```bash
just check-governance-repo flashcards
# or
uv run python scripts/check_fleet_governance.py --repo flashcards
```

### Strict Mode (warnings = failures)
```bash
just check-governance-strict
# or
uv run python scripts/check_fleet_governance.py --strict
```

### Export as JSON
```bash
just check-governance-json
# or
uv run python scripts/check_fleet_governance.py --json
```

---

## CLI Reference

### Options

| Option | Description |
|--------|-------------|
| `--repo REPO` | Check specific repo (e.g., `flashcards`) |
| `--json` | Export results as JSON instead of table |
| `--strict` | Treat warnings as failures (exit code 1) |
| `--fleet-root PATH` | Fleet root directory (default: parent of fleet-coordination) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All repos compliant |
| 1 | One or more repos non-compliant |

---

## What It Checks

### Required Files (All Repos)

| File | Purpose |
|------|---------|
| `boundaries.yaml` | Repository boundaries and scope (structured YAML) |
| `catalog-info.yaml` | Backstage component metadata |
| `config.yaml` | Fleet configuration with standards |

All must have `schema_version: "1.0"` field.

### Optional Files (As Needed)

| File | Purpose | Repos |
|------|---------|-------|
| `roadmap.yaml` | Milestone tracking | 3 |
| `standards.md` | Repo-specific standards | 1 |
| `maintenance.md` | Maintenance procedures | 1 |
| `onboarding.md` | Contributor onboarding | 1 |

### Violations Detected

| Violation | Severity |
|-----------|----------|
| Missing `.fleet/` directory | **ERROR** |
| Missing required file | **ERROR** |
| Missing `schema_version` field | **ERROR** |
| Wrong `schema_version` (not "1.0") | **ERROR** |
| Uppercase filenames | **ERROR** |
| Invalid YAML syntax | **ERROR** |
| Unexpected files in `.fleet/` | WARNING |

---

## Output Examples

### Table Format (Default)

```
================================================================================
Fleet Governance Compliance Check
================================================================================
Schema Version: 1.0
Total Repos: 19
✅ Compliant: 19
❌ Non-Compliant: 0
================================================================================

✅ COMPLIANT REPOS:
  fleet-agents                  (v1.0)
  cv                             (v1.0)
  flashcards                     (v1.0)
  ...

================================================================================
✅ All repos compliant!
================================================================================
```

### JSON Format

```json
[
  {
    "repo_name": "cv",
    "valid": true,
    "schema_version": "1.0",
    "has_fleet_dir": true,
    "required_files": {
      "boundaries.yaml": true,
      "catalog-info.yaml": true,
      "config.yaml": true
    },
    "optional_files": {...},
    "errors": [],
    "warnings": []
  },
  ...
]
```

---

## Integration with CI/CD

### GitHub Actions Example

Add to `.github/workflows/governance.yml`:

```yaml
name: Fleet Governance

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    # Run daily
    - cron: '0 0 * * *'

jobs:
  check-governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up uv
        uses: astral-sh/setup-uv@v3
      
      - name: Set up Python
        run: uv python install 3.13
      
      - name: Check governance compliance
        run: cd fleet-coordination && uv run python scripts/check_fleet_governance.py --strict
      
      - name: Export governance report
        if: always()
        run: cd fleet-coordination && uv run python scripts/check_fleet_governance.py --json > /tmp/governance-report.json
      
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: governance-report
          path: /tmp/governance-report.json
```

---

## Troubleshooting

### "Repository not found: X"
The repo doesn't have a `.fleet/` directory. Create one with required files.

### "Missing required file: boundaries.yaml"
Run from `.fleet/` directory:
```bash
cat > boundaries.yaml << 'EOF'
schema_version: "1.0"
name: repo-name
title: Human Readable Title
description: What this repo does
layer: 1
owner: team-name
status: approved
EOF
```

### "schema_version is 0.9, expected 1.0"
Update the file to use schema_version: "1.0":
```bash
# Edit .fleet/boundaries.yaml, .fleet/catalog-info.yaml, .fleet/config.yaml
# Change schema_version: "0.9" → schema_version: "1.0"
```

### "File not lowercase: BOUNDARIES.md"
Rename uppercase files to lowercase:
```bash
cd .fleet/
mv BOUNDARIES.md boundaries.md
mv STANDARDS.md standards.md
```

---

## Maintenance

### Update Checker
When schema v1.0 is updated or v2.0 released, edit:
- `scripts/check_fleet_governance.py`: Update `SCHEMA_VERSION`
- `.fleet/governance-schema-v1.md`: Document changes
- All repos: Update `.fleet/*.yaml` files

### Regular Audits
Run compliance check:
- **Weekly:** Automated CI check
- **Monthly:** Manual audit report
- **Quarterly:** Review schema compliance across fleet

### Future Enhancements
- [ ] Integrate with fleet-base.GovernanceSchemaValidator
- [ ] Add compliance scoring (e.g., 95% of required fields)
- [ ] Support schema v2.0 with enhanced fields
- [ ] Generate compliance certificates
