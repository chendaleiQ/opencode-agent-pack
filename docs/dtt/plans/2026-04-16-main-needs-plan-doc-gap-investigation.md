# Plan：调查 main 最新代码中 `needsPlan=true` 未稳定落盘 spec / plan 的原因

## 目标

基于已批准的 spec，完成一次只读、证据化调查，解释为什么在 main 最新代码中，`needsPlan=true` 仍然可能没有把 spec / plan 稳定落盘到 `docs/dtt/specs/` 与 `docs/dtt/plans/`。

本次 plan 的目标不是立即修复，而是先把问题归因清楚，再决定后续最小修复范围。

## 已批准 spec

- `docs/dtt/specs/2026-04-16-main-needs-plan-doc-gap-investigation.md`

## 架构摘要

当前行为要分四层看：

1. **方法/契约层**：`leader` 与 `dtt-*` skills 负责声明 `needsPlan=true` 时必须先写 spec、再等批准、再写 plan。
2. **runtime guard 层**：`.opencode/plugins/runtime/*` 负责阻断不合规动作、记录 planning artifact、识别审批并推进 planning gate 状态。
3. **安装态同步层**：插件初始化时会把仓库内 `agents/`、`skills/` 等同步到 `~/.config/opencode/`，因此需要确认用户实际运行的是不是同步后的最新规则。
4. **测试/eval 层**：测试可能覆盖了“明确写了批准”这种窄路径，但未覆盖真实用户自然表达，导致 main 看起来“有实现”，实际交互仍会卡住。

## 有序调查步骤

### Step 1：确认契约层是否已经要求 spec / plan 落盘与审批停点

读取并核对：

- `agents/leader.md`
- `skills/dtt-brainstorming/SKILL.md`
- `skills/dtt-writing-plans/SKILL.md`
- `docs/WORKFLOW.md`

要回答：

- `needsPlan=true` 是否已经被定义为 spec -> 批准 -> plan -> 批准 的硬流程。
- spec / plan 是否明确要求写入 `docs/dtt/specs/` 与 `docs/dtt/plans/`。
- 聊天展示与审批停点是否是显式契约，而不是隐含约定。

### Step 2：确认 runtime 的真实职责边界

读取并核对：

- `.opencode/plugins/runtime/evidence_gate.js`
- `.opencode/plugins/runtime/hook_runtime.js`
- `.opencode/plugins/runtime/state_store.js`
- `.opencode/plugins/runtime/paths.js`

要回答：

- runtime 是否会自动创建 spec / plan 文件，还是只允许并记录这些写入。
- planning gate 何时从 `spec` 推进到 `plan`。
- planning artifact 与 approval 是通过什么事件和什么文本模式识别的。
- 哪种用户批准表达会被识别，哪种不会被识别。

### Step 3：核对当前会话状态与安装态是否一致

读取并核对：

- `~/.config/opencode/agents/leader.md`
- `~/.config/opencode/skills/dtt-brainstorming/SKILL.md`
- `~/.config/opencode/skills/dtt-writing-plans/SKILL.md`
- 当前 session state：`~/.config/opencode/do-the-thing/sessions/.../latest.json`

要回答：

- 安装态规则是否与仓库 main 一致。
- 当前会话里 spec 是否已被记录为 artifact。
- 用户批准是否被写入 `planningGate.approvals`。
- 当前被卡在 spec 还是 plan。

### Step 4：核对测试和 eval 的覆盖缺口

读取并核对：

- `tests/test_opencode_plugin_runtime.py`
- `tests/test_workflow_state_store.py`
- `tests/test_pack_skills.py`
- `evals/cases/standard-needs-plan-approval-stop-points.md`

要回答：

- 测试是否只覆盖了“批准 / approved”这类窄表达。
- 是否缺少“可以 / 继续”等真实中文确认语的覆盖。
- eval 是否声明了正确行为，但没有对应自动化测试兜底。

### Step 5：输出归因结论与最小修复入口

最终产出应明确区分：

1. 哪些部分已经正确实现；
2. 哪些部分只是契约存在，但行为不够稳定；
3. 本次问题的主根因是否是 approval 文本识别过窄；
4. 若继续修复，最小改动文件集合是什么；
5. 需要补哪些回归测试。

## 预期结论格式

调查完成后，结论应至少包含：

- **现状**：main 已实现了哪些 gate / doc path / sync 行为。
- **主根因**：为什么用户感觉“没有落实到文档”。
- **次级因素**：测试、eval、交互表达等辅助原因。
- **建议修复点**：文件清单 + 最小变更方向。

## 验证方式

本次是只读调查，不运行实现型修改。

验证依据来自：

- 代码路径阅读
- 安装态文件对比
- 当前 session state 检查
- 现有测试断言阅读

如果进入后续修复阶段，再补充 pytest 级验证。

## 执行边界

- plan 未批准前，不修改 runtime、skills、agents、tests 或 evals。
- 本阶段只允许继续读文件和总结证据。
- 不提交 git commit。
- 不把“体验上没发生”直接等同于“完全没实现”，必须以代码和状态文件为准。

## 当前停点

本 plan 等待用户确认。确认后，才开始按以上步骤执行调查并给出最终归因结论。
