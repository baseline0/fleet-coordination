#!/usr/bin/env python3
"""Phase A Trial Posture Audit — Static configuration and profile validation.

This tool performs read-only compliance checks on the internal trial environment.
It validates that the trial profile, repository declarations, and ownership
structures remain within the approved posture.

Usage:
    uv run python scripts/dev/trial_posture_audit.py \\
        --config scripts/dev/trial-audit.yaml \\
        --json-out results/trial-posture.json \\
        --text-out results/trial-posture.txt

Exit codes:
    0: pass or warnings only
    1: policy failure / trial unsafe
    2: audit tool / configuration error
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from ruamel.yaml import YAML
except ImportError:
    print("Error: ruamel.yaml required. Install with: uv add ruamel-yaml", file=sys.stderr)
    sys.exit(2)


class AuditCheck:
    """Represents a single compliance check result."""

    def __init__(
        self,
        check_id: str,
        category: str,
        status: str,
        message: str,
        evidence: list[str] | None = None,
        remediation: str | None = None,
        owner: str | None = None,
    ):
        self.check_id = check_id
        self.category = category
        self.status = status  # pass, warn, fail, pending, error
        self.message = message
        self.evidence = evidence or []
        self.remediation = remediation
        self.owner = owner

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.check_id,
            "category": self.category,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "owner": self.owner,
        }


class TrialPostureAudit:
    """Phase A static audit of trial profile and repository state."""

    def __init__(self, config_path: Path, project_root: Path):
        self.config_path = config_path
        self.project_root = project_root
        self.config: dict[str, Any] = {}
        self.checks: list[AuditCheck] = []
        self.start_time = datetime.now(timezone.utc)

        # Load configuration
        self._load_config()

    def _load_config(self) -> None:
        """Load audit configuration from YAML."""
        try:
            yaml = YAML()
            yaml.preserve_quotes = True
            with open(self.config_path) as f:
                self.config = yaml.load(f)
            if not self.config:
                raise ValueError("Config file is empty")
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="CONFIG-001",
                    category="configuration",
                    status="error",
                    message=f"Failed to load config: {e}",
                    remediation="Check YAML syntax and file permissions",
                    owner="audit-tool",
                )
            )
            raise

    def run(self) -> int:
        """Execute all Phase A checks. Return exit code."""
        try:
            # Phase A checks
            self._check_profile_exists()
            self._check_profile_parses()
            self._check_profile_unexpired()
            self._check_read_only_enforced()
            self._check_provider_allowlist()
            self._check_workspace_allowlist()
            self._check_repositories_declared()
            self._check_boundary_files()
            self._check_ownership_assigned()
            self._check_contract_version()

            return self._exit_code()
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="AUDIT-001",
                    category="audit",
                    status="error",
                    message=f"Audit execution failed: {e}",
                    remediation="Review audit tool logs",
                    owner="audit-tool",
                )
            )
            return 2

    def _check_profile_exists(self) -> None:
        """PROFILE-001: Trial profile file exists."""
        profile_path = self._resolve_path(
            self.config["trial_profile"]["path"]
        )

        if profile_path.exists():
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-001",
                    category="profile",
                    status="pass",
                    message="Trial profile file exists",
                    evidence=[str(profile_path.relative_to(self.project_root))],
                )
            )
        else:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-001",
                    category="profile",
                    status="fail",
                    message=f"Trial profile not found: {profile_path}",
                    evidence=[],
                    remediation="Create trial profile file at configured path",
                    owner="trial-lead",
                )
            )

    def _check_profile_parses(self) -> None:
        """PROFILE-002: Trial profile parses as valid YAML."""
        profile_path = self._resolve_path(
            self.config["trial_profile"]["path"]
        )

        try:
            yaml = YAML()
            with open(profile_path) as f:
                profile = yaml.load(f)
            if not profile or not isinstance(profile, dict):
                raise ValueError("Profile is empty or not a dict")

            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-002",
                    category="profile",
                    status="pass",
                    message="Trial profile parses successfully",
                    evidence=[str(profile_path.relative_to(self.project_root))],
                )
            )
            self._profile = profile  # Cache for later checks
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-002",
                    category="profile",
                    status="fail",
                    message=f"Trial profile parse error: {e}",
                    evidence=[],
                    remediation="Fix YAML syntax in trial profile",
                    owner="trial-lead",
                )
            )
            self._profile = None

    def _check_profile_unexpired(self) -> None:
        """PROFILE-003: Trial profile has not expired."""
        if not hasattr(self, "_profile") or self._profile is None:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-003",
                    category="profile",
                    status="pending",
                    message="Cannot check expiry; profile not loaded",
                    remediation="Fix profile parsing errors first",
                )
            )
            return

        try:
            profile = self._profile
            expires_at_str = profile.get("metadata", {}).get("expires_at")
            if not expires_at_str:
                raise ValueError("expires_at field missing from profile")

            # Parse ISO format timestamp
            expires_at = datetime.fromisoformat(
                expires_at_str.replace("Z", "+00:00")
            )
            now = datetime.now(timezone.utc)
            days_remaining = (expires_at - now).days

            if expires_at > now:
                status = "pass" if days_remaining > 7 else "warn"
                msg = (
                    f"Trial profile unexpired ({days_remaining} days remaining)"
                )
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-003",
                        category="profile",
                        status=status,
                        message=msg,
                        evidence=[expires_at_str],
                    )
                )
            else:
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-003",
                        category="profile",
                        status="fail",
                        message=f"Trial profile expired on {expires_at_str}",
                        evidence=[expires_at_str],
                        remediation="Request profile extension from trial-lead",
                        owner="trial-lead",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-003",
                    category="profile",
                    status="error",
                    message=f"Failed to validate expiry: {e}",
                    remediation="Check expires_at format in trial profile",
                    owner="trial-lead",
                )
            )

    def _check_read_only_enforced(self) -> None:
        """PROFILE-004: Read-only enforcement is configured."""
        if not hasattr(self, "_profile") or self._profile is None:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-004",
                    category="profile",
                    status="pending",
                    message="Cannot check read-only; profile not loaded",
                )
            )
            return

        try:
            profile = self._profile
            security = profile.get("security", {})
            read_only = security.get("read_only")
            denied_caps = profile.get("capabilities", {}).get("denied", [])

            # Check that write operations are in denied list
            write_ops = [
                "workspace-file-write",
                "workspace-file-delete",
                "workspace-replace",
            ]
            denied_cap_names = [cap["name"] if isinstance(cap, dict) else cap for cap in denied_caps]
            writes_denied = all(op in str(denied_caps) for op in write_ops)

            if read_only and writes_denied:
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-004",
                        category="profile",
                        status="pass",
                        message="Read-only enforcement configured",
                        evidence=[
                            "security.read_only: true",
                            "write operations in capabilities.denied",
                        ],
                    )
                )
            else:
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-004",
                        category="profile",
                        status="fail",
                        message="Read-only enforcement not properly configured",
                        evidence=[],
                        remediation="Ensure security.read_only=true and write operations denied",
                        owner="security-owner",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-004",
                    category="profile",
                    status="error",
                    message=f"Failed to validate read-only: {e}",
                    remediation="Check profile security section",
                    owner="security-owner",
                )
            )

    def _check_provider_allowlist(self) -> None:
        """PROFILE-005: Provider allowlist is non-empty and valid."""
        if not hasattr(self, "_profile") or self._profile is None:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-005",
                    category="profile",
                    status="pending",
                    message="Cannot check providers; profile not loaded",
                )
            )
            return

        try:
            profile = self._profile
            allowed_providers = profile.get("providers", {}).get("allowed", [])

            if allowed_providers and len(allowed_providers) > 0:
                provider_names = (
                    [p["name"] if isinstance(p, dict) else p for p in allowed_providers]
                    if allowed_providers
                    else []
                )
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-005",
                        category="profile",
                        status="pass",
                        message=f"Provider allowlist present ({len(provider_names)} provider(s))",
                        evidence=provider_names,
                    )
                )
            else:
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-005",
                        category="profile",
                        status="fail",
                        message="Provider allowlist is empty",
                        evidence=[],
                        remediation="Add approved providers to capabilities.allowed",
                        owner="trial-lead",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-005",
                    category="profile",
                    status="error",
                    message=f"Failed to validate provider allowlist: {e}",
                    remediation="Check providers section in trial profile",
                    owner="trial-lead",
                )
            )

    def _check_workspace_allowlist(self) -> None:
        """PROFILE-006: Workspace allowlist is non-empty."""
        if not hasattr(self, "_profile") or self._profile is None:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-006",
                    category="profile",
                    status="pending",
                    message="Cannot check workspaces; profile not loaded",
                )
            )
            return

        try:
            profile = self._profile
            allowlist = profile.get("workspaces", {}).get("allowlist", [])

            if allowlist and len(allowlist) > 0:
                workspace_ids = [
                    w["workspace_id"] if isinstance(w, dict) else str(w)
                    for w in allowlist
                ]
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-006",
                        category="profile",
                        status="pass",
                        message=f"Workspace allowlist present ({len(workspace_ids)} workspace(s))",
                        evidence=workspace_ids,
                    )
                )
            else:
                self.checks.append(
                    AuditCheck(
                        check_id="PROFILE-006",
                        category="profile",
                        status="fail",
                        message="Workspace allowlist is empty",
                        evidence=[],
                        remediation="Add approved workspaces to workspaces.allowlist",
                        owner="trial-lead",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="PROFILE-006",
                    category="profile",
                    status="error",
                    message=f"Failed to validate workspace allowlist: {e}",
                    remediation="Check workspaces section in trial profile",
                    owner="trial-lead",
                )
            )

    def _check_repositories_declared(self) -> None:
        """REPO-001: Trial repositories are declared in manifest."""
        try:
            manifest_path = self._resolve_path(
                self.config["manifest"]["path"]
            )
            yaml = YAML()
            with open(manifest_path) as f:
                manifest = yaml.load(f)

            trial_repos = self.config["scope"]["repositories"]
            declared_repos = manifest.get("repositories", {}).keys()

            missing = [r for r in trial_repos if r not in declared_repos]
            found = [r for r in trial_repos if r in declared_repos]

            if not missing:
                self.checks.append(
                    AuditCheck(
                        check_id="REPO-001",
                        category="repository",
                        status="pass",
                        message=f"All trial repositories declared ({len(found)} repos)",
                        evidence=found,
                    )
                )
            else:
                self.checks.append(
                    AuditCheck(
                        check_id="REPO-001",
                        category="repository",
                        status="fail",
                        message=f"Missing repositories in manifest: {missing}",
                        evidence=found,
                        remediation="Add missing repositories to repository-manifest.yaml",
                        owner="trial-lead",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="REPO-001",
                    category="repository",
                    status="error",
                    message=f"Failed to check manifest: {e}",
                    remediation="Check repository-manifest.yaml syntax",
                    owner="trial-lead",
                )
            )

    def _check_boundary_files(self) -> None:
        """REPO-003: Boundary files exist for trial repositories."""
        try:
            manifest_path = self._resolve_path(
                self.config["manifest"]["path"]
            )
            yaml = YAML()
            with open(manifest_path) as f:
                manifest = yaml.load(f)

            trial_repos = self.config["scope"]["repositories"]
            missing_files = []
            found_files = []

            for repo in trial_repos:
                repo_config = manifest.get("repositories", {}).get(repo, {})
                boundary_file = repo_config.get("boundary_file")

                if boundary_file:
                    boundary_path = self.project_root / repo / boundary_file
                    if boundary_path.exists():
                        found_files.append(
                            str(boundary_path.relative_to(self.project_root))
                        )
                    else:
                        missing_files.append(f"{repo}/{boundary_file}")

            if not missing_files:
                self.checks.append(
                    AuditCheck(
                        check_id="REPO-003",
                        category="repository",
                        status="pass",
                        message=f"All boundary files present ({len(found_files)} files)",
                        evidence=found_files,
                    )
                )
            else:
                status = "warn"  # Phase A: warn only; Phase C will enforce
                self.checks.append(
                    AuditCheck(
                        check_id="REPO-003",
                        category="repository",
                        status=status,
                        message=f"Missing boundary files: {missing_files}",
                        evidence=found_files,
                        remediation="Create BOUNDARIES.md files in trial repositories",
                        owner="trial-lead",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="REPO-003",
                    category="repository",
                    status="error",
                    message=f"Failed to check boundary files: {e}",
                    remediation="Check repository-manifest.yaml boundary_file fields",
                    owner="trial-lead",
                )
            )

    def _check_contract_version(self) -> None:
        """REPO-004: Contract version in manifest matches expected."""
        try:
            manifest_path = self._resolve_path(
                self.config["manifest"]["path"]
            )
            yaml = YAML()
            with open(manifest_path) as f:
                manifest = yaml.load(f)

            contract_version = manifest.get("contract_version")
            expected = self.config["manifest"]["expected_contract_version"]

            if contract_version == expected:
                self.checks.append(
                    AuditCheck(
                        check_id="REPO-004",
                        category="repository",
                        status="pass",
                        message=f"Contract version matches: {contract_version}",
                        evidence=[contract_version],
                    )
                )
            else:
                status = "warn"  # Phase A: warn only
                self.checks.append(
                    AuditCheck(
                        check_id="REPO-004",
                        category="repository",
                        status=status,
                        message=f"Contract version mismatch: {contract_version} (expected {expected})",
                        evidence=[contract_version],
                        remediation="Update contract_version in repository-manifest.yaml",
                        owner="trial-lead",
                    )
                )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="REPO-004",
                    category="repository",
                    status="error",
                    message=f"Failed to check contract version: {e}",
                    remediation="Check repository-manifest.yaml contract_version field",
                    owner="trial-lead",
                )
            )

    def _check_ownership_assigned(self) -> None:
        """OWN-001/002/003: Required ownership roles are assigned."""
        if not hasattr(self, "_profile") or self._profile is None:
            self.checks.append(
                AuditCheck(
                    check_id="OWN-001",
                    category="ownership",
                    status="pending",
                    message="Cannot check ownership; profile not loaded",
                )
            )
            return

        try:
            profile = self._profile
            metadata = profile.get("metadata", {})

            roles = {
                "trial_lead": "OWN-001",
                "security_owner": "OWN-002",
                "rollback_owner": "OWN-003",
            }

            for role_key, check_id in roles.items():
                role_value = metadata.get(role_key)

                if role_value and role_value not in (
                    "# NOTE: assign",
                    "",
                    None,
                ):
                    self.checks.append(
                        AuditCheck(
                            check_id=check_id,
                            category="ownership",
                            status="pass",
                            message=f"{role_key} assigned",
                            evidence=[role_value],
                        )
                    )
                else:
                    self.checks.append(
                        AuditCheck(
                            check_id=check_id,
                            category="ownership",
                            status="fail",
                            message=f"{role_key} not assigned in profile",
                            evidence=[],
                            remediation=f"Assign {role_key} in trial profile metadata",
                            owner="trial-lead",
                        )
                    )
        except Exception as e:
            self.checks.append(
                AuditCheck(
                    check_id="OWN-001",
                    category="ownership",
                    status="error",
                    message=f"Failed to validate ownership: {e}",
                    remediation="Check metadata section in trial profile",
                    owner="trial-lead",
                )
            )

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve path relative to project root."""
        path = Path(path_str)
        if path.is_absolute():
            return path
        return self.project_root / path

    def _exit_code(self) -> int:
        """Determine exit code based on check results."""
        statuses = [c.status for c in self.checks]

        if "error" in statuses:
            return 2
        if "fail" in statuses:
            return 1
        return 0

    def _promotion_eligible(self) -> bool:
        """Is the system eligible for promotion based on audit results?"""
        # Promotion requires: no fails, no errors, no pending required checks
        statuses = [c.status for c in self.checks]
        return (
            "fail" not in statuses
            and "error" not in statuses
            and "pending" not in statuses
        )

    def summary(self) -> dict[str, Any]:
        """Generate summary statistics."""
        status_counts = {"pass": 0, "warn": 0, "fail": 0, "pending": 0, "error": 0}
        for check in self.checks:
            status_counts[check.status] = status_counts.get(check.status, 0) + 1

        return {
            "audit_version": self.config.get("version", "0.1.0"),
            "scope": self.config["scope"]["name"],
            "checked_at": self.start_time.isoformat(),
            "status": (
                "fail"
                if "fail" in [c.status for c in self.checks]
                or "error" in [c.status for c in self.checks]
                else "pass"
            ),
            "promotion_eligible": self._promotion_eligible(),
            "checks": [c.to_dict() for c in self.checks],
            "summary": status_counts,
        }

    def write_json(self, output_path: Path) -> None:
        """Write results to JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(self.summary(), f, indent=2)

    def write_text(self, output_path: Path) -> None:
        """Write results to text file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            summary = self.summary()

            f.write("=" * 70 + "\n")
            f.write("TRIAL POSTURE AUDIT REPORT\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Scope: {summary['scope']}\n")
            f.write(f"Checked at: {summary['checked_at']}\n")
            f.write(f"Status: {summary['status'].upper()}\n")
            f.write(f"Promotion eligible: {summary['promotion_eligible']}\n\n")

            stats = summary["summary"]
            f.write("Summary:\n")
            f.write(f"  Pass:    {stats['pass']}\n")
            f.write(f"  Warn:    {stats['warn']}\n")
            f.write(f"  Fail:    {stats['fail']}\n")
            f.write(f"  Pending: {stats['pending']}\n")
            f.write(f"  Error:   {stats['error']}\n\n")

            f.write("=" * 70 + "\n")
            f.write("DETAILED FINDINGS\n")
            f.write("=" * 70 + "\n\n")

            for check in summary["checks"]:
                f.write(f"[{check['status'].upper()}] {check['id']}: {check['message']}\n")
                if check["evidence"]:
                    f.write(f"  Evidence: {', '.join(check['evidence'])}\n")
                if check["remediation"]:
                    f.write(f"  Remediation: {check['remediation']}\n")
                if check["owner"]:
                    f.write(f"  Owner: {check['owner']}\n")
                f.write("\n")


def main() -> int:
    """Parse arguments and run audit."""
    parser = argparse.ArgumentParser(
        description="Trial posture audit — Phase A static checks"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("scripts/dev/trial-audit.yaml"),
        help="Path to audit config (default: scripts/dev/trial-audit.yaml)",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        help="Write JSON results to this file",
    )
    parser.add_argument(
        "--text-out",
        type=Path,
        help="Write text results to this file",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current working directory)",
    )

    args = parser.parse_args()

    try:
        audit = TrialPostureAudit(args.config, args.project_root)
        exit_code = audit.run()

        # Write outputs
        if args.json_out:
            audit.write_json(args.json_out)
        if args.text_out:
            audit.write_text(args.text_out)

        # Print summary to stdout
        summary = audit.summary()
        print(f"\nTrial Posture Audit Results")
        print(f"Scope: {summary['scope']}")
        print(
            f"Status: {summary['status'].upper()} (exit code: {exit_code})"
        )
        print(
            f"Checks: {summary['summary']['pass']} pass, "
            f"{summary['summary']['warn']} warn, "
            f"{summary['summary']['fail']} fail"
        )

        return exit_code

    except Exception as e:
        print(f"Audit failed: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
