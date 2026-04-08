# Command: /task（V5）

## Purpose
Single-entry command for end users.
User gives one requirement; system handles everything else automatically.

## User Usage
- `/task <your request>`
- or natural language request (same effect)

## Fixed Execution Pipeline
1. `leader(tier_top)` receives request
2. if request is chat-only, answer directly with `chat-only: no code/file/command action requested`
3. otherwise, only `leader` may run `change-triage`
4. route lane + tiers + minimal execution path
5. quick lane dispatches only the minimal required role; non-quick lanes dispatch the roles required by that lane
6. subagents must not rerun triage or re-enter the heavyweight workflow
7. auto-escalate lane/tier when triggered
8. `leader(tier_top)` final closure with unified execution summary

## Lane Rules
- quick: low complexity + low risk + no sensitive + estimatedFiles<=2
- standard: high complexity + low risk
- guarded: low complexity + high risk
- strict: high complexity + high risk

## Tier Rules
- quick: analysis fast, executor fast, review mid only when needed, final top
- standard: analysis fast|mid, executor fast|mid, review mid, final top
- guarded: analysis mid, executor mid|fast, review mid, final top
- strict: analysis mid|top, executor mid, review top|mid, final top

Hard constraints:
- finalApprovalTier is always tier_top
- sensitive hit cannot be low risk
- sensitive hit cannot go to quick/standard
- strict cannot be fast-tier-led
- quick must not default to analyzer + implementer + reviewer as a fixed chain
- only leader can invoke workflow-routing skills such as `change-triage`
- external skill integration must not override explicit handoff boundaries for delegated subagents
- chat-only bypass must not be used when execution signals are present

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
