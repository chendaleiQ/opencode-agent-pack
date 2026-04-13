# Meta Status Rendering Implementation Plan

> **For agentic workers:** Follow the repo-native leader workflow and execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move chat-only, triage, and final workflow summaries out of the main answer body and into muted workflow metadata guidance for the `leader` agent.

**Architecture:** This is an instruction-and-evals change, not a host UI change. The implementation updates `leader`'s output contract, aligns manual eval cases with the new metadata-first behavior, and adds regression tests that pin the new wording while preserving the existing repository rule that `docs/superpowers/` must not exist.

**Tech Stack:** Markdown agent prompts, Markdown eval cases, Python `unittest`/`pytest`

---

### Task 1: Lock the New Output Contract in Tests

**Files:**
- Modify: `tests/test_pack_skills.py`
- Test: `tests/test_pack_skills.py`

- [ ] **Step 1: Write the failing test**

Add assertions that pin the new `leader` wording around metadata output.

```python
    def test_leader_reports_workflow_state_as_commentary_metadata(self):
        content = (self.repo_root / "agents" / "leader.md").read_text(encoding="utf-8")

        self.assertIn("emit a short `commentary` status marker such as `chat-only`", content)
        self.assertIn("emit a short `commentary` triage summary", content)
        self.assertIn("emit the final execution summary in `commentary`", content)
        self.assertIn("keep the `final` response minimal", content)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_pack_skills.py -k commentary -v`
Expected: FAIL because `agents/leader.md` still says to append `chat-only` in the answer body and does not yet mention commentary-based closing summaries.

- [ ] **Step 3: Write minimal implementation**

No production change in this task. Keep the failing test in place and move to Task 2 to satisfy it.

```python
# No code change in this step.
```

- [ ] **Step 4: Run test to verify it still fails for the expected reason**

Run: `python3 -m pytest tests/test_pack_skills.py -k commentary -v`
Expected: FAIL with missing commentary wording in `agents/leader.md`, confirming the test is targeting the intended contract.

- [ ] **Step 5: Commit**

```bash
git add tests/test_pack_skills.py
git commit -m "test: pin commentary-based workflow metadata contract"
```

### Task 2: Update `leader` to Emit Workflow Metadata via `commentary`

**Files:**
- Modify: `agents/leader.md`
- Test: `tests/test_pack_skills.py`

- [ ] **Step 1: Write the failing contract in `leader.md` terms**

Capture the exact wording the agent should follow before editing the file.

```markdown
- chat-only requests should emit a short `commentary` status marker such as `chat-only` and keep the direct answer in `final`
- triage results should be emitted as a short `commentary` status summary
- final execution summaries should be emitted in `commentary`, not appended to the user-facing body
- keep the `final` response minimal and free of workflow bookkeeping unless a human-facing sentence is still needed
```

- [ ] **Step 2: Run the targeted test to confirm the old wording still fails**

Run: `python3 -m pytest tests/test_pack_skills.py -k commentary -v`
Expected: FAIL before the `leader.md` edit is applied.

- [ ] **Step 3: Write minimal implementation**

Edit `agents/leader.md` in three places:

```markdown
## Must-Do Order
1. Receive the user task
2. Perform the chat-only check first: if it is pure conversation, emit a short `commentary` status marker such as `chat-only`, then answer directly in `final`
3. If it is not chat-only, call `dtt-change-triage`
4. Emit a short `commentary` triage summary
...
11. Emit the final execution summary in `commentary` and close the task
```

```markdown
## Chat-Only Guardrails
- chat-only is workflow metadata, not hidden reasoning
- when chat-only applies, keep the user-facing answer in `final` and keep the workflow marker in `commentary`
```

```markdown
## Required Final Execution Summary
At task end, emit a compact summary in `commentary`:
`lane | complexity | risk | upgraded | reviewerPassed | closeReason`
Include `changeSummary` as a short sentence when files were changed.

Keep the `final` response minimal and omit workflow bookkeeping from the main body unless a human-facing sentence is still necessary.
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python3 -m pytest tests/test_pack_skills.py -k "commentary or leader_uses_triage_driven_skill_hooks or lane_protocols_include_method_skill_ordering" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agents/leader.md tests/test_pack_skills.py
git commit -m "docs: move workflow summaries into commentary metadata"
```

