# Plan：`needsPlan` 硬门禁与文档结构收敛

## 目标

在不修改 `dtt-change-triage` schema 的前提下，让 `needsPlan=true` 的任务改为强制走：

`triage -> spec -> 用户确认 -> plan -> 用户确认 -> todo -> analyze/execute/review`

同时完成文档目录收敛：

- DTT 生成产物进入 `docs/dtt/specs/` 与 `docs/dtt/plans/`
- 当前项目长期文档迁移到 `docs/` 根目录
- 删除 ECC 分析文档与 `pack-methods` 占位目录
- 将 `ROUTER.md` 并入 `WORKFLOW.md`

## 架构摘要

本次实现分成四层同步修改，避免只改提示词、不改运行时，或者只改目录、不改引用：

1. **方法层**：让 `dtt-brainstorming` 真正产出 spec，`dtt-writing-plans` 真正产出可审阅 plan
2. **leader 工作流层**：把 spec/plan 审批停点写成明确硬门禁，并补上“输出语言跟随当前对话语言”的全局规则
3. **runtime guard 层**：在已有 triage-before-execution 基础上，为 `needsPlan=true` 增加 planning gate 状态与阻断，降低弱模型绕过 spec/plan 的概率
4. **文档与测试层**：迁移路径、合并文档、删除废弃文档，并更新测试和 eval 断言

## 实施步骤

### Step 1：完成文档路径迁移设计与清单固化

目标：先把最终目录结构和迁移范围固定下来，避免后续边改边漂移。

涉及文件：

- `docs/dtt/specs/2026-04-15-needs-plan-hard-gate-and-doc-layout.md`（已完成）
- `docs/dtt/plans/2026-04-15-needs-plan-hard-gate-and-doc-layout.md`（当前文件）

产出：

- 确认最终目录为：
  - `docs/WORKFLOW.md`
  - `docs/ARCHITECTURE.md`
  - `docs/RELEASE.md`
  - `docs/MAINTAINING.md`
  - `docs/README.zh-CN.md`
  - `docs/dtt/specs/...`
  - `docs/dtt/plans/...`

### Step 2：迁移并精简长期文档

目标：先完成文档物理结构调整和链接收敛，减少后续逻辑改动时的路径混乱。

涉及文件：

- `docs/project/WORKFLOW.md` -> `docs/WORKFLOW.md`
- `docs/project/V2-ARCHITECTURE.md` -> `docs/ARCHITECTURE.md`
- `docs/project/RELEASE.md` -> `docs/RELEASE.md`
- `docs/project/MAINTAINING.md` -> `docs/MAINTAINING.md`
- `docs/project/README.zh-CN.md` -> `docs/README.zh-CN.md`
- `docs/project/ROUTER.md`（内容并入 `docs/WORKFLOW.md` 后删除）
- `docs/project/specs/2026-04-13-meta-status-rendering-design.md` -> `docs/dtt/specs/...`
- `docs/project/plans/2026-04-13-meta-status-rendering-implementation.md` -> `docs/dtt/plans/...`
- 删除：
  - `docs/ECC-ANALYSIS.md`
  - `docs/ECC-ANALYSIS.zh-CN.md`
  - `docs/pack-methods/README.md`

实现要点：

- `ROUTER.md` 中关于 `tools/subagent_model_router.py` 的说明合并到 `docs/WORKFLOW.md`
- `README.md` 与中文 README 的文档链接全部改到新路径
- 清理迁移后空目录和旧路径引用

### Step 3：把 spec/plan 产出契约写进方法层

目标：让 `dtt-brainstorming` 和 `dtt-writing-plans` 的定义本身就要求产出文件和停下审批，而不是只靠 leader 临时解释。

涉及文件：

- `skills/dtt-brainstorming/SKILL.md`
- `skills/dtt-writing-plans/SKILL.md`
- 如有需要，同步镜像到安装态技能目录对应文件

实现要点：

- `dtt-brainstorming` 改为：
  - 产出完整 spec，而不是“short design summary”
  - 指定 spec 路径为 `docs/dtt/specs/YYYY-MM-DD-<slug>.md`
  - 要求 spec 同时输出到聊天框与文件
  - 明确在 spec 后停下，等待用户确认
- `dtt-writing-plans` 改为：
  - 以“已批准 spec”为输入
  - 指定 plan 路径为 `docs/dtt/plans/YYYY-MM-DD-<slug>.md`
  - 要求 plan 同时输出到聊天框与文件
  - 明确在 plan 后停下，等待用户确认
- 两个 skill 都补上：
  - 输出语言跟随当前对话语言

### Step 4：把硬门禁写进 leader 工作流

