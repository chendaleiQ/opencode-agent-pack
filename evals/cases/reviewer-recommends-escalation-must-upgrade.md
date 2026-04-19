# Case: reviewer-recommends-escalation-must-upgrade

## Task Description
After a guarded implementation, the reviewer reports that the change touches a broader public contract than expected and recommends escalation before closure.

## Background
- the task may begin in `guarded` or `standard`
- reviewer discovers a boundary or risk mismatch
- the reviewer recommendation is specifically to escalate
- this case protects reviewer-driven escalation

## Expected Initial Triage
- taskType: `feature|bugfix`
- complexity: `high`
- risk: `low|high` depending on whether public contract impact is confirmed during triage
- lane: `guarded|standard`
- needsReviewer: `true`
- finalApprovalTier: `tier_top`

## Expected Tier Routing
- initial reviewTier: `tier_mid|tier_top`
- upgraded boundary control: `tier_top`
- upgraded lane: `strict` when the public contract impact is confirmed high risk
- finalApprovalTier: `tier_top`

## Expected Behavior After Reviewer Escalation Recommendation
- `leader` treats the reviewer recommendation as a blocking escalation signal
- closure is paused until the upgraded lane/tier path is resolved
- follow-up analysis determines whether public API contract risk requires `strict`
- final summary records the reviewer escalation signal and outcome

## Why This Is Correct
Reviewer findings are part of the safety net. If review reveals broader public contract impact, the workflow must upgrade rather than close under stale routing assumptions.

## Misclassification Risks
- treating reviewer escalation as optional advice
- closing because implementation tests passed before review
- keeping the old lane after public contract impact is discovered
- failing to record the reviewer escalation in final evidence

## Manual Review Checks
- verify that the reviewer recommendation is surfaced to `leader`
- verify that closure is blocked pending escalation handling
- verify that lane/tier are upgraded when public contract risk is confirmed
- verify that the final summary includes the escalation decision and evidence
