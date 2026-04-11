---
name: dtt-requesting-code-review
description: Review method skill. Use when reviewer output should focus on findings, risks, regressions, and verification gaps.
---

# Skill: dtt-requesting-code-review

## Review Priorities

1. bugs and regressions
2. scope drift and boundary violations
3. missing tests or missing verification
4. maintainability concerns that matter to correctness

## Output Rules

- findings first
- include file references when possible
- keep summary secondary to findings
- if no findings, say so explicitly and mention residual risk if any
- output must be JSON, not prose sections
- JSON must include at least `specCompliance`, `codeQuality`, and `findings`
- when there are no findings, use `findings: []` instead of prose like `无发现`
