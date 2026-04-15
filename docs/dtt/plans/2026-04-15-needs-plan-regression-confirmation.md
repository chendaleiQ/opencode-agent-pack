# Plan：修复 `needsPlan=true` 未强制落盘与确认停点的回归

## 目标

修复 `needsPlan=true` 工作流中 spec / plan 没有稳定写入文件、且没有严格停下来等待用户确认的问题。

本计划基于已确认的 spec：修复 `needsPlan=true` 未强制落盘与确认停点的回归。

## 架构摘要

本次修复需要把门禁闭环补完整，而不是只改提示词：

1. 检查方法技能是否明确要求 spec / plan 落盘、聊天展示、用户确认停点。
2. 检查 leader 工作流是否把 `needsPlan=true` 视为硬门禁。
3. 修复 runtime planning gate，让它允许规划阶段必要的 spec / plan 文件写入。
4. 增加或更新回归测试，覆盖“spec/plan 可以落盘，但未获确认前不能执行”。

## 实施步骤

### Step 1：定位当前 planning gate 阻断点

涉及文件预计包括：

- `.opencode/plugins/runtime/hook_runtime.js`
- `.opencode/plugins/runtime/state_store.js`
- `.opencode/plugins/runtime/evidence_gate.js`
- 相关测试文件，如 `tests/test_opencode_plugin_runtime.py` 或 planning gate 专用测试

操作：

- 找到阻止 `apply_patch` 写入 `docs/dtt/specs/*.md` 的规则。
- 确认 guard 如何识别当前 stage：spec、plan、approved。
- 确认工具调用路径是否能区分规划文档写入与实现型代码修改。

### Step 2：补齐规划阶段允许列表

目标行为：

- spec 阶段允许写入 `docs/dtt/specs/*.md`。
- spec 阶段仍禁止写入代码、测试、runtime、agent 配置等实现文件。
- plan 阶段允许写入 `docs/dtt/plans/*.md`。
- plan 阶段仍禁止进入 analyze / implement / review 或实现型文件修改。

实现原则：

- 优先用最小改动修复 guard 判定。
- 不放宽到允许任意文件写入。
- 不改变 `dtt-change-triage` schema。

### Step 3：检查并补强方法层与 leader 规则

涉及文件预计包括：

- `skills/dtt-brainstorming/SKILL.md`
- `skills/dtt-writing-plans/SKILL.md`
- `agents/leader.md`
- 如仓库维护安装态镜像，则同步检查 `.opencode/` 或安装输出对应文件

操作：

- 确认 `dtt-brainstorming` 要求写入 `docs/dtt/specs/`、聊天展示、等待 spec approval。
- 确认 `dtt-writing-plans` 要求写入 `docs/dtt/plans/`、聊天展示、等待 plan approval。
- 确认 leader 规则明确：plan 未批准前不得 todo / analyze / execute / review。

### Step 4：增加回归测试

测试应覆盖：

1. `needsPlan=true` 且 spec 未生成时，允许写入 `docs/dtt/specs/*.md`。
2. spec 未批准前，阻止非 spec 文档写入或执行型工具。
3. spec 批准后，允许写入 `docs/dtt/plans/*.md`。
4. plan 未批准前，阻止实现型操作。
5. plan 批准后，允许继续正常执行链路。

优先更新已有 runtime/plugin 测试；只有在结构更清晰时才新增测试文件。

### Step 5：运行验证

优先运行最小相关测试：

```bash
python3 -m pytest tests/test_opencode_plugin_runtime.py tests/test_workflow_state_store.py
```

如果修改涉及 skill/agent 文档规则，再运行：

```bash
python3 -m pytest tests/test_pack_skills.py
```

最后视改动范围运行更大回归：

```bash
python3 -m pytest
```

## 执行边界

- plan 获批前，不开始 Step 1 的代码/测试实现。
- 如果 runtime guard 继续阻止 plan 文件写入，应先报告该阻塞，不绕过门禁。
- 不回滚或修改用户已有无关改动。
- 不提交 git commit，除非用户明确要求。

## 当前停点

本 plan 已由用户确认通过，可作为本次实现与验证依据。
