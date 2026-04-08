# Case: high-low-large-refactor

## 任务描述
将重复的日志格式化逻辑从 12 个文件抽到共享工具模块，保持对外行为不变。

## 背景
- 涉及多文件重构
- 不改接口契约、不改鉴权、不改数据库
- 风险相对可控，但复杂度高

## 预期 triage
- taskType: `refactor`
- complexity: `high`
- risk: `low`
- touchesAuth: `false`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `12`
- lane: `standard`
- analysisTier: `tier_mid`
- executorTier: `tier_mid`
- reviewTier: `tier_mid`
- finalApprovalTier: `tier_top`

## 为什么这样判断
改动范围大、耦合高，complexity 高；但不触发敏感项，risk 可低。

## 错分风险点
若误进 quick 会缺少 plan 与充分 review，容易引入回归。

## 人工检查要点
- standard 是否给出简短 plan
- review 是否覆盖多文件一致性
- 是否出现范围扩张并触发升级
