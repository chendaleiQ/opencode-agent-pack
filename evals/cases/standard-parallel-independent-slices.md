# Case: standard-parallel-independent-slices

## Task Description
Update two independent plugin docs: one for Cursor installation wording and one for Codex installation wording, with no shared files.

## Background
- work is split across clearly independent files
- low risk, but more than one slice exists
- this case checks whether the plugin can safely identify parallelizable work

## Expected Triage
- taskType: `refactor`
- complexity: `high`
- risk: `low`
- lane: `standard`
- needsPlan: `true`
- needsReviewer: `true`

## Expected Workflow
- `leader` runs `change-triage`
- `leader` may use `dispatching-parallel-agents` because the slices are clearly independent
- if parallel dispatch is chosen, each subtask still keeps fresh context and its own review path

## Why This Is Correct
The plugin should only parallelize when independence is clear, not as a default optimization.

## Misclassification Risks
- forcing serial execution when the slices are obviously independent
- parallelizing work that still shares state or file boundaries

## Manual Review Checks
- verify that `dispatching-parallel-agents` is only used if the files are actually independent
- verify that subtask boundaries remain explicit
- verify that reviewer still sees the completed work before closure
