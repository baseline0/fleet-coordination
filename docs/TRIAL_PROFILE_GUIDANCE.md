# Trial Profile Guidance

## Overview

Trial profiles define the explicit runtime policies and capability constraints for internal trials. They establish the boundary between what capabilities are available and what must be denied, enforced, or escalated during the trial period.

**Current Active Trial:** `internal-readonly-poc-v1`

## Trial Profile Structure

### Metadata Section

```yaml
metadata:
  version: "0.1.0"
  created_at: "2026-09-20T19:00:00Z"
  expires_at: "2026-10-18T23:59:59Z"
  extension_possible_until: "2026-10-11T23:59:59Z"
  trial_lead: "# NOTE: assign"
  contact_email: "# NOTE: assign"
```

- **version**: Semantic version of the trial profile schema
- **created_at**: Trial start timestamp (UTC)
- **expires_at**: Trial end date; profiles auto-disable after expiration
- **extension_possible_until**: Deadline for requesting trial extension
- **trial_lead**: Contact responsible for trial governance
- **contact_email**: Escalation contact for trial issues

### Capabilities Section

Defines which operations are allowed and which are denied.

**Allowed capabilities** (what agents/tools can do):
- `find-files`: Search and glob-match workspace files
- `read-workspace-file`: Read file contents
- `read-workspace-metadata`: Access workspace structure/metadata

**Denied capabilities** (what is explicitly blocked):
- `workspace-file-write`: No file modifications
- `workspace-file-delete`: No file deletions
- `organize-python-imports`: No code transformation tools
- `execute-command`: No arbitrary shell execution
- `delete-anything`: Catch-all deny for any delete operation

### Providers Section

Specifies which MCP servers/tools are available.

```yaml
providers:
  allowed:
    - vscode-workspace-mcp
  approval_required: false
  quarantine_available: true
```

- **allowed**: List of MCP providers permitted in this trial
- **approval_required**: If true, each operation needs explicit approval
- **quarantine_available**: If true, providers can be auto-quarantined on error

### Workspaces Section

Defines which workspaces agents can access.

```yaml
workspaces:
  allowlist:
    - workspace_id: "trial-vscode-workspace-mcp"
      path: "/home/mark/projects/vscode-workspace-mcp"
      description: "vscode-workspace-mcp repository (approved trial project)"
  blocked:
    - "all others"
```

- **allowlist**: Approved workspaces with paths and descriptions
- **blocked**: Pattern for blocked workspaces (e.g., "all others" = deny-by-default)

### Limits Section

Resource and rate limits for trial operations.

```yaml
limits:
  max_files_per_operation: 100
  max_results_per_operation: 500
  timeout_seconds: 30
  max_concurrent_operations: 2
  max_operations_per_run: 50
  max_retries: 1
```

- **max_files_per_operation**: Max files matched in a single find/search
- **max_results_per_operation**: Max results returned per operation
- **timeout_seconds**: Operation timeout in seconds
- **max_concurrent_operations**: Max parallel operations allowed
- **max_operations_per_run**: Max total operations per agent run
- **max_retries**: Max automatic retries on failure

### Security Section

Safety and isolation constraints.

```yaml
security:
  read_only: true
  deny_symlink_escape: true
  deny_sensitive_paths: true
  sandbox_mode: true
  output_truncation: true
```

- **read_only**: If true, no mutations allowed
- **deny_symlink_escape**: Prevent symlinks that escape the workspace
- **deny_sensitive_paths**: Block access to system paths (e.g., /etc, /root)
- **sandbox_mode**: Run operations in isolated environment
- **output_truncation**: Truncate large outputs to prevent memory exhaustion

### Approval Section

Approval requirements for different operation classes.

```yaml
approval:
  writes: required
  admin_operations: denied
  provider_modification: denied
```

- **writes**: "required" = approval needed for mutations, "denied" = all mutations blocked
- **admin_operations**: Approval for admin-level actions
- **provider_modification**: Approval for changing provider configuration

### Emergency Section

Controls for incident response.

```yaml
emergency:
  provider_quarantine_enabled: true
  global_kill_switch_enabled: true
  audit_failure_action: "deny_and_log"
```

- **provider_quarantine_enabled**: If true, failing providers are auto-quarantined
- **global_kill_switch_enabled**: If true, trial can be globally disabled
- **audit_failure_action**: Action on audit system failure ("deny_and_log", "allow_and_alert", etc.)

## Creating a New Trial Profile

1. **Copy template** from `trial/trial-profile-readonly-poc.yaml`
2. **Update metadata**:
   - New profile_id (e.g., `internal-dispatch-v1`)
   - expires_at (28 days from now)
   - extension_possible_until (7 days before expiry)
   - trial_lead and contact_email
3. **Define capabilities**:
   - List allowed operations in `capabilities.allowed`
   - List denied operations in `capabilities.denied`
4. **Assign workspaces**:
   - List approved workspace_ids and paths
   - Set block rule (usually "all others")
5. **Validate**:
   ```bash
   uv run python -c "import yaml; yaml.safe_load(open('trial/your-profile.yaml')); print('Valid')"
   ```
6. **Register in fleet-coordination**:
   - Commit to `trial/` directory
   - Document in governance changelog
   - Notify trial lead

## Enforcing Trial Profiles

Trial profiles are enforced by the fleet governance system:

1. **On agent startup**: Load active trial profile
2. **Per operation**: Check capabilities, limits, workspace access
3. **On error**: Apply emergency policies (quarantine, kill-switch)
4. **On expiry**: Auto-disable profile, deny all requests

## Escalation

For questions about trial scope or emergency interventions:
- **Trial questions**: Contact trial_lead
- **Emergency kill-switch**: Contact contact_email
- **Profile changes**: Submit PR with updated profile + rationale

---

**Last Updated:** 2026-09-20  
**Trial Profile Version:** 0.1.0