目标：让 `leader` 明确知道 spec / plan 不是建议步骤，而是必须停下来的审批节点。

涉及文件：

- `agents/leader.md`
- `AGENTS.md`
- `docs/WORKFLOW.md`

实现要点：

- 将现有 `needsPlan=true -> dtt-brainstorming then dtt-writing-plans` 扩展为带审批停点的文字约束
- 在 standard / strict lane 中明确：
  - spec 未批准不得进入 plan
  - plan 未批准不得进入 analyze / execute / review
  - plan 批准后先更新 todo，再进入执行
- 在全局响应规则中增加：
  - 人类可读输出默认跟随当前对话语言
  - spec / plan 文档内容也跟随当前对话语言
- 保持 `leader` 对 lane/tier/closure 的唯一所有权不变

### Step 5：为 runtime guard 增加 planning gate

目标：不仅靠 prompt 约束，还要在运行时尽量阻止“needsPlan 任务直接开干”。

涉及文件：

- `.opencode/plugins/runtime/state_store.js`
- `.opencode/plugins/runtime/hook_runtime.js`
- `.opencode/plugins/runtime/evidence_gate.js`

实现要点：

- 在 state 中新增 planning 相关状态，例如：
  - spec 文档路径
  - spec 状态（missing / drafted / approved）
  - plan 文档路径
  - plan 状态（missing / drafted / approved）
- 在 `hook_runtime.js` 中扩展 pre-execution 阻断逻辑：
  - 对 `needsPlan=true` 的 leader 会话，如果 plan 尚未批准，则阻止进入实现型工具路径
  - 预批准阶段只允许为规划服务的动作（如读文件、写 spec/plan 文档、更新 todo、相关 skill 调用）
- 在 `chat.message` / `experimental.text.complete` 相关链路里记录：
  - spec 已产出
  - spec 已获用户确认
  - plan 已产出
  - plan 已获用户确认
- 在 runtime system guard 文案中加入 planning gate 提示，明确当前卡在 spec 还是 plan 审批

### Step 6：补齐与更新测试

目标：让路径迁移、spec/plan 门禁、语言规则至少在关键回归点上可验证。

涉及文件：

- `tests/test_pack_skills.py`
- `tests/test_release_process_docs.py`
- `tests/test_workflow_state_store.py`
- `tests/test_opencode_plugin_runtime.py`
- 视实现需要补充：
  - `tests/test_close_time_evidence_gate.py`
  - 新增 planning-gate 测试文件

实现要点：

- 更新所有 `docs/project/...`、`docs/pack-methods/...` 的断言路径
- 删除或改写“pack-methods 目录必须存在”的断言
- 增加对 planning state 的断言：
  - `needsPlan=true` 时进入 spec/plan 审批态
  - plan 未批准时实现型工具被阻断
  - 审批通过后才允许继续执行
- 保留原有 close gate 行为不回退

### Step 7：补充 eval / 文档一致性检查

目标：让新门禁不只存在于代码，也体现在评估样例与文档中。

涉及文件：

- `evals/cases/standard-feature-plan-and-batches.md`
- `evals/cases/standard-parallel-independent-slices.md`
- 视需要新增：一个专门覆盖 spec/plan 审批停点的 case
- `evals/rubric.md`
- `README.md`
- `docs/README.zh-CN.md`

实现要点：

- 更新 eval 预期：`needsPlan=true` 时不能直接进执行
- README 中解释新文档路径与 spec/plan 审批流程
- 中文 README 与英文 README 保持入口描述一致

## 验证检查点

### 检查点 A：文档结构与引用

- 不再存在 README 指向 `docs/project/...`
- `docs/pack-methods/` 不再作为有效文档入口
- `ROUTER.md` 内容已并入 `docs/WORKFLOW.md`

建议验证：

- `python3 -m pytest tests/test_pack_skills.py tests/test_release_process_docs.py`

### 检查点 B：planning gate 状态与阻断

- `needsPlan=true` 后会先进入 spec 阶段
- spec 未批准前不能进入 plan 后续执行链
- plan 未批准前不能进入 analyze / execute / review

建议验证：

- `python3 -m pytest tests/test_workflow_state_store.py tests/test_opencode_plugin_runtime.py`

### 检查点 C：整体回归

- 现有 close gate、review gate、verification gate 不被破坏
- 文档迁移没有造成断链

建议验证：

- `python3 -m pytest`

## 执行边界

- 在 plan 获批前，不开始实际实现步骤
- 实现时优先按“文档迁移 -> 方法/leader 规则 -> runtime gate -> 测试/evals”顺序推进
- 若 runtime 层发现无法可靠识别“用户批准 spec/plan”，先报告阻塞点，不做猜测式修补
