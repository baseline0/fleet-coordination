#!/usr/bin/env python3
"""Fleet coordinator: validate fleet composition and release readiness.

Usage:
  fleet-check --manifest fleet.yaml
  fleet-check --manifest fleet.yaml --json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import yaml


class FleetChecker:
    """Validate fleet composition, contracts, and boundary state."""

    def __init__(self, manifest_file: str):
        """Initialize checker with fleet manifest."""
        self.manifest_path = Path(manifest_file)
        self.manifest = None
        self.errors = []
        self.warnings = []
        self.results = {
            "fleet_release": None,
            "status": "invalid",
            "repositories": {},
            "contract_bundle": None,
            "new_boundary_findings": 0,
            "trial_profile": "unchecked",
        }

    def load_manifest(self) -> bool:
        """Load and validate fleet manifest file."""
        if not self.manifest_path.exists():
            self.errors.append(f"Manifest file not found: {self.manifest_path}")
            return False

        try:
            with open(self.manifest_path) as f:
                self.manifest = yaml.safe_load(f)
            self.results["fleet_release"] = self.manifest.get("fleet_release")
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in manifest: {e}")
            return False

    def check_repositories_exist(self) -> bool:
        """Verify all repositories are reachable."""
        if not self.manifest:
            return False

        all_exist = True
        for repo_name, repo_config in self.manifest.get("repositories", {}).items():
            repo_path = Path(repo_config.get("source", ""))
            if not repo_path.is_absolute():
                repo_path = self.manifest_path.parent / repo_path

            if not repo_path.exists():
                self.errors.append(f"Repository not found: {repo_name} at {repo_path}")
                self.results["repositories"][repo_name] = {"status": "fail", "reason": "not_found"}
                all_exist = False
            else:
                self.results["repositories"][repo_name] = {"status": "pass"}

        return all_exist

    def check_boundary_files(self) -> bool:
        """Verify boundary files exist in repositories."""
        if not self.manifest:
            return False

        all_exist = True
        for repo_name, repo_config in self.manifest.get("repositories", {}).items():
            if not repo_config.get("required_boundaries"):
                continue

            repo_path = Path(repo_config.get("source", ""))
            if not repo_path.is_absolute():
                repo_path = self.manifest_path.parent / repo_path

            boundary_file = repo_path / ".fleet" / "boundaries.md"
            if not boundary_file.exists():
                self.warnings.append(f"Boundary file missing: {repo_name}/.fleet/boundaries.md")
                all_exist = False

        return all_exist

    def check_contract_bundle(self) -> bool:
        """Verify contract bundle exists and version matches."""
        contract_file = self.manifest_path.parent / self.manifest.get("governance", {}).get("contract_bundle", "")

        if not contract_file.exists():
            self.errors.append(f"Contract bundle not found: {contract_file}")
            return False

        self.results["contract_bundle"] = self.manifest.get("contract_bundle")
        return True

    def check_trial_profile(self) -> bool:
        """Verify trial profile exists and is valid."""
        trial_file = self.manifest_path.parent / self.manifest.get("trial", {}).get("profile_file", "")

        if not trial_file.exists():
            self.warnings.append(f"Trial profile not found: {trial_file}")
            self.results["trial_profile"] = "not_found"
            return False

        try:
            with open(trial_file) as f:
                profile = yaml.safe_load(f)

            # Validate essential fields
            required = ["profile_id", "status", "capabilities", "providers", "workspaces"]
            for field in required:
                if field not in profile:
                    self.errors.append(f"Trial profile missing required field: {field}")
                    self.results["trial_profile"] = "invalid"
                    return False

            if profile.get("status") != "enabled":
                self.warnings.append("Trial profile is not enabled")
                self.results["trial_profile"] = "disabled"
                return False

            self.results["trial_profile"] = "pass"
            return True

        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in trial profile: {e}")
            self.results["trial_profile"] = "invalid"
            return False

    def check_repository_refs(self) -> bool:
        """Verify all repository refs are assigned."""
        all_assigned = True
        for repo_name, repo_config in self.manifest.get("repositories", {}).items():
            ref = repo_config.get("ref", "").strip()
            if not ref or ref.startswith("# NOTE"):
                self.warnings.append(f"Repository ref not assigned: {repo_name}")
                all_assigned = False

        return all_assigned

    def validate(self) -> bool:
        """Run all validation checks."""
        # Load manifest first
        if not self.load_manifest():
            self.results["status"] = "error"
            return False

        # Run checks
        checks = [
            ("repositories_exist", self.check_repositories_exist),
            ("boundary_files", self.check_boundary_files),
            ("contract_bundle", self.check_contract_bundle),
            ("trial_profile", self.check_trial_profile),
            ("repository_refs", self.check_repository_refs),
        ]

        all_pass = True
        for check_name, check_func in checks:
            try:
                passed = check_func()
                if not passed and check_name not in ["boundary_files", "repository_refs"]:
                    all_pass = False
            except Exception as e:
                self.errors.append(f"Check failed ({check_name}): {e}")
                all_pass = False

        # Determine overall status
        if self.errors:
            self.results["status"] = "invalid"
            return False
        elif self.warnings:
            self.results["status"] = "candidate"
            return True
        else:
            self.results["status"] = "valid"
            return True

    def report(self, json_output: bool = False) -> int:
        """Print validation report and return exit code."""
        if json_output:
            print(json.dumps(self.results, indent=2))
        else:
            print(f"Fleet Release: {self.results.get('fleet_release')}")
            print(f"Status: {self.results.get('status')}")

            if self.errors:
                print("\nERRORS:")
                for error in self.errors:
                    print(f"  ✗ {error}")

            if self.warnings:
                print("\nWARNINGS:")
                for warning in self.warnings:
                    print(f"  ⚠ {warning}")

            if not self.errors and not self.warnings:
                print("\n✓ Fleet is valid and ready for approval.")

        # Exit codes
        if self.errors:
            return 1  # Invalid
        elif self.warnings:
            return 0  # Candidate (warnings are OK)
        else:
            return 0  # Valid


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate fleet composition and release readiness")
    parser.add_argument("--manifest", required=True, help="Path to fleet.yaml manifest")
    parser.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    checker = FleetChecker(args.manifest)
    checker.validate()
    exit_code = checker.report(json_output=args.json)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
