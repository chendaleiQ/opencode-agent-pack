---
name: executing-plans
description: Leader-only method skill. Use when a plan already exists and the work should be executed in ordered batches with review and verification checkpoints.
---

# Skill: executing-plans

## Purpose

Turn an existing plan into a controlled execution mode without changing pack workflow ownership.

## Use When

- a plan already exists
- the task is large enough to benefit from batch execution
- ordered progress, checkpoints, and blocker handling matter

## Required Discipline

- read the plan before starting a batch
- execute in small batches rather than all-at-once
- after each batch, review status and verification evidence before continuing
- if a blocker appears, stop and escalate instead of guessing

## Guardrails

- only `leader` invokes this skill
- this skill executes an existing plan; it does not replace `change-triage`
- review and verification still happen under pack rules
