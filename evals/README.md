# Evals

This directory is used to manually evaluate the routing and workflow quality of `do-the-thing`, with the highest priority on preventing high-risk under-classification.

The evals in this repository are intentionally **manual-run, manual-compare, manual-record** checks. They are not wired into CI by default.

## Contents
- `rubric.md`: the shared scoring rubric
- `cases/`: representative task scenarios that exercise the workflow

## How to Use
1. Pick a case
2. Run the system manually through triage, and continue into review or closure when the case requires it
3. Save or record the actual outputs
4. Compare the observed behavior with the expected behavior in the case file and score it with `rubric.md`
5. Record deviations and verification evidence:
   - which commands were run, if any
   - which manual checks were performed when no formal verify command existed
   - whether reviewer and end-gate behavior happened correctly
6. Turn the result into a correction action and update release notes when needed

## Common Deviation Types
- high-risk under-classification
- low-risk over-escalation
- wrong lane choice
- wrong tier routing
- escalation that should have happened but did not
- reviewer or end-gate inconsistency
- quick task taking an unnecessary full workflow path
- subagent rerunning triage or heavyweight workflow logic

## Case Authoring Requirements
Each case should include:
- task description
- background
- expected complexity/risk/lane
- expected tier routing
- why the judgment is correct
- misclassification risks
- manual review checks (optional, but recommended)

## Evaluation Priority
The top priority is **keeping the high-risk miss rate low**, not maximizing general accuracy.

## Notes
- these evals are mainly for local review or manual workflow checks
- if CI is added later, it should not change the current manual-first operating model
