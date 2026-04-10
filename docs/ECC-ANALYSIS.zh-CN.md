# 深度分析：Everything Claude Code vs do-the-thing

**日期**: 2026-04-10
**参考项目**: [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code)
**被分析项目**: do-the-thing（本仓库）

---

## 执行摘要

do-the-thing 在**工作流理论**上优于 Everything Claude Code（ECC）（单入口 Lane+Tier 路由 + 严格安全默认值），但在**执行基础设施**上与 ECC 存在显著差距（无 Hooks、无持久化、无可观测性）。建议优先引入 Hook 系统——这将使你的系统从"希望 LLM 遵守规则"跨越到"确保执行落地"。

---

## 第一部分：Everything Claude Code — 核心精华

### 1.1 项目规模

| 指标 | 数值 |
|------|------|
| Stars | 149K+ |
| Forks | 23.1K |
| 提交数 | 1,268 |
| Agent 数量 | 47 |
| Skill 数量 | 181 |
| Command 数量 | 79 |
| MCP 配置 | 14 |
| 内部测试 | 1,700+ |
| 获奖 | Anthropic 黑客松冠军 |

### 1.2 核心架构（六子系统）

```
everything-claude-code/
├── agents/*.md        # 专业子 agent 定义（YAML frontmatter）
├── skills/            # 规范工作流定义（主要表面）
├── commands/          # 遗留 slash 入口垫片（正在迁移到 skills/）
├── hooks/             # 事件驱动自动化（PreToolUse、PostToolUse 等）
├── rules/             # 始终遵循的指南（common/ + per-language/）
└── mcp-configs/       # 外部服务集成
```

**五项基本原则（SOUL.md）**：
1. **Agent-First** — 尽早将任务路由到正确的专家
2. **Test-Driven** — 在信任实现之前先写/刷新测试
3. **Security-First** — 验证输入、保护密钥、保持安全默认值
4. **Immutability** — 偏好显式状态转换而非变更
5. **Plan Before Execute** — 复杂变更分阶段审慎进行

### 1.3 Hook 系统 — 确定性自动化

ECC 最成熟的子系统。六种事件类型，30+ 个 hooks：

| 事件 | 数量 | 可阻塞？ |
|------|------|----------|
| `PreToolUse` | 11 | 是（exit 2） |
| `PostToolUse` | 10 | 否 |
| `PostToolUseFailure` | 1 | 否 |
| `Stop` | 6 | 否 |
| `SessionStart` | 1 | 否 |
| `SessionEnd` | 1 | 否 |
| `PreCompact` | 1 | 否 |

**关键洞察**：Hook **100% 确定性触发**。Skill 大约 50-80% 概率性触发。这就是 ECC v2 将观察机制从 Skill 迁移到 Hook 的核心原因。

#### 必须实现的 5 个核心 Hook

| Hook ID | 匹配器 | 用途 |
|---------|--------|------|
| `pre:bash:block-no-verify` | Bash | 阻止 `git commit --no-verify` |
| `pre:bash:commit-quality` | Bash | 提交前检测密钥、console.log |
| `pre:config-protection` | Write/Edit | **阻止 AI 削弱 lint/格式化配置** |
| `post:edit:accumulator` | Edit/Write | 收集编辑路径以供批量处理 |
| `stop:format-typecheck` | * | 在 Stop 时统一运行格式化和类型检查 |

`pre:config-protection` hook 解决了一个关键的 AI 失败模式：**AI 不是修复代码，而是通过禁用规则来"修复" lint 错误**。

### 1.4 Instinct-Based 持续学习系统（v2.1）

```
会话活动 → Hook 捕获所有工具使用（100% 可靠）
  → observations.jsonl（项目级）
  → 后台 agent 检测模式（Haiku — 便宜）
  → 用置信度评分创建/更新 instincts
  → /evolve 将 instincts 聚类为 skills/commands/agents
  → /promote 在 2+ 项目中见过的模式提升为全局
```

**Instinct 属性**：
- **原子化**：一个触发器，一个动作
- **置信度加权**：0.3（试探性）到 0.9（近确定性）
- **项目作用域**：React 模式留在 React 项目
- **证据驱动**：置信度随观察增加/随矛盾证据衰减

### 1.5 Token 优化

| 策略 | 实现方式 |
|------|----------|
| 模型路由 | Haiku=探索/文档，Sonnet=90% 编码，Opus=安全/架构 |
| MCP 纪律 | 配置 20-30 个，激活 <10 个，<80 工具 |
| MCP→CLI 转换 | 用 CLI 封装替代常驻 MCP |
| 批量处理 | `accumulator` + `stop:format-typecheck` 模式 |
| Hook 异步化 | 学习/构建分析/质量检查设为 `async: true` |
| 上下文预算 | 大型重构避免使用最后 20% 上下文窗口 |