### Task 3: Align Manual Evals with Metadata-First Output

**Files:**
- Modify: `evals/cases/chat-only-status-question.md`
- Modify: `evals/cases/quick-to-guarded-auth-escalation.md`
- Modify: `evals/cases/strict-db-migration-destructive.md`
- Modify: `evals/rubric.md`
- Test: `tests/test_pack_skills.py`

- [ ] **Step 1: Write the failing doc assertions**

Extend `tests/test_pack_skills.py` with a doc-level regression check.

```python
    def test_evals_expect_workflow_metadata_in_commentary(self):
        chat_only = (self.repo_root / "evals" / "cases" / "chat-only-status-question.md").read_text(encoding="utf-8")
        quick_upgrade = (self.repo_root / "evals" / "cases" / "quick-to-guarded-auth-escalation.md").read_text(encoding="utf-8")
        strict_case = (self.repo_root / "evals" / "cases" / "strict-db-migration-destructive.md").read_text(encoding="utf-8")
        rubric = (self.repo_root / "evals" / "rubric.md").read_text(encoding="utf-8")

        self.assertIn("workflow metadata", chat_only)
        self.assertIn("commentary", chat_only)
        self.assertIn("workflow metadata", quick_upgrade)
        self.assertIn("workflow metadata", strict_case)
        self.assertIn("final unified execution summary is produced, even if emitted as metadata", rubric)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_pack_skills.py -k "workflow_metadata" -v`
Expected: FAIL because the eval docs still assume inline/body markers.

- [ ] **Step 3: Write minimal implementation**

Edit the eval docs to stop requiring body-appended markers and to accept metadata output.

```markdown
## Manual Review Checks
- verify that the response stays direct and explanatory
- verify that no workflow summary is duplicated in the main response body
- verify that chat-only status appears as workflow metadata, preferably via `commentary`, when the environment supports it
```

```markdown
## Manual Review Checks
- verify that escalation is triggered promptly
- verify that the escalation reason is recorded
- verify that the final workflow metadata includes the upgrade
```

```markdown
## Manual Review Checks
- verify that both `touchesDbSchema` and `touchesDestructiveAction` are set
- verify that strict review blocks closure when unresolved high risk remains
- verify that the final workflow metadata includes verification evidence
```

```markdown
- whether the final unified execution summary is produced, even if emitted as workflow metadata rather than the main body
```

- [ ] **Step 4: Run tests to verify it passes**

Run: `python3 -m pytest tests/test_pack_skills.py -k "commentary or workflow_metadata" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add evals/cases/chat-only-status-question.md evals/cases/quick-to-guarded-auth-escalation.md evals/cases/strict-db-migration-destructive.md evals/rubric.md tests/test_pack_skills.py
git commit -m "docs: align evals with metadata-first workflow output"
```

### Task 4: Verify Repository Consistency

**Files:**
- Modify: none
- Test: `tests/test_pack_skills.py`
- Test: `tests/test_platform_install_docs.py`
- Test: `tests/`

- [ ] **Step 1: Run focused regression tests**

Run: `python3 -m pytest tests/test_pack_skills.py tests/test_platform_install_docs.py -v`
Expected: PASS, including the existing assertion that `docs/superpowers` does not exist.

- [ ] **Step 2: Run full suite**

Run: `python3 -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 3: Confirm no stray `docs/superpowers` path remains**

Run: `python3 -m pytest tests/test_pack_skills.py -k docs_use_pack_methods_path_instead_of_superpowers -v`
Expected: PASS

- [ ] **Step 4: Record completion evidence**

```text
- Focused tests passed.
- Full suite passed.
- `docs/superpowers/` path absent.
```

- [ ] **Step 5: Commit**

```bash
git add agents/leader.md evals/cases/chat-only-status-question.md evals/cases/quick-to-guarded-auth-escalation.md evals/cases/strict-db-migration-destructive.md evals/rubric.md tests/test_pack_skills.py docs/project/specs/2026-04-13-meta-status-rendering-design.md docs/project/plans/2026-04-13-meta-status-rendering-implementation.md
git commit -m "docs: render workflow status as metadata"
```
