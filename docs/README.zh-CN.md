# do-the-thing

[English](../README.md) | [简体中文](./README.zh-CN.md)

do-the-thing 是一个单入口的 agent workflow plugin。
安装后，直接把任务交给 `leader`，剩余的分诊、委派、评审、验证和收口交给系统处理。

## 这是什么
- 单入口工作流：统一从 `leader` 开始
- 自动路由：按任务复杂度与风险选择 lane / tier
- 更少手动判断：不需要自己先决定该叫哪个 agent、用哪个模型

## 平台支持
- OpenCode：已支持，含 `agent router`
- Claude Code：coming soon
- Cursor：coming soon
- Codex：coming soon

## 工作方式
- 默认入口：`leader`
- 低风险本地任务可委派给更快的 tier
- 高风险判断、升级与最终收口由高 tier 负责
- 当 `needsPlan=true` 时，必须先过 spec 审批，再过 plan 审批，之后才能进入执行
- 规划产物统一落在 `docs/dtt/specs/` 与 `docs/dtt/plans/`

## 安装

### OpenCode

一条命令原生安装，默认跟随仓库 `main` 分支。

macOS / Linux：

```bash
curl -fsSL https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.sh | bash -s -- opencode
```

Windows PowerShell：

```powershell
irm https://raw.githubusercontent.com/chendaleiQ/do-the-thing/refs/heads/main/install/install.ps1 | iex; Install-DoTheThing opencode
```

如需在重装时指定版本，可先设置 `DTT_PLUGIN_REF`。

详细说明：[`../.opencode/INSTALL.md`](../.opencode/INSTALL.md)

### Claude Code

coming soon

### Cursor

coming soon

### Codex

coming soon

### 验证安装

重启 OpenCode，新开会话后运行：`switch to leader and say ready`。

## 使用
1. 切换到 `leader`
2. 直接描述任务
3. 由工作流处理路由、升级与收口

如果任务命中规划流程，`leader` 会按当前对话语言输出可读的 spec / plan，同时将产物写入 `docs/dtt/`。

需要调整 provider 允许列表时，使用 `/providers`。

## 项目文档
- 工作流：[`WORKFLOW.md`](./WORKFLOW.md)
- 架构：[`ARCHITECTURE.md`](./ARCHITECTURE.md)
- 发布：[`RELEASE.md`](./RELEASE.md)
- 维护：[`MAINTAINING.md`](./MAINTAINING.md)

## 适用人群
- 希望低摩擦自动化的个人开发者
- 需要统一执行规则的团队
- 需要可复用工作流插件的项目
