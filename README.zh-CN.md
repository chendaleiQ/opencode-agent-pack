# do-the-thing

[English](./README.md) | [简体中文](./README.zh-CN.md)

do-the-thing 是一个单入口、自动路由的 OpenCode agent workflow。  
安装一次后，你只需要和默认最强入口代理 `leader` 对话。  
文档中的工作流会把分诊、委派、升级、评审、验证和最终收口都通过这个单一入口来完成。

把任务交给一个 agent，剩下的流程交给系统。

## 解决什么问题
多数多代理方案会让用户手动决定：
- 用哪个模型
- 调哪个代理
- 任务是否有风险
- 走快速路径还是严格路径

这个 pack 在工作流层面消除了这些负担：
- 你只要把任务交给 `leader`
- pack 会定义分诊、lane 路由、tier 路由、子代理分发、评审/验证、升级与最终收口该如何执行

## 核心定位
这是 **do-the-thing**：一个**单入口、自动 lane+tier 路由的 OpenCode workflow**。

它**不是**：
- 提示词片段集合
- 单一孤立技能
- 多入口代理菜单

## 为什么只保留一个最强入口
`leader`（tier_top）负责所有关键决策：
- 任务理解
- 风险边界判断
- lane 选择
- 升级决策
- 最终批准

低价值的本地工作会在安全前提下委派给更快、更便宜的 tier。

## Lane 路由（使用哪条流程）
系统会把每个任务分诊到一个 lane：

- `quick`：低复杂度 + 低风险 + 无敏感标记 + 小改动
- `standard`：高复杂度 + 低风险
- `guarded`：低复杂度 + 高风险
- `strict`：高复杂度 + 高风险

命中敏感项（`auth/db schema/public api/destructive`）时，不能维持为低风险。

## Quick Lane 走最小路径
`quick` 不是强制的 analyzer -> implementer -> reviewer 串行链路。

相反，`leader` 应该按任务只选最小必要下游路径：
- 快速实现：`implementer`
- 快速调查：`analyzer`
- 快速评审：`reviewer`

如果 quick 任务需要多个下游角色，或需要反复往返才能安全完成，就应该升级，而不是假装保持轻量。

## Tier 路由（使用哪档模型能力）
抽象 tier：
- `tier_top`：最强模型（入口、分诊理解、严格边界、最终收口）
- `tier_mid`：均衡模型（评审、非最终验证、复杂分析）
- `tier_fast`：低成本/高速度模型（低风险实现、扫描、重复性草拟）

默认行为：
- 低风险本地任务：委派给 `tier_fast`
- 高风险决策与最终收口：始终由 `tier_top` 处理
- 评审质量控制：通常由 `tier_mid` 负责（严格场景可升到 `tier_top`）

## 为什么低风险任务会被委派
因为这类任务边界清晰、影响较小，适合低成本快速执行。  
这并不代表每个低风险任务都要走完整工作流。目标是最小化安全委派，然后回到 `tier_top` 完成最终收口。

## 子代理行为
只有 `leader` 应执行如 `change-triage` 这类工作流路由逻辑。

被委派的子代理应当：
- 直接消费交接内容
- 保持在自己的角色范围内
- 避免为本地任务重复跑分诊或重进重量级工作流技能
- 当交接内容或边界不清晰时，回报并请求升级

## 内建方法技能
本 pack 现在内建了一组方法技能，在不放弃单入口工作流控制的前提下，提升执行深度与质量。

当前内建方法技能包括：
- `brainstorming`
- `dispatching-parallel-agents`
- `executing-plans`
- `finishing-a-development-branch`
- `writing-plans`
- `systematic-debugging`
- `test-driven-development`
- `verification-before-completion`
- `requesting-code-review`
- `receiving-code-review`

`change-triage` 仍负责决定工作流骨架；这些方法技能只会根据任务形态、评审需求、不确定性与收口状态按条件插入。

## 外部技能系统
这个 pack 的正常使用不再需要外部工作流系统。
- 本 pack 仍是 lane/tier/升级/收口的工作流事实来源
- 优先使用 pack 内建方法技能，而不是外部同类技能
- 子代理必须先遵守交接边界，不要重新进入外部重量级技能链

