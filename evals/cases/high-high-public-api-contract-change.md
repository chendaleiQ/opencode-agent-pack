# Case: high-high-public-api-contract-change

## 任务描述
将公开 REST 接口响应字段 `user_name` 改为 `name`，并移除旧字段。

## 背景
- 对外 API 契约变更
- 可能影响外部客户端
- 涉及版本兼容策略与迁移窗口

## 预期 triage
- taskType: `feature`
- complexity: `high`
- risk: `high`
- touchesAuth: `false`
- touchesDbSchema: `false`
- touchesPublicApi: `true`
- touchesDestructiveAction: `false`
- estimatedFiles: `6`
- lane: `strict`
- analysisTier: `tier_mid`
- executorTier: `tier_mid`
- reviewTier: `tier_top`
- finalApprovalTier: `tier_top`

## 为什么这样判断
public API 变化属于敏感高风险；且涉及兼容策略，复杂度高。

## 错分风险点
误判低风险会导致客户端大面积兼容性故障。

## 人工检查要点
- 是否识别 touchesPublicApi=true
- 是否避免 quick/standard
- review 是否覆盖兼容与回退说明
