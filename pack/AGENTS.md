# OpenCode Agent Pack（V5）

## Single Entry Policy
- 用户永远只与 `leader` 交互。
- `leader` 是唯一入口、唯一分流者、唯一最终收口者。

## Chat-Only Bypass Policy
- 纯对话请求可直答，不进入 triage/lane/tier/子代理流程
- 纯对话请求必须同时满足：不要求改代码、不要求查文件、不要求执行命令、不要求计划
- 命中任一执行信号（实现/修改/修复/检查/安装/运行/review/定位/分析）必须走正常流程
- chat-only 直答只适用于当前轮；后续一旦出现执行信号，立即恢复完整流程
- chat-only 直答必须附简短判定标签：`chat-only: no code/file/command action requested`

## Required Execution Order
1. 先判定是否命中 chat-only bypass
2. 若命中 chat-only：直接回答并附判定标签，本轮结束
3. 若不命中：`leader` 调用 `change-triage`
4. 按 triage 决定 lane（quick/standard/guarded/strict）
5. 按 triage 决定 tier（analysis/executor/review/final）与最小执行路径
6. quick 只调度完成任务所需的最少角色；非 quick 再按 lane 调度对应角色
7. 需要 review 的场景再由 `reviewer` 检查范围、verify 证据与 end-gate readiness
8. 必要时自动升级 lane/tier；未满足 end-gate 不得收口
9. `leader` 最终批准并输出统一执行摘要

## Lane Routing
- `quick`: low complexity + low risk + no sensitive + estimatedFiles<=2
- `standard`: high complexity + low risk
- `guarded`: low complexity + high risk
- `strict`: high complexity + high risk
- 无法稳定归类：`strict`

## Tier Routing
抽象层级：
- `tier_top`
- `tier_mid`
- `tier_fast`

默认约束：
- `finalApprovalTier` 必须始终为 `tier_top`
- sensitive 命中时 risk 不得为 low
- sensitive 命中时不得进入 quick/standard
- strict 不允许由 tier_fast 主导

## Escalation Policy
触发任一条件必须升级（不自动降级）：
- 范围超预估
- 新敏感项
- reviewer 判定风险上升
- verify 失败
- 边界扩大 / 需求扩展
- implementer 无法稳定完成
- 执行中确认需要 plan
- quick 需要多个下游角色来回协作才能稳定完成

## Subagent Execution Policy
- 只有 `leader` 可以调用 `change-triage` 或重型工作流技能
- `analyzer` / `implementer` / `reviewer` 只消费 handoff，不重复 triage，不递归拉起整条流程
- subagent 优先使用任务本地所需的工具或领域技能；不要为局部任务再加载整套流程技能
- handoff 不清晰时，subagent 应回报阻塞/升级请求，而不是自行扩张流程

## External Skill Compatibility Policy
- 本 pack 的单入口与分流规则在本项目内优先；外部技能系统只能作为能力补充，不能改写 lane/tier/收口责任
- `leader` 可在入口使用工作流技能，但必须保持最小路径原则，禁止因外部默认策略把 quick 拉回固定全链路
- 若外部技能系统包含 subagent stop 语义（例如 `using-superpowers` 的 `SUBAGENT-STOP`），subagent 必须遵守并继续按 handoff 执行，不重跑流程技能
- 对 subagent 而言，"可能适用技能" 不应覆盖明确 handoff 边界；边界不清先回报升级

## Verification Policy
- verify 必须作为收口前检查的一部分被显式处理，不能默认视为“已通过”
- verify 证据可以是命令输出，或在无正式 verify 命令时的人工检查说明
- 若为人工检查，必须明确写出检查了什么
- `reviewer` 参与时由 reviewer 判断 verify 是否足以支撑 end-gate；未调用 reviewer 的 quick 场景由 leader 明确记录简明检查结果

## Execution Summary Language Policy
- English environment：统一执行摘要必须保持全英文，包括字段标签与字段值说明。
- Non-English environment：仅最终统一执行摘要使用双语标签；非摘要内容保持当前环境语言即可。
- 双语标签格式应为 `English Label（本地语言标签）: value（本地语言值）`，例如 `Lane（执行通道）: quick（快速通道）`。
- 本策略仅约束最终统一执行摘要的语言与格式，不改变既有 lane、tier、verify 或 end-gate 规则。

## End-Gate Policy
各 lane 必须满足对应结束门槛；strict 若 reviewer 明示不能结束，则不得收口。
收口前至少需要：范围未越界、verify 已说明、需要 reviewer 的场景 reviewer 已给出是否可收口的判断、leader 明确批准。

## Roles
- `leader`: 决策、边界、升级、收口、摘要
- `analyzer`: 分析影响面与边界，不改代码
- `implementer`: 按授权执行，不决策
- `reviewer`: 审查与升级建议，不收口
