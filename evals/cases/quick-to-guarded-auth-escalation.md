# Case: quick-to-guarded-auth-escalation

## Task Description
Initial request: fix a small bug where the profile page shows an empty nickname.
During execution, the root cause turns out to be in role-checking logic and requires auth changes.

## Background
- initially looks like a one-file low-risk bugfix
- execution reveals auth impact
- this is the main upgrade-boundary scenario for the plugin

## Expected Initial Triage
- taskType: `bugfix`
- complexity: `low`
- risk: `low`
- touchesAuth: `false`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `1`
- lane: `quick`
- executorTier: `tier_fast`
- finalApprovalTier: `tier_top`

## Expected Upgrade During Execution
When auth impact is discovered:
- `touchesAuth` becomes `true`
- risk escalates to `high`
- lane escalates to at least `guarded`
- tier escalates to at least `tier_mid`
- `leader` adds new boundaries before work continues

## Why This Is Correct
The plugin must react to new risk discovered during execution instead of freezing the original quick classification.

## Misclassification Risks
- staying in quick after auth impact is discovered
- failing to add guarded boundaries

## Manual Review Checks
- verify that escalation is triggered promptly
- verify that the escalation reason is recorded
- verify that the final workflow metadata includes the upgrade
