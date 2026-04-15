# Maintaining Guide

This document defines the false-classification correction process and the long-term convergence workflow. The goal is to stay measurable, iterative, and resistant to prompt bloat.

## Maintenance Priorities (Fixed)
1. **Protect against high-risk misses first**
2. Then optimize low-risk over-escalation
3. Handle wording and UX details last

## Development and Merge Discipline
- All development should happen in pull requests.
- Do not develop directly on `main`.
- Treat `main` as protected and always releasable.
- Before merging to `main`, confirm the change is acceptable to ship in the next release.
- If a change is still exploratory, incomplete, or risky, keep it on the PR branch until it is ready.

## Fix Order When You Find a Misclassification
1. Add a real case to `evals/cases` first, redacted if needed
2. Use `evals/rubric.md` to describe the exact failure
3. Adjust triage rules, preferring small and explainable changes
4. Tighten the quick lane threshold when necessary
5. Raise the priority of sensitive-signal handling when necessary
6. Update README and supporting docs afterward

Do not jump straight to piling on more long prompts without first adding a case.

## When To Add a Hard Rule
Consider adding a hard rule when any of these is true:
- the same kind of high-risk miss happens repeatedly (>=2 times)
- the impact of the miss is severe (security, data, external contract)
- wording guidance alone cannot prevent recurrence reliably

Examples of hard-rule directions:
- force `risk=high` when a sensitive signal is hit
- ban a certain task class from entering `quick`
- require escalation to `strict` after a certain verification failure

## When To Update Documentation Only
Only do this when all of the following are true:
- the behavior itself is correct and the issue comes from unclear explanation
- there is no real misclassification evidence
- the issue does not involve security, data, or external contract risk

In that case, make only a PATCH-level documentation change.

## How To Keep the System From Becoming Bloated
- every new rule must be tied to at least one eval case
- prefer changing thresholds and priority instead of adding free-form exceptions
- merge overlapping rules instead of restating them
- regularly remove outdated or duplicate rule text
- review total rule count and readability before release
- do not regress `quick` back into a fixed analyzer + implementer + reviewer chain
- do not require subagents to rerun triage or a full workflow stack for local tasks

## Misclassification Types and Handling Guidance

### A. High-Risk Work Incorrectly Downgraded (Most Severe)
- add a case immediately
- prefer a hard rule or tighter quick/standard conditions
- move related task types to guarded/strict by default when necessary
- usually at least MINOR, or MAJOR if schema or core logic changes

### B. Low-Risk Work Over-Escalated
- first decide whether the conservative behavior is acceptable
- if it clearly hurts efficiency, loosen it carefully
- optimize cost through tier selection before loosening the lane itself
- if the issue is process weight, first check whether quick is wrongly using the full chain or whether subagents are rerunning the workflow
- usually PATCH or MINOR

### C. Risk Only Becomes Visible During Execution
- add cases for boundary-triggered escalation
- strengthen escalation triggers for analyzer and reviewer
- make sure the auto-escalation chain can still trigger and be recorded

## Suggested Maintenance Workflow
1. collect real tasks, redacted if needed
2. classify them: missed risk / over-permissive pass / delayed escalation
3. add or update the matching eval case
4. run manual evaluation and record the result, including command verification or explicit manual evidence
5. submit the rule correction
6. update the release level in `RELEASE.md`
7. release and retest during the next evaluation cycle

## Minimum PR Review Requirements
- did it add or update the matching eval case?
- did it explain the impact of the high-risk miss?
- did it explain the release level and why?
- did it preserve the single-entry and final-closure model?
- did it avoid unbounded rule growth?
