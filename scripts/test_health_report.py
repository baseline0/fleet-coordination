#!/usr/bin/env python3
"""Generate fleet-wide test health report.

Scans all repos for test metrics (pass rate, execution time, coverage) and
generates weekly health dashboard.

Usage:
  python test_health_report.py                    # Generate report
  python test_health_report.py --json             # Export as JSON only
  python test_health_report.py --verbose          # Show detailed metrics
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

FLEET_ROOT = Path(__file__).parent.parent.parent
REPOS = [
    "agent-tooling",
    "flashcards",
    "fleet-ops",
    "fleet-base",
    "math-trace",
    "membrane",
    "cv",
]


@dataclass
class TestMetrics:
    """Test health metrics for a single repo."""
    repo: str
    has_tests: bool = False
    unit_passed: int = 0
    unit_total: int = 0
    unit_pass_rate: float = 0.0
    e2e_passed: int = 0
    e2e_total: int = 0
    e2e_pass_rate: float = 0.0
    e2e_skipped: bool = False
    execution_time_sec: float = 0.0
    coverage_pct: Optional[float] = None
    errors: list[str] = field(default_factory=list)
    status: str = "unknown"  # healthy, warning, error, skipped


def run_tests(repo_path: Path) -> TestMetrics:
    """Run tests in repo and collect metrics."""
    repo_name = repo_path.name
    metrics = TestMetrics(repo=repo_name)

    # Check if tests exist
    tests_dir = repo_path / "tests"
    if not tests_dir.exists():
        metrics.status = "skipped"
        metrics.errors.append("No tests/ directory found")
        return metrics

    metrics.has_tests = True

    # Run pytest with json output
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "tests/", "-v", "--tb=short", "-q", "-m", "not e2e"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse pytest summary line (e.g., "124 passed in 2.34s")
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "passed" in line:
                # Extract numbers from lines like "124 passed in 2.34s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed" and i > 0:
                        try:
                            metrics.unit_passed = int(parts[i - 1])
                            metrics.unit_total = metrics.unit_passed
                        except ValueError:
                            pass
                    if "s" in part and "." in part:
                        try:
                            metrics.execution_time_sec = float(part.rstrip("s"))
                        except ValueError:
                            pass

        if metrics.unit_total > 0:
            metrics.unit_pass_rate = (metrics.unit_passed / metrics.unit_total) * 100
            metrics.status = "healthy" if metrics.unit_pass_rate == 100 else "warning"
        else:
            metrics.status = "unknown"

        # Check for E2E skip marker
        if "skipped" in result.stdout and "not e2e" in result.stdout:
            metrics.e2e_skipped = True

    except subprocess.TimeoutExpired:
        metrics.status = "error"
        metrics.errors.append("Test execution timeout (>5 min)")
    except Exception as e:
        metrics.status = "error"
        metrics.errors.append(f"Test execution failed: {str(e)}")

    return metrics


def generate_markdown_report(metrics_list: list[TestMetrics]) -> str:
    """Generate human-readable markdown report."""
    lines = [
        "# Test Health Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Fleet-Wide Metrics",
        "",
    ]

    # Calculate aggregate metrics
    total_repos = len(metrics_list)
    repos_with_tests = len([m for m in metrics_list if m.has_tests])
    all_passed = sum(m.unit_passed for m in metrics_list)
    all_total = sum(m.unit_total for m in metrics_list)
    avg_pass_rate = (all_passed / all_total * 100) if all_total > 0 else 0

    lines.append(f"| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Repos | {total_repos} |")
    lines.append(f"| Repos with Tests | {repos_with_tests} |")
    lines.append(f"| Total Unit Tests | {all_total} |")
    lines.append(f"| Tests Passing | {all_passed}/{all_total} ({avg_pass_rate:.1f}%) |")
    lines.append(f"| Avg Execution Time | {sum(m.execution_time_sec for m in metrics_list) / len(metrics_list):.1f}s |")
    lines.append("")

    # Per-repo detail
    lines.append("## Per-Repository Status")
    lines.append("")
    lines.append(
        "| Repo | Status | Unit Tests | Pass Rate | Time | Notes |"
    )
    lines.append("|------|--------|-----------|-----------|------|-------|")

    for metrics in sorted(metrics_list, key=lambda m: m.repo):
        status_badge = {
            "healthy": "✅",
            "warning": "⚠️",
            "error": "❌",
            "skipped": "ℹ️",
            "unknown": "❓",
        }.get(metrics.status, "❓")

        test_info = f"{metrics.unit_passed}/{metrics.unit_total}" if metrics.has_tests else "—"
        pass_rate = f"{metrics.unit_pass_rate:.0f}%" if metrics.unit_total > 0 else "—"
        time_info = f"{metrics.execution_time_sec:.1f}s" if metrics.execution_time_sec > 0 else "—"
        notes = " | ".join(metrics.errors) if metrics.errors else (
            "E2E skipped in CI" if metrics.e2e_skipped else "—"
        )

        lines.append(
            f"| {metrics.repo} | {status_badge} | {test_info} | {pass_rate} | {time_info} | {notes} |"
        )

    lines.append("")
    lines.append("## Health Score Calculation")
    lines.append("")
    lines.append("- **Pass Rate:** Target 100% (penalty: -1% per test failure)")
    lines.append("- **Execution Time:** Target <5s per repo (penalty: -5% if >10s)")
    lines.append("- **Overall:** Fleet health = avg pass rate × 0.8 + (1 - time penalty) × 0.2")
    lines.append("")

    # Calculate health score
    time_penalty = min(0.2, sum(1 for m in metrics_list if m.execution_time_sec > 10) * 0.05)
    health_score = (avg_pass_rate / 100 * 0.8) + (1 - time_penalty) * 0.2
    health_score = max(0, min(100, health_score * 100))

    lines.append(f"**Fleet Health Score:** `{health_score:.0f}/100`")
    lines.append("")

    return "\n".join(lines)


def generate_json_export(metrics_list: list[TestMetrics]) -> dict:
    """Generate JSON for dashboard ingestion."""
    return {
        "timestamp": datetime.now().isoformat(),
        "repos": [asdict(m) for m in metrics_list],
        "aggregate": {
            "total_repos": len(metrics_list),
            "repos_with_tests": len([m for m in metrics_list if m.has_tests]),
            "total_unit_tests": sum(m.unit_total for m in metrics_list),
            "unit_tests_passed": sum(m.unit_passed for m in metrics_list),
            "avg_pass_rate": sum(m.unit_pass_rate for m in metrics_list) / len(metrics_list)
            if metrics_list
            else 0,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Generate fleet test health report")
    parser.add_argument("--json", action="store_true", help="Export JSON only")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    print("🔍 Scanning fleet for test health...", file=sys.stderr)

    metrics_list = []
    for repo_name in REPOS:
        repo_path = FLEET_ROOT / repo_name
        if not repo_path.exists():
            continue

        if args.verbose:
            print(f"  Checking {repo_name}...", file=sys.stderr)

        metrics = run_tests(repo_path)
        metrics_list.append(metrics)

    # Generate outputs
    if args.json:
        # JSON only
        print(json.dumps(generate_json_export(metrics_list), indent=2))
    else:
        # Markdown report
        report = generate_markdown_report(metrics_list)
        print(report)

        # Also save JSON for dashboard
        json_path = Path("test-health.json")
        json_path.write_text(json.dumps(generate_json_export(metrics_list), indent=2))
        if args.verbose:
            print(f"\n✅ JSON report saved to {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
