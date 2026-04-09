---
name: dtt-systematic-debugging
description: Method skill for bugfix or investigation tasks. Use after triage when failures, unexpected behavior, or uncertainty require root-cause analysis before fixing.
---

# Skill: dtt-systematic-debugging

## Core Rule

No fix before root-cause investigation.

## Required Sequence

1. read the error or symptom carefully
2. reproduce or restate the failure clearly
3. gather evidence from the relevant boundary or call chain
4. identify the most likely root cause
5. only then attempt a minimal fix

## Guardrails

- do not guess with stacked fixes
- if the issue is still unclear, report uncertainty and request escalation
- this skill improves diagnosis only; it does not change lane/tier ownership
