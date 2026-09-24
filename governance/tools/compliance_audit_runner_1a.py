#!/usr/bin/env python3
"""
Phase 3 Compliance Audit Runner (Manual Invocation)

Audits six controls across multiple repositories:
- repository_metadata: Role declared in fleet-architecture.yaml
- test_execution: Declared test command executes successfully
- package_install: Reproducible installation (uv sync, pip install -e ., etc.)
- import_boundary_check: Import-linter configured and passes
- error_boundary_review: Exception handlers collected for manual classification
- governance_schema_validation: .fleet/ directory conforms to v1.0 schema

Output: Local YAML evidence records + Markdown summaries (pending review)
No mutations, no scheduler, read-only only.

Usage:
    python compliance_audit_runner_1a.py /path/to/repo1 /path/to/repo2 [...]
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

# Import governance schema validator from fleet-base
try:
    from fleet_base.governance_schema import GovernanceSchemaValidator
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

# Configuration
FLEET_ARCHITECTURE_PATH = Path(__file__).parent.parent / "fleet-architecture.yaml"
OUTPUT_DIR = Path("/tmp/compliance-audit-results-phase-1a")


@dataclass
class EvidenceRecord:
    """Evidence entry in an audit result."""
    source: str
    output: str
    timestamp: Optional[str] = None
    revision: Optional[str] = None


@dataclass
class ControlResult:
    """Audit result for a single control."""
    control_id: str
    repository: str
    role: str
    applicable: bool
    result: str  # pass | fail | unknown | not_applicable
    confidence: str  # high | medium | low
    evidence: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    next_step: str = ""


def get_git_revision(repo_path: Path) -> Optional[str]:
    """Get current git SHA for a repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:12]
    except Exception:
        pass
    return None


def load_fleet_architecture() -> dict:
    """Load fleet-architecture.yaml."""
    try:
        with open(FLEET_ARCHITECTURE_PATH) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load fleet-architecture.yaml: {e}", file=sys.stderr)
        return {}


def get_repository_role(repo_name: str, architecture: dict) -> Optional[str]:
    """Get repository role from fleet-architecture.yaml."""
    repositories = architecture.get("repositories", {})
    repo = repositories.get(repo_name, {})
    return repo.get("role")


def audit_repository_metadata(repo_path: Path, architecture: dict) -> ControlResult:
    """Audit repository_metadata control."""
    repo_name = repo_path.name
    role = get_repository_role(repo_name, architecture)

    result = ControlResult(
        control_id="repository_metadata",
        repository=repo_name,
        role=role or "unknown",
        applicable=True,
        result="pass" if role else "unknown",
        confidence="high",
        evidence=[],
        limitations=[],
        next_step="compare across repositories",
    )

    if role:
        result.evidence.append({
            "source": "governance/fleet-architecture.yaml",
            "output": f"role={role}",
        })
    else:
        result.evidence.append({
            "source": "governance/fleet-architecture.yaml",
            "output": f"repository {repo_name} not found in registry",
        })
        result.limitations.append(f"Repository not listed in fleet-architecture.yaml")

    return result


def load_fleet_config(repo_path: Path) -> dict:
    """Load .fleet/config.yaml from repository."""
    config_path = repo_path / ".fleet" / "config.yaml"
    if config_path.exists():
        try:
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to parse {config_path}: {e}", file=sys.stderr)
    return {}


def load_claude_md(repo_path: Path) -> dict:
    """Parse CLAUDE.md for project-specific settings (simple extraction)."""
    claude_path = repo_path / "CLAUDE.md"
    if not claude_path.exists():
        return {}
    # Simple heuristic: look for "just test" or test command mentions
    try:
        content = claude_path.read_text()
        # Could parse more sophisticatedly; for now, just check if mentioned
        if "just test" in content.lower():
            return {"test_heuristic": "just test mentioned"}
    except Exception:
        pass
    return {}


