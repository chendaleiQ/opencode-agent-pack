# Release Policy

This project uses semantic versioning: `MAJOR.MINOR.PATCH`.

## Version Levels

## PATCH (x.y.Z)
Use for changes that do not alter core behavior and can be released safely in small steps:
- README, examples, comments, and wording fixes
- new or updated `evals/cases` without changing core routing rules
- small install fixes that do not change default install semantics
- spelling, formatting, and link fixes

## MINOR (x.Y.z)
Use for backward-compatible feature additions or rule refinements:
- compatibility improvements to triage rules without breaking existing fields or flow
- refinements to default lane or tier strategy without changing core roles or the single-entry model
- new optional checks or evaluation tooling guidance
- new optional install parameters that keep the default behavior compatible

## MAJOR (X.y.z)
Use for incompatible or high-impact behavior changes:
- `change-triage` output field changes, including additions, removals, renames, or semantic redefinition
- major lane model changes, such as adding/removing lanes or restructuring routing logic
- key tier constraint changes, such as `finalApprovalTier` no longer being fixed at top
- breaking the single-entry model so that leader is no longer the only entry point
- incompatible changes to install paths or default install behavior

## Specific Change Classification Rules

- small triage rule tuning without schema changes: MINOR
- triage output schema changes: MAJOR
- compatible tightening of lane or tier behavior: MINOR
- fundamental lane or tier changes: MAJOR
- changing the default install target path: MAJOR
- adding optional install flags while keeping defaults unchanged: MINOR
- small README or examples changes: PATCH
- adding only a new eval case: PATCH, unless the same change also alters core rules

## Minimum Pre-Release Checks
Before each release, confirm at minimum:
1. the core model is still intact: single entry, single router, single closer
2. the `change-triage` output format still matches the current version contract
3. `evals/rubric.md` still matches the active rules
4. README still matches actual behavior
5. evals still match verify and end-gate guidance
6. the platform install instructions still work in their supported platforms

## Release Notes Template (Recommended)
- version:
- release level: MAJOR/MINOR/PATCH
- core changes:
- risk assessment:
- triage/lane/tier impact:
- migration note needed:
