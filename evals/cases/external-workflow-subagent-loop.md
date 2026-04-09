# Case: external-workflow-subagent-loop

## Task Description
Fix a simple docs typo while an external workflow system is installed in the environment.

## Background
- the task itself is low-risk quick work
- the environment includes an external workflow system that could try to re-trigger heavyweight process logic
- the main risk is subagent workflow loopback

## Expected Triage
- taskType: `refactor`
- complexity: `low`
- risk: `low`
- estimatedFiles: `1`
- lane: `quick`
- delegate: `true`
- needsPlan: `false`
- needsReviewer: `false`
- executorTier: `tier_fast`
- finalApprovalTier: `tier_top`

## Expected Workflow
- only `leader` runs `dtt-change-triage`
- quick path dispatches only the minimum necessary downstream role
- delegated subagent must not rerun triage or launch an external heavyweight workflow chain
- if handoff is unclear, the subagent should report back instead of expanding scope

## Why This Is Correct
This case protects the plugin boundary when external workflow systems are present.

## Misclassification Risks
- simple work gets inflated into a high-cost process chain
- subagent boundaries are lost because the environment prefers an external system

## Manual Review Checks
- verify that no subagent reruns workflow routing
- verify that quick still stays minimal-path
- verify that `leader` remains the only closer and final approver
