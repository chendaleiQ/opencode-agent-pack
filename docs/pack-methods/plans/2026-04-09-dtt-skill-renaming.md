# DTT Skill Renaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the pack's subagent-driven-development equivalent (recommended) or `dtt-executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename every pack-owned built-in skill to a `dtt-` prefixed name and update all repository references so the pack no longer collides with same-named Superpowers skills.

**Architecture:** Perform the rename as one atomic repository-wide migration. First rename the skill directories and frontmatter names, then update all agent prompts, docs, and tests to reference only the new names, and finally verify that the plugin duplicate-detection behavior still protects against true duplicate `dtt-*` names.

**Tech Stack:** Markdown, JavaScript (OpenCode plugin), Python `unittest`, filesystem moves, ripgrep

---

### Task 1: Rename the built-in skill directories and frontmatter names

**Files:**
- Modify after rename: `skills/dtt-brainstorming/SKILL.md`
- Modify after rename: `skills/dtt-change-triage/SKILL.md`
- Modify after rename: `skills/dtt-dispatching-parallel-agents/SKILL.md`
- Modify after rename: `skills/dtt-executing-plans/SKILL.md`
- Modify after rename: `skills/dtt-finishing-a-development-branch/SKILL.md`
- Modify after rename: `skills/dtt-receiving-code-review/SKILL.md`
- Modify after rename: `skills/dtt-requesting-code-review/SKILL.md`
- Modify after rename: `skills/dtt-systematic-debugging/SKILL.md`
- Modify after rename: `skills/dtt-test-driven-development/SKILL.md`
- Modify after rename: `skills/dtt-verification-before-completion/SKILL.md`
- Modify after rename: `skills/dtt-writing-plans/SKILL.md`

- [ ] **Step 1: Record the exact rename map in a scratch note before touching files**

```text
dtt-brainstorming
dtt-change-triage
dtt-dispatching-parallel-agents
dtt-executing-plans
dtt-finishing-a-development-branch
dtt-receiving-code-review
dtt-requesting-code-review
dtt-systematic-debugging
dtt-test-driven-development
dtt-verification-before-completion
dtt-writing-plans
```

- [ ] **Step 2: Rename the directories in one batch**

Run:

```bash
python3 - <<'PY'
print('historical rename step: legacy unprefixed skill directories were moved to the dtt-* directories listed above')
PY
```

Expected: command exits successfully and `skills/` contains only the `dtt-*` directories for built-in pack skills.

- [ ] **Step 3: Update every renamed `SKILL.md` frontmatter `name:` field to match the new directory names**

Use this exact pattern in each file:

```md
---
name: dtt-change-triage
description: Leader-only skill. Run before any implementation. Outputs structured JSON for lane, tier, and minimal execution-path routing. Must not be invoked by analyzer, implementer, or reviewer.
---
```

Apply the same transformation to all renamed skills, changing only the `name:` value and preserving the existing descriptions and body text unless they explicitly mention the old pack-owned skill names.

- [ ] **Step 4: Verify the frontmatter rename is complete**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

expected = {
    'dtt-brainstorming',
    'dtt-change-triage',
    'dtt-dispatching-parallel-agents',
    'dtt-executing-plans',
    'dtt-finishing-a-development-branch',
    'dtt-receiving-code-review',
    'dtt-requesting-code-review',
    'dtt-systematic-debugging',
    'dtt-test-driven-development',
    'dtt-verification-before-completion',
    'dtt-writing-plans',
}

found = set()
for path in Path('skills').glob('*/SKILL.md'):
    text = path.read_text(encoding='utf-8').splitlines()
    for line in text[:5]:
        if line.startswith('name: '):
            found.add(line.split(': ', 1)[1].strip())
            break

assert expected.issubset(found), (expected - found)
print('skill frontmatter names verified')
PY
```

Expected: `skill frontmatter names verified`

- [ ] **Step 5: Commit the pure skill rename slice**

```bash
git add skills && git commit -m "refactor: prefix built-in skill names with dtt"
```

### Task 2: Update workflow prompts and repository documentation to use only `dtt-*` names

**Files:**
- Modify: `agents/leader.md`
- Modify: `agents/implementer.md`
- Modify: `agents/reviewer.md`
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/project/WORKFLOW.md`
- Modify: `docs/project/README.zh-CN.md`
- Modify: `.opencode/INSTALL.md`
- Modify: `.codex/INSTALL.md`
- Modify: `.cursor-plugin/README.md`
- Modify: `.claude-plugin/README.md`

- [ ] **Step 1: Write a failing search that proves old unprefixed references still exist before the edit**

Run:

```bash
rg --pcre2 -n "$LEGACY_PACK_SKILL_REGEX" agents AGENTS.md README.md docs .opencode .codex .cursor-plugin .claude-plugin
```

Expected: matches in agent prompts and docs that still use the old names.

Use the repository's standard legacy-skill detector regex here; keep the literal legacy names out of this post-rename document so later verification does not treat the plan itself as an active reference source.

- [ ] **Step 2: Replace pack-owned skill references with their `dtt-*` equivalents**

Make these exact style changes where applicable:

```md
- `dtt-change-triage` defines the workflow skeleton
- needsPlan=true -> `dtt-brainstorming` then `dtt-writing-plans`
- before any completion claim -> `dtt-verification-before-completion`
```

Use the same prefixing rule for every pack-owned skill mention in the listed files. Preserve the surrounding workflow meaning and do not rename non-skill terms such as `leader`, `implementer`, or `reviewer`.

- [ ] **Step 3: Update user-facing docs to explain the rename rationale where helpful**

Add or adjust one short note in install or workflow documentation using wording like:

```md
Pack-owned built-in skills use a `dtt-` prefix to avoid collisions with similarly named skills from external Superpowers installations.
```

