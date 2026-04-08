# OpenCode Agent Pack（V5）

## Single Entry Policy
- 用户永远只与 `orchestrator` 交互。
- `orchestrator` 是唯一入口、唯一分流者、唯一最终收口者。

## Required Execution Order
1. `orchestrator` 先调用 `change-triage`
2. 按 triage 决定 lane（quick/standard/guarded/strict）
3. 按 triage 决定 tier（analysis/executor/review/final）
4. 调度 `analyzer` / `implementer` / `reviewer`
5. 必要时自动升级 lane/tier
6. `orchestrator` 输出最终收口与统一执行摘要

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

## End-Gate Policy
各 lane 必须满足对应结束门槛；strict 若 reviewer 明示不能结束，则不得收口。

## Roles
- `orchestrator`: 决策、边界、升级、收口、摘要
- `analyzer`: 分析影响面与边界，不改代码
- `implementer`: 按授权执行，不决策
- `reviewer`: 审查与升级建议，不收口
