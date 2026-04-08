# Case: low-low-superpowers-subagent-skill-loop

## 任务描述
修正一个文档错字（单文件），运行环境同时启用了外部技能系统（例如 superpowers）。

## 背景
- 任务本身是 low-low quick
- 环境有流程型外部技能，可能触发“先用技能”默认策略
- 风险点是 delegated subagent 被拉去重跑流程技能

## 预期 triage
- taskType: `refactor`
- complexity: `low`
- risk: `low`
- touchesAuth: `false`
- touchesDbSchema: `false`
- touchesPublicApi: `false`
- touchesDestructiveAction: `false`
- estimatedFiles: `1`
- lane: `quick`
- delegate: `true`
- needsReviewer: `false`
- analysisTier: `tier_fast`
- executorTier: `tier_fast`
- finalApprovalTier: `tier_top`

## 预期行为
- 仅 leader 运行 `change-triage`
- quick 路径只调度最小必要角色（实现类仅 implementer）
- delegated subagent 不重跑 triage、不拉起全流程技能链
- 若 handoff 不清晰，subagent 返回升级请求而不是扩张流程

## 错分风险点
若 subagent 因外部默认策略重跑工作流，简单任务会被放大为高成本流程，且可能打乱 lane/tier 边界。

## 人工检查要点
- 是否出现 subagent 侧 triage/全流程技能回流
- 是否仍维持 quick 最小路径
- leader 是否保持唯一收口与最终批准