### 1.6 Profile 化运行时控制

```bash
export ECC_HOOK_PROFILE=standard  # minimal | standard | strict
export ECC_DISABLED_HOOKS="pre:bash:tmux-reminder,post:edit:typecheck"
```

Hook 在 `hooks.json` 中声明 profile：`"standard,strict"` 表示在 standard 和 strict 模式下运行，不在 minimal 模式。

### 1.7 Verification Loop（六阶段验证管道）

```
阶段 1: Build        → npm run build
阶段 2: Type Check   → tsc --noEmit / pyright
阶段 3: Lint         → npm run lint / ruff check
阶段 4: Tests        → npm test --coverage（最低 80%）
阶段 5: Security     → grep secrets, console.log
阶段 6: Diff Review  → git diff --stat
```

输出：结构化 PASS/FAIL 报告，READY/NOT READY for PR。

### 1.8 安全模型（纵深防御）

| 层次 | 机制 |
|------|------|
| Rules 层 | 始终加载 security.md，无硬编码密钥 |
| PreToolUse Hooks | 阻止危险操作、提交质量门禁 |
| Agent 层 | `security-reviewer` agent（推荐：Opus） |
| Skills 层 | `security-scan`、`hipaa-compliance`、`security-review` |
| 供应链安全 | 禁止随意安装外部运行时，PR 需人工审计 |

### 1.9 跨平台策略

| 平台 | 支持级别 |
|------|----------|
| Claude Code | 原生插件，全套 hooks/agents/commands |
| OpenCode | `.opencode/dist/` 编译插件 |
| Codex | `scripts/sync-ecc-to-codex.sh`，配置合并 |
| Cursor | `after-file-edit.js` hook 接线 |
| Gemini | 已规划 |

---

## 第二部分：do-the-thing 现状评估

### 2.1 架构概览

```
do-the-thing/
├── AGENTS.md           # 仅 Agent 注册表（非工作流逻辑）
├── agents/            # 4 个 agents：leader, analyzer, implementer, reviewer
├── skills/            # 11 个 dtt-* 方法 skills
├── commands/          # 1 个 command：/providers
├── tools/             # 3 个 Python 工具（模型路由、配置、提供商策略）
├── tests/             # 6 个 Python 测试文件（49 个测试）
├── evals/             # 手动评估系统（14 个 case，评分标准）
├── install/           # Bash + PowerShell 安装器
├── docs/              # 双语文档（EN + zh-CN）
├── .opencode/         # OpenCode 原生插件
├── .codex/            # Codex skills 符号链接
├── .claude-plugin/    # 已推迟（无持久化注册机制）
└── .cursor-plugin/    # 已推迟（引导机制待验证）
```

### 2.2 Lane + Tier 路由系统

**四种 Lane**：

| Lane | 触发条件 | Agent 链路 |
|------|----------|------------|
| `quick` | complexity=low, risk=low, 无敏感信号 | 最小链路：仅 1 个角色（implementer/analyzer/reviewer） |
| `standard` | complexity=high, risk=low | analyzer → implementer → reviewer |
| `guarded` | risk=high（敏感信号） | analyzer (tier_mid) → implementer（受限）→ reviewer |
| `strict` | complexity+risk 双高 | tier_top 写计划 → 逐步执行 → tier_top 审查 |

**三个 Tier**：
- `tier_fast` → Haiku/mini/flash 模型
- `tier_mid` → Sonnet/pro 模型
- `tier_top` → Opus/pro/sonnet 模型（leader 始终 tier_top）

### 2.3 优势

| 领域 | 评价 |
|------|------|
| 工作流理论 | Lane+Tier 路由设计精良，解决了真实用户痛点 |
| 安全默认值 | 保守默认值、仅升级策略、敏感信号强制高风险 |
| 关注点分离 | 边界清晰：注册表 / 工作流逻辑 / skills / 工具 |
| 反膨胀哲学 | MAINTAINING.md 明确警告规则膨胀 |
| Eval 驱动开发 | 14 个手动 case + 5 维评分标准 + 风险不对称评分 |
| 安装系统 | 跨平台、幂等、有集成测试 |
| 提供商路由 | 动态检测、allowlist 控制、基于 tier 的模型选择 |

### 2.4 与 ECC 的差距

