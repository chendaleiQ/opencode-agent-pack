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
- `leader` runs `dtt-change-triage`
- because `needsPlan=true`, execution cannot start until spec approval and plan approval both happen
- spec/plan artifacts are written to `docs/dtt/specs/...` and `docs/dtt/plans/...`
- `leader` may use `dtt-dispatching-parallel-agents` because the slices are clearly independent
- if parallel dispatch is chosen, each subtask still keeps fresh context and its own review path

## Why This Is Correct
The plugin should only parallelize when independence is clear, not as a default optimization.

## Misclassification Risks
- dispatching parallel execution before the planning gate is cleared
- forcing serial execution when the slices are obviously independent
- parallelizing work that still shares state or file boundaries

## Manual Review Checks
- verify that any parallel dispatch happens only after the spec/plan approval stops are cleared
- verify that `dtt-dispatching-parallel-agents` is only used if the files are actually independent
- verify that subtask boundaries remain explicit
- verify that reviewer still sees the completed work before closure
