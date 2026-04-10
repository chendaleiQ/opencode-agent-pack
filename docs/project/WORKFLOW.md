# Workflow Reference

## Why One Strongest Entry
`leader` (`tier_top`) owns all critical decisions:
- task interpretation
- risk boundary judgment
- lane choice
- escalation
- final approval

Low-value local work is delegated to cheaper and faster tiers when safe.

## Lane Routing
System triages every task into one lane:

- `quick`: low complexity + low risk + no sensitive flags + small change
- `standard`: high complexity + low risk
- `guarded`: low complexity + high risk
- `strict`: high complexity + high risk

Sensitive hits (`auth/db schema/public api/destructive`) cannot stay low risk.

## Quick Lane Is Minimal Path
`quick` is not a mandatory analyzer -> implementer -> reviewer chain.

Instead, `leader` should pick only the smallest downstream path that matches the task:
- quick implementation: `implementer`
- quick investigation: `analyzer`
- quick review: `reviewer`

If a quick task needs multiple downstream roles or repeated back-and-forth to finish safely, it should escalate instead of pretending to stay lightweight.

## Tier Routing
Abstract tiers:
- `tier_top`: strongest model (entry, triage interpretation, strict boundaries, final closure)
- `tier_mid`: balanced model (review, non-final verification, complex analysis)
- `tier_fast`: cheap/fast model (low-risk implementation, scan, repetitive drafting)

Default behavior:
- low-risk local tasks: delegated to `tier_fast`
- higher-risk decisions and closure: always handled by `tier_top`
- review quality control: mostly `tier_mid` (or `tier_top` for strict scenarios)

## Why Low-Risk Tasks Are Delegated
Low-risk work is bounded, lower impact, and cheaper to execute quickly.
That does not mean every low-risk task should traverse the full workflow. The goal is minimal safe delegation, then return to `tier_top` for final closure.

## Subagent Behavior
Only `leader` should run workflow-routing logic such as `dtt-change-triage`.

Delegated subagents should:
- consume the handoff directly
- stay within their role
- avoid rerunning triage or re-entering heavyweight workflow skills for a local task
- report back for escalation when the handoff or boundary is unclear

## Built-In Method Skills
The plugin carries its own method skills for deeper execution quality without giving up single-entry workflow control.

Current built-in method skills:
- `dtt-brainstorming`
- `dtt-dispatching-parallel-agents`
- `dtt-executing-plans`
- `dtt-finishing-a-development-branch`
- `dtt-writing-plans`
- `dtt-systematic-debugging`
- `dtt-test-driven-development`
- `dtt-verification-before-completion`
- `dtt-requesting-code-review`
- `dtt-receiving-code-review`

`dtt-change-triage` still decides the workflow skeleton. These method skills are inserted conditionally based on task shape, review needs, uncertainty, and completion state.

## External Workflow Systems
External workflow systems are not needed for normal operation.
- this plugin remains the workflow source of truth for lane/tier/escalation/closure
- plugin-native method skills should be preferred over external equivalents
- delegated subagents must honor handoff boundaries first and should not re-enter external heavyweight workflow chains

## Why High-Risk Tasks Are Not Started by Weak Models
High-risk or sensitive tasks require strong boundary control from the start:
- guarded/strict boundary rules are set by `tier_top`
- strict final approval is always `tier_top`
- escalation can promote tier/lane automatically

## Design Principles
- single entry (`leader`)
- strongest model controls decisions and closure
- triage before implementation
- lane routing + tier routing
- entry-driven state flow, not one fixed workflow for every task
- automatic escalation only upward (no auto-downgrade)
- explicit end-gates by lane
- unified execution summary at close

## Verification and End-Gates
- work should not close on implementation output alone
- reviewer output remains part of standard/guarded/strict flow, and is added to quick when review is actually needed
- verification evidence can be command output or an explicit manual check when no formal verify command exists
- when verification is manual, the agent should say exactly what was checked
- `leader` should only close work after the relevant end-gate is satisfied

## OpenCode Runtime Guard
When running inside OpenCode, do-the-thing can add a lightweight runtime guard layer in addition to the prompt workflow.

The runtime guard is designed to make workflow bypass harder for weaker models by adding:
- Hooks-based blocking for obvious bypasses
- entry-driven workflow state (`entryType`) and phase tracking (`phase`)
- layered evidence tracking for triage, review, verification, manual checks, and escalation
- workflow state persisted per session
- audit logging for important workflow events
- close-time evidence gating before completion claims

This does not replace `leader` workflow ownership. It reinforces it with execution-time checks.

### Entry-Driven State Flow
The runtime guard is not a single fixed pipeline. It tracks which kind of entry the current task resembles and which phase the task is currently in.

Examples of entry types:
- `general`
- `chat`
- `implement`
- `review`
- `debug`
- `close`

Examples of phases:
- `created`
- `triaged`
- `implementing`
- `reviewing`
- `verifying`
- `closable`
- `closed`

This allows different task entry shapes to follow different paths while still enforcing a controlled close gate.

### Layered Evidence Model
The runtime guard can also track structured evidence instead of treating all checks as one generic verification flag.

Current evidence categories include:
- `triage`
- `review`
- `verification`
- `manual`
- `escalation`

Close gating can then ask not only "is there evidence" but also "is the right kind of evidence present for this lane and current task state".

## Evals and Maintenance
Project includes `evals/` as a manual assessment kit for triage/lane/tier behavior.

How to use evals:
1. Pick a case in `evals/cases/`
2. Run triage (and the rest of the flow when needed) manually
3. Compare the observed outputs with the expected outputs in the case file
4. Score with `evals/rubric.md`
5. Record what you checked, then use [`MAINTAINING.md`](./MAINTAINING.md) if a fix is needed

Primary metric is low high-risk miss rate, not overall accuracy.

Contributing new eval cases:
1. Copy an existing case format from `evals/cases/`
2. Fill task/background/expected triage/lane/tier/risk points
3. Open a PR and explain what failure mode this case covers
4. Reference `evals/rubric.md`

Release and maintenance references:
- [`RELEASE.md`](./RELEASE.md)
- [`MAINTAINING.md`](./MAINTAINING.md)
