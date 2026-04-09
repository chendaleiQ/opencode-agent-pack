---
name: dtt-verification-before-completion
description: Method skill for any task that is about to be declared complete. Use before any completion claim, closure, or success statement.
---

# Skill: dtt-verification-before-completion

## Core Rule

No completion claim without fresh verification evidence.

## Required Sequence

1. identify the command or check that proves the claim
2. run it now
3. read the output fully
4. state the actual result, not the hoped-for result

## Guardrails

- previous runs do not count
- partial checks do not count when a fuller check is available
- if verification fails, report failure and request follow-up instead of closing
