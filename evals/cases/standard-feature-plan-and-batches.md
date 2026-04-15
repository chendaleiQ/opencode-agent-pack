# Case: standard-feature-plan-and-batches

## Task Description
Add a new configuration toggle that affects several components, update the related docs, and keep behavior backward-compatible.

## Background
- cross-module feature work
- not obviously high risk
- should require planning and likely batch execution

## Expected Triage
- taskType: `feature`
- complexity: `high`
- risk: `low`
- touchesAuth: `false`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `4` or more
- lane: `standard`
- needsPlan: `true`
- needsReviewer: `true`
- analysisTier: `tier_fast|tier_mid`
- executorTier: `tier_fast|tier_mid`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## Expected Workflow
- `leader` runs `dtt-brainstorming`
- writes the spec to `docs/dtt/specs/...` and stops for approval
- then `leader` runs `dtt-writing-plans`
- writes the plan to `docs/dtt/plans/...` and stops for approval
- if work is large enough, `dtt-executing-plans` is inserted for batch execution
- analyzer -> implementer -> reviewer flow happens under `standard`
- `dtt-verification-before-completion` runs before closure
- human-readable spec/plan output follows the current conversation language

## Why This Is Correct
This case checks the hard planning gate for planned standard work, not just method-skill selection.

## Misclassification Risks
- skipping the plan for multi-file feature work
- skipping the spec approval or plan approval stop point
- routing to quick despite high complexity
- closing without reviewer or verification

## Manual Review Checks
- verify that the system stops after spec generation and again after plan generation until approval is given
- verify that spec/plan artifacts land under `docs/dtt/specs/` and `docs/dtt/plans/`
- verify that planning output stays human-readable in the active conversation language
- verify that reviewer is used
- verify that closure returns through `leader`
