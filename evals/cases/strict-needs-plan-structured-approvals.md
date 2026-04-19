# Case: strict-needs-plan-structured-approvals

## Task Description
Implement a high-risk public authentication API change that requires coordinated code changes, migration notes, tests, and rollback guidance.

## Background
- the task is strict due to auth and public contract impact
- planning is required before execution
- both spec approval and plan approval must be explicit stop points
- this case protects structured approval discipline in the strict lane

## Expected Triage
- taskType: `feature`
- complexity: `high`
- risk: `high`
- touchesAuth: `true`
- touchesPublicApi: `true`
- lane: `strict`
- needsPlan: `true`
- needsReviewer: `true`

## Expected Tier Routing
- analysisTier: `tier_top|tier_mid`
- executorTier: `tier_mid|tier_top`
- reviewTier: `tier_top`
- finalApprovalTier: `tier_top`

## Expected Workflow
- `leader` creates a structured spec under `docs/dtt/specs/...` and stops for approve/change/reject
- after spec approval, `leader` creates a structured plan under `docs/dtt/plans/...` and stops for approve/change/reject
- implementation does not start before both approvals are complete
- strict review and verification run before closure

## Why This Is Correct
Strict work with `needsPlan=true` needs both planning artifacts and human approval gates. Starting execution before either approval would bypass the main risk-control mechanism.

## Misclassification Risks
- writing a plan without a prior approved spec
- executing after spec approval but before plan approval
- using informal chat approval without recording the structured stop point
- downgrading strict auth/API work into standard planning

## Manual Review Checks
- verify that both `question` prompts or equivalent structured approval options are present
- verify that spec and plan artifacts are stored in the expected directories
- verify that implementation begins only after both approvals
- verify that strict reviewer and final approval gates remain active
