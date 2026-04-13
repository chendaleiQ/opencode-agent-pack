# Meta Status Rendering Design

## Goal

Render workflow status such as `chat-only`, triage summaries, and final workflow summaries as host-rendered meta events instead of normal assistant body text.

The target effect is to make these status lines appear like tool/read/skill activity in OpenCode's muted event style when the host supports that rendering.

## Context

- This repository controls agent instructions, plugin hooks, tests, and workflow docs.
- This repository does not contain OpenCode frontend/UI rendering code.
- Because of that, this change must be expressed as output-channel and wording policy, not CSS or custom UI styling.

## Proposed Behavior

### Chat-only

- Keep chat-only as a workflow classification, not hidden chain-of-thought.
- Stop requiring the final answer body to append the literal `chat-only` marker.
- Emit a short `commentary` status event such as `chat-only` before the final direct answer.
- Keep the final answer itself user-facing and free of workflow suffixes.

### Triage Summary

- Keep triage as explicit workflow metadata.
- Replace body-text triage notices with a short `commentary` status event.
- Limit that event to compact routing facts, for example lane, risk, and reviewer requirement.

### Final Workflow Summary

- Move final workflow bookkeeping into `commentary` as well.
- This includes the compact closing summary and related workflow-only fields such as `changeSummary` when they are being emitted to satisfy the workflow contract rather than to help the user understand the outcome.
- Keep user-facing body text separate from workflow bookkeeping.

## Scope

### In scope

- `leader` instruction changes that move chat-only and triage-result reporting to the `commentary` channel.
- Eval and documentation updates that currently expect a body-appended `chat-only` marker.
- Tests that lock the new expected wording or channel usage where this repo can verify it.

### Out of scope

- Any OpenCode host/frontend styling change.
- New custom event schemas beyond existing assistant channels.
- Hiding reasoning or internal chain-of-thought.

## Design

### Output model

Use existing assistant channels as follows:

- `commentary`: short workflow metadata intended to render like muted host status lines
- `final`: user-facing answer or outcome, minimized as much as possible

This aligns workflow state with the same presentation class as tool activity without introducing a new transport format.

### Instruction changes

Update `agents/leader.md` so that:

- chat-only requests produce a direct final answer plus a short `commentary` marker
- non-chat-only requests may emit a short `commentary` triage summary after `dtt-change-triage`
- closing summaries also move to `commentary`
- the final answer should not carry workflow suffixes or bookkeeping fields
- the final answer should be minimal, and may be nearly empty except for any human-facing sentence that is still needed

### Compatibility

- If the host renders `commentary` as muted metadata, the user gets the desired grey effect.
- If the host renders `commentary` like plain text, behavior still remains correct and readable.
- If the user ignores muted metadata, they are effectively choosing not to inspect workflow details; the main answer should not duplicate those details just to preserve visibility.
- No runtime gate or evidence model change is required for this feature.

## Risks

### Host rendering variance

Different hosts may style `commentary` differently. This design accepts that and optimizes for OpenCode's current muted rendering.

### Eval drift

Some eval/docs currently expect a literal body marker. Those must be updated together so the repository's documented behavior stays consistent.

## Testing

- Update or add eval expectations for chat-only so they accept meta-status output instead of a body suffix.
- Update workflow docs/evals that expect final inline summary text in the main response body.
- Add or update doc tests if they pin the old wording.
- Run the relevant Python test files plus the full `tests/` suite.

## Recommended Implementation Order

1. Update `agents/leader.md` wording for chat-only, triage, and closing-summary reporting.
2. Update eval/docs that mention a required inline `chat-only` marker or body-level workflow summary.
3. Add targeted tests for the new expectation where possible.
4. Run verification.

## Non-Goals

- Introduce hidden reasoning output.
- Rewrite the runtime hook system.
- Add host-specific UI code to this repository.
