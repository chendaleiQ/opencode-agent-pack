# Spec：修复 `needsPlan=true` 普通文本绕过 spec / plan 审批停点

## 背景

当前 `needsPlan=true` 的契约要求：

1. 先输出并落盘 spec。
2. 停下等待用户批准 spec。
3. 再输出并落盘 plan。
4. 停下等待用户批准 plan。
5. plan 批准后才进入 analyze / implement / review / closure。

但实际 runtime guard 主要拦截 `tool.execute.before` 和 `command.execute.before`。如果 assistant 不调用工具，只是在普通回复文本里继续输出 plan、分析、实现说明或结论，当前 runtime 不会阻断或改写这段文本。因此用户会看到“没有批准也直接走完流程”。

已通过最小复现确认：在 planning gate 仍处于 `spec` 阶段时，assistant 可以输出类似 `## Plan ...` 的普通文本，输出不会被改写，状态仍保持 `blockedStage=spec`。

## 目标

1. 让 `needsPlan=true` 的 spec / plan 审批停点对普通 assistant 文本也生效，而不只是对工具和命令生效。
2. 在 spec 阶段：允许输出 spec 和等待批准提示；阻止或改写提前输出 plan / analyze / implement / review / closure 的普通文本。
3. 在 plan 阶段：允许输出 plan 和等待批准提示；阻止或改写提前进入 analyze / implement / review / closure 的普通文本。
4. 保持现有工具级 planning gate：未批准前仍不得调用非允许工具。
5. 补回归测试，覆盖普通文本绕过路径。

## 非目标

- 不重写整个 workflow state machine。
- 不改变 `dtt-change-triage` schema。
- 不让 runtime 自动生成完整 spec / plan 文档；文档生成仍由 leader / skill 执行。
- 不放宽实现型工具限制。
- 不在本修复中处理所有自然语言 approval 变体；可以作为后续小修，但本次主目标是文本输出绕过。

## 设计约束

- 修复应尽量小：优先在 `experimental.text.complete` 增加 planning gate 输出检查，而不是改动多层架构。
- 输出检查要避免误伤合法 spec / plan 内容：
  - spec 阶段允许 spec 内容和“请批准 spec”的停点提示。
  - plan 阶段允许 plan 内容和“请批准 plan”的停点提示。
- 如果文本明显越过当前 gate，应改写为明确停点消息，而不是静默失败。
- close gate 仍保持独立；不要把普通 planning gate rewrite 与 closure rewrite 混在一起导致关闭证据逻辑回退。

## 推荐方案

在 `.opencode/plugins/runtime/hook_runtime.js` 的 `experimental.text.complete` 中增加 planning-output guard：

1. 在解析 triage / artifacts 后读取当前 state。
2. 如果 `planningGate.blockedStage === 'spec'`：
   - 允许 spec 产出或等待批准提示。
   - 如果文本看起来在生成 plan、执行步骤、分析/实现/评审、或总结完成，则改写为“当前仍需 spec 审批，不能继续到 plan / execution”。
3. 如果 `planningGate.blockedStage === 'plan'`：
   - 允许 plan 产出或等待批准提示。
   - 如果文本看起来在进入 analyze / implement / review / closure，则改写为“当前仍需 plan 审批，不能继续执行”。
4. 增加测试覆盖：
   - spec 阶段普通文本 plan 被改写；
   - spec 阶段普通文本 analyze / implement 被改写；
   - plan 阶段普通文本 execution 被改写；
   - 合法 spec / plan 文本不被误改写；
   - 现有 tool-level planning gate 测试继续通过。

## 可选方案与取舍

### 方案 A：只强化 prompt / skill 文档

- 优点：改动最小。
- 缺点：不能解决用户观察到的绕过；弱模型仍可能继续输出普通文本。
- 结论：不推荐。

### 方案 B：在 `experimental.text.complete` 增加输出改写 guard

- 优点：最小 runtime 修复，直接覆盖普通文本绕过。
- 缺点：需要设计启发式检测，存在误伤风险。
- 结论：推荐。

### 方案 C：引入更完整的 planning output state machine

- 优点：长期更严格。
- 缺点：改动大，容易引入回归。
- 结论：不作为本次最小修复。

## 验收标准

1. `needsPlan=true` 且 spec 未批准时，普通 assistant 文本不能直接输出 plan 并继续流程。
2. `needsPlan=true` 且 spec 未批准时，普通 assistant 文本不能进入 analyze / implement / review / closure。
3. spec 批准但 plan 未批准时，普通 assistant 文本不能进入 analyze / implement / review / closure。
4. 合法 spec 输出、合法 plan 输出和等待用户批准提示不被误改写。
5. 现有工具级 planning gate 行为不回退。
6. 新增或更新测试覆盖普通文本绕过。

## 执行边界

- spec 未批准前，不写 plan，不修改 runtime 或测试。
- plan 未批准前，不实现修复。
- 不提交 git commit，除非用户明确要求。

## 当前停点

本 spec 等待用户确认。确认后才能写 plan；plan 再确认后才开始修改代码。
