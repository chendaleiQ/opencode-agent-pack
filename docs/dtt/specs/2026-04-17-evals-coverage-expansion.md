# Spec：补齐 evals 场景用例，尽可能覆盖 rubric 与 leader/workflow 缺口

## 背景

当前 `evals/cases/` 已经覆盖了大部分主干路径，但仍存在一批明显空白或弱覆盖项，主要集中在：

1. escalation 子触发条件不完整；
2. end-gate / final summary 的显式负例不足；
3. tier 约束与 triage 负例覆盖不足；
4. strict 场景下的 planning / reviewer 阻断场景仍不够完整。

用户当前目标是：**把已识别的缺口尽量补齐，新增全部建议 case，尽可能提升 evals 的场景覆盖面**。

## 目标

1. 在 `evals/cases/` 下新增一组缺失场景 case，优先补齐此前识别出的 10 个缺口。
2. 每个新增 case 保持与现有 eval case 相同的人工评测风格：human-readable、manual-run、manual-compare、manual-record。
3. 新 case 要明确对应 rubric A-F 的一个或多个缺口，并写清楚 expected complexity/risk/lane、expected tier routing、为什么如此判断、误判风险、manual review checks。
4. 如果仓库中有自动化回归骨架测试依赖 case 名单，则同步更新该回归骨架，使新 case 被纳入自动检查。
5. 改动后重新验证：现有测试通过，新增 case 已被纳入 eval 自动化骨架检查。

## 非目标

- 不把 `evals/` 从 manual-first 模式改造成 CI 自动评测系统。
- 不修改 triage schema、lane 规则、runtime 行为或 reviewer/leader 核心逻辑。
- 不在本次实现中重写 rubric 结构，除非为新增 case 做极小的说明性补充且确有必要。
- 不承诺“数学意义上的 100% 覆盖率”；本次目标是**尽可能补齐已知明显缺口**。

## 约束

- 新增 case 文案语言保持与当前仓库一致（英文 case 内容可接受；聊天说明保持当前中文）。
- 保持现有 case 的目录结构与命名风格，文件放在 `evals/cases/`。
- 不删除现有 case，不重命名现有 case，避免无关 churn。
- 若更新自动化骨架测试，应仅做最小必要改动。
- 不提交 git commit，除非用户明确要求。

## 推荐方案

采用“**新增缺口 case + 同步更新回归骨架**”的最小扩充方案：

1. 基于已识别缺口，新增 10 个 case 文件；
2. 每个 case 直接对齐一个高优先级规则空白，避免含糊重叠；
3. 更新 `tests/test_eval_regression_skeleton.py` 中的期望 case 列表，确保新 case 至少被自动化骨架发现；
4. 运行全量测试与 eval 骨架测试，确认没有回归。

这个方案的优点：

- 与现有 evals 设计一致；
- 能快速提高覆盖面；
- 改动边界清晰，便于 reviewer 检查；
- 不把“补 case”变成“改系统行为”的大任务。

## 拟新增 case 清单

1. `scope-expansion-standard-to-strict-escalation.md`
   - 覆盖执行中 scope expansion / requirements grow 导致升级。
2. `implementer-instability-must-escalate.md`
   - 覆盖 implementer instability 导致升级。
3. `strict-reviewer-cannot-close-blocks-final.md`
   - 覆盖 strict reviewer 明确不能关闭时，leader 不得关闭。
4. `final-approval-tier-must-remain-top.md`
   - 覆盖 `finalApprovalTier` 不能下放。
5. `ambiguous-high-impact-task-enters-strict.md`
   - 覆盖 ambiguous / unstable task 应保守进入 strict。
6. `estimated-files-distortion-detected.md`
   - 覆盖 `estimatedFiles` 明显失真时的 triage 偏差识别。
7. `strict-needs-plan-structured-approvals.md`
   - 覆盖 strict + needsPlan 下完整 spec/plan 结构化审批路径。
8. `final-summary-metadata-required-before-close.md`
   - 覆盖关闭前必须输出统一 execution summary 与 evidence metadata。
9. `chat-only-misuse-workflow-trigger.md`
   - 覆盖 workflow-triggering 请求被错误当作 chat-only 的严重错误。
10. `reviewer-recommends-escalation-must-upgrade.md`
   - 覆盖 reviewer recommends escalation 后必须升级。

## 验收标准

1. `evals/cases/` 中新增上述 10 个 case 文件。
2. 每个文件都包含：task description、background、expected complexity/risk/lane、expected tier routing、why this judgment is correct、misclassification risks、manual review checks。
3. 若 `tests/test_eval_regression_skeleton.py` 维护 case 列表，则新增文件已纳入列表。
4. 全量自动化测试通过。
5. eval 自动化骨架测试通过。
6. 新增 case 与现有文档规则一致，不自相矛盾。

## 执行边界

- 在 plan 批准前，不新增 case 文件、不改测试。
- 若实施中发现新增 case 数量需要增减，需先记录原因，再决定是否调整范围。

## 当前停点

本 spec 已写出，等待你确认。确认后我再写 plan；plan 再确认后才开始实际新增 case 和更新测试。
