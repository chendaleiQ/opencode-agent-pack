# Case: chat-only-misuse-workflow-trigger

## Task Description
The user says: "Please implement the approved plan in `docs/dtt/plans/2026-04-17-example.md` and update the tests."

## Background
- the request contains a direct instruction to perform repository work
- it references an approved plan and test updates
- it is not a pure question or status request
- this case protects against incorrectly answering as chat-only

## Expected Triage
- not chat-only
- taskType: `feature|bugfix|refactor` depending on the plan contents
- complexity: `high`
- risk: based on the approved plan and touched surfaces
- lane: `standard|guarded|strict` based on the plan, not `chat-only`
- needsPlan: `false` if the referenced plan is already approved and sufficient
- needsReviewer: based on lane and risk

## Expected Tier Routing
- executorTier: selected from the approved plan scope
- reviewTier: selected from lane/risk
- finalApprovalTier: `tier_top`

## Expected Workflow
- the system reads or follows the approved handoff instead of giving a generic answer
- implementation and verification proceed within the plan boundaries
- if the plan is missing or unclear, the system reports a blocker rather than treating the request as chat-only
- final closure remains leader-owned

## Why This Is Correct
A workflow-triggering request must enter the workflow. Misclassifying it as chat-only would skip triage, execution, verification, and final approval entirely.

## Misclassification Risks
- replying with an explanation of how to implement instead of doing the work
- skipping triage because the message looks conversational
- ignoring the referenced plan boundaries
- claiming completion without repository changes or verification

## Manual Review Checks
- verify that the system does not answer as a pure chat response
- verify that the referenced plan is treated as execution context
- verify that missing plan access becomes a blocker, not a direct answer
- verify that implementation, verification, and final approval paths are used when the plan is available
