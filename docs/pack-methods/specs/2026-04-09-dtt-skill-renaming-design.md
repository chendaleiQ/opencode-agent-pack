# DTT Skill Renaming Design

## Summary

Rename every project-local built-in skill to a `dtt-` prefixed name so the pack no longer collides with same-named skills installed from Superpowers or other external skill sources.

This is an intentional breaking change with no legacy alias layer. All project-owned references, tests, and documentation will move to the new names in one pass.

## Problem

Before this rename, the pack shipped built-in method skills under generic unprefixed names. Those legacy names could overlap with skills already installed from Superpowers under other roots such as `~/.agents/skills`.

The current OpenCode plugin detects duplicate skill names and aborts installation when it finds overlap. That protects correctness, but it creates friction for users who already have Superpowers installed. The conflict is caused by name reuse, not by a real intent to share the same skill implementation.

## Goals

- eliminate name collisions between pack-owned skills and external skill sets
- preserve the pack's single-entry workflow and plugin-native method-skill preference
- keep naming simple and human-readable
- update tests and docs so the new naming is the only documented source of truth

## Non-Goals

- preserving old skill names as aliases
- changing workflow semantics, lane routing, or tier ownership
- replacing the duplicate-source detection mechanism entirely
- renaming non-skill concepts such as agent role names

## Chosen Approach

Use a uniform `dtt-<original-name>` convention for every built-in pack skill.

Examples of the resulting names:

- `dtt-brainstorming`
- `dtt-change-triage`
- `dtt-dispatching-parallel-agents`
- `dtt-executing-plans`
- `dtt-finishing-a-development-branch`
- `dtt-receiving-code-review`
- `dtt-requesting-code-review`
- `dtt-systematic-debugging`
- `dtt-test-driven-development`
- `dtt-verification-before-completion`
- `dtt-writing-plans`

## Alternatives Considered

### 1. `dtt-method-*`

Rejected because it adds precision but makes prompts, docs, and tests noisier without solving more problems than `dtt-*`.

### 2. Rename only the overlapping skills

Rejected because it leaves inconsistent naming across the built-in skill set and requires ongoing judgment about which names are risky enough to prefix.

### 3. Keep names and rely only on duplicate detection

Rejected because it preserves installation failures for a predictable and avoidable conflict.

## Scope of Change

### Skill Definitions

- rename each directory under `skills/` to its `dtt-` prefixed form
- update each `SKILL.md` frontmatter `name:` field to the new prefixed name

### Workflow Prompts and Agent Instructions

Update all pack-owned references so they call the new names consistently, including at minimum:

- `agents/leader.md`
- `agents/implementer.md`
- `agents/reviewer.md`
- `AGENTS.md`
- any install or workflow docs that name built-in skills directly

### Tests

Update tests that assert skill presence or literal skill names, including:

- `tests/test_pack_skills.py`
- any install or documentation tests that reference the old names

### Installation and Duplicate Detection

Keep the duplicate-source detection in `.opencode/plugins/do-the-thing.js`, but let it operate on the renamed pack-owned skill set.

Expected outcome:

- a machine with external Superpowers skills installed under their original names should no longer conflict with this pack's built-in skills
- duplicate detection still remains available for future collisions against `dtt-*` names from another root

## Migration and Compatibility

This change is intentionally non-backward-compatible at the skill-name level.

Implications:

- old references to unprefixed built-in skill names inside this repository must be updated atomically
- external docs or prompts that mention the old pack-owned names will stop being correct and should be updated in release notes or migration guidance
- no dual registration, alias directory, or compatibility shim will be added

## Risks

### Missed Internal Reference

If any pack-owned document, test, or prompt still references an old skill name, the workflow may fail or the docs may drift.

Mitigation:

- perform repository-wide replacement and targeted grep verification
- update tests to assert the new names only

### Partial Rename

If directory names change without frontmatter name updates, or vice versa, tool discovery may become inconsistent.

Mitigation:

- treat each skill rename as a pair: directory name + `name:` field
- verify both filesystem and content references

### User Surprise From Breaking Change

Users familiar with the old names may be surprised.

Mitigation:

- document the change clearly in README/install docs/release notes
- explain that the purpose is to eliminate collisions with existing Superpowers installations

## Verification Plan

After implementation, verify at least the following:

1. every built-in skill exists only under its `dtt-` prefixed directory
2. every built-in `SKILL.md` uses the matching `name: dtt-*`
3. workflow prompts and docs no longer reference the old unprefixed pack-owned skill names except where discussing migration history explicitly
4. automated tests pass
5. duplicate detection still behaves correctly for true duplicate `dtt-*` skill names from another source

## Open Questions

None for the chosen scope. The naming convention and migration policy are both decided:

- prefix: `dtt-`
- migration mode: one-shot breaking rename without compatibility aliases
