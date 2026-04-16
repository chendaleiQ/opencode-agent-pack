# Plan：修复 `needsPlan=true` 普通文本绕过 spec / plan 审批停点

## 目标

在不重写整体 workflow 的前提下，修复当前 `needsPlan=true` 只拦工具/命令、不拦普通 assistant 文本继续推进的问题。

修复后应满足：

1. spec 未批准时，assistant 不能直接在普通文本里继续输出 plan、分析、实现、评审或完成总结。
2. plan 未批准时，assistant 不能直接在普通文本里继续输出 analyze / implement / review / closure 内容。
3. 合法的 spec 输出、plan 输出以及等待用户批准的提示仍然允许通过。
4. 现有工具级 planning gate 不回退。

## 已批准 spec

- `docs/dtt/specs/2026-04-16-needs-plan-output-gate-fix.md`

## 架构摘要

当前 planning gate 的强制面主要在：

- `tool.execute.before`
- `command.execute.before`

而 `experimental.text.complete` 目前主要负责：

- 记录 triage
- 记录 planning artifacts / review / verification evidence
- 在 close attempt 时做 rewrite

因此最小修复点应放在 `experimental.text.complete`：

- 读取当前 `planningGate.blockedStage`
- 判断当前 assistant 文本是否越过 gate
- 如越过，则改写为等待批准的停点消息

## 有序实现步骤

### Step 1：实现 planning-output guard

目标文件：

- `.opencode/plugins/runtime/hook_runtime.js`
- 如有必要：`.opencode/plugins/runtime/evidence_gate.js`

工作内容：

1. 在 `experimental.text.complete` 中加入普通文本 planning gate 检查。
2. 根据 `blockedStage` 区分：
   - `spec` 阶段允许 spec 输出与等待 spec 批准提示；
   - `plan` 阶段允许 plan 输出与等待 plan 批准提示。
3. 如果文本明显越过当前阶段：
   - `spec` 阶段输出了 plan / analyze / implement / review / close 内容；
   - `plan` 阶段输出了 analyze / implement / review / close 内容；
   则把输出改写为明确的等待批准提示。
4. 保持现有 close gate rewrite 与 planning gate rewrite 的职责分离，避免互相覆盖。

### Step 2：定义最小检测规则

目标文件：

- `.opencode/plugins/runtime/evidence_gate.js`（如果抽 helper）
- 或者直接在 `hook_runtime.js` 内部实现小型检测函数

工作内容：

1. 为以下文本建立启发式检测：
   - plan 文本（如 `# Plan`、`## Plan`、`实施步骤`、`实现步骤`、ordered steps 等）
   - execution 文本（如 `analyze`、`implement`、`review`、`执行步骤`、`我将修改`、`我已经修复`、`完成` 等）
2. 同时保留 allow path：
   - spec 文本
   - plan 文本（仅在 plan 阶段）
   - 明确等待批准提示
3. 规则尽量小而可测，不做过度 NLP。

### Step 3：补运行时回归测试

目标文件：

- `tests/test_opencode_plugin_runtime.py`

新增测试至少覆盖：

1. `spec` 阶段普通文本输出 plan 会被改写。
2. `spec` 阶段普通文本输出 analyze / implement / review / completion 会被改写。
3. `plan` 阶段普通文本输出 execution / completion 会被改写。
4. 合法 spec 文本在 `spec` 阶段不被改写。
5. 合法 plan 文本在 `plan` 阶段不被改写。
6. 现有 tool-level planning gate 测试继续通过。

### Step 4：运行验证

优先验证命令：

- `pytest tests/test_opencode_plugin_runtime.py`

如果需要，再补充更小范围复现检查，确认：

1. 普通 assistant plan 文本在 `spec` 阶段被 rewrite。
2. 普通 assistant execution 文本在 `plan` 阶段被 rewrite。
3. 合法 spec / plan 文本未被误伤。

## 风险与控制

### 风险 1：误伤合法 spec / plan 输出

控制：

- 先定义 allow path，再定义 bypass path。
- 测试中显式覆盖合法 spec / plan 文本。

### 风险 2：planning gate rewrite 与 close gate rewrite 冲突

控制：

- 明确执行顺序；planning gate 应先阻断越权推进，close gate 继续负责 completion 形态。

### 风险 3：检测规则过宽导致正常对话被误拦

控制：

- 仅拦明显的 forward-progress 文本。
- 用最小关键词集，避免泛化过度。

## 验收标准

1. 复现你报告的问题时，assistant 不能再在未批准阶段直接把流程文本走完。
2. runtime 状态仍正确保持 `blockedStage=spec|plan`，且输出被改写为等待批准消息。
3. 合法 spec / plan 输出仍保留。
4. `pytest tests/test_opencode_plugin_runtime.py` 通过。

## 执行边界

- plan 未批准前，不修改代码。
- 不扩大到 approval 短语识别优化，除非实现中发现必须一起处理。
- 不提交 git commit，除非用户明确要求。

## 当前停点

本 plan 等待用户确认。确认后，才开始修改 runtime 和测试。
