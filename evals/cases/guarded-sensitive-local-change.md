# Case: guarded-sensitive-local-change

## Task Description
Update a local account-lockout threshold in authentication logic without changing the database schema or public API.

## Background
- the code change is local and bounded
- the task touches authentication logic
- this is the canonical `guarded` starting case: low complexity, high risk

## Expected Triage
- taskType: `bugfix` or `refactor`
- complexity: `low`
- risk: `high`
- touchesAuth: `true`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `1` or `2`
- lane: `guarded`
- delegate: `true`
- needsPlan: `false`
- needsReviewer: `true`
- analysisTier: `tier_mid`
- executorTier: `tier_mid|tier_fast`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## Expected Workflow
- `leader` sets explicit guarded boundaries before downstream work starts
- analyzer may be used, but a full strict flow is not required by default
- reviewer checks scope and risk before closure
- final approval remains with `tier_top`

## Why This Is Correct
This task is not cross-module enough to be `strict`, but auth impact prevents it from staying in `quick` or `standard`.

## Misclassification Risks
- routing to `quick` because the change is small
- routing to `standard` because complexity is low but risk was ignored

## Manual Review Checks
- verify that `touchesAuth` forces `risk=high`
- verify that `leader` defines guarded boundaries
- verify that closure still requires reviewer plus `tier_top`
