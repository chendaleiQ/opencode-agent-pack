# Spec：修复 `needsPlan=true` 未强制落盘与确认停点的回归

## 背景

用户反馈：当前在 `needsPlan=true` 的任务中，流程仍然可能没有把 spec 和 plan 写入文件，也没有在 spec / plan 阶段停下来等待用户确认。

当前还观察到一个更具体的回归：planning gate 处于 spec 阶段时，会阻止写入 spec 文件本身，导致 `dtt-brainstorming` 要求的“写 spec 到 `docs/dtt/specs/`”无法完成。

## 目标

1. `needsPlan=true` 时必须先生成 spec。
2. spec 必须写入 `docs/dtt/specs/`，并在聊天中展示。
3. spec 获得用户确认前，不得生成 plan。
4. plan 必须写入 `docs/dtt/plans/`，并在聊天中展示。
5. plan 获得用户确认前，不得进入 analyze / implement / review。
6. runtime guard 必须允许规划阶段写入 spec/plan 文件，但仍阻止实现型操作。

## 推荐方案

修复 runtime planning gate：在 spec 阶段允许写入 `docs/dtt/specs/*.md`；在 plan 阶段允许写入 `docs/dtt/plans/*.md`；除此之外继续阻断实现型工具。

## 验收标准

1. spec 阶段允许写入 `docs/dtt/specs/*.md`。
2. spec 未批准前不能进入 plan。
3. plan 阶段允许写入 `docs/dtt/plans/*.md`。
4. plan 未批准前不能进入 analyze / implement / review。
5. 有回归测试覆盖该行为。

## 当前停点

本 spec 已由用户确认通过，并作为本次计划与实现的依据。
