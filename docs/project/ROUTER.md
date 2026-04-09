# Router Reference

## Optional Tool: Subagent Model Router
The plugin includes an optional tool at `tools/subagent_model_router.py`.

What it does:
- takes triage JSON as input
- returns recommended subagent dispatch order
- returns model choice per role based on tier (`tier_fast|tier_mid|tier_top`)
- supports provider-aware model mapping (auto-detected from config, no hardcoded default provider)
- can auto-pick from available models list
- can auto-detect provider/models from local opencode config
- can auto-discover provider-available models and build tier candidates
- honors the plugin-scoped provider allowlist stored in `settings.json`
- falls back inside the allowlist if the active provider is disallowed
- treats an explicit empty `allowedProviders: []` as deny-all until you reconfigure it
- when `--config-path` points at a custom `opencode.json`, the router reads the sibling `settings.json` from that same directory

## Example
```bash
PYTHONPATH=. python3 -m tools.subagent_model_router \
    --auto-detect-config \
    --discover-models \
    --triage-json '{"taskType":"refactor","lane":"quick","analysisTier":"tier_fast","executorTier":"tier_fast","reviewTier":"tier_mid","needsReviewer":false}'
```

The router auto-detects your provider and available models from your opencode config.
If the active provider is not allowed, the router warns and falls back to the first usable provider inside the allowlist instead of routing outside policy.

## Custom Config Example
```bash
PYTHONPATH=. python3 -m tools.subagent_model_router \
    --config-path /tmp/my-opencode-pack/opencode.json \
    --auto-detect-config \
    --triage-json '{"taskType":"review","lane":"quick","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}'
```

With `--config-path`, provider policy is read from `/tmp/my-opencode-pack/settings.json`.

## Provider Model Discovery Example
```bash
PYTHONPATH=. python3 -m tools.subagent_model_router \
    --auto-detect-config \
    --discover-models \
    --triage-json '{"taskType":"feature","lane":"strict","analysisTier":"tier_top","executorTier":"tier_mid","reviewTier":"tier_top","needsReviewer":true}'
```

Output also includes:
- `provider`
- `availableModelsCount`
- `tierCandidates` (auto-graded buckets for fast/mid/top)
- `warnings` (for example, missing API key during provider discovery)

Override model mapping with environment variables:
- `OPENCODE_MODEL_TIER_FAST`
- `OPENCODE_MODEL_TIER_MID`
- `OPENCODE_MODEL_TIER_TOP`

You do not need to:
- switch models manually
- choose agents manually
- judge complexity/risk manually
- pick the process lane manually
