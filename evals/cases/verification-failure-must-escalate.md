# Case: verification-failure-must-escalate

## Task Description
Fix a low-risk bug in a helper function, but the targeted verification command fails after implementation.

## Background
- the task starts as a low-risk implementation
- the important behavior is what happens after verification failure
- this case exists to protect `dtt-verification-before-completion` and escalation rules

## Expected Initial Triage
- taskType: `bugfix`
- complexity: `low`
- risk: `low`
- lane: `quick`
- delegate: `true`
- needsPlan: `false`
- needsReviewer: `false`
- executorTier: `tier_fast`
- finalApprovalTier: `tier_top`

## Expected Behavior After Verification Fails
- `dtt-verification-before-completion` records the failed evidence
- the task must not close on a success claim
- escalation is triggered because verification failed
- the final summary must describe the failure rather than implying completion

## Why This Is Correct
The plugin should never allow a completion claim to pass through when fresh verification failed.

## Misclassification Risks
- treating failed verification as a warning only
- allowing `leader` to close the task anyway

## Manual Review Checks
- verify that the failed command or manual check is explicitly recorded
- verify that closure is blocked or escalated
- verify that no success wording is emitted after failed verification
