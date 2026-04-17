---
name: dtt-writing-plans
description: Leader-only method skill. Use after triage and design clarification when `needsPlan=true` to produce an implementation plan.
---

# Skill: dtt-writing-plans

## Purpose

Turn a clarified task into an actionable implementation plan without taking control away from pack workflow.

## Rules

- only `leader` invokes this skill
- only use when `dtt-change-triage` says `needsPlan=true`
- require an approved spec before writing the plan
- keep the plan aligned with the chosen lane and risk boundary
- break work into small, verifiable steps
- include exact files and verification expectations when possible
- use the approved spec as the planning source of truth
- write the plan to `docs/dtt/plans/`
- show the plan in chat
- require plan approval before todo or analyze/execute/review dispatch through the `question` tool, not only free-form chat text
- the plan approval question must offer exactly these decision types: approve plan and start implementation; request plan changes; reject/cancel plan
- follow the current conversation language for the chat output and plan document
- plans support execution; they do not replace lane/tier control

## Expected Output

- goal
- approved spec
- architecture summary
- ordered implementation steps
- verification checkpoints
- plan path under `docs/dtt/plans/`
- human-readable plan content shown in chat
- structured `question` approval prompt before execution

## Required Approval Question

After writing and showing the plan, call `question` with one single-select question whose labels include:

- `批准 plan，开始实现`
- `需要修改 plan`
- `拒绝 plan`

If the user requests changes or enters custom feedback, update the plan and ask the structured approval question again. Do not create todos or dispatch analyze/execute/review work until the structured answer approves the plan.
