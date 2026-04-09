# Case: strict-public-api-contract-change

## Task Description
Change a public API response shape by removing an old field and introducing a new nested object.

## Background
- breaks external contract
- crosses multiple modules
- should never stay outside strict routing

## Expected Triage
- taskType: `feature`
- complexity: `high`
- risk: `high`
- touchesPublicApi: `true`
- estimatedFiles: `5` or more
- lane: `strict`
- needsPlan: `true`
- needsReviewer: `true`
- analysisTier: `tier_mid|tier_top`
- executorTier: `tier_mid`
- reviewTier: `tier_top|tier_mid`
- finalApprovalTier: `tier_top`

## Expected Workflow
- `leader` runs `brainstorming` and `writing-plans`
- strict boundaries and prohibited actions are stated by `tier_top`
- reviewer must verify contract risk before closure
- if reviewer says the task cannot close, closure must be blocked

## Why This Is Correct
Public API contract changes are exactly the kind of work that should force strict handling.

## Misclassification Risks
- routing to standard despite public API impact
- letting `tier_fast` lead any part of strict decision-making

## Manual Review Checks
- verify that `touchesPublicApi` is detected
- verify that strict boundaries are stated
- verify that final approval stays with `tier_top`
