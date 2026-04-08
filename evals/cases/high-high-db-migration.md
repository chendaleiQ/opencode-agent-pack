# Case: high-high-db-migration

## 任务描述
新增订单状态字段并执行历史数据迁移脚本，需兼容旧数据读取。

## 背景
- 涉及 schema 变更 + migration
- 涉及多步骤发布与回滚策略
- 风险与复杂度均高

## 预期 triage
- taskType: `feature`
- complexity: `high`
- risk: `high`
- touchesAuth: `false`
- touchesDbSchema: `true`
- touchesPublicApi: `false`
- touchesDestructiveAction: `true`
- estimatedFiles: `8`
- lane: `strict`
- analysisTier: `tier_top`
- executorTier: `tier_mid`
- reviewTier: `tier_top`
- finalApprovalTier: `tier_top`

## 为什么这样判断
db schema 与 destructive 同时命中；必须 strict，且需要强边界和严格验证。

## 错分风险点
误降级会造成数据损坏、迁移失败、线上不可逆问题。

## 人工检查要点
- strict 的 plan/边界/禁止事项是否齐全
- reviewer 是否保留未解决高风险
- 若 reviewer 不放行，是否阻止结束
