# Fleet Coordination

**Fleet-wide versioned governance, contracts, and release state.**

This repository holds:
- Federated architecture contracts (CapabilityRequest, AuditEvent, etc.)
- Repository manifest (which repos, roles, lifecycle)
- Boundary rules and remediations
- Compatibility matrix (tested version combinations)
- Trial profiles and rollback procedures
- Fleet-check validator (ensures fleet is ready for deployment)

## Not Here

- Runtime orchestration → lives in `fleet-ops`
- Reusable library code → lives in `fleet-base`
- Repository-specific code → lives in each repo

## Key Distinction

| What | Where |
|---|---|
| Code that can be reused by another fleet | `fleet-base` |
| Code that orchestrates requests at runtime | `fleet-ops` |
| Versioned contracts this fleet agrees to | `fleet-coordination` |
| Boundary definitions this repo enforces | `.fleet/boundaries.md` (in each repo) |

## Quick Start

```bash
# Validate fleet composition
python scripts/fleet-check.py --manifest fleet.yaml

# Machine-readable output
python scripts/fleet-check.py --manifest fleet.yaml --json
```

## Fleet Release Candidate (0.1.0)

Current manifest: `fleet.yaml`

**Status:** candidate (warnings OK, errors block)

**Repositories:**
- `agent-tooling` — architecture control plane (approved)
- `fleet-ops` — runtime control plane (mature)
- `rope-mcp` — provider adapter (approved)
- `vscode-workspace-mcp` — provider adapter (approved)
- `toolboxes` — domain capabilities (proposed)

## Directory Structure

```
fleet-coordination/
├── contracts/                    # Versioned contract definitions
│   ├── CORRECTED_ARCHITECTURE_CONTRACTS.md
│   ├── WEEK_2_DECISIONS_RECORD.md
│   └── contract-bundle.yaml
├── governance/                   # Fleet governance rules & state
│   ├── repository-manifest.yaml
│   ├── repository-lifecycle.yaml
│   ├── boundary-rules.yaml
│   └── boundary-remediations.yaml
├── compatibility/                # Version compatibility & testing
│   └── compatibility-matrix.yaml
├── trial/                        # Trial (Track A) profiles
│   ├── trial-profile-readonly-poc.yaml
│   └── TRIAL_ROLLBACK_PROCEDURE.md
├── scripts/
│   └── fleet-check.py            # Fleet validator
├── tests/
│   └── test_fleet_check.py
├── fleet.yaml                    # Fleet release manifest
├── pyproject.toml
└── README.md
```

## Fleet-Check Exit Codes

```
0: Valid (all checks pass)
1: Invalid (errors found)
2: Configuration error
```

JSON output includes:
```json
{
  "fleet_release": "0.1.0",
  "status": "valid|candidate|invalid",
  "repositories": {
    "agent-tooling": {"status": "pass", "ref": "abc123"},
    ...
  },
  "contract_bundle": "0.1.0",
  "new_boundary_findings": 0,
  "trial_profile": "pass|fail|invalid|disabled"
}
```

## Tests

```bash
pytest tests/ -v
```

Validates:
- Fleet manifest loads and parses
- All repositories exist and are reachable
- Boundary files exist (if required)
- Contract bundle exists and version matches
- Trial profile exists and is valid
- All repository refs are assigned
- JSON output format

## Ownership

**Maintainer:** # NOTE: architecture-lead

**Contact:** # NOTE: assign email

**Reviews:** Architecture council (monthly or on release)
