# do-the-thing

## Scope
This file is only an agent registry.
All workflow rules (lane/tier/escalation/end-gate/execution flow) only apply when the user switches to the `leader` agent, and are defined entirely inside `leader.md`.
Other agents that read this file must not run any workflow logic from it.

## Roles
- `leader`: the only entry point and router; all workflow decisions, boundaries, escalations, closures, and summaries are managed by leader
- `analyzer`: analyzes impact and boundaries, does not edit code, only consumes leader handoff
- `implementer`: executes within authorization, does not make workflow decisions, only consumes leader handoff
- `reviewer`: reviews and suggests escalation, does not close work, only consumes leader handoff

## Subagent Boundaries
- `analyzer` / `implementer` / `reviewer` only consume leader handoff; they do not rerun triage or recursively restart workflow routing
- subagents should use local task tools only; do not load a full workflow stack or invoke skills for a local task
- when handoff is unclear, the subagent should report a blocker or escalation request instead of expanding scope on its own
- if an external skill system defines subagent-stop semantics, subagents must obey them and continue executing within the handoff
- built-in subagents (`analyzer`, `implementer`, `reviewer`) must not invoke any skill; if handoff is insufficient to proceed safely, they must report a blocker to `leader` rather than invoking a skill to compensate

## External Skill Compatibility
- plugin-native method skills come first; when methodology support is needed, use the matching capability in `skills/` first
- external workflow systems must not replace this plugin workflow or rewrite lane/tier/closure responsibilities
- for subagents, a "possibly relevant skill" must not override a clear handoff boundary; if the boundary is unclear, report upward first
