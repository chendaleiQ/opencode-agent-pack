# Spec：调查 main 最新代码中 `needsPlan=true` 仍未稳定落盘 spec / plan 的原因

## 背景

用户反馈：已更新到 `main` 分支最新代码后，`needsPlan=true` 的任务仍然没有稳定把 spec 和 plan 落实到 `docs/dtt/specs/` 与 `docs/dtt/plans/` 文档中。

仓库中已经存在与该能力相关的历史 spec / plan，明确期望流程为：

1. `needsPlan=true` 后先产出 spec。
2. spec 写入 `docs/dtt/specs/` 并在聊天中展示。
3. spec 获得用户确认前不得进入 plan。
4. plan 写入 `docs/dtt/plans/` 并在聊天中展示。
5. plan 获得用户确认前不得进入 analyze / implement / review。

本次任务不是先假设修复方案，而是先解释“为什么 main 最新代码仍然没有表现出这个行为”。

## 目标

1. 对比当前 main 最新代码中的实际实现与上述期望流程。
2. 找出 `needsPlan=true` 未稳定落盘 spec / plan 的具体原因。
3. 区分问题属于以下哪一层：
   - leader / agent 规则没有强制执行；
   - `dtt-brainstorming` 或 `dtt-writing-plans` skill 文档定义不足；
   - runtime planning gate 阻止了规划文档写入；
   - runtime 只提示但没有自动生成 / 自动写文件；
   - 安装态文件与仓库源码不同步；
   - 测试或 eval 只覆盖了文档存在性，没有覆盖真实会话停点。
4. 给出证据化结论：引用相关文件和行为路径，而不是只给推测。
5. 如果确认需要代码或规则修复，再进入 plan 阶段制定最小修复方案。

## 非目标

- spec 未批准前，不修改 runtime、agent、skill 或测试实现。
- 不直接提交 git commit。
- 不把历史文档当作已经完成当前调查的证据；本次要核对当前 main 的真实状态。
- 不绕过当前 planning gate。

## 约束

- 当前对话语言为中文，调查结论、plan 与后续文档默认使用中文。
- 当前任务已被 triage 为 `standard` / `needsPlan=true`，因此必须先完成 spec 审批，再写 plan，再执行调查。
- 调查阶段应优先只读检查；只有在用户批准后，才根据 plan 进入代码或规则修改。

## 推荐调查方法

采用“契约 vs 实现 vs 安装态 vs 测试覆盖”的四段式调查：

1. **契约层**：读取 `agents/leader.md`、`skills/dtt-brainstorming/SKILL.md`、`skills/dtt-writing-plans/SKILL.md`，确认 `needsPlan=true` 的文档落盘和审批停点是否是硬约束。
2. **runtime 层**：读取 `.opencode/plugins/runtime/*` 中 planning gate 相关逻辑，确认它是否只是阻断执行，还是会记录 / 允许 / 要求 spec 与 plan 文件写入。
3. **安装态同步层**：比较仓库内源码与实际加载的 `.config/opencode` 安装态文件，确认用户当前会话是否使用了最新规则。
4. **测试覆盖层**：读取相关测试与 eval，确认是否存在能复现“真实会话必须落盘 spec/plan”的回归用例。

## 待验证假设

1. 最新 main 可能已经把“要求写 spec / plan”写进 skill 文档，但 runtime 仍只是给模型提示，并不会自动替模型创建文件。
2. planning gate 可能允许或阻止工具调用，但没有把“未写 spec / plan”变成可执行的强制状态迁移。
3. 当前会话实际加载的安装态 skill / agent 可能来自 `.config/opencode`，与仓库内 main 源码存在不同步。
4. 测试可能验证了文档文本规则，而没有覆盖端到端的真实 agent 会话行为。

## 验收标准

本次调查完成时，应能回答：

1. main 最新代码中，`needsPlan=true` 的 spec / plan 落盘责任具体落在哪一层。
2. 哪个文件或逻辑导致它没有稳定落盘。
3. 当前行为是“实现缺失”“安装态未同步”“runtime guard 阻断”“测试缺口”，还是多因素组合。
4. 后续若需要修复，应修改哪些文件，如何验证。

## 当前停点

本 spec 等待用户确认。确认后才能进入 plan 阶段；plan 再获确认后，才开始实际调查。
