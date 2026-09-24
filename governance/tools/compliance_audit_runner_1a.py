#!/usr/bin/env python3
"""
Phase 1A Compliance Audit Runner (Manual Invocation)

Audits two controls across two repositories:
- repository_metadata: Role declared in fleet-architecture.yaml
- test_execution: Declared test command executes successfully

Output: Local YAML evidence records + Markdown summaries (pending review)
No mutations, no scheduler, read-only only.

Usage:
    python compliance_audit_runner_1a.py /path/to/fleet-agents /path/to/fleet-ops
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

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
    """Execute test command and capture output."""
    try:
        env = dict(__import__("os").environ)
        if fleet_root:
            env["FLEET_ROOT"] = str(fleet_root)

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
