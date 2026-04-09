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
- then `dtt-writing-plans`
- if work is large enough, `dtt-executing-plans` is inserted for batch execution
- analyzer -> implementer -> reviewer flow happens under `standard`
- `dtt-verification-before-completion` runs before closure

## Why This Is Correct
This case checks the method-skill hooks for planned standard work.

## Misclassification Risks
- skipping the plan for multi-file feature work
- routing to quick despite high complexity
- closing without reviewer or verification

## Manual Review Checks
- verify that planning hooks actually run
- verify that reviewer is used
- verify that closure returns through `leader`