Only add the note once or twice where it helps users understand the breaking change; do not scatter duplicate explanations everywhere.

- [ ] **Step 4: Verify docs and prompts no longer reference old pack-owned names**

Run:

```bash
rg --pcre2 -n "$LEGACY_PACK_SKILL_REGEX" agents AGENTS.md README.md docs .opencode .codex .cursor-plugin .claude-plugin
```

Expected: no matches, unless a line explicitly discusses the pre-rename history; if such a history note exists, rewrite it to make the old name clearly historical.

- [ ] **Step 5: Commit the prompt and doc updates**

```bash
git add agents AGENTS.md README.md docs .opencode .codex .cursor-plugin .claude-plugin && git commit -m "docs: update workflow references to dtt skill names"
```

### Task 3: Update automated tests and plugin expectations for the renamed skill set

**Files:**
- Modify: `tests/test_pack_skills.py`
- Modify: `tests/test_platform_install_docs.py`
- Modify: `.opencode/plugins/do-the-thing.js`

- [ ] **Step 1: Write failing assertions for the new skill names and duplicate behavior**

Update `tests/test_pack_skills.py` to assert the new expected list exactly like this:

```python
expected = [
    "dtt-brainstorming",
    "dtt-change-triage",
    "dtt-dispatching-parallel-agents",
    "dtt-executing-plans",
    "dtt-finishing-a-development-branch",
    "dtt-receiving-code-review",
    "dtt-requesting-code-review",
    "dtt-systematic-debugging",
    "dtt-test-driven-development",
    "dtt-verification-before-completion",
    "dtt-writing-plans",
]
```

Also update any literal string assertions in `tests/test_pack_skills.py` that reference old skill names in agent/docs content so they now expect the `dtt-*` names.

- [ ] **Step 2: Add or update a test expectation for the plugin duplicate story**

If `.opencode/plugins/do-the-thing.js` needs no logic change, still add or adjust a test assertion that proves the install docs/plugin now describe or operate on the prefixed pack-owned skill set. A minimal acceptable assertion is a new documentation expectation mentioning the `dtt-` prefix note added in Task 2.

- [ ] **Step 3: Run the targeted tests to confirm they fail before the full fix is complete**

Run:

```bash
python3 -m unittest tests/test_pack_skills.py tests/test_platform_install_docs.py -v
```

Expected: failures showing old skill names or outdated doc expectations.

- [ ] **Step 4: Apply the minimal code or assertion updates until the targeted tests pass**

For `.opencode/plugins/do-the-thing.js`, keep this behavior intact:

```js
const repoSkills = new Set(listSkillNames(path.join(repoDir, 'skills')));
...
if (repoSkills.has(skillName)) {
  duplicates.push({ skillName, root });
}
```

Only adjust nearby error/help text if you need it to clarify that the managed pack ships `dtt-*` skill names. Do not weaken duplicate detection or remove the external root scan.

- [ ] **Step 5: Run the targeted tests again**

Run:

```bash
python3 -m unittest tests/test_pack_skills.py tests/test_platform_install_docs.py -v
```

Expected: `OK`

- [ ] **Step 6: Commit the automated coverage updates**

```bash
git add tests/test_pack_skills.py tests/test_platform_install_docs.py .opencode/plugins/do-the-thing.js && git commit -m "test: cover dtt-prefixed built-in skills"
```

### Task 4: Run repository-wide verification and finalize the migration

**Files:**
- Modify if needed: `docs/project/RELEASE.md`
- Modify if needed: any file revealed by verification search

- [ ] **Step 1: Run a repository-wide search for stale old skill names**

Run:

```bash
rg --pcre2 -n "$LEGACY_PACK_SKILL_REGEX" .
```

Expected: only historical discussion that explicitly marks the old names as previous names; no active pack-owned workflow reference should remain unprefixed.

- [ ] **Step 2: Run the full relevant test suite**

Run:

```bash
python3 -m unittest tests/test_pack_skills.py tests/test_platform_install_docs.py -v
```

Expected: `OK`

- [ ] **Step 3: Verify the renamed skill directories on disk**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

expected = sorted([
    'dtt-brainstorming',
    'dtt-change-triage',
    'dtt-dispatching-parallel-agents',
    'dtt-executing-plans',
    'dtt-finishing-a-development-branch',
    'dtt-receiving-code-review',
    'dtt-requesting-code-review',
    'dtt-systematic-debugging',
    'dtt-test-driven-development',
    'dtt-verification-before-completion',
    'dtt-writing-plans',
])

found = sorted(p.name for p in Path('skills').iterdir() if p.is_dir())
missing = [name for name in expected if name not in found]
assert not missing, missing
print('skill directories verified')
PY
```

Expected: `skill directories verified`

- [ ] **Step 4: Update release guidance only if the repo already tracks this class of breaking change there**

If `docs/project/RELEASE.md` contains a versioning or breaking-change note section, add a short entry like:

```md
- breaking: rename pack-owned built-in skills from generic names to `dtt-*` names to avoid collisions with external Superpowers installs
```

If no such section exists, skip this edit.

- [ ] **Step 5: Create the final migration commit**

```bash
git add skills agents AGENTS.md README.md docs .opencode .codex .cursor-plugin .claude-plugin tests && git commit -m "refactor: rename built-in skills with dtt prefix"
```

## Self-Review Checklist

- Spec coverage: directory rename, frontmatter rename, prompt/doc updates, test updates, duplicate-detection preservation, and verification are all covered by Tasks 1-4.
- Placeholder scan: no `TODO`, `TBD`, or implicit “similar to above” instructions remain.
- Type/name consistency: every planned reference uses the same `dtt-<original-name>` mapping.