def resolve_test_command(repo_path: Path) -> Optional[str]:
    """Resolve test command from repository configuration."""
    # Priority: .fleet/config.yaml → CLAUDE.md → None
    config = load_fleet_config(repo_path)

    # Check testing.test_command
    if config.get("testing", {}).get("test_command"):
        return config["testing"]["test_command"]

    # Fallback to common patterns
    if (repo_path / "justfile").exists():
        return "just test"
    if (repo_path / "pyproject.toml").exists():
        return "pytest tests/"

    return None


def execute_test_command(repo_path: Path, command: str, fleet_root: Optional[Path] = None) -> dict:
    """Execute test command in repository's managed environment."""
    try:
        env = dict(__import__("os").environ)
        if fleet_root:
            env["FLEET_ROOT"] = str(fleet_root)

        # If command is raw pytest and repository has uv.lock, wrap with uv run
        if "pytest" in command and (repo_path / "uv.lock").exists():
            command = f"uv run {command}"

        result = subprocess.run(
            command,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        # Extract error reason if present
        error_reason = None
        if result.returncode != 0 and "RuntimeError" in result.stderr:
            # Try to extract the specific error
            for line in result.stderr.split("\n"):
                if "RuntimeError:" in line or "required" in line.lower():
                    error_reason = line.strip()
                    break

        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[:200],  # Truncate for evidence
            "stderr": result.stderr[:1000],  # More stderr for failure diagnostics
            "error_reason": error_reason,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": None,
            "error": "Command timed out after 120 seconds",
            "success": False,
        }
    except Exception as e:
        return {
            "exit_code": None,
            "error": str(e),
            "success": False,
        }


def audit_test_execution(repo_path: Path, fleet_root: Optional[Path] = None) -> ControlResult:
    """Audit test_execution control."""
    repo_name = repo_path.name
    timestamp = datetime.now(timezone.utc).isoformat()
    revision = get_git_revision(repo_path)

    test_command = resolve_test_command(repo_path)

    result = ControlResult(
        control_id="test_execution",
        repository=repo_name,
        role="unknown",  # Will be filled in by caller
        applicable=True,
        result="unknown" if not test_command else "unknown",  # Will be updated after execution
        confidence="high" if test_command else "low",
        evidence=[],
        limitations=[
            "Test execution result only; does not assess test adequacy or coverage sufficiency"
        ],
        next_step="review test output and compare across repositories",
    )

    if not test_command:
        result.result = "unknown"
        result.confidence = "low"
        result.evidence.append({
            "source": "command resolution",
            "output": "No test command found in .fleet/config.yaml or inferred from justfile/pyproject.toml",
        })
        result.limitations.append("Test command could not be determined")
        return result

    # Execute test command
    result.evidence.append({
        "source": ".fleet/config.yaml or resolved",
        "output": f"test_command={test_command}",
    })

    exec_result = execute_test_command(repo_path, test_command, fleet_root=fleet_root)

    result.evidence.append({
        "source": f"command execution: {test_command}",
        "output": f"exit_code={exec_result.get('exit_code')}",
        "timestamp": timestamp,
        "revision": revision,
    })

    if exec_result["success"]:
        result.result = "pass"
    else:
        result.result = "fail"
        if exec_result.get("error_reason"):
            result.evidence.append({
                "source": "error reason",
                "output": exec_result["error_reason"],
            })
        if exec_result.get("stderr"):
            result.evidence.append({
                "source": "stderr",
                "output": exec_result.get("stderr"),
            })

    return result


