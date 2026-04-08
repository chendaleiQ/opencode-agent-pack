# Command: /task（V5）

## Purpose
Single-entry command for end users.
User gives one requirement; system handles everything else automatically.

## User Usage
- `/task <your request>`
- or natural language request (same effect)

## Fixed Execution Pipeline
1. `orchestrator(tier_top)` receives task
2. must run `change-triage`
3. route lane + tiers
4. dispatch analyzer / implementer / reviewer
5. auto-escalate lane/tier when triggered
6. `orchestrator(tier_top)` final closure with unified execution summary

## Lane Rules
- quick: low complexity + low risk + no sensitive + estimatedFiles<=2
- standard: high complexity + low risk
- guarded: low complexity + high risk
- strict: high complexity + high risk

## Tier Rules
- quick: analysis fast, executor fast, review mid, final top
- standard: analysis fast|mid, executor fast|mid, review mid, final top
- guarded: analysis mid, executor mid|fast, review mid, final top
- strict: analysis mid|top, executor mid, review top|mid, final top

Hard constraints:
- finalApprovalTier is always tier_top
- sensitive hit cannot be low risk
- sensitive hit cannot go to quick/standard
- strict cannot be fast-tier-led

## Escalation Rules
Triggered by:
- scope grows beyond estimate
- new sensitive signals
- reviewer asks escalation
- verify failure
- requirement scope expansion
- implementer instability
- execution discovers plan is required

Escalation only upward:
- tier_fast -> tier_mid -> tier_top
- quick -> standard/guarded/strict
- standard -> strict
- guarded -> strict
