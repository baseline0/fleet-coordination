#!/usr/bin/env python3
"""Collect six-repository inventory for fleet architecture validation.

Produces machine-readable JSON table with facts (not design choices):
- Repository metadata
- Package distribution and import roots
- Existing governance metadata
- Boundary enforcement configs
- Dependency declarations
- Actual import patterns
- CI entry points
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPOS = ["fleet-base", "fleet-agents", "fleet-coordination", "fleet-ops", "fleet-spec", "fleet-toolbox"]
PROJECT_ROOT = Path("/home/mark/projects")


def run(cmd: str, cwd: Path | None = None) -> str:
    """Run command and return stdout."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout.strip()
    except Exception as e:
        return f"ERROR: {e}"


def get_repo_revision(repo_path: Path) -> str:
    """Get Git HEAD revision."""
    return run("git rev-parse HEAD", cwd=repo_path)


def get_repo_working_state(repo_path: Path) -> dict[str, Any]:
    """Check if working tree is clean."""
    status = run("git status --porcelain", cwd=repo_path)
    untracked = run("git ls-files --others --exclude-standard", cwd=repo_path)
    return {
        "is_clean": status == "",
        "untracked_files": untracked.count("\n") if untracked else 0,
    }


def get_package_name(repo_path: Path) -> str:
    """Extract project.name from pyproject.toml."""
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        for line in content.split("\n"):
            if line.startswith('name = "'):
                return line.split('"')[1]
    return "UNKNOWN"


def get_import_roots(repo_path: Path) -> list[str]:
    """Discover top-level Python packages under src/."""
    src = repo_path / "src"
    if not src.exists():
        return []

    roots = []
    for item in src.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            roots.append(item.name)
    return sorted(roots)


def get_fleet_files(repo_path: Path) -> dict[str, str]:
    """Find .fleet metadata files."""
    fleet_dir = repo_path / ".fleet"
    if not fleet_dir.exists():
        return {}

    files = {}
    for f in fleet_dir.iterdir():
        if f.is_file():
            files[f.name] = f.relative_to(repo_path).as_posix()
    return files


def get_importlinter_config(repo_path: Path) -> dict[str, Any]:
    """Check for importlinter configuration."""
    config_file = repo_path / ".importlinter"
    if config_file.exists():
        return {
            "exists": True,
            "path": config_file.relative_to(repo_path).as_posix(),
        }
    return {"exists": False}


def get_declared_fleet_deps(repo_path: Path) -> list[str]:
    """Extract declared fleet dependencies from pyproject.toml."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return []

    content = pyproject.read_text()
    deps = []
    in_deps = False

    for line in content.split("\n"):
        if line.startswith("dependencies"):
            in_deps = True
        elif in_deps and line.startswith("]"):
            break
        elif in_deps and "fleet-" in line:
            # Extract distribution name
            if "@" in line:
                name = line.split('"')[1]
            else:
                name = line.split('"')[1]
            if name.startswith("fleet-"):
                deps.append(name)

    return sorted(deps)


def get_actual_fleet_imports(repo_path: Path) -> dict[str, Any]:
    """Scan for actual fleet_* imports in source code."""
    src = repo_path / "src"
    if not src.exists():
        return {"imports_found": 0, "packages": []}

    # Scan for 'from fleet_' imports
    packages = set()
    count = 0

    for py_file in src.rglob("*.py"):
        content = py_file.read_text(errors="ignore")
        for line in content.split("\n"):
            if line.startswith("from fleet_"):
                pkg = line.split()[1].split(".")[0]
                packages.add(pkg)
                count += 1

    return {
        "imports_found": count,
        "packages": sorted(packages),
    }


def get_ci_entry_points(repo_path: Path) -> dict[str, Any]:
    """Find CI workflow files and justfile commands."""
    workflows = []

    # GitHub Actions
    gh_workflows = repo_path / ".github" / "workflows"
    if gh_workflows.exists():
        workflows.extend([f.name for f in gh_workflows.glob("*.yml")])

    # Justfile
    justfile = repo_path / "justfile"
    just_cmds = []
    if justfile.exists():
        content = justfile.read_text()
        for line in content.split("\n"):
            if line and not line.startswith(" ") and not line.startswith("\t") and ":" in line:
                cmd = line.split(":")[0].strip()
                if cmd and not cmd.startswith("#"):
                    just_cmds.append(cmd)

    return {
        "github_workflows": workflows,
        "justfile_commands": sorted(set(just_cmds)),
    }


def collect_inventory() -> dict[str, Any]:
    """Collect inventory for all six repositories."""
    inventory = {
        "timestamp": run("date -u +%Y-%m-%dT%H:%M:%SZ"),
        "collection_tool": "collect_inventory.py",
        "repositories": {},
    }

    for repo in REPOS:
        repo_path = PROJECT_ROOT / repo
        if not repo_path.exists():
            print(f"❌ {repo} not found at {repo_path}", file=sys.stderr)
            continue

        print(f"📋 Collecting {repo}...", file=sys.stderr)

        inventory["repositories"][repo] = {
            "repository_path": repo,
            "repository_revision": get_repo_revision(repo_path),
            "working_state": get_repo_working_state(repo_path),
            "package_distribution_name": get_package_name(repo_path),
            "python_import_roots": get_import_roots(repo_path),
            "fleet_metadata_files": get_fleet_files(repo_path),
            "importlinter_config": get_importlinter_config(repo_path),
            "declared_fleet_dependencies": get_declared_fleet_deps(repo_path),
            "actual_fleet_imports": get_actual_fleet_imports(repo_path),
            "ci_entry_points": get_ci_entry_points(repo_path),
        }

    return inventory


if __name__ == "__main__":
    try:
        inventory = collect_inventory()
        print(json.dumps(inventory, indent=2))
    except Exception as e:
        print(f"❌ Inventory collection failed: {e}", file=sys.stderr)
        sys.exit(1)
