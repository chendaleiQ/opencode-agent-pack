# Command: /providers（V5）

## Purpose
Pack-scoped command for inspecting and updating the `opencode-agent-pack` provider allowlist after install.

## User Usage
- `/providers`
- or a direct request to review or change the pack provider allowlist

## Fixed Execution Pipeline
1. Read the current pack settings from `settings.json`
2. Detect candidate providers through `pack/tools/provider_policy.py`
3. Show the current allowed providers and the detected candidate set
4. Let the user keep, replace, or reset the allowlist to all detected providers
5. Write only `settings.json` through the shared provider policy helper

## Scope Boundary
- Update only `settings.json` under `opencodeAgentPack.allowedProviders`
- Never rewrite `opencode.json`
- Never copy, print, or persist values from `auth.json`
- Provider names only: no tokens, no OAuth payloads, no raw auth content

## Behavior
- If `allowedProviders` is missing, treat all detected providers as allowed
- Support multi-select provider replacement
- Pressing Enter accepts the full detected provider set
- Resetting to default means writing the full detected provider list into `settings.json`
- An explicit empty list means deny-all routing until the allowlist is reconfigured
- The command must stay pack-scoped even when the user asks to inspect provider state

## Safety Notes
- Use the provider helper for detection and writes so the command stays aligned with install-time behavior
- Keep unrelated `settings.json` fields intact when updating the allowlist
- If no providers are detected, report that clearly and leave the current allowlist unchanged unless the user explicitly confirms writing an empty list
