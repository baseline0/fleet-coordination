#!/usr/bin/env python3
"""Fleet coordinator: validate fleet composition and release readiness.

Usage:
  fleet-check --manifest fleet.yaml --scope core
  fleet-check --manifest fleet.yaml --scope managed --json
  fleet-check --manifest fleet.yaml --scope trial
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml


class FleetChecker:
    """Validate fleet composition, contracts, and boundary state."""

    def __init__(self, manifest_file: str, scope: str = "core"):
        """Initialize checker with fleet manifest."""
        self.manifest_path = Path(manifest_file)
        self.manifest = None
        self.scope = scope  # core, managed, or trial
        self.errors = []
        self.warnings = []
        self.results = {
            "fleet_release": None,
            "scope": scope,
            "status": "invalid",
            "repositories": [],
            "checks": {
                "manifest": "pending",
                "repos": "pending",
                "refs": "pending",
                "boundaries": "pending",
                "contracts": "pending",
                "trial_profile": "pending",
            },
            "promotion_eligible": False,
        }

    def load_manifest(self) -> bool:
        """Load and validate fleet manifest file."""
        if not self.manifest_path.exists():
            self.errors.append(f"Manifest file not found: {self.manifest_path}")
            self.results["checks"]["manifest"] = "fail"
            return False

        try:
            with open(self.manifest_path) as f:
                self.manifest = yaml.safe_load(f)
            self.results["fleet_release"] = self.manifest.get("fleet_release")
            self.results["checks"]["manifest"] = "pass"
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in manifest: {e}")
            self.results["checks"]["manifest"] = "fail"
            return False

    def get_scope_repositories(self) -> list:
        """Get repositories for current scope."""
        if not self.manifest:
            return []

        scopes = self.manifest.get("fleet_scope", {})
        return scopes.get(self.scope, [])

    def validate_sha(self, repo_name: str, ref: str, repo_path: Path) -> tuple:
        """Validate SHA: format, existence in repo, and reachability.

        Returns: (is_valid: bool, reason: str)
        """
        # Check format: 40-character lowercase hex
        if not re.match(r"^[0-9a-f]{40}$", ref.lower()):
            return (False, "invalid_format: not 40-char hex")

        # Check if short SHA (would need .git to verify)
        if len(ref) < 40:
            return (False, "short_sha: use full 40-character SHA")

        # If repo exists locally, verify SHA
        git_dir = repo_path / ".git"
        if git_dir.exists():
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode != 0:
                    return (False, "sha_not_found: not reachable in repo")
                return (True, "valid")
            except subprocess.TimeoutExpired:
                return (False, "timeout: git operation timed out")
            except Exception as e:
                return (False, f"validation_error: {str(e)}")

        # If .git doesn't exist, accept as unverified (external repos)
        return (True, "unverified: repo not local")

    def check_repositories_exist(self) -> bool:
        """Verify repositories and refs are valid."""
        if not self.manifest:
            return False

        scope_repos = self.get_scope_repositories()
        all_valid = True

        for repo_name in scope_repos:
            repo_config = self.manifest.get("repositories", {}).get(repo_name)
            if not repo_config:
                self.errors.append(f"Repository not in manifest: {repo_name}")
                self.results["repositories"].append({
                    "id": repo_name,
                    "status": "error",
                    "reason": "not_in_manifest"
                })
                all_valid = False
                continue

            repo_path = Path(repo_config.get("source", ""))
            if not repo_path.is_absolute():
                repo_path = self.manifest_path.parent / repo_path

            # Check path exists
            if not repo_path.exists():
                self.errors.append(f"Repository not found: {repo_name} at {repo_path}")
                self.results["repositories"].append({
                    "id": repo_name,
                    "status": "error",
                    "reason": "path_not_found"
                })
                all_valid = False
                continue

            # Check SHA format and validity
            ref = repo_config.get("ref", "").strip()
            sha_valid, sha_reason = self.validate_sha(repo_name, ref, repo_path)

            repo_result = {
                "id": repo_name,
                "role": repo_config.get("role"),
                "lifecycle": repo_config.get("lifecycle"),
                "ref": ref,
                "ref_valid": sha_valid,
                "ref_reason": sha_reason if not sha_valid else None,
                "status": "pass" if sha_valid else "warning",
            }
            self.results["repositories"].append(repo_result)

            if not sha_valid:
                self.warnings.append(f"Repository {repo_name}: {sha_reason}")

        self.results["checks"]["repos"] = "pass" if all_valid else ("warn" if self.warnings else "pass")
        return all_valid

    def check_boundary_files(self) -> bool:
        """Verify boundary files exist and are valid."""
        if not self.manifest:
            return False

        scope_repos = self.get_scope_repositories()
        all_valid = True
        boundary_status = "pass"

        for repo_name in scope_repos:
            repo_config = self.manifest.get("repositories", {}).get(repo_name)
            if not repo_config:
                continue

            if not repo_config.get("required_boundaries"):
                continue

            repo_path = Path(repo_config.get("source", ""))
            if not repo_path.is_absolute():
                repo_path = self.manifest_path.parent / repo_path

            boundary_path = repo_config.get("boundary_path", ".fleet/boundaries.md")
            boundary_file = repo_path / boundary_path

            file_status = "present" if boundary_file.exists() else "missing"
            content_status = "not_checked"

            # Update repo result with boundary status
            for repo_result in self.results["repositories"]:
                if repo_result["id"] == repo_name:
                    repo_result["boundary_file"] = boundary_path
                    repo_result["boundary_file_status"] = file_status
                    repo_result["boundary_content_status"] = content_status
                    repo_result["status"] = "pass" if file_status == "present" else "warning"

            if file_status == "missing":
                lifecycle = repo_config.get("lifecycle", "")
                # Missing boundaries are errors for approved/mature, warnings otherwise
                if lifecycle in ["approved", "mature"]:
                    self.errors.append(f"REQUIRED: Boundary file missing: {repo_name}/{boundary_path}")
                    boundary_status = "fail"
                    all_valid = False
                else:
                    self.warnings.append(f"Boundary file missing: {repo_name}/{boundary_path} ({lifecycle})")
                    if boundary_status != "fail":
                        boundary_status = "warn"

        self.results["checks"]["boundaries"] = boundary_status
        return all_valid

    def check_contract_bundle(self) -> bool:
        """Verify contract artifact exists. Verification is separate."""
        scope_requirements = self.manifest.get("scope_requirements", {}).get(self.scope, {})
        artifact_required = scope_requirements.get("contract_artifact_required", False)

        contract_file = self.manifest_path.parent / self.manifest.get("governance", {}).get("contract_bundle", "")

        if not contract_file.exists():
            if artifact_required:
                self.errors.append(f"REQUIRED: Contract bundle not found: {contract_file}")
                self.results["checks"]["contracts"] = "fail"
                return False
            else:
                # Artifact not required for this scope
                self.results["checks"]["contracts"] = "pending"
                return True

        # Artifact exists; verification is separate check (pending)
        self.results["checks"]["contracts"] = "pending"  # Pending verification
        return True

    def check_trial_profile(self) -> bool:
        """Verify trial profile exists and is valid."""
        trial_file = self.manifest_path.parent / self.manifest.get("trial", {}).get("profile_file", "")

        if not trial_file.exists():
            self.warnings.append(f"Trial profile not found: {trial_file}")
            self.results["checks"]["trial_profile"] = "pending"
            return False

        try:
            with open(trial_file) as f:
                profile = yaml.safe_load(f)

            # Validate essential fields
            required = ["profile_id", "status", "capabilities", "providers", "workspaces"]
            for field in required:
                if field not in profile:
                    self.errors.append(f"Trial profile missing required field: {field}")
                    self.results["checks"]["trial_profile"] = "fail"
                    return False

            if profile.get("status") != "enabled":
                self.warnings.append("Trial profile is not enabled")
                self.results["checks"]["trial_profile"] = "pending"
                return False

            self.results["checks"]["trial_profile"] = "pass"
            return True

        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in trial profile: {e}")
            self.results["checks"]["trial_profile"] = "fail"
            return False

    def check_repository_refs(self) -> bool:
        """Verify repository refs are assigned per scope requirements."""
        scope_repos = self.get_scope_repositories()
        scope_requirements = self.manifest.get("scope_requirements", {}).get(self.scope, {})
        refs_required = scope_requirements.get("refs_required", True)

        all_assigned = True
        refs_status = "pass"

        for repo_name in scope_repos:
            repo_config = self.manifest.get("repositories", {}).get(repo_name)
            if not repo_config:
                continue

            ref = repo_config.get("ref", "").strip()
            if not ref or ref.startswith("# NOTE"):
                # Only warn/fail if this scope requires refs
                if refs_required:
                    self.warnings.append(f"Repository ref not assigned: {repo_name}")
                    all_assigned = False
                    refs_status = "warn"
                else:
                    # If scope doesn't require refs, report as pending
                    refs_status = "pending"

        self.results["checks"]["refs"] = refs_status
        return all_assigned

    def validate(self) -> bool:
        """Run all validation checks per scope requirements."""
        # Load manifest first
        if not self.load_manifest():
            self.results["status"] = "error"
            return False

        # Run checks
        checks = [
            ("repositories_exist", self.check_repositories_exist),
            ("boundary_files", self.check_boundary_files),
            ("repository_refs", self.check_repository_refs),
            ("contract_bundle", self.check_contract_bundle),
            ("trial_profile", self.check_trial_profile),
        ]

        for check_name, check_func in checks:
            try:
                check_func()
            except Exception as e:
                self.errors.append(f"Check failed ({check_name}): {e}")

        # Determine promotion eligibility based on scope requirements
        has_errors = bool(self.errors)
        has_warnings = bool(self.warnings)
        scope_requirements = self.manifest.get("scope_requirements", {}).get(self.scope, {})

        # Check what blocks promotion for this scope
        contract_verification_blocks = scope_requirements.get("contract_verification_blocks_promotion", False)
        contract_pending = self.results["checks"]["contracts"] == "pending"
        trial_pending = self.results["checks"]["trial_profile"] == "pending"

        # Promotion logic: errors always block, then check scope-specific gates
        if has_errors:
            self.results["status"] = "invalid"
            self.results["promotion_eligible"] = False
            return False
        elif has_warnings or (contract_pending and contract_verification_blocks) or trial_pending:
            self.results["status"] = "candidate"
            self.results["promotion_eligible"] = False
            return True
        else:
            self.results["status"] = "verified"
            self.results["promotion_eligible"] = True
            return True

    def report(self, json_output: bool = True) -> int:
        """Print validation report and return exit code."""
        if json_output:
            # Add errors and warnings to results
            self.results["errors"] = self.errors
            self.results["warnings"] = self.warnings
            print(json.dumps(self.results, indent=2))
        else:
            print(f"Fleet Release: {self.results.get('fleet_release')}")
            print(f"Status: {self.results.get('status')}")
            print(f"Scope: {self.results.get('scope')}")
            print(f"Promotion Eligible: {self.results.get('promotion_eligible')}")

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

            print(f"\nChecks:")
            for check, status in self.results["checks"].items():
                symbol = "✓" if status == "pass" else "⚠" if status == "warn" else "⏳" if status == "pending" else "✗"
                print(f"  {symbol} {check}: {status}")

        # Exit codes
        if self.errors:
            return 1  # Invalid
        elif self.warnings or self.results.get("checks", {}).get("contracts") == "pending":
            return 0  # Candidate (warnings are OK, pending checks are OK)
        else:
            return 0  # Valid


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate fleet composition and release readiness")
    parser.add_argument("--manifest", required=True, help="Path to fleet.yaml manifest")
    parser.add_argument("--scope", choices=["core", "managed", "trial"], default="core",
                        help="Scope to validate (default: core)")
    parser.add_argument("--json", action="store_true", default=True, help="Output JSON format (default: true)")
    parser.add_argument("--text", action="store_true", help="Output text format")

    args = parser.parse_args()

    json_output = not args.text  # JSON by default unless --text is specified

    checker = FleetChecker(args.manifest, scope=args.scope)
    checker.validate()
    exit_code = checker.report(json_output=json_output)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