## 为什么高风险任务不会由弱模型起步
高风险或敏感任务从一开始就需要强边界控制：
- guarded/strict 的边界规则由 `tier_top` 设定
- strict 的最终批准始终是 `tier_top`
- 升级可自动提升 tier/lane

## 安装

### 一键安装（默认）
无需 clone 仓库，直接从最新 GitHub Release 安装：

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/main/bootstrap/install.sh | bash
```

PowerShell：
```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/main/bootstrap/install.ps1 | iex
```

如果要安装固定版本而不是 `latest`，先设置 `DO_THE_THING_VERSION`：

```bash
DO_THE_THING_VERSION=v1.0.0 curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/main/bootstrap/install.sh | bash
```

PowerShell：
```powershell
$env:DO_THE_THING_VERSION = "v1.0.0"
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/main/bootstrap/install.ps1 | iex
```

bootstrap 脚本会下载对应的 GitHub Release 压缩包，解压到临时目录后再调用包内的本地安装器。

### 本地手动安装
适用于离线安装、本地调试或贡献者工作流：

```bash
git clone git@github.com:chendaleiQ/do-the-thing.git
cd do-the-thing
bash install.sh
```

PowerShell：
```powershell
git clone git@github.com:chendaleiQ/do-the-thing.git
cd do-the-thing
.\install.ps1
```

### 自定义目标目录
安装到任意目录：

```bash
bash install.sh --target /path/to/target
```

PowerShell：
```powershell
.\install.ps1 -Target "C:\path\to\target"
```

### 安全行为
- 安装器默认全局安装（`~/.config/opencode/`）
- 不支持项目级安装
- 目标目录若存在且非空，除非传 `--force` / `-Force`，否则会中止安装
- `--force` / `-Force` 会执行干净重建（安装前清空目标目录内容）
- `--force` / `-Force` 会保留已知用户配置文件：`opencode.json`、`settings.json`
- 不执行破坏性 reset 操作

### Provider Allowlist
安装期间，pack 会在 `settings.json` 中配置一个 pack 作用域的 provider allowlist：
- provider 候选会从本地 OpenCode 状态中检测
- 默认会选中全部已检测到的 provider，直接回车即可接受
- 选中的策略会写入 `doTheThing.allowedProviders`
- 如果一个 provider 都没检测到，安装器会保留现有 allowlist，除非你显式确认写入空列表
- 安装后可通过 `/providers` 查看或重新配置允许路由到哪些 provider

## 使用

安装后，用户工作流刻意保持简单：
1. 切换到 `leader` agent，然后直接提任务
2. `leader` 按文档流程处理分诊/路由/升级
3. `leader` 在评审/结束门通过后给出最终收口总结
4. 需要调整 pack 允许使用的 provider 时，使用 `/providers`

## 可选工具：子代理模型路由器
本 pack 提供了一个可选工具：`pack/tools/subagent_model_router.py`。

作用：
- 输入 triage JSON
- 返回推荐的子代理分发顺序
- 按 tier（`tier_fast|tier_mid|tier_top`）返回每个角色的模型选择
- 支持按 provider 映射模型（从配置自动检测，无硬编码默认 provider）
- 可从可用模型列表自动选择
- 可从本地 opencode 配置自动检测 provider/models
- 可自动发现 provider 可用模型并构建 tier 候选
- 会遵守 `settings.json` 中 pack 作用域的 provider allowlist
- 若当前 provider 不在 allowlist 中，会在 allowlist 内部回退，不会越过策略边界
- 若 `allowedProviders: []` 是显式写入的空列表，则表示全部禁用，直到重新配置
- 若传入 `--config-path` 指向自定义目录下的 `opencode.json`，router 会同时读取同目录下的 `settings.json`

示例：
```bash
PYTHONPATH=. python3 -m pack.tools.subagent_model_router \
    --auto-detect-config \
    --discover-models \
    --triage-json '{"taskType":"refactor","lane":"quick","analysisTier":"tier_fast","executorTier":"tier_fast","reviewTier":"tier_mid","needsReviewer":false}'
```

Router 会从你的 opencode 配置自动检测 provider 和可用模型。
如果当前 provider 不被允许，router 会给出 warning，并回退到 allowlist 中第一个可用的 provider，而不是绕过策略继续路由。

自定义目标目录示例：
```bash
PYTHONPATH=. python3 -m pack.tools.subagent_model_router \
    --config-path /tmp/my-opencode-pack/opencode.json \
    --auto-detect-config \
    --triage-json '{"taskType":"review","lane":"quick","analysisTier":"tier_mid","executorTier":"tier_mid","reviewTier":"tier_mid","needsReviewer":false}'
