# Case: low-low-investigation-log-trace

## 任务描述
排查“订单列表偶发超时”，先只输出调用链和可能瓶颈，不改业务逻辑。

## 背景
- investigation 类型
- 以读取日志、定位瓶颈为主
- 预计改动文件极少或不改代码

## 预期 triage
- taskType: `investigation`
- complexity: `low`
- risk: `low`
- touchesAuth: `false`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `1`
- lane: `quick`
- analysisTier: `tier_fast`
- executorTier: `tier_fast`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## 为什么这样判断
仅排查、不变更敏感逻辑，低风险低复杂度。

## 错分风险点
若被错误升级到 strict，属于效率损失；
若排查过程实际触及敏感变更需求，必须触发升级。

## 人工检查要点
- 是否保持 investigation 边界
- 若中途发现敏感变更需求，是否升级 lane/tier
