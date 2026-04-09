# do-the-thing

[English](./README.md) | [简体中文](./README.zh-CN.md)

do-the-thing is a single-entry, auto-routed agent workflow for OpenCode.
Install once, then only talk to one default strongest entry agent: `leader`.
The documented workflow routes triage, delegation, escalation, review, verification, and final closure through that single entry.

Tell one agent the task, let the system handle the rest.

## What Problem This Solves
Most multi-agent setups force users to manually decide:
- which model to use
- which agent to call
- whether a task is risky
- whether to run fast path or strict path

This pack removes that burden at the workflow level:
- you give one task to `leader`
- the pack defines how triage, lane routing, tier routing, subagent dispatch, review/verify, escalation, and final closure should happen

## Core Positioning
This is **do-the-thing**: a single-entry OpenCode workflow with automatic lane+tier routing.

It is **not**:
- a prompt snippet collection
- a single isolated skill
- a multi-entry agent menu

## Why One Strongest Entry
`leader` (tier_top) owns all critical decisions:
- task interpretation
- risk boundary judgment
- lane choice
- escalation
- final approval

Low-value local work is delegated to cheaper/faster tiers when safe.

## Lane Routing (What Flow Is Used)
System triages every task into one lane:

- `quick`: low complexity + low risk + no sensitive flags + small change
- `standard`: high complexity + low risk
- `guarded`: low complexity + high risk
- `strict`: high complexity + high risk

Sensitive hits (`auth/db schema/public api/destructive`) cannot stay low risk.

## Quick Lane Is Minimal-Path
`quick` is not a mandatory analyzer -> implementer -> reviewer chain.

Instead, `leader` should pick only the smallest downstream path that matches the task:
- quick implementation: `implementer`
- quick investigation: `analyzer`
- quick review: `reviewer`

If a quick task needs multiple downstream roles or repeated back-and-forth to finish safely, it should escalate instead of pretending to stay lightweight.

## Tier Routing (Which Model Strength Is Used)
Abstract tiers:
- `tier_top`: strongest model (entry, triage interpretation, strict boundaries, final closure)
- `tier_mid`: balanced model (review, non-final verification, complex analysis)
- `tier_fast`: cheap/fast model (low-risk implementation, scan, repetitive drafting)

Default behavior:
- low-risk local tasks: delegated to `tier_fast`
- higher-risk decisions and closure: always handled by `tier_top`
- review quality control: mostly `tier_mid` (or `tier_top` for strict scenarios)

## Why Low-Risk Tasks Are Delegated
Because they are bounded, low-impact, and cheaper to execute quickly.
That does not mean every low-risk task should traverse the full workflow. The goal is minimal safe delegation, then return to `tier_top` for final closure.

## Subagent Behavior
Only `leader` should run workflow-routing logic such as `change-triage`.

Delegated subagents should:
- consume the handoff directly
- stay within their role
- avoid rerunning triage or re-entering heavyweight workflow skills for a local task
- report back for escalation when the handoff or boundary is unclear

## Built-In Method Skills
This pack now carries its own method skills for deeper execution quality without giving up single-entry workflow control.

Current built-in method skills include:
- `brainstorming`
- `dispatching-parallel-agents`
- `executing-plans`
- `finishing-a-development-branch`
- `writing-plans`
- `systematic-debugging`
- `test-driven-development`
- `verification-before-completion`
- `requesting-code-review`
- `receiving-code-review`

`change-triage` still decides the workflow skeleton. These method skills are conditionally inserted as hooks based on task shape, review needs, uncertainty, and completion state.

## External Skill Systems
External workflow systems are not needed for this pack's normal operation.
- this pack remains the workflow source of truth for lane/tier/escalation/closure
- pack-native method skills should be preferred over external equivalents
- delegated subagents must honor handoff boundaries first and should not re-enter external heavyweight skill chains

