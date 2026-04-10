# Deep Analysis: Everything Claude Code vs do-the-thing

**Date**: 2026-04-10
**Reference Project**: [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
**Analyzed Project**: do-the-thing (this repository)

---

## Executive Summary

do-the-thing has a **superior workflow theory** (single-entry lane+tier routing with strict safety defaults) but lags significantly in **execution infrastructure** (no Hooks, no persistence, no observability) compared to Everything Claude Code (ECC). The recommended priority is adding a Hook system — this bridges the gap between "rules that hope LLM complies" and "automation that guarantees execution."

---

## Part 1: Everything Claude Code — Core Essence

### 1.1 Project Scale

| Metric | Value |
|--------|-------|
| Stars | 149K+ |
| Forks | 23.1K |
| Commits | 1,268 |
| Agents | 47 |
| Skills | 181 |
| Commands | 79 |
| MCP Configs | 14 |
| Internal Tests | 1,700+ |
| Hackathon | Anthropic Winner |

### 1.2 Core Architecture (Six Subsystems)

```
everything-claude-code/
├── agents/*.md        # Specialized subagent definitions (YAML frontmatter)
├── skills/            # Canonical workflow definitions (primary surface)
├── commands/          # Legacy slash-entry shims (migrating to skills/)
├── hooks/             # Event-driven automations (PreToolUse, PostToolUse, etc.)
├── rules/             # Always-follow guidelines (common/ + per-language/)
└── mcp-configs/       # External service integrations
```

**Governing Principles (SOUL.md)**:
1. **Agent-First** — Route work to the right specialist early
2. **Test-Driven** — Write/refresh tests before trusting implementation
3. **Security-First** — Validate inputs, protect secrets, safe defaults
4. **Immutability** — Prefer explicit state transitions over mutation
5. **Plan Before Execute** — Complex changes in deliberate phases

### 1.3 The Hook System — Deterministic Automation

ECC's most mature subsystem. Six event types with 30+ hooks:

| Event | Count | Can Block? |
|-------|-------|------------|
| `PreToolUse` | 11 | Yes (exit 2) |
| `PostToolUse` | 10 | No |
| `PostToolUseFailure` | 1 | No |
| `Stop` | 6 | No |
| `SessionStart` | 1 | No |
| `SessionEnd` | 1 | No |
| `PreCompact` | 1 | No |

**Critical Insight**: Hooks fire **100% deterministically**. Skills fire ~50-80% probabilistically. This is why ECC v2 migrated observation from Skills to Hooks.

#### Top 5 Must-Have Hooks

| Hook ID | Matcher | Purpose |
|---------|---------|---------|
| `pre:bash:block-no-verify` | Bash | Block `git commit --no-verify` |
| `pre:bash:commit-quality` | Bash | Detect secrets, console.log before commit |
| `pre:config-protection` | Write/Edit | **Block AI from weakening lint/formatter configs** |
| `post:edit:accumulator` | Edit/Write | Record edited paths for batch processing |
| `stop:format-typecheck` | * | Batch Biome/Prettier + tsc once at Stop |

The `pre:config-protection` hook solves a critical AI failure mode: **AI "fixes" lint errors by disabling rules instead of fixing code**.

### 1.4 Instinct-Based Continuous Learning (v2.1)

```
Session Activity → Hooks capture ALL tool use (100% reliable)
  → observations.jsonl (project-scoped)
  → Background agent detects patterns (Haiku — cheap)
  → Creates/updates instincts with confidence scores
  → /evolve clusters instincts into skills/commands/agents
  → /promote moves project instincts global when seen 2+ projects
```

**Instinct Properties**:
- **Atomic**: one trigger, one action
- **Confidence-weighted**: 0.3 (tentative) to 0.9 (near-certain)
- **Project-scoped**: React patterns stay in React project
- **Evidence-backed**: confidence increases/decreases based on observations

### 1.5 Token Optimization

| Strategy | Implementation |
|----------|---------------|
| Model routing | Haiku=explore/docs, Sonnet=90% coding, Opus=security/architecture |
| MCP discipline | 20-30 configured, <10 enabled, <80 tools active |
| MCP→CLI conversion | Replace persistent MCPs with CLI-based skill wrappers |
| Batch processing | `accumulator` + `stop:format-typecheck` pattern |
| Hook async | Learning/build analysis/quality checks are `async: true` |
| Context budget | Avoid last 20% of context for large refactors |

### 1.6 Profile-Gated Runtime Control

```bash
export ECC_HOOK_PROFILE=standard  # minimal | standard | strict
export ECC_DISABLED_HOOKS="pre:bash:tmux-reminder,post:edit:typecheck"
```

Hooks declare profiles in `hooks.json`: `"standard,strict"` means runs in standard and strict, but not minimal.

### 1.7 Verification Loop (6-Phase Pipeline)

```
Phase 1: Build        → npm run build
Phase 2: Type Check   → tsc --noEmit / pyright
Phase 3: Lint         → npm run lint / ruff check
Phase 4: Tests        → npm test --coverage (80% min)
Phase 5: Security     → grep secrets, console.log
Phase 6: Diff Review  → git diff --stat
```

Output: structured PASS/FAIL report, READY/NOT READY for PR.

### 1.8 Security Model (Defense in Depth)

| Layer | Mechanism |
|-------|-----------|
| Rules | Always-loaded security.md, no hardcoded secrets |
| PreToolUse Hooks | Block dangerous operations, commit quality gates |
| Agent | `security-reviewer` agent (recommended: Opus) |
| Skills | `security-scan`, `hipaa-compliance`, `security-review` |
| Supply Chain | No external runtime installs, manual audit for PRs |

### 1.9 Cross-Platform Strategy

| Platform | Support Level |
|----------|---------------|
| Claude Code | Native plugin, full hooks/agents/commands |
| OpenCode | `.opencode/dist/` compiled plugin |
| Codex | `scripts/sync-ecc-to-codex.sh`, config merge |
| Cursor | `after-file-edit.js` hook wiring |
| Gemini | Referenced, planned |

---

## Part 2: do-the-thing Current State

### 2.1 Architecture Overview

```
do-the-thing/
├── AGENTS.md           # Agent registry only (not workflow logic)
├── agents/            # 4 agents: leader, analyzer, implementer, reviewer
├── skills/            # 11 dtt-* method skills
├── commands/          # 1 command: /providers
├── tools/             # 3 Python tools (model router, config, provider policy)
├── tests/             # 6 Python test files (49 tests)
├── evals/             # Manual eval system (14 cases, rubric)
├── install/           # Bash + PowerShell installers
├── docs/              # Bilingual docs (EN + zh-CN)
├── .opencode/         # OpenCode native plugin
├── .codex/            # Codex skills symlink
├── .claude-plugin/    # Deferred (no persistent registration)
└── .cursor-plugin/    # Deferred (under investigation)
```

### 2.2 Lane + Tier Routing System

**Four Lanes**:

| Lane | Trigger | Agent Chain |
|------|---------|-------------|
| `quick` | complexity=low, risk=low, no sensitive | Minimal: 1 role only (implementer/analyzer/reviewer) |
| `standard` | complexity=high, risk=low | analyzer → implementer → reviewer |
| `guarded` | risk=high (sensitive signals) | analyzer (tier_mid) → implementer (restricted) → reviewer |
| `strict` | complexity+risk both high | tier_top writes plan → step-by-step → tier_top review |

**Three Tiers**:
- `tier_fast` → Haiku/mini/flash models
- `tier_mid` → Sonnet/pro models
- `tier_top` → Opus/pro/sonnet models (leader always tier_top)

### 2.3 Strengths

| Area | Assessment |
|------|------------|
| Workflow theory | Lane+tier routing is well-conceived, addresses real user pain |
| Safety defaults | Conservative defaults, escalation-only, sensitive signals force high-risk |
| Separation of concerns | Clean boundaries: registry / workflow logic / skills / tools |
| Anti-bloat philosophy | MAINTAINING.md explicitly warns against rule inflation |
| Eval-driven development | 14 manual cases + 5-dimension rubric + risk-asymmetric scoring |
| Installer system | Cross-platform, idempotent, integration-tested |
| Provider routing | Dynamic detection, allowlist control, tier-based model selection |

### 2.4 Weaknesses vs ECC

| Dimension | do-the-thing | ECC | Gap |
|-----------|-------------|-----|-----|
| Hook system | ❌ None | ✅ 30+ hooks | 🔴 Critical |
| Deterministic automation | ❌ LLM-instruction-only | ✅ 100% Hook triggers | 🔴 Critical |
| Continuous learning | ❌ None | ✅ Instinct v2.1 | 🟡 Important |
| Session persistence | ❌ None | ✅ Multi-layer | 🟡 Important |
| Security automation | ⚠️ Rules-only | ✅ Multi-layer depth | 🟡 Important |
| Verification pipeline | ⚠️ Instruction-only | ✅ Hook-driven 6-phase | 🟡 Important |
| Token optimization | ⚠️ Model routing exists | ✅ Full-stack | 🟡 Important |
| Observability | ❌ None | ⚠️ Cost tracking + audit | 🟡 Important |
| Tests | 49 | 1,700+ | 🟡 Important |
| Platform support | 2/4 deferred | 4/5+ native | 🟢 Acceptable |

---

## Part 3: Recommendations for do-the-thing

### Priority Matrix

| Priority | Recommendation | Impact | Effort |
|----------|----------------|--------|--------|
| **P0** | Add Hook system | Closes critical gap | High |
| **P0** | Hook profile runtime control | Enables flexibility | Medium |
| **P1** | Session persistence | Improves context continuity | Medium |
| **P1** | Verification Hook-ization | Ensures end-gate proof | Medium |
| **P1** | Audit logging | Enables observability | Low |
| **P1** | Automated eval regression | Scales quality | Medium |
| **P2** | Batch processing pattern | Reduces token waste | Low |
| **P2** | WORKING-CONTEXT.md | Project-level state | Low |
| **P2** | Token budget awareness | Improves first-pass success | Low |
| **P2** | Domain skills (security, migrations) | Fills knowledge gaps | Medium |

---

### P0 Recommendations

#### R1: Introduce Hook System

**Current problem**: All workflow enforcement depends on LLM following markdown instructions. No deterministic guarantees.

**Proposed structure**:
```
skills/dtt-hooks/
├── hooks.json           # Hook registry
└── scripts/
    pre-commit-quality.js      # Commit safety checks
    pre-config-protection.js   # Block lint-weakening edits
    post-edit-accumulator.js   # Collect edited paths
    stop-batch-verify.js       # Unified verification at Stop
    session-start-context.js   # Load previous context
    pre-compact-state-save.js  # Save before compaction
```

**Top 5 hooks to implement first**:
1. `pre:config-protection` — Solves AI's "disable rules instead of fixing code" failure mode
2. `pre:bash:block-no-verify` — Prevent bypassing pre-commit hooks
3. `post:edit:accumulator` + `stop:batch-verify` — Batch verification reduces 70%+ overhead
4. `session:start:context-load` — Restore previous session state
5. `pre:compact:state-save` — Preserve context before auto-compaction

#### R2: Hook Profile Runtime Control

```bash
export DTT_HOOK_PROFILE=standard  # minimal | standard | strict
export DTT_DISABLED_HOOKS="pre:bash:tmux-reminder"
```

Each hook in `hooks.json` declares required profiles:
```json
{
  "id": "pre:config-protection",
  "profiles": ["standard", "strict"],
  "async": false
}
```

---

### P1 Recommendations

#### R3: Session Persistence

```
~/.config/opencode/do-the-thing/
└── sessions/
    └── <project-git-remote-hash>/
        ├── latest-context.json   # Last session state
        ├── observations.jsonl   # Tool use log
        └── instincts/           # Future: learned patterns
```

Leader behavior:
- **SessionStart**: Load `latest-context.json` → restore work context
- **Stop**: Write current state to `latest-context.json`
- **PreCompact**: Save compressed snapshot

#### R4: Verification Hook-ization

Current `dtt-verification-before-completion` is instruction-only. Upgrade to hook-driven:

```javascript
// stop:verification-gate.js
// Runs automatically before leader can declare completion:
// 1. Check for unsaved edits
// 2. Run lint (if package.json has lint script)
// 3. Run tests (if package.json has test script)
// 4. Verify git diff within estimatedFiles
// 5. Output structured PASS/FAIL report
```

#### R5: Audit Logging

```json
// post:audit-log.js records:
{
  "timestamp": "2026-04-10T...",
  "taskType": "feature",
  "lane": "standard",
  "escalated": false,
  "tiers": { "analysis": "tier_fast", "executor": "tier_mid" },
  "filesChanged": 3,
  "duration": "4m32s",
  "verificationPassed": true
}
```

Stored at `~/.config/opencode/do-the-thing/audit/`.

#### R6: Automated Eval Regression

Convert 14 manual eval cases to pytest:

```python
# tests/test_triage_conformance.py
def test_quick_doc_typo_routes_to_implementer_only():
    triage = simulate_triage("Fix typo in README.md")
    assert triage["lane"] == "quick"
    assert triage["complexity"] == "low"
    assert triage["risk"] == "low"
    assert triage["needsReviewer"] == False

def test_auth_signal_forces_guarded_or_strict():
    triage = simulate_triage("Add OAuth login to API")
    assert triage["risk"] == "high"  # Must be high due to touchesAuth
    assert triage["lane"] in ["guarded", "strict"]
```

While this cannot perfectly simulate LLM behavior, it validates triage schema conformance.

---

### P2 Recommendations

#### R7: Batch Processing Pattern

Learn from ECC's `accumulator + stop:batch` pattern:

```
When implementer edits multiple files:
  → post:edit records each path to a list
  → stop: runs format + typecheck + lint ONCE for all accumulated files

Instead of running verification after EACH edit
```

Saves 70%+ verification overhead for multi-file tasks.

#### R8: WORKING-CONTEXT.md

Add a living document at project root:

```markdown
# Working Context

## Current State
- Version: 1.4.0
- Skills: 11 dtt-* method skills
- Agents: 4 (leader, analyzer, implementer, reviewer)
- Platforms: OpenCode (native), Codex (skills only)

## Active Constraints
- No Claude Code plugin (no persistent registration mechanism)
- No Cursor support (bootstrap not validated)
- All dtt-* skills are leader-only except debugging and TDD

## Roadmap
- [ ] P0: Hook system implementation
- [ ] P1: Session persistence
- [ ] P1: Verification hook-ization

## Execution Log
<!-- Timestamped entries of significant changes -->
```

#### R9: Token Budget Awareness

Add to leader's lane protocols:

```markdown
## Token Budget Rules
- quick lane: should complete within <20% context window
- standard lane: trigger /compact when context >80% used
- strict lane: recommend /compact between each phase
- When estimatedFiles > 5 and context >60% used, suggest batching
```

#### R10: Domain Skills (Selective)

Expand beyond 11 method skills, but **resist ECC's 181-skill bloat**:

Priority domain skills for your project:
1. `dtt-security-review` — Security checklist for ProjectCloud backend
2. `dtt-migration-safety` — DB migration safety (touchesDbSchema is high-risk)
3. `dtt-api-contract` — API change regression checks (touchesPublicApi)

---

## Part 4: Architecture Comparison

| Dimension | ECC Approach | do-the-thing Approach | Recommendation |
|-----------|-------------|----------------------|----------------|
| Workflow control | Loose multi-agent | **Strict single-entry lane routing** | Keep yours (safer) |
| Automation | Hook deterministic | LLM instruction only | **Learn ECC** (add Hooks) |
| Learning | Instinct confidence system | None | Optional (do Hooks first) |
| Model routing | Static agent.yaml | **Dynamic Python detection** | Keep yours (more flexible) |
| Security | Multi-layer depth | Rules + sensitive signals | **Learn ECC** (add Hooks) |
| Anti-bloat | 181 skills, growing pain | **11 skills, disciplined** | Keep yours (quality > quantity) |
| Eval | pass@k/pass^k benchmarks | Manual case + rubric | Combine both (add regression) |
| Cross-platform | 4+ native | 2 + honest deferral | Keep yours (broken > deferred) |

---

## Part 5: Implementation Roadmap

```
Phase 1: Hook Infrastructure (Near-term)
  ├── Implement hooks.json schema
  ├── Add 5 core hooks (R1)
  ├── Add profile runtime control (R2)
  └── Add audit logging (R5)

Phase 2: Session & Verification (Mid-term)
  ├── Session persistence (R3)
  ├── Verification hook-ization (R4)
  └── Automated eval regression (R6)

Phase 3: Learning & Extension (Long-term)
  ├── Observation system (Hook-based tool capture)
  ├── Token budget awareness (R9)
  └── Domain skills expansion (R10, selective)
```

---

## Conclusion

do-the-thing's **workflow theory is superior** to ECC's loose multi-agent approach — single-entry routing with lane+tier classification is safer and more predictable. The gap is in **execution infrastructure**:

| ECC's Advantage | What to Borrow |
|-----------------|----------------|
| 30+ deterministic Hooks | Add Hook system (R1) — this is the #1 gap |
| Instinct learning | Do after Hooks are stable |
| Batch verification | Add accumulator pattern (R7) |
| Context persistence | Add session save/load (R3) |
| Multi-layer security | Add security Hooks (R1) |

**Do NOT copy**:
- ECC's 181-skill bloat (your anti-bloat philosophy is correct)
- Its loose agent orchestration (your strict lane routing is better)
- Its fragmented multi-platform surface (your honest deferrals are better than broken support)

The synthesis: **Keep your rigorous lane+tier routing, add ECC's deterministic Hook automation layer, and your system becomes both safer and more reliable than either project alone.**

---

*Analysis completed. No files were modified — this is a research-only task.*
