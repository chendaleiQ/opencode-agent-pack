# Case: standard-structured-spec-question-approval

## Task Description
Design and implement a medium-sized settings refactor that spans several files and requires `needsPlan=true` planning discipline before any execution starts.

## Background
- standard-lane eligible work
- not sensitive, but coupled enough to require spec and plan artifacts
- this case focuses on the spec approval checkpoint using OpenCode `question` options rather than free-form chat confirmation

## Expected Triage
- taskType: `refactor`
- complexity: `high`
- risk: `low`
- lane: `standard`
- needsPlan: `true`
- needsReviewer: `true`

## Expected Workflow
- `leader` produces a human-readable spec in the current conversation language
- the spec is written to `docs/dtt/specs/...`
- `leader` asks a structured `question` for spec approval with approve/change/reject options
- the approve option should be phrased as `批准 spec，进入 plan` or an equivalent explicit spec-approval label
- selecting the approve option clears the spec gate and allows `dtt-writing-plans` to run
- no analyzer/implementer/reviewer execution begins before the structured spec approval is recorded

## Why This Is Correct
This case catches regressions where the workflow still depends on brittle free-form approvals such as `可以`, instead of the structured `question` path.

## Misclassification Risks
- accepting free-form text as the only approval path when the structured question should be the primary path
- generating the plan before the structured spec approval is recorded
- asking a generic unrelated question that does not clearly capture approve/change/reject for the spec

## Manual Review Checks
- verify that the spec approval prompt is emitted through the `question` tool, not only as plain chat text
- verify that the question offers explicit approve/change/reject options for the spec
- verify that choosing the approve option advances to plan generation
- verify that the saved spec artifact path matches `docs/dtt/specs/...`