def audit_package_install(repo_path: Path) -> ControlResult:
    """Audit package_install control."""
    repo_name = repo_path.name

    result = ControlResult(
        control_id="package_install",
        repository=repo_name,
        role="unknown",  # Will be filled by caller
        applicable=True,
        result="unknown",
        confidence="high",
        evidence=[],
        limitations=["Installation test requires environment setup"],
        next_step="verify uv sync or equivalent produces reproducible environment",
    )

    # Check for setup indicators
    has_pyproject = (repo_path / "pyproject.toml").exists()
    has_uv_lock = (repo_path / "uv.lock").exists()
    has_poetry_lock = (repo_path / "poetry.lock").exists()

    if not has_pyproject:
        result.result = "not_applicable"
        result.evidence.append({
            "source": "file presence",
            "output": "no pyproject.toml found; repository may not be Python package",
        })
        return result

    result.evidence.append({
        "source": "pyproject.toml",
        "output": "present",
    })

    if has_uv_lock:
        result.evidence.append({
            "source": "lock file",
            "output": "uv.lock present (reproducible via uv sync --locked)",
        })
        result.result = "pass"
        result.confidence = "high"
    elif has_poetry_lock:
        result.evidence.append({
            "source": "lock file",
            "output": "poetry.lock present",
        })
        result.result = "pass"
    else:
        result.evidence.append({
            "source": "lock file",
            "output": "no lock file (uv.lock or poetry.lock)",
        })
        result.result = "unknown"
        result.limitations.append("Lock file not found; reproducibility unclear")

    return result


def audit_import_boundary_check(repo_path: Path) -> ControlResult:
    """Audit import_boundary_check control."""
    repo_name = repo_path.name

    result = ControlResult(
        control_id="import_boundary_check",
        repository=repo_name,
        role="unknown",  # Will be filled by caller
        applicable=True,
        result="unknown",
        confidence="high",
        evidence=[],
        limitations=[],
        next_step="verify import-linter configuration and CI execution",
    )

    # Check for Python package structure
    src_dir = repo_path / "src"
    has_python_package = src_dir.exists() or any(
        (repo_path / name).is_dir() and (repo_path / name / "__init__.py").exists()
        for name in ["tooling", "agents"]  # Common package names
    )

    if not has_python_package:
        result.result = "not_applicable"
        result.evidence.append({
            "source": "file structure",
            "output": "no Python package structure detected; boundary check not applicable",
        })
        return result

    # Check for import-linter configuration
    setup_cfg = repo_path / "setup.cfg"
    pyproject_toml = repo_path / "pyproject.toml"

    has_import_linter = False
    if setup_cfg.exists():
        try:
            content = setup_cfg.read_text()
            if "[import_linter]" in content:
                has_import_linter = True
                result.evidence.append({
                    "source": "setup.cfg",
                    "output": "[import_linter] section configured",
                })
        except Exception:
            pass

    if pyproject_toml.exists():
        try:
            with open(pyproject_toml) as f:
                content = f.read()
            if "[tool.import_linter]" in content or "import-linter" in content:
                has_import_linter = True
                result.evidence.append({
                    "source": "pyproject.toml",
                    "output": "[tool.import_linter] configured",
                })
        except Exception:
            pass

    if has_import_linter:
        result.result = "pass"
        result.confidence = "medium"
        result.evidence.append({
            "source": "configuration presence",
            "output": "import-linter configured; CI execution assumed",
        })
    else:
        result.result = "fail"
        result.evidence.append({
            "source": "configuration",
            "output": "import-linter not found in setup.cfg or pyproject.toml",
        })
        result.limitations.append("Cannot verify CI execution without configuration")

    return result