## Why High-Risk Tasks Are Not Started by Weak Model
High-risk or sensitive tasks require strong boundary control from the start:
- guarded/strict boundary rules are set by `tier_top`
- strict final approval is always `tier_top`
- escalation can promote tier/lane automatically

## Install

### One-Command Install (default)
Install from the latest GitHub Release without cloning the repository:

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.sh | bash
```

PowerShell:
```powershell
irm https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.ps1 | iex
```

To install a fixed release instead of `latest`, set `OPENCODE_AGENT_PACK_VERSION` before running the bootstrap command:

```bash
OPENCODE_AGENT_PACK_VERSION=v1.0.0 curl -fsSL https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.sh | bash
```

PowerShell:
```powershell
$env:OPENCODE_AGENT_PACK_VERSION = "v1.0.0"
irm https://raw.githubusercontent.com/chendaleiQ/opencode-agent-pack/main/bootstrap/install.ps1 | iex
```

The bootstrap script downloads the matching GitHub Release archive, extracts it into a temporary directory, and then runs the packaged local installer.

### Manual Local Install
For offline use, local testing, or contributor workflows:

```bash
git clone git@github.com:chendaleiQ/opencode-agent-pack.git
cd opencode-agent-pack
bash install.sh
```

PowerShell:
```powershell
git clone git@github.com:chendaleiQ/opencode-agent-pack.git
cd opencode-agent-pack
.\install.ps1
```

### Custom Target
Install pack to any directory:

```bash
bash install.sh --target /path/to/target
```

PowerShell:
```powershell
.\install.ps1 -Target "C:\path\to\target"
```

### Safe Behavior
- installer defaults to global install (`~/.config/opencode/`)
- project-level install is not supported
- if target exists and is non-empty, install aborts unless `--force` / `-Force`
- `--force` / `-Force` performs a clean rebuild (removes target contents before install)
- `--force` / `-Force` preserves known user config files: `opencode.json`, `settings.json`
- no destructive reset operations

### Provider Allowlist
During install, the pack configures a pack-scoped provider allowlist in `settings.json`:
- provider candidates are detected from local OpenCode state
- provider selection defaults to all detected local providers, so pressing Enter accepts the full set
- the selected policy is stored under `opencodeAgentPack.allowedProviders`
- if no providers are detected, the installer leaves the existing allowlist unchanged unless you explicitly confirm writing an empty list
- after install, use `/providers` to review or reconfigure the allowed routing providers

## Use

After install, user workflow is intentionally simple:
1. switch to `leader` agent, then ask task directly
2. `leader` handles triage/routing/escalation within the documented workflow
3. `leader` provides the final closure summary after review/end-gate checks
4. use `/providers` whenever you want to update the pack-scoped provider allowlist

## Optional Tool: Subagent Model Router
This pack includes an optional tool at `pack/tools/subagent_model_router.py`.

What it does:
- takes triage JSON as input
- returns recommended subagent dispatch order
- returns model choice per role based on tier (`tier_fast|tier_mid|tier_top`)
- supports provider-aware model mapping (auto-detected from config, no hardcoded default provider)
- can auto-pick from available models list
- can auto-detect provider/models from local opencode config
- can auto-discover provider-available models and build tier candidates
- honors the pack-scoped provider allowlist stored in `settings.json`
- falls back inside the allowlist if the active provider is disallowed
- treats an explicit empty `allowedProviders: []` as deny-all until you reconfigure it
- when `--config-path` points at a custom `opencode.json`, the router reads the sibling `settings.json` from that same directory

Example:
```bash
PYTHONPATH=. python3 -m pack.tools.subagent_model_router \
    --auto-detect-config \
    --discover-models \
    --triage-json '{"taskType":"refactor","lane":"quick","analysisTier":"tier_fast","executorTier":"tier_fast","reviewTier":"tier_mid","needsReviewer":false}'