| 维度 | do-the-thing | ECC | 差距 |
|------|-------------|-----|------|
| Hook 系统 | ❌ 无 | ✅ 30+ hooks | 🔴 严重 |
| 确定性自动化 | ❌ 纯 LLM 指令 | ✅ 100% Hook 触发 | 🔴 严重 |
| 持续学习 | ❌ 无 | ✅ Instinct v2.1 | 🟡 重要 |
| 会话持久化 | ❌ 无 | ✅ 多层持久化 | 🟡 重要 |
| 安全自动化 | ⚠️ 仅 Rules | ✅ 多层纵深 | 🟡 重要 |
| 验证管道 | ⚠️ 仅指令 | ✅ Hook 驱动 6 阶段 | 🟡 重要 |
| Token 优化 | ⚠️ 有模型路由 | ✅ 全栈优化 | 🟡 重要 |
| 可观测性 | ❌ 无 | ⚠️ 成本追踪 + 审计 | 🟡 重要 |
| 测试 | 49 | 1,700+ | 🟡 重要 |
| 平台支持 | 2/4 已推迟 | 4/5+ 原生 | 🟢 可接受 |

---

## 第三部分：do-the-thing 改进建议

### 优先级矩阵

| 优先级 | 建议 | 影响 | 工作量 |
|--------|------|------|--------|
| **P0** | 引入 Hook 系统 | 弥补严重差距 | 高 |
| **P0** | Hook profile 运行时控制 | 提升灵活性 | 中 |
| **P1** | 会话持久化 | 提升上下文连续性 | 中 |
| **P1** | Verification Hook 化 | 确保终门有证据 | 中 |
| **P1** | 审计日志 | 提升可观测性 | 低 |
| **P1** | 自动化 Eval 回归 | 规模化质量保障 | 中 |
| **P2** | 批量处理模式 | 减少 Token 浪费 | 低 |
| **P2** | WORKING-CONTEXT.md | 项目级状态管理 | 低 |
| **P2** | Token 预算感知 | 提升首次成功率 | 低 |
| **P2** | 领域 Skills（安全、迁移） | 填补知识空白 | 中 |

---

### P0 建议

#### R1：引入 Hook 系统

**现状问题**：所有工作流执行完全依赖 LLM 遵循 Markdown 指令，没有确定性保证。

**建议结构**：
```
skills/dtt-hooks/
├── hooks.json           # Hook 注册表
└── scripts/
    pre-commit-quality.js      # 提交安全检查
    pre-config-protection.js   # 阻止削弱 lint 配置
    post-edit-accumulator.js   # 收集编辑路径
    stop-batch-verify.js       # Stop 时统一验证
    session-start-context.js   # 加载上次会话
    pre-compact-state-save.js  # 压缩前保存状态
```

**优先实现的 5 个 Hook**：
1. `pre:config-protection` — 解决 AI"禁用规则而非修复代码"的失败模式
2. `pre:bash:block-no-verify` — 阻止绕过 pre-commit hooks
3. `post:edit:accumulator` + `stop:batch-verify` — 批量验证节省 70%+ 开销
4. `session:start:context-load` — 恢复上次会话状态
5. `pre:compact:state-save` — 自动压缩前保存上下文

#### R2：Hook Profile 运行时控制

```bash
export DTT_HOOK_PROFILE=standard  # minimal | standard | strict
export DTT_DISABLED_HOOKS="pre:bash:tmux-reminder"
```

`hooks.json` 中的 Hook 声明所需 profile：
```json
{
  "id": "pre:config-protection",
  "profiles": ["standard", "strict"],
  "async": false
}
```

---

### P1 建议

#### R3：会话持久化

```
~/.config/opencode/do-the-thing/
└── sessions/
    └── <project-git-remote-hash>/
        ├── latest-context.json   # 上次会话状态
        ├── observations.jsonl   # 工具使用日志
        └── instincts/           # 未来：学习到的模式
```

Leader 行为：
- **SessionStart**：加载 `latest-context.json` → 恢复工作上下文
- **Stop**：将当前状态写入 `latest-context.json`
- **PreCompact**：保存压缩快照

#### R4：Verification Hook 化

当前 `dtt-verification-before-completion` 仅为指令。建议升级为 hook 驱动：

```javascript
// stop:verification-gate.js
// 在 leader 声明完成前自动运行：
// 1. 检查是否有未保存的编辑
// 2. 运行 lint（如果 package.json 有 lint 脚本）
// 3. 运行 tests（如果 package.json 有 test 脚本）
// 4. 验证 git diff 是否在 estimatedFiles 范围内
// 5. 输出结构化 PASS/FAIL 报告
```

#### R5：审计日志

```json
// post:audit-log.js 记录：
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

存储在 `~/.config/opencode/do-the-thing/audit/`。

#### R6：自动化 Eval 回归

将 14 个手动 eval case 转化为 pytest 测试：

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
    assert triage["risk"] == "high"  # touchesAuth 强制 high
    assert triage["lane"] in ["guarded", "strict"]
```

虽然无法完美模拟 LLM 行为，但可以验证 triage 输出 Schema 合规性。

---

### P2 建议

#### R7：批量处理模式

