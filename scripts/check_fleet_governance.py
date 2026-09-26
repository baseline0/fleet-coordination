#!/usr/bin/env python3
"""Check fleet governance compliance across all repos.

Validates that all repos have current schema version and valid .fleet/ content.

Usage:
  python check_fleet_governance.py                    # Check all repos
  python check_fleet_governance.py --repo flashcards  # Check single repo
  python check_fleet_governance.py --json             # Export as JSON
  python check_fleet_governance.py --strict           # Fail on any warnings
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import yaml


FLEET_ROOT = Path(__file__).parent.parent.parent
SCHEMA_VERSION = "1.0"

REQUIRED_FILES = {
    "boundaries.yaml": "Repository boundaries and scope",
    "catalog-info.yaml": "Backstage component metadata",
    "config.yaml": "Fleet configuration",
}

OPTIONAL_FILES = {
    "health.yaml": "CI dashboards, coverage, alerts, and health pointers",
    "release-strategy.yaml": "Versioning, release cadence, and deployment target",
    "roadmap.yaml": "Milestone and roadmap tracking",
    "standards.md": "Repository-specific standards",
    "maintenance.md": "Maintenance procedures",
    "onboarding.md": "Onboarding documentation",
}


@dataclass
class GovernanceCheck:
    """Result of governance compliance check."""
    repo_name: str
    valid: bool
    schema_version: str
    has_fleet_dir: bool
    required_files: dict[str, bool]
    optional_files: dict[str, bool]
    errors: list[str]
    warnings: list[str]


def check_repo(repo_path: Path) -> GovernanceCheck:
    """Check a single repository's governance compliance.

    Args:
        repo_path: Path to repository root

    Returns:
        GovernanceCheck result
    """
    repo_name = repo_path.name
    fleet_dir = repo_path / ".fleet"
    errors = []
    warnings = []
    detected_version = "unknown"
    required_files_status = {}
    optional_files_status = {}

    # Check .fleet/ directory exists
    if not fleet_dir.exists():
        return GovernanceCheck(
            repo_name=repo_name,
            valid=False,
            schema_version="none",
            has_fleet_dir=False,
            required_files={},
            optional_files={},
            errors=[".fleet/ directory not found"],
            warnings=[],
        )

    # Check required files
    for filename, description in REQUIRED_FILES.items():
        file_path = fleet_dir / filename
        exists = file_path.exists()
        required_files_status[filename] = exists

        if not exists:
            errors.append(f"Missing required file: {filename} ({description})")
        else:
            # Validate YAML structure and schema_version
            try:
                with open(file_path) as f:
                    data = yaml.safe_load(f) or {}

                if "schema_version" not in data:
                    errors.append(f"{filename}: missing schema_version field")
                elif data["schema_version"] != SCHEMA_VERSION:
                    errors.append(
                        f"{filename}: schema_version is {data['schema_version']}, "
                        f"expected {SCHEMA_VERSION}"
                    )
                else:
                    detected_version = data["schema_version"]
            except yaml.YAMLError as e:
                errors.append(f"{filename}: invalid YAML — {e}")
            except Exception as e:
                errors.append(f"{filename}: read error — {e}")

    # Check optional files
    for filename in OPTIONAL_FILES:
        file_path = fleet_dir / filename
        optional_files_status[filename] = file_path.exists()

    # Check for unexpected files
    allowed_files = set(REQUIRED_FILES.keys()) | set(OPTIONAL_FILES.keys())
    for file_path in fleet_dir.glob("*"):
        if file_path.name not in allowed_files:
            warnings.append(f"Unexpected file in .fleet/: {file_path.name}")

    # Check for uppercase files (should be lowercase)
    for file_path in fleet_dir.glob("*"):
        if file_path.name != file_path.name.lower():
            errors.append(f"File not lowercase: {file_path.name}")

    # Determine overall validity
    valid = len(errors) == 0 and detected_version == SCHEMA_VERSION

    return GovernanceCheck(
        repo_name=repo_name,
        valid=valid,
        schema_version=detected_version,
        has_fleet_dir=True,
        required_files=required_files_status,
        optional_files=optional_files_status,
        errors=errors,
        warnings=warnings,
    )


def check_fleet(
    fleet_root: Path,
    target_repo: Optional[str] = None,
    strict: bool = False,
) -> list[GovernanceCheck]:
    """Check all repos in fleet for governance compliance.

    Args:
        fleet_root: Root directory containing all repos
        target_repo: If specified, check only this repo
        strict: If True, warnings count as failures

    Returns:
        List of GovernanceCheck results
    """
    if target_repo:
        repos = [fleet_root / target_repo]
    else:
        repos = sorted(
            [d for d in fleet_root.iterdir() if d.is_dir() and (d / ".fleet").exists()]
        )

    results = []
    for repo_dir in repos:
        result = check_repo(repo_dir)
        if strict and result.warnings:
            result.valid = False
        results.append(result)

    return results


def print_report(results: list[GovernanceCheck], as_json: bool = False) -> None:
    """Print governance compliance report.

    Args:
        results: List of GovernanceCheck results
        as_json: If True, print as JSON; otherwise print as table
    """
    if as_json:
        data = [asdict(r) for r in results]
        print(json.dumps(data, indent=2))
        return

    # Table format
    valid_count = sum(1 for r in results if r.valid)
    invalid_count = len(results) - valid_count

    print("\n" + "=" * 80)
    print("Fleet Governance Compliance Check")
    print("=" * 80)
    print(f"Schema Version: {SCHEMA_VERSION}")
    print(f"Total Repos: {len(results)}")
    print(f"✅ Compliant: {valid_count}")
    print(f"❌ Non-Compliant: {invalid_count}")
    print("=" * 80 + "\n")

    # Print results by status
    compliant = [r for r in results if r.valid]
    non_compliant = [r for r in results if not r.valid]

    if compliant:
        print("✅ COMPLIANT REPOS:")
        for result in compliant:
            print(f"  {result.repo_name:30} (v{result.schema_version})")
        print()

    if non_compliant:
        print("❌ NON-COMPLIANT REPOS:")
        for result in non_compliant:
            print(f"\n  {result.repo_name}")
            if not result.has_fleet_dir:
                print(f"    ERROR: .fleet/ directory not found")
            else:
                print(f"    Schema: {result.schema_version}")

                # Show missing required files
                missing = [f for f, exists in result.required_files.items() if not exists]
                if missing:
                    print(f"    Missing required files:")
                    for f in missing:
                        print(f"      - {f}")

                # Show errors
                if result.errors:
                    print(f"    Errors:")
                    for error in result.errors:
                        print(f"      - {error}")

                # Show warnings
                if result.warnings:
                    print(f"    Warnings:")
                    for warning in result.warnings:
                        print(f"      - {warning}")

    print("\n" + "=" * 80)
    if valid_count == len(results):
        print("✅ All repos compliant!")
    else:
        print(f"⚠️  {invalid_count} repo(s) need attention")
    print("=" * 80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check fleet governance compliance across all repos"
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="Check specific repo (e.g., flashcards)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Export results as JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    parser.add_argument(
        "--fleet-root",
        type=Path,
        default=FLEET_ROOT,
        help="Fleet root directory (default: parent of fleet-coordination)",
    )

    args = parser.parse_args()

    # Run checks
    results = check_fleet(
        fleet_root=args.fleet_root,
        target_repo=args.repo,
        strict=args.strict,
    )

    # Print report
    print_report(results, as_json=args.json)

    # Exit with appropriate code
    compliant = all(r.valid for r in results)
    sys.exit(0 if compliant else 1)


if __name__ == "__main__":
    main()
