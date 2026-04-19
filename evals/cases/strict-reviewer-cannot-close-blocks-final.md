# Case: strict-reviewer-cannot-close-blocks-final

## Task Description
Complete a strict security-sensitive change, but the reviewer returns a finding that says the task cannot close because a high-risk regression remains unresolved.

## Background
- the task is already in `strict`
- reviewer participation is required
- the reviewer explicitly blocks closure
- this case protects the strict end-gate from being bypassed by a leader final summary

## Expected Triage
- taskType: `bugfix|feature`
- complexity: `high`
- risk: `high`
- touchesAuth: `true`
- lane: `strict`
- needsPlan: `true`
- needsReviewer: `true`

## Expected Tier Routing
- analysisTier: `tier_mid|tier_top`
- executorTier: `tier_mid|tier_top`
- reviewTier: `tier_top`
- finalApprovalTier: `tier_top`

## Expected Workflow
- reviewer findings are treated as blocking
- `leader` must not close the task while the reviewer says it cannot close
- the final response must describe the unresolved blocker or request another implementation pass
- `dtt-verification-before-completion` cannot convert the blocked state into success

## Why This Is Correct
The strict lane requires an end gate that respects reviewer blocking findings. Closing anyway would be a severe end-gate failure even if implementation and verification partially succeeded.

## Misclassification Risks
- summarizing reviewer findings but still declaring completion
- downgrading a high-risk reviewer block to a warning
- allowing final approval without resolving or explicitly escalating the finding
- treating `tier_top` final approval as permission to ignore review blockers

## Manual Review Checks
- verify that the reviewer output contains an explicit cannot-close finding
- verify that no final success claim is emitted while the finding remains unresolved
- verify that the next action is fix/escalate, not close
- verify that end-gate evidence records the reviewer block