借鉴 ECC 的 `accumulator + stop:batch` 模式：

```
当 implementer 连续编辑多个文件时：
  → post:edit 将每个路径记录到列表
  → stop: 时统一运行 format + typecheck + lint（仅一次）

而不是每次编辑后都运行验证
```

节省多文件任务 70%+ 的验证开销。

#### R8：WORKING-CONTEXT.md

在项目根目录添加活文档：

```markdown
# Working Context

## 当前状态
- 版本：1.4.0
- Skills：11 个 dtt-* 方法 skills
- Agents：4 个（leader, analyzer, implementer, reviewer）
- 平台：OpenCode（原生），Codex（仅 skills）

## 活跃约束
- 无 Claude Code 插件（无持久化注册机制）
- 无 Cursor 支持（引导机制未验证）
- 所有 dtt-* skills 均为 leader 专属，调试和 TDD 除外

## 路线图
- [ ] P0：Hook 系统实现
- [ ] P1：会话持久化
- [ ] P1：Verification Hook 化

## 执行日志
<!-- 重大变更的时间戳条目 -->
```

#### R9：Token 预算感知

在 leader 的 lane 协议中添加：

```markdown
## Token 预算规则
- quick lane：应在 <20% 上下文窗口内完成
- standard lane：上下文使用 >80% 时触发 /compact
- strict lane：每个阶段之间建议 /compact
- 当 estimatedFiles > 5 且上下文 >60% 时，建议拆分为批次
```

#### R10：领域 Skills（选择性扩展）

在 11 个方法 skill 之外选择性扩展，**但不要追求 ECC 的 181 个规模**：

推荐优先扩展的领域 skills：
1. `dtt-security-review` — ProjectCloud 后端安全审查清单
2. `dtt-migration-safety` — 数据库迁移安全（touchesDbSchema 是高风险）
3. `dtt-api-contract` — API 变更回归检查（touchesPublicApi）

---

## 第四部分：架构对比总结

| 维度 | ECC 方式 | do-the-thing 方式 | 建议 |
|------|---------|------------------|------|
| 工作流控制 | 松散多 agent | **严格单入口 Lane 路由** | 保留你的（更安全） |
| 自动化 | Hook 确定性触发 | 纯 LLM 指令 | **学习 ECC**（添加 Hooks） |
| 学习机制 | Instinct 置信度系统 | 无 | 可选（先做 Hooks） |
| 模型路由 | 静态 agent.yaml | **动态 Python 检测** | 保留你的（更灵活） |
| 安全模型 | 多层纵深防御 | Rules + 敏感信号 | **学习 ECC**（添加 Hooks） |
| 反膨胀 | 181 skills，渐显压力 | **11 skills，纪律严明** | 保留你的（质量优于数量） |
| Eval | pass@k/pass^k 基准 | 手动 case + rubric | 两者结合（添加回归） |
| 跨平台 | 4+ 原生 | 2 + 诚实推迟 | 保留你的（推迟优于破损） |

---

## 第五部分：实施路线图

```
阶段 1：Hook 基础设施（近期）
  ├── 实现 hooks.json Schema
  ├── 添加 5 个核心 Hooks（R1）
  ├── 添加 Profile 运行时控制（R2）
  └── 添加审计日志（R5）

阶段 2：会话与验证（中期）
  ├── 会话持久化（R3）
  ├── Verification Hook 化（R4）
  └── 自动化 Eval 回归（R6）

阶段 3：学习与扩展（远期）
  ├── 观察系统（基于 Hook 的工具使用捕获）
  ├── Token 预算感知（R9）
  └── 领域 Skills 选择性扩展（R10）
```

---

## 结论

do-the-thing 的**工作流理论优于 ECC** 的松散多 agent 编排——单入口路由 + Lane+Tier 分类更安全、更可预测。差距在于**执行基础设施**：

| ECC 的优势 | 借鉴内容 |
|-----------|----------|
| 30+ 确定性 Hooks | 添加 Hook 系统（R1）—— 第一差距 |
| Instinct 学习 | 在 Hooks 稳定后再做 |
| 批量验证 | 添加 accumulator 模式（R7） |
| 上下文持久化 | 添加会话保存/加载（R3） |
| 多层安全 | 添加安全 Hooks（R1） |

**不要复制**：
- ECC 的 181 skills 膨胀（你的反膨胀哲学是正确的）
- 其松散的 agent 编排（你的严格 Lane 路由更好）
- 其碎片化的多平台表面（你诚实的推迟比破损支持更好）

**综合建议**：**保留你严谨的 Lane+Tier 路由，添加 ECC 的确定性 Hook 自动化层，你的系统将比两个项目中的任何一个都更安全、更可靠。**

---

*分析完成。未修改任何文件——这是一项纯研究任务。*
