# Release Policy

本项目采用语义化版本：`MAJOR.MINOR.PATCH`。

## 版本级别定义

## PATCH（x.y.Z）
适用于不改变核心行为、可安全小步发布的变更：
- README、示例、注释、措辞修正
- `evals/cases` 新增或补充（不修改核心路由规则）
- 安装脚本的小修复（不改变默认安装语义）
- 拼写、格式、链接修复

## MINOR（x.Y.z）
适用于向后兼容的功能增强或规则细化：
- triage 规则的兼容性优化（不破坏已有字段/流程）
- lane/tier 的默认策略细化（不改变核心角色与单入口定位）
- 新增可选检查项或评测工具说明
- 安装流程新增可选参数（默认行为兼容）

## MAJOR（X.y.z）
适用于不兼容或高影响行为变化：
- `change-triage` 输出字段变更（增删改字段、语义重定义）
- lane 体系重大变更（如新增/删除 lane，或判定逻辑重构）
- tier 关键约束改变（如 finalApprovalTier 不再固定 top）
- 单入口模型被破坏（不是 leader 单入口）
- 安装路径/默认行为发生不兼容变化

## 特定变更分级规则

- triage 规则微调（不改 schema）：MINOR
- triage 输出 schema 变更：MAJOR
- lane/tier 逻辑轻度收紧且兼容：MINOR
- lane/tier 根本性变更：MAJOR
- install 默认目标目录改变：MAJOR
- install 新增可选 flag 且默认不变：MINOR
- README/examples 小改动：PATCH
- 仅新增 eval case：PATCH（若顺带改规则，按规则本身升级）

## 发布前最小检查
每次发布前至少确认：
1. 核心定位未破坏（单入口、唯一分流、唯一收口）
2. `change-triage` 输出格式符合当前版本规范
3. `evals/rubric.md` 与规则一致
4. README 与实际行为一致
5. evals 与 verify / end-gate 说明保持一致
6. 安装脚本可在基础场景工作（project/global/custom）

## 发布说明模板（建议）
- 版本号：
- 变更级别：MAJOR/MINOR/PATCH
- 核心变更：
- 风险评估：
- 是否影响 triage/lane/tier：
- 是否需要迁移说明：