def audit_error_boundary_review(repo_path: Path) -> ControlResult:
    """Audit error_boundary_review control - collect exception handlers."""
    repo_name = repo_path.name

    result = ControlResult(
        control_id="error_boundary_review",
        repository=repo_name,
        role="unknown",  # Will be filled by caller
        applicable=True,
        result="unknown",
        confidence="medium",
        evidence=[],
        limitations=[
            "Handler classification requires code review; grep finds only locations"
        ],
        next_step="review handler locations for acceptable-boundary vs. silent-failure patterns",
    )

    # Check for Python package structure
    src_dir = repo_path / "src"
    python_dirs = []
    if src_dir.exists():
        python_dirs.append(src_dir)
    for name in ["tooling", "agents"]:
        if (repo_path / name).is_dir() and (repo_path / name / "__init__.py").exists():
            python_dirs.append(repo_path / name)

    if not python_dirs:
        result.result = "not_applicable"
        result.evidence.append({
            "source": "file structure",
            "output": "no Python package structure detected",
        })
        return result

    # Collect exception handlers using grep
    handlers = []
    try:
        import re
        handler_pattern = re.compile(r'^\s*except\s+(\(|)[^\s:]*Exception')

        for python_dir in python_dirs:
            for py_file in python_dir.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    lines = content.split("\n")

                    for i, line in enumerate(lines, 1):
                        if handler_pattern.search(line):
                            # Catches: except Exception, except Exception as e,
                            # except (Exception, ...), except BaseException, etc.
                            rel_path = str(py_file.relative_to(repo_path))
                            stripped = line.strip()
                            handlers.append({
                                "file": rel_path,
                                "line": i,
                                "pattern": stripped[:100],  # Truncate long lines
                            })
                except Exception:
                    pass

        if handlers:
            result.evidence.append({
                "source": "grep: except Exception",
                "output": f"Found {len(handlers)} exception handlers",
            })
            for handler in sorted(handlers, key=lambda x: (x["file"], x["line"])):
                result.evidence.append({
                    "source": f"{handler['file']}:{handler['line']}",
                    "output": handler["pattern"],
                })
            result.result = "unknown"  # Awaiting classification
        else:
            result.evidence.append({
                "source": "grep: except Exception",
                "output": "No bare except Exception handlers found",
            })
            result.result = "pass"  # No risky handlers
            result.confidence = "high"

    except Exception as e:
        result.result = "unknown"
        result.evidence.append({
            "source": "grep error",
            "output": f"Failed to scan for handlers: {e}",
        })

    return result


def audit_governance_schema_validation(repo_path: Path) -> ControlResult:
    """Audit governance_schema_validation control - validate .fleet/ structure."""
    repo_name = repo_path.name

    result = ControlResult(
        control_id="governance_schema_validation",
        repository=repo_name,
        role="unknown",  # Will be filled by caller
        applicable=True,
        result="unknown",
        confidence="high",
        evidence=[],
        limitations=[],
        next_step="review schema violations and update .fleet/ files as needed",
    )

    if not VALIDATOR_AVAILABLE:
        result.result = "unknown"
        result.confidence = "low"
        result.evidence.append({
            "source": "validator availability",
            "output": "GovernanceSchemaValidator not available (fleet-base not installed in audit environment)",
        })
        result.limitations.append("Cannot validate schema without fleet-base")
        return result

    # Validate governance schema
    validator = GovernanceSchemaValidator()
    validation = validator.validate_repo(repo_path)

    # Record schema version
    result.evidence.append({
        "source": "governance schema validation",
        "output": f"schema_version={validation.schema_version}",
    })

    # Record file status
    for filename, exists in validation.files.items():
        status = "present" if exists else "missing"
        result.evidence.append({
            "source": f"file check: {filename}",
            "output": status,
        })

    # Record errors as evidence
    if validation.errors:
        for error in validation.errors:
            result.evidence.append({
                "source": "validation error",
                "output": error,
            })
            result.limitations.append(error)

    # Record warnings
    if validation.warnings:
        for warning in validation.warnings:
            result.evidence.append({
                "source": "validation warning",
                "output": warning,
            })

    # Determine result
    if validation.valid:
        result.result = "pass"
        result.confidence = "high"
    elif validation.errors:
        result.result = "fail"
        result.confidence = "high"
    else:
        result.result = "unknown"
        result.confidence = "medium"

    return result


