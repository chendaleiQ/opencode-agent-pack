# Spec：`needsPlan` 硬门禁与文档结构收敛

## 背景

当前 DTT 在 `needsPlan=true` 时，会走 `dtt-brainstorming -> dtt-writing-plans`，但实际行为更接近“先做简短澄清，再直接写 plan”，而不是先产出可审阅的 spec。这样会带来几个问题：

- 用户没有在执行前审阅 spec 的停点
- plan 也没有独立审阅停点
- spec / plan 不会稳定落盘
- 输出语言没有被明确要求跟随当前对话语言
- `docs/project`、`docs/pack-methods` 这类目录命名不清晰，且不利于跨项目复用

## 目标

1. 当 triage 判断 `needsPlan=true` 时，强制进入 spec -> plan 的硬门禁流程
2. spec 和 plan 都必须同时输出到聊天框与文件
3. spec 审批前不得进入 plan；plan 审批前不得进入 analyze / execute / review
4. 所有人类可读输出与生成文档都跟随当前对话语言
5. 将 DTT 生成产物统一收敛到 `docs/dtt/`
6. 将当前 DTT 项目的长期说明文档收敛到 `docs/` 根目录，并清理不再需要的文档

## 非目标

- 不修改 `dtt-change-triage` 的 JSON 输出 schema
- 不要求所有 quick 任务都写 spec / plan
- 不自动翻译已经生成完成的旧文档，除非用户明确要求

## 核心决策

### 1. 硬门禁触发条件

- 触发条件以 `needsPlan=true` 为准，不单独以 `complexity=high` 为准
- 只要命中 `needsPlan=true`，就没有跳过 spec / plan 的正常通道
- 如果任务起初未命中 `needsPlan=true`，但在分析、执行或评审阶段发现实际上需要 plan，则必须：
  - 停止继续执行
  - 升级到需要 plan 的流程
  - 补齐 spec、plan 与 todo 后再继续

### 2. 必经流程

当 `needsPlan=true` 时，流程固定为：

1. triage
2. 产出 spec
3. 将 spec 写入 `docs/dtt/specs/...`
4. 在聊天框输出 spec 摘要/正文
5. 停下等待用户确认 spec
6. 用户确认后，产出 plan
7. 将 plan 写入 `docs/dtt/plans/...`
8. 在聊天框输出 plan 摘要/正文
9. 停下等待用户确认 plan
10. 用户确认后，更新 opencode todo
11. 再进入 analyze / execute / review

### 3. 语言规则

- 所有人类可读输出默认跟随当前对话语言
- spec 与 plan 文件内容也必须跟随当前对话语言
- 如果用户当前用中文交流，则聊天输出、spec、plan 都使用中文
- 如果用户当前用英文交流，则聊天输出、spec、plan 都使用英文
- 如果对话语言中途切换，则后续新输出按当前语言执行；已落盘文件不自动回写翻译

### 4. DTT 产物目录

- spec 固定放在：`docs/dtt/specs/`
- plan 固定放在：`docs/dtt/plans/`
- 文件命名采用日期 + 语义化 slug：`YYYY-MM-DD-<slug>.md`
- `docs/dtt/` 仅承载 DTT 生成或 DTT 管理的任务文档产物

### 5. DTT 项目长期文档目录

当前 DTT 项目的长期说明文档直接放在 `docs/` 根目录，不再使用 `docs/project/` 或 `docs/pack-methods/`。

目标结构：

- `docs/WORKFLOW.md`
- `docs/ARCHITECTURE.md`
- `docs/RELEASE.md`
- `docs/MAINTAINING.md`
- `docs/README.zh-CN.md`
- `docs/dtt/specs/...`
- `docs/dtt/plans/...`

### 6. 文档迁移与清理

- `docs/project/WORKFLOW.md` -> `docs/WORKFLOW.md`
- `docs/project/V2-ARCHITECTURE.md` -> `docs/ARCHITECTURE.md`
- `docs/project/RELEASE.md` -> `docs/RELEASE.md`
- `docs/project/MAINTAINING.md` -> `docs/MAINTAINING.md`
- `docs/project/README.zh-CN.md` -> `docs/README.zh-CN.md`
- `docs/project/ROUTER.md` 合并进 `docs/WORKFLOW.md`
- 删除 `docs/ECC-ANALYSIS.md`
- 删除 `docs/ECC-ANALYSIS.zh-CN.md`
- 删除 `docs/pack-methods/README.md`
- 清理迁移后变为空的旧目录

### 7. 审批语义

- spec 通过前，只允许继续 spec 修订，不允许进入 plan
- plan 通过前，不允许进入 analyze / execute / review
- plan 通过后，先更新 todo，再开始执行
- 该门禁是正常流程中的强约束，而不是建议

## 验收标准

满足以下条件时，本次变更视为完成：

1. `needsPlan=true` 的任务会先产出 spec，而不是直接进入 plan
2. spec 会同时出现在聊天框和 `docs/dtt/specs/`
3. 未获 spec 确认时，流程不能进入 plan
4. plan 会同时出现在聊天框和 `docs/dtt/plans/`
5. 未获 plan 确认时，流程不能进入 analyze / execute / review
6. plan 确认后，先更新 todo，再进入执行
7. 输出语言与当前对话语言一致
8. 旧的 `docs/project/` 与 `docs/pack-methods/` 命名不再作为主路径
9. `ROUTER.md` 被并入 `WORKFLOW.md`
10. ECC 分析文档和无实际价值的占位文档被清理

## 实施风险

- 需要同步更新 README、测试、文档链接与引用路径
- 需要避免只改文档名而未改工作流门禁逻辑
- 需要避免 spec / plan 只写入文件但未在聊天框显式展示