```

传入 `--config-path` 后，provider 策略会从 `/tmp/my-opencode-pack/settings.json` 读取。

Provider 模型发现（可选）：
```bash
PYTHONPATH=. python3 -m pack.tools.subagent_model_router \
    --auto-detect-config \
    --discover-models \
    --triage-json '{"taskType":"feature","lane":"strict","analysisTier":"tier_top","executorTier":"tier_mid","reviewTier":"tier_top","needsReviewer":true}'
```

输出还包括：
- `provider`
- `availableModelsCount`
- `tierCandidates`（自动分桶后的 fast/mid/top 候选）
- `warnings`（例如 provider 发现时缺失 API key）

可通过环境变量覆盖模型映射：
- `OPENCODE_MODEL_TIER_FAST`
- `OPENCODE_MODEL_TIER_MID`
- `OPENCODE_MODEL_TIER_TOP`

你**不需要**：
- 手动切换模型
- 手动选择代理
- 手动判断复杂度/风险
- 手动选流程 lane

## 设计原则（当前版本）
- 单入口（`leader`）
- 最强模型掌控决策和收口
- 先分诊，再实现
- lane 路由 + tier 路由
- 只允许自动向上升级（不自动降级）
- 按 lane 定义明确结束门
- 收口时统一执行摘要

## 验证与结束门
- 不能仅凭实现输出就关闭工作
- reviewer 输出仍是 standard/guarded/strict 流程的一部分，quick 在确实需要评审时也会加入
- 验证证据可以是命令输出，或在无正式 verify 命令时的显式人工检查
- 若采用人工验证，代理应明确说明具体检查了什么
- `leader` 只有在对应结束门满足后才应收口

## V5 新增：Evals 与维护
项目包含 `evals/`，作为 triage/lane/tier 行为的手工评估工具包。

如何使用 evals：
1. 在 `evals/cases/` 中选择一个 case
2. 手动运行 triage（必要时继续跑后续流程）
3. 将实际输出与 case 中的预期输出对比
4. 使用 `evals/rubric.md` 打分
5. 记录你检查了什么；若需修复，使用 `MAINTAINING.md`

仓库默认不提供这些 eval 的 CI 自动化；它们旨在手动执行与评审。

### 为什么高风险漏判率最重要
核心指标是**高风险漏判率低**，而不是总体准确率高。

原因：
- 低风险任务被过度升级，通常只是时间/成本损耗
- 高风险任务被低估，可能导致安全/数据/API 事故

### 如何贡献新的 eval case
1. 复制 `evals/cases/` 里一个现有 case 格式
2. 填写 task/background/expected triage/lane/tier/risk points
3. 提交 PR，并说明该 case 覆盖了哪种失败模式
4. 引用 `evals/rubric.md` 标准

## 发布策略（简版）
版本遵循 `MAJOR.MINOR.PATCH`。
- PATCH：文档/示例/case/安全修复
- MINOR：向后兼容的路由改进
- MAJOR：破坏性 lane/tier/schema/install 行为变化

完整规则见 `RELEASE.md`。

## 维护（简版）
修复顺序：
1. 新增 eval case
2. 调整 triage 规则或阈值
3. 必要时收紧 quick lane
4. 仅在高风险漏判反复出现时再加硬规则

完整流程见 `MAINTAINING.md`。

## 适用人群
- 希望低摩擦自动化的个人开发者
- 需要一致且安全路由规则的团队
- 需要可复用默认自动化包的 OSS 仓库
- 需要统一任务执行策略的内部工程组织

## 目录结构
```text
do-the-thing/
├─ README.md
├─ README.zh-CN.md
├─ LICENSE
├─ install.sh
├─ install.ps1
├─ RELEASE.md
├─ MAINTAINING.md
├─ evals/
│  ├─ README.md
│  ├─ rubric.md
│  └─ cases/
├─ examples/
│  └─ minimal-project/
└─ pack/
   ├─ AGENTS.md
   ├─ agents/
   ├─ commands/
   └─ skills/
```