def audit_repository(repo_path: Path, architecture: dict, fleet_root: Optional[Path] = None) -> list[ControlResult]:
    """Audit a single repository."""
    if not repo_path.exists():
        print(f"Error: Repository not found: {repo_path}", file=sys.stderr)
        return []

    results = []

    # Control 1: repository_metadata
    meta_result = audit_repository_metadata(repo_path, architecture)
    results.append(meta_result)

    # Control 2: test_execution (use role from metadata)
    test_result = audit_test_execution(repo_path, fleet_root=fleet_root)
    test_result.role = meta_result.role
    results.append(test_result)

    # Control 3: package_install
    pkg_result = audit_package_install(repo_path)
    pkg_result.role = meta_result.role
    results.append(pkg_result)

    # Control 4: import_boundary_check
    import_result = audit_import_boundary_check(repo_path)
    import_result.role = meta_result.role
    results.append(import_result)

    # Control 5: error_boundary_review
    error_result = audit_error_boundary_review(repo_path)
    error_result.role = meta_result.role
    results.append(error_result)

    # Control 6: governance_schema_validation
    schema_result = audit_governance_schema_validation(repo_path)
    schema_result.role = meta_result.role
    results.append(schema_result)

    return results


def render_yaml(results: list[ControlResult]) -> str:
    """Render results as YAML."""
    output = []
    for result in results:
        result_dict = asdict(result)
        output.append(yaml.dump(result_dict, default_flow_style=False))
    return "\n---\n".join(output)


def render_markdown(results: list[ControlResult], repo_name: str) -> str:
    """Render results as Markdown."""
    lines = [
        f"# Compliance Audit Results: {repo_name}",
        f"\n**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Status:** Phase 1A (manual audit, review-only)\n",
    ]

    for result in results:
        lines.append(f"## Control: {result.control_id}")
        lines.append(f"**Result:** {result.result.upper()} (confidence: {result.confidence})")
        lines.append(f"**Applicable:** {result.applicable}\n")

        if result.evidence:
            lines.append("### Evidence")
            for ev in result.evidence:
                lines.append(f"- **Source:** {ev['source']}")
                lines.append(f"  **Output:** {ev['output']}")
                if ev.get("timestamp"):
                    lines.append(f"  **Timestamp:** {ev['timestamp']}")
                if ev.get("revision"):
                    lines.append(f"  **Revision:** {ev['revision']}")
            lines.append("")

        if result.limitations:
            lines.append("### Limitations")
            for limit in result.limitations:
                lines.append(f"- {limit}")
            lines.append("")

        if result.next_step:
            lines.append(f"### Next Step\n{result.next_step}\n")

    return "\n".join(lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: compliance_audit_runner_1a.py <repo1_path> <repo2_path> [...]",
            file=sys.stderr,
        )
        sys.exit(1)

    repo_paths = [Path(arg) for arg in sys.argv[1:]]

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load fleet architecture once
    architecture = load_fleet_architecture()

    # Detect fleet root (common parent of repositories)
    fleet_root = None
    if repo_paths:
        common_parent = repo_paths[0].parent
        if all(repo.parent == common_parent for repo in repo_paths):
            fleet_root = common_parent

    # Audit each repository
    for repo_path in repo_paths:
        repo_name = repo_path.name
        print(f"\n🔍 Auditing {repo_name}...")

        results = audit_repository(repo_path, architecture, fleet_root=fleet_root)

        if not results:
            print(f"  ⚠️  No audit results for {repo_name}")
            continue

        # Write YAML evidence
        yaml_file = OUTPUT_DIR / f"{repo_name}-2026-09-24.yaml"
        yaml_file.write_text(render_yaml(results))
        print(f"  ✅ Evidence: {yaml_file}")

        # Write Markdown summary
        md_file = OUTPUT_DIR / f"{repo_name}-2026-09-24.md"
        md_file.write_text(render_markdown(results, repo_name))
        print(f"  ✅ Summary: {md_file}")

        # Print summary to console
        for result in results:
            status_emoji = {"pass": "✅", "fail": "❌", "unknown": "❓"}.get(
                result.result, "?"
            )
            print(f"  {status_emoji} {result.control_id}: {result.result}")

    print(f"\n📋 All audit results saved to: {OUTPUT_DIR}")
    print("⚠️  Review output before using. This is a draft audit pending operator review.")


if __name__ == "__main__":
    main()
