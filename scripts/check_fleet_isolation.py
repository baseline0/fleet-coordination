#!/usr/bin/env python3
"""Verify fleet-coordination has no fleet dependencies (Python equivalent to import-linter).

Since fleet-coordination has no Python package root, we use static checks:
1. No fleet distribution in pyproject.toml
2. No fleet imports in Python source/scripts/tests
"""

import subprocess
import sys
from pathlib import Path


def check_dependencies() -> bool:
    """Check pyproject.toml for fleet distributions."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("❌ pyproject.toml not found")
        return False

    with open(pyproject) as f:
        content = f.read()

    fleet_dists = ["fleet-base", "fleet-agents", "fleet-toolbox", "fleet-ops", "fleet-spec"]
    found_deps = []

    for dist in fleet_dists:
        if dist in content:
            # Check if it's actually a dependency, not just in a comment
            for line in content.split("\n"):
                if dist in line and ("dependencies" in content[:content.index(line)] or "fleet" in line):
                    found_deps.append(f"  {line.strip()}")

    if found_deps:
        print("❌ Fleet dependencies found in pyproject.toml:")
        for dep in found_deps:
            print(dep)
        return False

    print("✅ No fleet distributions in dependencies")
    return True


def check_imports() -> bool:
    """Check Python files for fleet imports."""
    fleet_roots = ["fleet_base", "tooling", "toolboxes", "fleet_ops", "fleet_experiment"]

    result = subprocess.run(
        [
            "grep",
            "-r",
            "--include=*.py",
            "-E",
            f"^(from|import) ({('|'.join(fleet_roots))})",
        ],
        cwd=".",
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:  # Found matches
        print("❌ Fleet imports found:")
        for line in result.stdout.strip().split("\n"):
            if line:
                print(f"  {line}")
        return False

    print("✅ No fleet imports in Python code")
    return True


def main():
    """Run all checks."""
    print("🔍 Checking fleet-coordination isolation...\n")

    checks = [
        ("Dependencies", check_dependencies()),
        ("Imports", check_imports()),
    ]

    all_pass = all(result for _, result in checks)

    print("\n" + "=" * 50)
    if all_pass:
        print("✅ fleet-coordination is properly isolated")
        return 0
    else:
        print("❌ fleet-coordination isolation violations found")
        return 1


if __name__ == "__main__":
    sys.exit(main())
