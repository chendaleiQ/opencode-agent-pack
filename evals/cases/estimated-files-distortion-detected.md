# Case: estimated-files-distortion-detected

## Task Description
The user says a change is a "one-line tweak," but the requested behavior requires updating routing logic, tests, docs, eval cases, and release notes across several directories.

## Background
- the user-provided size estimate is misleading
- the actual file footprint is visibly larger than one file
- this case checks whether triage detects distorted `estimatedFiles`
- the goal is not to punish inaccurate wording, but to prevent unsafe under-classification

## Expected Triage
- taskType: `feature|refactor`
- complexity: `high`
- risk: `low`
- estimatedFiles: greater than `1`
- lane: `standard`
- needsPlan: `true` if cross-module behavior changes are required
- needsReviewer: `true`

## Expected Tier Routing
- analysisTier: `tier_fast|tier_mid`
- executorTier: `tier_fast|tier_mid`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## Expected Workflow
- triage uses actual impact and file footprint rather than the user's "one-line" label
- the response identifies the estimate distortion
- planning or batching is used if the real scope is cross-module
- verification covers all touched areas, not only the first file changed

## Why This Is Correct
The rubric explicitly checks whether `estimatedFiles` is obviously distorted. Under-counting files can cause a multi-part change to be routed through an unsafe quick path.

## Misclassification Risks
- accepting the user's file estimate without checking impact
- routing cross-directory behavior changes to `quick`
- omitting tests or docs from the expected footprint
- using the distorted estimate to skip review

## Manual Review Checks
- verify that `estimatedFiles` reflects the likely actual footprint
- verify that the lane follows actual complexity, not the user's label
- verify that the workflow includes review when multiple areas are affected
- verify that verification evidence covers each relevant touched area
