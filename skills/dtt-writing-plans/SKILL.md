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
- require plan approval before todo or analyze/execute/review dispatch
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
