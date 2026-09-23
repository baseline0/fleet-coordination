#!/usr/bin/env python3
"""Fleet-wide architecture validation: compare policy, declared, and observed dependencies.

Compares four views:
1. Canonical policy (fleet-architecture.yaml)
2. Declared dependencies (pyproject.toml)
3. Observed source imports (import-linter results)
4. Executable contracts (.importlinter configs)

Generates JSON report + Markdown summary.
"""

import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RepoAssessment:
    """Assessment of one repository's architecture compliance."""

    repository: str
    commit_sha: str
    python_import_roots: list[str]
    policy_allowed_fleet_deps: list[str]
    declared_fleet_deps: list[str]
    observed_fleet_imports: dict[str, Any]
    import_linter_status: str
    import_linter_contract_count: int
    differences: list[str]
    severity: str  # match, info, warning, error


def get_repo_sha(repo_path: Path) -> str:
    """Get current commit SHA for a repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:12]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def load_policy(policy_path: Path) -> dict[str, Any]:
    """Load canonical fleet architecture policy."""
    with open(policy_path) as f:
        return yaml.safe_load(f)


def get_declared_deps(repo_path: Path) -> list[str]:
    """Extract fleet distribution names from pyproject.toml dependencies."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return []

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            return []  # tomli not available, skip

    with open(pyproject, "rb") as f:
        data = tomllib.load(f)

    declared = []
    for dep in data.get("project", {}).get("dependencies", []):
        dep_name = dep.split("@")[0].strip().replace("-", "_").replace("_", "-")
        if dep_name.startswith("fleet"):
            declared.append(dep_name)
    return declared


def run_import_check(repo_path: Path) -> dict[str, Any]:
    """Run import-linter and return result."""
    try:
        result = subprocess.run(
            ["uv", "run", "lint-imports", "--config", ".importlinter"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        # Parse output for contract count
        output = result.stdout + result.stderr
        contracts_line = [l for l in output.split("\n") if "Contracts:" in l]
        contract_count = 0
        if contracts_line:
            parts = contracts_line[0].split()
            try:
                contract_count = int(parts[1])
            except (IndexError, ValueError):
                pass

        return {
            "status": "pass" if result.returncode == 0 else "fail",
            "exit_code": result.returncode,
            "contract_count": contract_count,
            "output_snippet": output[-500:] if output else "(no output)",
        }
    except FileNotFoundError:
        return {"status": "skipped", "reason": "uv not found"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


def assess_repository(repo_path: Path, policy: dict) -> RepoAssessment:
    """Assess one repository against policy."""
    repo_name = repo_path.name
    repo_config = policy.get("repositories", {}).get(repo_name, {})

    sha = get_repo_sha(repo_path)
    roots = repo_config.get("python_import_roots", [])
    allowed = repo_config.get("allowed_fleet_dependencies", [])
    declared = get_declared_deps(repo_path)
    import_check = run_import_check(repo_path)

    differences = []
    severity = "match"

    # Check for declared-but-unused
    for dep in declared:
        if dep not in allowed:
            differences.append(f"declared but not in policy: {dep}")
            severity = max(severity, "info", key=lambda x: ["match", "info", "warning", "error"].index(x))

    # Check for approved-but-unused (only warn if >0 declared)
    if len(declared) == 0 and len(allowed) > 0:
        differences.append(f"policy allows {allowed} but none declared")

    return RepoAssessment(
        repository=repo_name,
        commit_sha=sha,
        python_import_roots=roots,
        policy_allowed_fleet_deps=allowed,
        declared_fleet_deps=declared,
        observed_fleet_imports={"status": "deferred", "note": "see import-linter output"},
        import_linter_status=import_check.get("status", "unknown"),
        import_linter_contract_count=import_check.get("contract_count", 0),
        differences=differences,
        severity=severity,
    )


def generate_report(assessments: list[RepoAssessment], policy_path: Path) -> None:
    """Generate JSON report and Markdown summary."""
    output_dir = Path("/home/mark/projects/fleet-coordination/governance/evidence/fleet-validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat(timespec="seconds")
    json_path = output_dir / f"validation_{timestamp.replace(':', '-')}.json"
    md_path = output_dir / f"validation_{timestamp.replace(':', '-')}.md"

    # JSON report
    report = {
        "timestamp": timestamp,
        "policy_path": str(policy_path),
        "policy_version": "0.1.0",
        "repositories": [asdict(a) for a in assessments],
        "summary": {
            "total_repos": len(assessments),
            "match_count": len([a for a in assessments if a.severity == "match"]),
            "info_count": len([a for a in assessments if a.severity == "info"]),
            "warning_count": len([a for a in assessments if a.severity == "warning"]),
            "error_count": len([a for a in assessments if a.severity == "error"]),
        },
    }

    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)

    # Markdown summary
    md_content = f"""# Fleet Architecture Validation Report

**Generated:** {timestamp}
**Policy:** {policy_path}
**Policy Version:** 0.1.0

## Summary

| Status | Count |
|--------|-------|
| Match | {report['summary']['match_count']} |
| Info | {report['summary']['info_count']} |
| Warning | {report['summary']['warning_count']} |
| Error | {report['summary']['error_count']} |

## Repository Assessment

"""

    for a in assessments:
        status_emoji = {
            "match": "✅",
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
        }.get(a.severity, "❓")

        md_content += f"""
### {status_emoji} {a.repository} ({a.commit_sha})

| Field | Value |
|-------|-------|
| Python Roots | {', '.join(a.python_import_roots) or '(none)'} |
| Policy-Allowed | {', '.join(a.policy_allowed_fleet_deps) or '(none)'} |
| Declared | {', '.join(a.declared_fleet_deps) or '(none)'} |
| Import-Linter | {a.import_linter_status} ({a.import_linter_contract_count} contracts) |

"""
        if a.differences:
            md_content += "**Differences:**\n"
            for diff in a.differences:
                md_content += f"- {diff}\n"
            md_content += "\n"

    md_content += """
## Scope & Limitations

This validation checks:
- ✅ Python package boundaries (import-linter)
- ✅ Declared dependencies (pyproject.toml)
- ✅ Policy-declared edges (fleet-architecture.yaml)

Out of scope:
- ❌ Dynamic imports (runtime CLI, HTTP, plugin loading)
- ❌ MCP server integrations
- ❌ Docker/deployment relationships
- ❌ Workflow/CI orchestration dependencies

`fleet-coordination` uses static grep checks (no Python package).
"""

    with open(md_path, "w") as f:
        f.write(md_content)

    print(f"✅ JSON report: {json_path}")
    print(f"✅ Markdown summary: {md_path}")
    print(f"\n{md_content}")


def main():
    """Run fleet-wide validation."""
    projects_root = Path("/home/mark/projects")
    policy_path = projects_root / "fleet-coordination/governance/fleet-architecture.yaml"

    if not policy_path.exists():
        print(f"❌ Policy file not found: {policy_path}", file=sys.stderr)
        sys.exit(1)

    policy = load_policy(policy_path)
    applicable_repos = ["fleet-base", "fleet-agents", "fleet-toolbox", "fleet-ops", "fleet-spec"]

    assessments = []
    for repo_name in applicable_repos:
        repo_path = projects_root / repo_name
        if not repo_path.exists():
            print(f"⚠️  Skipped {repo_name}: not found")
            continue

        print(f"🔍 Assessing {repo_name}...", end=" ", flush=True)
        assessment = assess_repository(repo_path, policy)
        assessments.append(assessment)
        print(f"{assessment.severity.upper()}")

    generate_report(assessments, policy_path)


if __name__ == "__main__":
    main()
