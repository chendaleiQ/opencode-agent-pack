---
name: test-driven-development
description: Method skill for implementation tasks that change behavior. Use when features, bugfixes, or behavior changes should be developed test-first.
---

# Skill: test-driven-development

## Core Rule

No production code without a failing test first.

## Required Sequence

1. write the smallest test for the intended behavior
2. run it and confirm it fails for the expected reason
3. implement the smallest code change that makes it pass
4. run the test again and confirm it passes
5. refactor only while staying green

## Guardrails

- use this for feature, bugfix, and behavior-change work when tests are available
- if the codebase has no test harness or the task is configuration-only, report that explicitly instead of pretending TDD happened
- this skill strengthens implementation discipline; it does not replace pack workflow routing
