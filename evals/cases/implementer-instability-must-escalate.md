# Case: implementer-instability-must-escalate

## Task Description
Implement a small bug fix, but the implementer reports that tests are flaky, the reproduction is inconsistent, and the change may have affected unrelated behavior.

## Background
- the task can begin as a quick low-risk fix
- instability appears during execution rather than at initial triage
- the important behavior is whether the workflow escalates instead of forcing closure
- this case covers implementer-reported uncertainty and instability

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

## Expected Tier Routing
- initial executorTier: `tier_fast`
- escalation target: at least `tier_mid` analysis or review
- finalApprovalTier: `tier_top`

## Expected Behavior After Instability
- implementer reports instability and does not claim completion
- `leader` escalates for analysis, review, or a higher-confidence fix path
- verification evidence must include the flaky or inconsistent result
- final closure is blocked until instability is resolved or explicitly recorded as unresolved

## Why This Is Correct
Low initial complexity does not justify closing when the executor discovers unstable behavior. Implementer instability is an escalation trigger because it means the original confidence and risk assumptions are no longer reliable.

## Misclassification Risks
- accepting a success summary despite unresolved instability
- treating flaky verification as a non-blocking note
- skipping reviewer involvement after uncertainty is reported
- losing the instability evidence in the final metadata

## Manual Review Checks
- verify that the implementer report is not overwritten by a success claim
- verify that escalation happens after instability is reported
- verify that failed or flaky checks are recorded as evidence
- verify that closure waits for a stable resolution path
