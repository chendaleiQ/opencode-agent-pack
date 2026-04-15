---
name: dtt-brainstorming
description: Leader-only method skill. Use after triage when a feature or high-complexity task needs design clarification before planning or implementation.
---

# Skill: dtt-brainstorming

## Purpose

Use this skill to deepen requirement discovery and turn a `needsPlan=true` task into a reviewable spec without replacing pack workflow routing.

## Rules

- only `leader` invokes this skill
- run after `dtt-change-triage`, never before it
- use only when `needsPlan=true` or when design uncertainty blocks safe execution
- ask one clarifying question at a time
- propose 2-3 approaches with trade-offs when architecture choices matter
- when `needsPlan=true`, write the spec to `docs/dtt/specs/`
- show the spec in chat
- require spec approval before planning
- follow the current conversation language for the chat output and spec document
- produce a complete, human-readable spec that becomes the planning source of truth after approval
- stop and wait for user approval before planning
- do not change lane/tier/escalation/final approval ownership

## Expected Output

- clarified goal
- confirmed constraints
- recommended approach
- reviewable spec content
- spec path under `docs/dtt/specs/`
- human-readable spec content shown in chat
- explicit wait for user approval before planning
