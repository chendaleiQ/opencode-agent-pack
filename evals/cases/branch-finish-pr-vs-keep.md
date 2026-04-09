# Case: branch-finish-pr-vs-keep

## Task Description
Implementation is complete and verified. The user asks what to do next: open a PR, keep the branch for later, or discard the work.

## Background
- this case checks the `finishing-a-development-branch` method hook
- it is post-implementation behavior, not implementation routing
- the plugin should present options rather than forcing one path

## Expected Workflow
- implementation is already complete
- verification evidence already exists
- `leader` enters `finishing-a-development-branch`
- the system presents explicit next-step options
- destructive cleanup paths require stronger confirmation

## Expected Good Output
- confirms verification status first
- presents PR / keep branch / discard work as separate choices
- does not force merge or deletion without user intent

## Why This Is Correct
The branch-finishing hook should standardize the post-implementation choice, not hijack the final decision.

## Misclassification Risks
- auto-pushing the user toward PR or deletion
- skipping verification confirmation before presenting closeout options

## Manual Review Checks
- verify that verification is referenced before branch-finish advice
- verify that at least two safe options are presented
- verify that destructive cleanup is not assumed by default
