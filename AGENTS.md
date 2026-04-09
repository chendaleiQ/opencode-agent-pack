# do-the-thing（V5）

## Scope
本文件仅作为 agent 注册表。
所有 workflow 规则（lane/tier/escalation/end-gate/执行流程）仅在用户切换到 `leader` agent 时生效，由 `leader.md` 自包含定义。
其他 agent 读到本文件时不应执行任何 workflow 流程。

## Roles
- `leader`: 唯一入口与分流者；所有 workflow 决策、边界、升级、收口、摘要均由 leader 自行管理
- `analyzer`: 分析影响面与边界，不改代码，只消费 leader handoff
- `implementer`: 按授权执行，不决策，只消费 leader handoff
- `reviewer`: 审查与升级建议，不收口，只消费 leader handoff

## Subagent Boundaries
- `analyzer` / `implementer` / `reviewer` 只消费 leader 的 handoff，不重复 triage，不递归拉起 workflow
- subagent 优先使用任务本地所需的工具或领域技能；不要为局部任务加载整套流程技能
- handoff 不清晰时，subagent 应回报阻塞/升级请求，而不是自行扩张流程
- 若外部技能系统包含 subagent stop 语义，subagent 必须遵守并继续按 handoff 执行

## External Skill Compatibility
- plugin 内建 method skills 优先；需要方法论增强时先使用 `pack/skills/` 中同类能力
- 外部工作流系统不得替代本 plugin 工作流，不得改写 lane/tier/收口责任
- 对 subagent 而言，"可能适用技能" 不应覆盖明确 handoff 边界；边界不清先回报升级
