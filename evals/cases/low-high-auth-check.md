# Case: low-high-auth-check

## 任务描述
在现有接口里增加管理员权限检查，非管理员返回 403。

## 背景
- 改动点可能仅 1~2 个文件
- 逻辑改动不大，但直接触及鉴权路径
- 可能影响权限边界

## 预期 triage
- taskType: `feature`
- complexity: `low`
- risk: `high`
- touchesAuth: `true`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `2`
- lane: `guarded`
- analysisTier: `tier_mid`
- executorTier: `tier_mid`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## 为什么这样判断
虽然改动小，但 auth 是敏感项；风险必须高，不能走 quick/standard。

## 错分风险点
最严重错分是进入 quick，可能导致权限绕过或误封。

## 人工检查要点
- sensitive 是否命中 auth
- guarded 的边界限制是否由 tier_top 给出
- reviewer 是否重点检查越界与权限副作用
