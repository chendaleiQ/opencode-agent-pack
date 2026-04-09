# Case: quick-review-reviewer-only

## Task Description
Review a small one-file patch and list any findings without changing code.

## Background
- review-only request
- no implementation requested
- bounded and low-risk

## Expected Triage
- taskType: `review`
- complexity: `low`
- risk: `low`
- estimatedFiles: `1`
- lane: `quick`
- delegate: `true`
- needsPlan: `false`
- needsReviewer: `true`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## Expected Workflow
- `leader` runs `change-triage`
- only `reviewer` is dispatched
- reviewer outputs findings-first review
- no analyzer/implementer chain is created

## Why This Is Correct
Quick review work should stay review-only and still use the stronger review tier.

## Misclassification Risks
- dispatching implementer even though code changes are not requested
- using the wrong role for review-only work

## Manual Review Checks
- verify that only `reviewer` is used downstream
- verify that the output is findings-first
- verify that final closure still stays with `leader`
