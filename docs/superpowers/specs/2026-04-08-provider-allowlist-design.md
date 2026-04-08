# Provider Allowlist Design

## Summary
Add a pack-scoped provider allowlist that can be configured during install and later updated via a command. The allowlist limits which providers `opencode-agent-pack` may use for routing and model selection. It does not change global OpenCode provider behavior outside this pack.
Status: implemented in Tasks 1-4; the notes below reflect the shipped behavior and the final acceptance criteria for this change.

## Background
Current routing logic reads the active provider and model from local OpenCode config and uses provider-aware defaults or discovery to choose models by tier. Before this change, the pack did not let users restrict routing to a subset of configured providers.

Local OpenCode state is currently split across multiple files:
- `~/.config/opencode/opencode.json`: active provider and default model
- `~/.local/share/opencode/auth.json`: authenticated providers
- `~/.cache/opencode/models.json`: cached provider model catalog

This means a provider allowlist lives in pack-owned configuration rather than overloading OpenCode's active provider setting.

## Goals
- Let users choose which providers this pack may use during install.
- Support multi-select provider configuration.
- Make provider configuration mandatory at install time, with Enter accepting the default full selection.
- Default to all locally configured or otherwise detectable providers.
- Let users reconfigure the allowlist later through a command.
- Enforce the allowlist in routing and provider/model discovery.
- Keep secrets out of pack-written config.

## Non-Goals
- Do not globally disable providers in OpenCode itself.
- Do not implement model-level allowlists in this change.
- Do not change OpenCode auth storage or model cache formats.
- Do not require network discovery for default configuration.

## User Experience

### Install Time
During install, the script presents a provider selection step.

Expected behavior:
- Candidate providers are discovered from local state.
- Multi-select is supported.
- Default selection is all candidates.
- Pressing Enter accepts the full selection.
- The step must always be shown in interactive installs.
- In non-interactive installs, the installer uses the default full selection and prints a note.

Example prompt shape:

```text
Select allowed providers for opencode-agent-pack
[1] openai
[2] openrouter
[3] minimax-cn-coding-plan
Enter comma-separated numbers, or press Enter for all:
```

### Post-Install
Users can reconfigure the allowlist with a command:

```text
/providers
```

Expected command capabilities:
- show current allowed providers
- show detected candidate providers
- let the user replace the current allowlist
- let the user reset to the default all-selected state

## Configuration

### Storage Location
Store pack-owned settings in `settings.json`, not `opencode.json`.

Final shape:

```json
{
  "opencodeAgentPack": {
    "allowedProviders": ["openai", "openrouter"]
  }
}
```

Rationale:
- `opencode.json` continues to represent OpenCode's active provider/model.
- `settings.json` is already preserved by installers and is appropriate for pack-specific extensions.

### Defaults
- If no allowlist is present, runtime behavior is equivalent to "all detected providers are allowed".
- Install-time configuration writes an explicit allowlist so the chosen state is durable.

## Provider Candidate Discovery

### Candidate Sources
Candidate providers are gathered in this order:
1. authenticated providers from `~/.local/share/opencode/auth.json`
2. provider keys from `~/.cache/opencode/models.json`
3. active provider from `~/.config/opencode/opencode.json`

The merged result is de-duplicated and sorted in a stable order that keeps the currently active provider near the front when present. In the implemented helper, the active provider is promoted to the front after merging local sources.

### Security Rule
Only provider names are read and persisted. Secrets from `auth.json` must never be copied into pack config, logs, prompts, or summaries.

## Routing and Discovery Behavior

### Router Inputs
`pack/tools/subagent_model_router.py` loads:
- current active provider/model from local OpenCode config
- allowed provider list from `settings.json`
- detected provider candidates from local OpenCode state
- provider model catalog from `~/.cache/opencode/models.json` when available

### Enforcement
The router must enforce the allowlist before model selection:
- only allowed providers can contribute available models
- provider auto-detection must be constrained by the allowlist
- provider discovery flags must not expand outside the allowlist

### Fallback Rules
If the current active provider is allowed:
- use it as the primary provider context

If the current active provider is not allowed:
- emit a warning
- fall back to the first allowed provider that has usable model data

If no allowed provider has usable model data:
- fail clearly instead of silently routing outside policy

### Missing Configuration
If `settings.json` has no `allowedProviders` entry:
- treat all detected providers as allowed
- do not fail

## Command Design

### New Command
Add a new command file:
- `pack/commands/providers.md`

### Command Responsibility
This command is the user-facing way to inspect and update provider policy after install.

The command instructs the leader to:
- read current pack settings
- detect available provider candidates from local OpenCode state
- present the current allowlist
- update `settings.json` based on the user's selection

### Scope Boundary
The command updates only pack configuration. It must not rewrite OpenCode auth, provider tokens, or active provider state unless the user explicitly asks for a separate change.

## Installer Changes

### Bash Installer
Update `install.sh` to:
- discover provider candidates
- prompt for selection in interactive mode
- write or update `settings.json` with `opencodeAgentPack.allowedProviders`
- preserve existing unrelated settings

### PowerShell Installer
Update `install.ps1` to mirror the same behavior and config shape.

### Existing Config Preservation
Current preserve behavior for `opencode.json` and `settings.json` stays in place. New writes must merge into existing `settings.json` rather than replacing unrelated keys.

## Data Handling Rules
- Never persist auth tokens outside OpenCode's existing auth store.
- Never include raw auth content in examples, docs, or command output.
- Only provider identifiers such as `openai` or `openrouter` may be written by the pack.

## Backward Compatibility
- Existing installs without `allowedProviders` continue to work.
- Existing `opencode.json` provider/model values remain untouched.
- Existing routing defaults continue to apply when no allowlist is set.

## Acceptance Criteria
- Interactive install asks for allowed providers and supports multi-select.
- Enter during install selects all detected provider candidates.
- Non-interactive install defaults to all detected provider candidates without blocking.
- `settings.json` stores provider allowlist under `opencodeAgentPack.allowedProviders`.
- `/providers` can display and update the allowlist after install.
- Router uses only allowed providers for provider selection and model discovery.
- No secrets are copied from `auth.json`.
- If the active provider is disallowed, the router warns and falls back inside the allowlist.
- If no allowed provider is usable, the router fails clearly.
- Model-level allowlists remain out of scope for this change.

## Deferred Work
- provider-specific preferred ordering controls
- model-level allowlists
- richer UI for provider and model policy editing
- surfacing per-provider fast-model suitability in the command flow

## Final Acceptance Notes
- Install-time provider selection writes a pack-scoped allowlist to `settings.json` under `opencodeAgentPack.allowedProviders`.
- When the installer runs non-interactively, it defaults to all detected local providers and still writes the explicit allowlist.
- `/providers` is the supported post-install path for reviewing and updating the allowed routing providers.
- The router is constrained by the pack-scoped allowlist and falls back inside that allowlist if the active provider is disallowed.
- Model-level allowlists remain out of scope for this change.
