# Leader Default Agent Design

## Goal

Make `leader` the default user-facing entry agent after install while reducing visibility of the pack's internal helper agents.

## Desired Behavior

- Install writes or merges `opencode.json` so `default_agent` is `leader`.
- Custom helper agents `analyzer`, `implementer`, and `reviewer` are configured as `mode: subagent`.
- Those helper agents are marked `hidden: true` so they do not appear in the user's `@` autocomplete menu.
- `leader` remains directly usable by the user.
- Built-in OpenCode agents such as `build` and `plan` are left unchanged.

## Non-Goals

- Do not disable built-in OpenCode agents.
- Do not remove helper agent files from disk.
- Do not attempt to hard-block a user from manually typing a hidden subagent name if they already know it.

## Product Constraint

OpenCode's documented behavior matters here:

- `default_agent` controls which primary agent is selected by default.
- `hidden: true` only hides a subagent from the autocomplete menu.
- Hidden subagents can still be invoked programmatically by another agent.
- Hidden subagents are not a hard security boundary against a user manually typing the subagent name.

Given that behavior, the best available outcome is to make `leader` the default and hide the pack-specific helper agents from normal user discovery.

## Configuration Design

### `opencode.json`

The installer should merge the following pack-owned setting into the target `opencode.json`:

```json
{
  "default_agent": "leader"
}
```

Requirements:

- Preserve existing user fields such as `provider`, `model`, `permission`, and unrelated agent config.
- Do not replace the whole file.
- If the file does not exist, create a minimal valid JSON object containing `default_agent`.

### Agent metadata

The pack-specific custom agents should be expressed so that OpenCode treats them as hidden subagents:

- `leader`: user-facing agent, not hidden
- `analyzer`: `mode: subagent`, `hidden: true`
- `implementer`: `mode: subagent`, `hidden: true`
- `reviewer`: `mode: subagent`, `hidden: true`

If the repo currently defines these agents only through markdown frontmatter-free prompt files, the implementation should introduce the smallest compatible metadata layer that OpenCode recognizes without changing the prompts' behavioral content.

## Installer Behavior

Both installers should behave consistently:

- `install.sh`
- `install.ps1`

After copying pack files into the target directory, the installer should merge `default_agent: "leader"` into the target `opencode.json`.

This should happen in the same spirit as the existing `settings.json` provider allowlist behavior:

- preserve unrelated user config
- keep behavior cross-platform
- prefer a shared helper for JSON merge logic instead of duplicating fragile shell or PowerShell JSON edits

## Implementation Shape

Recommended minimal shape:

1. Add a small Python helper for safe `opencode.json` read/merge/write.
2. Reuse that helper from both installers.
3. Update custom agent definitions to include subagent visibility metadata.
4. Add tests covering install output and merged config behavior.

## Testing

Add or update tests to verify:

- non-interactive install preserves existing `provider` and `model` in `opencode.json`
- install writes `default_agent: "leader"`
- repeated install does not duplicate or corrupt config
- helper agents are configured as hidden subagents in the installed pack content

## Risks

- If the current markdown agent format in this repo does not yet expose OpenCode metadata fields, changing agent file structure must not alter prompt semantics.
- Users can still manually reference a hidden subagent if they already know its name; this is an accepted platform limitation.

## Success Criteria

- Fresh install opens with `leader` as the default primary agent.
- `analyzer`, `implementer`, and `reviewer` no longer appear in normal user autocomplete discovery.
- `leader` can still dispatch those helper agents successfully.
- Existing user config in `opencode.json` remains intact apart from the merged `default_agent` field.
