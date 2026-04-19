# Case: final-summary-metadata-required-before-close

## Task Description
Finish a standard implementation after tests pass, then close the task without a unified final execution summary or verification metadata.

## Background
- the implementation itself may be correct
- the risk is an incomplete end gate
- final closure must include evidence, changed scope, and status metadata
- this case protects the final summary requirement before close

## Expected Triage
- taskType: `feature|bugfix`
- complexity: `low`
- risk: `low`
- lane: `standard`
- needsPlan: `false|true` depending on exact scope
- needsReviewer: `true`

## Expected Tier Routing
- executorTier: `tier_fast|tier_mid`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## Expected Workflow
- verification evidence is collected before closure
- final output includes a unified execution summary or equivalent workflow metadata
- the summary states files changed, verification performed, and any remaining risks
- task does not close with only "done" or a raw test result

## Why This Is Correct
The end gate is not satisfied by passing tests alone. Reviewers and future maintainers need final metadata to understand what changed and what evidence supports closure.

## Misclassification Risks
- treating test success as sufficient final summary
- omitting changed files or verification evidence
- closing without describing unresolved risks or manual checks
- burying required metadata in delegated agent output only

## Manual Review Checks
- verify that the final response or workflow metadata contains a concise execution summary
- verify that command output or manual verification evidence is named explicitly
- verify that remaining risks are either listed or explicitly absent
- verify that closure occurs only after the summary is available
