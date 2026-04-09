---
name: finishing-a-development-branch
description: Leader-only method skill. Use when implementation is complete and the user is choosing how to merge, PR, keep, or discard the work.
---

# Skill: finishing-a-development-branch

## Purpose

Standardize post-implementation integration choices without taking over final approval.

## Use When

- implementation is complete
- verification has already passed
- the user wants to merge, open a PR, keep the branch, or discard the work

## Required Discipline

- confirm verification status first
- present explicit next-step options
- require extra confirmation for destructive cleanup paths
- keep final approval with `leader`

## Guardrails

- only `leader` invokes this skill
- do not use this before verification is complete
- do not force a merge or PR path the user did not ask for
