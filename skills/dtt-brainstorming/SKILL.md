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
- require spec approval before planning through the `question` tool, not only free-form chat text
- the spec approval question must offer exactly these decision types: approve spec and proceed to plan; request spec changes; reject/cancel spec
- follow the current conversation language for the chat output and spec document
- produce a complete, human-readable spec that becomes the planning source of truth after approval
- stop and wait for the structured `question` response before planning
- do not change lane/tier/escalation/final approval ownership

## Expected Output

- clarified goal
- confirmed constraints
- recommended approach
- reviewable spec content
- spec path under `docs/dtt/specs/`
- human-readable spec content shown in chat
- structured `question` approval prompt before planning

## Required Approval Question

After writing and showing the spec, call `question` with one single-select question whose labels include:

- `批准 spec，进入 plan`
- `需要补充 spec`
- `拒绝 spec`

If the user requests changes or enters custom feedback, update the spec and ask the structured approval question again. Do not call `dtt-writing-plans` until the structured answer approves the spec.
