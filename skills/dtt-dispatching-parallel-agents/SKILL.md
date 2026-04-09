---
name: dtt-dispatching-parallel-agents
description: Leader-only method skill. Use when multiple task slices are independent enough to be dispatched in parallel without shared-state or edit conflicts.
---

# Skill: dtt-dispatching-parallel-agents

## Purpose

Help `leader` decide when parallel dispatch is actually safe.

## Safe To Parallelize When

- tasks touch different files or isolated areas
- one task's result is not required to understand another
- there is no shared mutable state or ordered dependency between them
- combining results later is straightforward

## Do Not Parallelize When

- tasks edit the same file or tightly coupled files
- one task's output determines the next task's scope
- the work is still exploratory and boundaries are unclear
- review or verification depends on serialized execution

## Guardrails

- only `leader` invokes this skill
- use parallel dispatch to reduce latency, not to bypass review or boundary control
- if independence is unclear, do not parallelize
