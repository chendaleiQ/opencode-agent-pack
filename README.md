# opencode-agent-pack

Single-entry, auto-routed OpenCode Agent Pack.
Install once, then only talk to one default strongest entry agent: `orchestrator`.

## What Problem This Solves
Most multi-agent setups force users to manually decide:
- which model to use
- which agent to call
- whether a task is risky
- whether to run fast path or strict path

This pack removes that burden:
- you give one task to `orchestrator`
- system auto-runs triage, lane routing, tier routing, subagent dispatch, review/verify, escalation, and final closure

## Core Positioning
This is a **single-entry OpenCode Agent Pack with automatic lane+tier routing**.

It is **not**:
- a prompt snippet collection
- a single isolated skill
- a multi-entry agent menu

## Why One Strongest Entry
`orchestrator` (tier_top) owns all critical decisions:
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
The system still returns to `tier_top` for final closure.

## Why High-Risk Tasks Are Not Started by Weak Model
High-risk or sensitive tasks require strong boundary control from the start:
- guarded/strict boundary rules are set by `tier_top`
- strict final approval is always `tier_top`
- escalation can promote tier/lane automatically

## Install

### Option 1: Project Install (recommended)
Install into current project as `.opencode/`:

```bash
bash install.sh --project
```

PowerShell:
```powershell
.\install.ps1 -Project
```

### Option 2: Global Install
Install into `~/.config/opencode/`:

```bash
bash install.sh --global
```

PowerShell:
```powershell
.\install.ps1 -Global
```

### Option 3: Custom Target
Install pack to any directory:

```bash
bash install.sh --target /path/to/target
```

PowerShell:
```powershell
.\install.ps1 -Target "C:\path\to\target"
```

### Safe Behavior
- installer is conservative by default
- if target exists and is non-empty, install aborts unless `--force` / `-Force`
- no destructive reset operations

## Use

After install, user workflow is intentionally simple:
1. ask task directly (or use `/task`)
2. system handles triage/routing/escalation automatically
3. `orchestrator` provides final closure summary

You do **not** need to:
- switch models manually
- choose agents manually
- judge complexity/risk manually
- pick process lane manually

## Design Principles (Current Version)
- single entry (`orchestrator`)
- strongest model controls decisions and closure
- triage before implementation
- lane routing + tier routing
- automatic escalation only upward (no auto downgrade)
- explicit end-gates by lane
- unified execution summary at close

## New in V5: Evals and Maintenance
Project now includes `evals/` for stable triage/lane/tier assessment.

How to use evals:
1. Pick a case in `evals/cases/`
2. Run triage (and flow when needed)
3. Compare results with expected outputs in case file
4. Score with `evals/rubric.md`
5. If misclassified, fix using `MAINTAINING.md`

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
