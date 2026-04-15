# Case: standard-needs-plan-approval-stop-points

## Task Description
Refactor a medium-sized workflow feature that spans several files and needs a reviewed design before implementation.

## Background
- standard-lane eligible work
- not sensitive, but coupled enough to require planning
- this case focuses on the required approval stop points before execution

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
- workflow stops for spec approval before plan generation
- after approval, `leader` produces a human-readable plan in the current conversation language
- the plan is written to `docs/dtt/plans/...`
- workflow stops for plan approval before analyzer/implementer/reviewer execution starts

## Why This Is Correct
This case isolates the hard `needsPlan` gate so evals can catch approval-stop regressions directly.

## Misclassification Risks
- generating a plan before the spec is approved
- starting execution before the plan is approved
- writing artifacts outside `docs/dtt/`

## Manual Review Checks
- verify that execution does not begin before both approvals happen
- verify that the saved artifact paths match `docs/dtt/specs/...` and `docs/dtt/plans/...`
- verify that the user-facing planning output follows the current conversation language