```

The router auto-detects your provider and available models from your opencode config.
If the active provider is not allowed, the router warns and falls back to the first usable provider inside the allowlist instead of routing outside policy.

Custom-target example:
```bash
PYTHONPATH=. python3 -m pack.tools.subagent_model_router \
    --config-path /tmp/my-opencode-pack/opencode.json \
    --auto-detect-config \
    --triage-json '{"taskType":"review","lane":"quick","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}'
```

With `--config-path`, provider policy is read from `/tmp/my-opencode-pack/settings.json`.

Provider model discovery (optional):
```bash
PYTHONPATH=. python3 -m pack.tools.subagent_model_router \
    --auto-detect-config \
    --discover-models \
    --triage-json '{"taskType":"feature","lane":"strict","analysisTier":"tier_top","executorTier":"tier_mid","reviewTier":"tier_top","needsReviewer":true}'
```

Output also includes:
- `provider`
- `availableModelsCount`
- `tierCandidates` (auto-graded buckets for fast/mid/top)
- `warnings` (e.g. missing API key for provider discovery)

Override model mapping with environment variables:
- `OPENCODE_MODEL_TIER_FAST`
- `OPENCODE_MODEL_TIER_MID`
- `OPENCODE_MODEL_TIER_TOP`

You do **not** need to:
- switch models manually
- choose agents manually
- judge complexity/risk manually
- pick process lane manually

## Design Principles (Current Version)
- single entry (`leader`)
- strongest model controls decisions and closure
- triage before implementation
- lane routing + tier routing
- automatic escalation only upward (no auto downgrade)
- explicit end-gates by lane
- unified execution summary at close

## Verification and End-Gates
- work should not close on implementation output alone
- reviewer output remains part of standard/guarded/strict flow, and is added to quick when review is actually needed
- verification evidence can be command output or an explicit manual check when no formal verify command exists
- when verification is manual, the agent should say exactly what was checked
- `leader` should only close work after the relevant end-gate is satisfied

## New in V5: Evals and Maintenance
Project includes `evals/` as a manual assessment kit for triage/lane/tier behavior.

How to use evals:
1. Pick a case in `evals/cases/`
2. Run triage (and the rest of the flow when needed) manually
3. Compare the observed outputs with the expected outputs in the case file
4. Score with `evals/rubric.md`
5. Record what you checked, then use `MAINTAINING.md` if a fix is needed

The repository does not add CI automation for these evals by default; they are intended to be run and reviewed manually.

### Why high-risk miss rate matters most
Primary metric is **low high-risk miss rate**, not overall accuracy.

Reason:
- low-risk over-upgrade usually costs time/money
- high-risk under-classification can cause security/data/API incidents

### Contributing new eval cases
1. Copy an existing case format from `evals/cases/`
2. Fill task/background/expected triage/lane/tier/risk points
3. Open PR and explain what failure mode this case covers
4. Reference `evals/rubric.md` criteria

## Release Strategy (Short)
Versioning follows `MAJOR.MINOR.PATCH`.
- PATCH: docs/examples/cases/safe fixes
- MINOR: backward-compatible routing improvements
- MAJOR: breaking lane/tier/schema/install behavior changes

See `RELEASE.md` for full rules.

## Maintenance (Short)
Fix order:
1. add eval case
2. adjust triage rule or thresholds
3. tighten quick lane when needed
4. add hard rule only if repeated high-risk misses

See `MAINTAINING.md` for full process.

## Who This Is For
- solo developers wanting low-friction automation
- teams needing consistent safe routing rules
- OSS repos wanting a reusable default automation pack
- internal engineering orgs standardizing task execution policy

## Directory Structure
```text
opencode-agent-pack/
├─ README.md
├─ README.zh-CN.md
├─ LICENSE
├─ install.sh
├─ install.ps1
├─ RELEASE.md
├─ MAINTAINING.md
├─ evals/
│  ├─ README.md
│  ├─ rubric.md
│  └─ cases/
├─ examples/
│  └─ minimal-project/
└─ pack/
   ├─ AGENTS.md
   ├─ agents/
   ├─ commands/
   └─ skills/
```
