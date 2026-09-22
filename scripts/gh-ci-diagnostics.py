#!/usr/bin/env python3
"""GitHub CI Diagnostic Utility: Diagnose fleet CI failures.

Queries GitHub Actions across the fleet to identify failing workflows,
categorize failures, and suggest remediation.

Usage:
    uv run scripts/gh-ci-diagnostics.py --fleet-root /home/mark/projects
    uv run scripts/gh-ci-diagnostics.py --fleet-root /home/mark/projects --repo flashcards
    uv run scripts/gh-ci-diagnostics.py --fleet-root /home/mark/projects --export json
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table


console = Console()


class FailureCategory(Enum):
    """Categories of CI failure."""

    LINT = "lint"  # Linting, formatting
    TEST = "test"  # Test failures
    BUILD = "build"  # Build failures
    COVERAGE = "coverage"  # Code coverage
    DEPENDENCY = "dependency"  # Dependency/version issues
    TIMEOUT = "timeout"  # Timeout
    UNKNOWN = "unknown"  # Unknown/other


@dataclass(frozen=True)
class WorkflowRun:
    """A GitHub Actions workflow run."""

    repo: str
    workflow_name: str
    status: str  # "completed", "in_progress", "queued"
    conclusion: str  # "success", "failure", "cancelled", etc.
    run_number: int
    run_id: int
    head_branch: str
    head_sha: str
    created_at: str
    updated_at: str
    html_url: str


@dataclass(frozen=True)
class FailureReport:
    """A categorized failure report."""

    repo: str
    workflow: str
    category: FailureCategory
    run_number: int
    branch: str
    url: str
    message: str  # Error message or summary


@dataclass(frozen=True)
class FleetCIDiagnostics:
    """Complete CI diagnostics for the fleet."""

    timestamp: str
    total_repos: int
    healthy_repos: int
    failing_repos: int
    failures_by_category: dict[str, int] = field(default_factory=dict)
    failure_reports: list[FailureReport] = field(default_factory=list)
    failure_trends: dict[str, int] = field(default_factory=dict)  # repo -> failure count


class GHCIDiagnosticsAgent:
    """Agent for diagnosing GitHub CI failures across the fleet."""

    def __init__(self, fleet_root: str = "/home/mark/projects"):
        """Initialize the agent.

        Args:
            fleet_root: Root directory for fleet repositories
        """
        self.fleet_root = Path(fleet_root)

    def scan_fleet(self, target_repo: Optional[str] = None) -> FleetCIDiagnostics:
        """Scan fleet for CI failures.

        Args:
            target_repo: If specified, scan only this repo; else scan all

        Returns:
            FleetCIDiagnostics with findings
        """
        from datetime import datetime

        # If target repo specified, scan just that; otherwise load manifest
        if target_repo:
            repos = [target_repo]
        else:
            manifest_path = self.fleet_root / "fleet-coordination" / "governance" / "repository-manifest.yaml"
            repos = self._load_repo_manifest(manifest_path) if manifest_path.exists() else []

        failure_reports: list[FailureReport] = []
        repos_with_failures = set()
        failures_by_category: dict[str, int] = {}
        failure_trends: dict[str, int] = {}

        console.print(f"[cyan]Scanning {len(repos)} repos for CI failures...[/cyan]")

        for repo in repos:
            runs = self._get_workflow_runs(repo)
            repo_failures = 0

            for run in runs:
                if run.conclusion == "failure":
                    category = self._categorize_failure(repo, run)
                    failures_by_category[category.value] = (
                        failures_by_category.get(category.value, 0) + 1
                    )

                    report = FailureReport(
                        repo=repo,
                        workflow=run.workflow_name,
                        category=category,
                        run_number=run.run_number,
                        branch=run.head_branch,
                        url=run.html_url,
                        message=f"Workflow {run.workflow_name} failed",
                    )
                    failure_reports.append(report)
                    repos_with_failures.add(repo)
                    repo_failures += 1

            failure_trends[repo] = repo_failures

        return FleetCIDiagnostics(
            timestamp=datetime.now().isoformat(),
            total_repos=len(repos),
            healthy_repos=len(repos) - len(repos_with_failures),
            failing_repos=len(repos_with_failures),
            failures_by_category=failures_by_category,
            failure_reports=failure_reports,
            failure_trends=failure_trends,
        )

    def _load_repo_manifest(self, manifest_path: Path) -> list[str]:
        """Load repository list from manifest.

        Args:
            manifest_path: Path to repository-manifest.yaml

        Returns:
            List of repository names
        """
        try:
            import yaml

            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)
                return [r.get("name") for r in manifest.get("repositories", [])]
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load manifest: {e}[/yellow]")
            return []

    def _get_workflow_runs(self, repo: str, limit: int = 5) -> list[WorkflowRun]:
        """Get recent workflow runs for a repo via GitHub CLI.

        Args:
            repo: Repository name
            limit: Number of recent runs to fetch

        Returns:
            List of WorkflowRun objects
        """
        try:
            result = subprocess.run(
                [
                    "gh",
                    "run",
                    "list",
                    "--repo",
                    f"baseline0/{repo}",
                    "--limit",
                    str(limit),
                    "--json",
                    "name,status,conclusion,number,databaseId,headBranch,headSha,createdAt,updatedAt,url",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                # Fallback: repo might not exist on GitHub
                return []

            runs = json.loads(result.stdout)
            return [
                WorkflowRun(
                    repo=repo,
                    workflow_name=run.get("name", "unknown"),
                    status=run.get("status", "unknown"),
                    conclusion=run.get("conclusion", "unknown"),
                    run_number=run.get("number", 0),
                    run_id=run.get("databaseId", 0),
                    head_branch=run.get("headBranch", "unknown"),
                    head_sha=run.get("headSha", "unknown"),
                    created_at=run.get("createdAt", ""),
                    updated_at=run.get("updatedAt", ""),
                    html_url=run.get("url", ""),
                )
                for run in runs
            ]
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
            return []

    def _categorize_failure(self, repo: str, run: WorkflowRun) -> FailureCategory:
        """Categorize a CI failure based on workflow name and other signals.

        Args:
            repo: Repository name
            run: WorkflowRun object

        Returns:
            FailureCategory
        """
        workflow_name = run.workflow_name.lower()

        if any(term in workflow_name for term in ["lint", "ruff", "format", "pre-commit"]):
            return FailureCategory.LINT
        elif any(term in workflow_name for term in ["test", "pytest", "unit"]):
            return FailureCategory.TEST
        elif any(term in workflow_name for term in ["coverage", "codecov"]):
            return FailureCategory.COVERAGE
        elif any(term in workflow_name for term in ["build", "docker", "compile"]):
            return FailureCategory.BUILD
        elif any(term in workflow_name for term in ["dep", "requirements", "lock"]):
            return FailureCategory.DEPENDENCY
        elif any(term in workflow_name for term in ["timeout"]):
            return FailureCategory.TIMEOUT
        else:
            return FailureCategory.UNKNOWN

    def report(self, diagnostics: FleetCIDiagnostics, export_format: Optional[str] = None) -> None:
        """Print diagnostics report.

        Args:
            diagnostics: FleetCIDiagnostics object
            export_format: "json", "csv", or None for table
        """
        if export_format == "json":
            data = asdict(diagnostics)
            data["failure_reports"] = [asdict(r) for r in diagnostics.failure_reports]
            console.print_json(data=data)
            return

        # Table format
        console.print(f"\n[bold cyan]Fleet CI Diagnostics[/bold cyan]")
        console.print(f"Timestamp: {diagnostics.timestamp}")
        console.print(f"Repos scanned: {diagnostics.total_repos}")
        console.print(f"  ✓ Healthy: {diagnostics.healthy_repos}")
        console.print(f"  ✗ Failing: {diagnostics.failing_repos}")

        if diagnostics.failures_by_category:
            console.print(f"\n[bold]Failures by Category:[/bold]")
            table = Table(title="Failure Categories")
            table.add_column("Category", style="cyan")
            table.add_column("Count", style="red")
            for category, count in sorted(
                diagnostics.failures_by_category.items(), key=lambda x: x[1], reverse=True
            ):
                table.add_row(category, str(count))
            console.print(table)

        if diagnostics.failure_reports:
            console.print(f"\n[bold]Failure Details:[/bold]")
            table = Table(title="Recent Failures")
            table.add_column("Repo", style="cyan")
            table.add_column("Workflow", style="yellow")
            table.add_column("Category", style="magenta")
            table.add_column("Branch", style="green")
            for report in sorted(
                diagnostics.failure_reports, key=lambda r: r.repo
            )[:20]:  # Limit to 20
                table.add_row(
                    report.repo,
                    report.workflow,
                    report.category.value,
                    report.branch,
                )
            console.print(table)

        if diagnostics.failure_trends:
            console.print(f"\n[bold]Failures per Repo:[/bold]")
            table = Table(title="Repo Failure Counts")
            table.add_column("Repo", style="cyan")
            table.add_column("Failure Count", style="red")
            for repo, count in sorted(
                diagnostics.failure_trends.items(), key=lambda x: x[1], reverse=True
            ):
                if count > 0:
                    table.add_row(repo, str(count))
            console.print(table)


def main(
    fleet_root: str = typer.Option(
        "/home/mark/projects", "--fleet-root", help="Fleet root directory"
    ),
    repo: Optional[str] = typer.Option(None, "--repo", help="Scan specific repo (optional)"),
    export: Optional[str] = typer.Option(
        None, "--export", help="Export format: json or csv"
    ),
):
    """Diagnose GitHub CI failures across the fleet."""
    agent = GHCIDiagnosticsAgent(fleet_root=fleet_root)
    diagnostics = agent.scan_fleet(target_repo=repo)
    agent.report(diagnostics, export_format=export)


if __name__ == "__main__":
    typer.run(main)
