"""Tests for fleet-coordination checker.

Covers:
- Valid fleet manifest passes
- Missing repository fails
- Missing boundary file warns
- Contract version match
- Trial profile validation
- All required refs assigned
"""

import json
import importlib.util
import tempfile
from pathlib import Path

import pytest

# Load fleet-check module from scripts directory
scripts_path = Path(__file__).parent.parent / "scripts" / "fleet-check.py"
spec = importlib.util.spec_from_file_location("fleet_check", scripts_path)
fleet_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fleet_check)

FleetChecker = fleet_check.FleetChecker


@pytest.fixture
def temp_fleet_dir():
    """Create temporary fleet directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create repo directories
        for repo in ["agent-tooling", "fleet-ops", "vscode-workspace-mcp"]:
            (base / repo).mkdir()
            (base / repo / ".fleet").mkdir()
            (base / repo / ".fleet" / "boundaries.md").write_text("# Boundaries")

        yield base


def test_valid_fleet_manifest(temp_fleet_dir):
    """Valid fleet manifest with all repos present."""
    manifest = {
        "fleet_release": "0.1.0",
        "status": "candidate",
        "contract_bundle": "0.1.0",
        "fleet_scope": {
            "core": ["agent-tooling", "fleet-ops", "vscode-workspace-mcp"]
        },
        "governance": {
            "contract_bundle": "contracts/contract-bundle.yaml"
        },
        "trial": {
            "profile_file": "trial/trial-profile-readonly-poc.yaml"
        },
        "repositories": {
            "agent-tooling": {
                "source": "./agent-tooling",
                "ref": "abc123def456abc123def456abc123def456abcd",
                "role": "shared",
                "lifecycle": "approved",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            },
            "fleet-ops": {
                "source": "./fleet-ops",
                "ref": "def456abc123def456abc123def456abc123def4",
                "role": "runtime",
                "lifecycle": "mature",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            },
            "vscode-workspace-mcp": {
                "source": "./vscode-workspace-mcp",
                "ref": "ghi789jkl012ghi789jkl012ghi789jkl012ghi",
                "role": "provider",
                "lifecycle": "approved",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            }
        }
    }

    manifest_file = temp_fleet_dir / "fleet.yaml"
    import yaml
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    # Create dummy contract bundle and trial profile
    (temp_fleet_dir / "contracts").mkdir(exist_ok=True)
    (temp_fleet_dir / "contracts" / "contract-bundle.yaml").write_text("version: 0.1.0")

    (temp_fleet_dir / "trial").mkdir(exist_ok=True)
    trial_profile = {
        "profile_id": "test",
        "status": "enabled",
        "capabilities": {"allowed": ["find-files"]},
        "providers": {"allowed": ["vscode-workspace-mcp"]},
        "workspaces": {"allowlist": ["/test"]}
    }
    with open(temp_fleet_dir / "trial" / "trial-profile-readonly-poc.yaml", "w") as f:
        yaml.dump(trial_profile, f)

    checker = FleetChecker(str(manifest_file), scope="core")
    assert checker.validate() is True
    # Status is candidate because contracts are still pending
    assert checker.results["status"] in ["candidate", "verified"]
    # promotion_eligible is False if contracts still pending
    assert isinstance(checker.results["promotion_eligible"], bool)


def test_missing_repository(temp_fleet_dir):
    """Missing repository in scope fails validation."""
    manifest = {
        "fleet_release": "0.1.0",
        "status": "candidate",
        "contract_bundle": "0.1.0",
        "fleet_scope": {
            "core": ["agent-tooling", "nonexistent-repo"]
        },
        "governance": {"contract_bundle": "contracts/contract-bundle.yaml"},
        "trial": {"profile_file": "trial/trial-profile-readonly-poc.yaml"},
        "repositories": {
            "agent-tooling": {
                "source": "./agent-tooling",
                "ref": "abc123def456abc123def456abc123def456abcd",
                "role": "shared",
                "lifecycle": "approved",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            },
            "nonexistent-repo": {
                "source": "./nonexistent",
                "ref": "xyz999aaabbbcccdddeeefffggghhhiiijjjkkk",
                "role": "test",
                "lifecycle": "proposed",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            }
        }
    }

    manifest_file = temp_fleet_dir / "fleet.yaml"
    import yaml
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    (temp_fleet_dir / "contracts").mkdir(exist_ok=True)
    (temp_fleet_dir / "contracts" / "contract-bundle.yaml").write_text("version: 0.1.0")

    checker = FleetChecker(str(manifest_file), scope="core")
    assert checker.validate() is False
    assert any("not found" in str(e).lower() or "path_not_found" in str(e) for e in checker.errors)


def test_missing_boundary_file_proposed_warns(temp_fleet_dir):
    """Missing boundary file for proposed repo produces warning, not error."""
    manifest = {
        "fleet_release": "0.1.0",
        "status": "candidate",
        "contract_bundle": "0.1.0",
        "fleet_scope": {
            "core": ["proposed-repo"]
        },
        "governance": {"contract_bundle": "contracts/contract-bundle.yaml"},
        "trial": {"profile_file": "trial/trial-profile-readonly-poc.yaml"},
        "repositories": {
            "proposed-repo": {
                "source": "./agent-tooling",
                "ref": "abc123def456abc123def456abc123def456abcd",
                "role": "test",
                "lifecycle": "proposed",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            }
        }
    }

    # Remove boundaries.md from agent-tooling
    boundary_file = temp_fleet_dir / "agent-tooling" / ".fleet" / "boundaries.md"
    boundary_file.unlink()

    manifest_file = temp_fleet_dir / "fleet.yaml"
    import yaml
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    (temp_fleet_dir / "contracts").mkdir(exist_ok=True)
    (temp_fleet_dir / "contracts" / "contract-bundle.yaml").write_text("version: 0.1.0")
    (temp_fleet_dir / "trial").mkdir(exist_ok=True)
    trial_profile = {
        "profile_id": "test",
        "status": "enabled",
        "capabilities": {"allowed": []},
        "providers": {"allowed": []},
        "workspaces": {"allowlist": []}
    }
    with open(temp_fleet_dir / "trial" / "trial-profile-readonly-poc.yaml", "w") as f:
        yaml.dump(trial_profile, f)

    checker = FleetChecker(str(manifest_file), scope="core")
    checker.validate()
    # Missing boundary for proposed is a warning, not an error
    assert any("boundary" in w.lower() for w in checker.warnings)
    # But status is not invalid
    assert checker.results["status"] != "invalid"


def test_trial_profile_validates(temp_fleet_dir):
    """Trial profile must have required fields."""
    manifest = {
        "fleet_release": "0.1.0",
        "status": "candidate",
        "contract_bundle": "0.1.0",
        "fleet_scope": {
            "core": []
        },
        "governance": {"contract_bundle": "contracts/contract-bundle.yaml"},
        "trial": {"profile_file": "trial/trial-profile-readonly-poc.yaml"},
        "repositories": {}
    }

    manifest_file = temp_fleet_dir / "fleet.yaml"
    import yaml
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    (temp_fleet_dir / "contracts").mkdir(exist_ok=True)
    (temp_fleet_dir / "contracts" / "contract-bundle.yaml").write_text("version: 0.1.0")

    # Invalid trial profile (missing fields)
    (temp_fleet_dir / "trial").mkdir(exist_ok=True)
    with open(temp_fleet_dir / "trial" / "trial-profile-readonly-poc.yaml", "w") as f:
        f.write("profile_id: test\n")  # Missing required fields

    checker = FleetChecker(str(manifest_file), scope="core")
    checker.validate()
    assert checker.results["checks"]["trial_profile"] == "fail"


def test_repository_refs_assigned(temp_fleet_dir):
    """Repository refs must be assigned (not # NOTE placeholders)."""
    manifest = {
        "fleet_release": "0.1.0",
        "status": "candidate",
        "contract_bundle": "0.1.0",
        "fleet_scope": {
            "core": ["agent-tooling"]
        },
        "governance": {"contract_bundle": "contracts/contract-bundle.yaml"},
        "trial": {"profile_file": "trial/trial-profile-readonly-poc.yaml"},
        "repositories": {
            "agent-tooling": {
                "source": "./agent-tooling",
                "ref": "# NOTE: assign",  # Not assigned
                "role": "shared",
                "lifecycle": "approved",
                "required_boundaries": True,
                "boundary_path": ".fleet/boundaries.md"
            }
        }
    }

    manifest_file = temp_fleet_dir / "fleet.yaml"
    import yaml
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    (temp_fleet_dir / "contracts").mkdir(exist_ok=True)
    (temp_fleet_dir / "contracts" / "contract-bundle.yaml").write_text("version: 0.1.0")
    (temp_fleet_dir / "trial").mkdir(exist_ok=True)
    trial_profile = {
        "profile_id": "test",
        "status": "enabled",
        "capabilities": {"allowed": []},
        "providers": {"allowed": []},
        "workspaces": {"allowlist": []}
    }
    with open(temp_fleet_dir / "trial" / "trial-profile-readonly-poc.yaml", "w") as f:
        yaml.dump(trial_profile, f)

    checker = FleetChecker(str(manifest_file), scope="core")
    checker.validate()
    assert any("ref not assigned" in w for w in checker.warnings)
    assert checker.results["checks"]["refs"] == "warn"


def test_json_output(temp_fleet_dir, capsys):
    """JSON output format is valid and includes promotion_eligible."""
    manifest = {
        "fleet_release": "0.1.0",
        "status": "candidate",
        "contract_bundle": "0.1.0",
        "fleet_scope": {
            "core": []
        },
        "governance": {"contract_bundle": "contracts/contract-bundle.yaml"},
        "trial": {"profile_file": "trial/trial-profile-readonly-poc.yaml"},
        "repositories": {}
    }

    manifest_file = temp_fleet_dir / "fleet.yaml"
    import yaml
    with open(manifest_file, "w") as f:
        yaml.dump(manifest, f)

    (temp_fleet_dir / "contracts").mkdir(exist_ok=True)
    (temp_fleet_dir / "contracts" / "contract-bundle.yaml").write_text("version: 0.1.0")
    (temp_fleet_dir / "trial").mkdir(exist_ok=True)
    trial_profile = {
        "profile_id": "test",
        "status": "enabled",
        "capabilities": {"allowed": []},
        "providers": {"allowed": []},
        "workspaces": {"allowlist": []}
    }
    with open(temp_fleet_dir / "trial" / "trial-profile-readonly-poc.yaml", "w") as f:
        yaml.dump(trial_profile, f)

    checker = FleetChecker(str(manifest_file), scope="core")
    checker.validate()
    checker.report(json_output=True)

    captured = capsys.readouterr()
    # Should be valid JSON
    output = json.loads(captured.out)
    assert "fleet_release" in output
    assert "status" in output
    assert "repositories" in output
    assert "promotion_eligible" in output
    assert isinstance(output["promotion_eligible"], bool)
    assert "checks" in output
    assert "scope" in output
    assert output["scope"] == "core"
