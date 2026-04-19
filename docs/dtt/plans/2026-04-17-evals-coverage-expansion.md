# Plan：补齐 evals 场景用例，尽可能覆盖 rubric 与 leader/workflow 缺口

## 目标

在不改动 workflow 运行逻辑的前提下，新增一批缺失的 eval case，补齐当前 `evals/cases/` 对 rubric A-F 与 leader/workflow 关键规则的空白或弱覆盖项，并把新增 case 纳入自动化骨架检查。

完成后应满足：

1. `evals/cases/` 新增 10 个高优先级缺口 case；
2. 每个 case 都符合现有 manual-first eval 文档风格；
3. `tests/test_eval_regression_skeleton.py` 能识别这些新增 case；
4. 全量测试与 eval 骨架测试通过；
5. 覆盖面较当前版本明显提升，尤其是 escalation / end-gate / tier 负例相关缺口。

## 已批准 spec

- `docs/dtt/specs/2026-04-17-evals-coverage-expansion.md`

## 架构摘要

本次工作只涉及两类内容：

1. **人工 eval case 文档**
   - 目录：`evals/cases/`
   - 作用：作为 manual-run / manual-compare / manual-record 的场景基准

2. **自动化回归骨架**
   - 文件：`tests/test_eval_regression_skeleton.py`
   - 作用：确保关键 case 文件存在，并覆盖当前约定的最小回归集合

因此最小实现路径是：

- 新增 case 文件；
- 更新骨架测试中的 expected 名单；
- 运行测试验证。

## 有序实现步骤

### Step 1：复核现有 case 风格与命名约定

目标文件：

- `evals/README.md`
- `evals/rubric.md`
- `evals/cases/*.md`

工作内容：

1. 确认现有 case 的标题、段落结构、期望字段写法。
2. 确认命名风格与内容密度，避免新增 case 过长或过短。
3. 把 10 个新增 case 各自映射到一个主要缺口，避免高重叠。

验收点：

- 能明确列出每个新增 case 的主覆盖目标。

### Step 2：新增 10 个缺口 case

目标目录：

- `evals/cases/`

新增文件：

1. `scope-expansion-standard-to-strict-escalation.md`
2. `implementer-instability-must-escalate.md`
3. `strict-reviewer-cannot-close-blocks-final.md`
4. `final-approval-tier-must-remain-top.md`
5. `ambiguous-high-impact-task-enters-strict.md`
6. `estimated-files-distortion-detected.md`
7. `strict-needs-plan-structured-approvals.md`
8. `final-summary-metadata-required-before-close.md`
9. `chat-only-misuse-workflow-trigger.md`
10. `reviewer-recommends-escalation-must-upgrade.md`

每个文件至少包含：

- task description
- background
- expected complexity / risk / lane
- expected tier routing
- why this judgment is correct
- misclassification risks
- manual review checks

工作内容：

1. 先写 escalation / strict / end-gate 高优先级 case；
2. 再补 triage / tier / summary 类负例；
3. 确保每个 case 对应 rubric A-F 的一个主要缺口，不只是换壳重复。

验收点：

- 10 个 case 文件全部存在；
- 内容与现有 case 风格一致；
- 每个 case 都能说明“为什么这个规则重要”。

### Step 3：更新 eval 自动化骨架回归

目标文件：

- `tests/test_eval_regression_skeleton.py`

工作内容：

1. 将新增 case 文件名补入 expected 列表。
2. 保持测试意图不变：该测试仍只负责校验关键 eval case 是否存在。
3. 如有必要，按主题排序 expected 名单，保持可读性。

验收点：

- 自动化骨架测试会在新增 case 缺失时失败；
- 测试语义仍然简单清晰。

### Step 4：自查新增 case 的覆盖映射

目标文件：

- 新增的 10 个 `evals/cases/*.md`
- `evals/rubric.md`

工作内容：

1. 核对 10 个 case 分别主要补哪一个维度空白。
2. 检查是否仍遗漏以下关键缺口：
   - scope expansion escalation
   - implementer instability escalation
   - strict reviewer cannot close
   - finalApprovalTier must remain tier_top
   - ambiguous/unstable -> strict
   - estimatedFiles distortion
   - strict needsPlan approvals
   - final summary metadata before close
   - chat-only misuse
   - reviewer recommends escalation
3. 如发现某项仍未真正落地，补充或修正文案后再进入验证。

验收点：

- 新增 case 与缺口清单一一对应；
- 不出现明显自相矛盾或与现有规则冲突的描述。

### Step 5：运行验证

优先验证命令：

- `python -m pytest tests/ -v`（若环境具备仓库 canonical 路径）
- 或可用环境下的等价 pytest 全量命令
- `python -m pytest tests/test_eval_regression_skeleton.py -v`

工作内容：

1. 运行 eval 骨架测试，确认新增 case 已纳入。
2. 运行全量测试，确认无回归。
3. 记录实际使用的命令、结果与必要说明。

验收点：

- `tests/test_eval_regression_skeleton.py` 通过；
- 全量测试通过；
- 工作区无意外改动。

### Step 6：评审与收尾

目标：

- 由 reviewer 检查新增 case 是否真正补齐缺口、是否与 spec/plan 一致。

工作内容：

1. reviewer 先查 spec/plan 对齐，再查新增 case 内容质量。
2. 若 reviewer 提出缺口未补齐或规则写错，再回 implementer 修正。
3. 通过后再进入 verification-before-completion 与最终总结。

验收点：

- reviewer 无未解决高风险问题；
- 验证证据完整。

## 风险与控制

### 风险 1：新增 case 名称或内容与现有风格不一致

控制：

- 先复核现有 case 模板风格，再统一写作。

### 风险 2：case 看似新增，实际没有补到缺口

控制：

- 每个 case 绑定一个主缺口；
- Step 4 做逐项映射自查。

### 风险 3：骨架测试未同步更新，导致新增 case 没被纳入回归

控制：

- 把 `tests/test_eval_regression_skeleton.py` 列为必改文件之一；
- 单独运行该测试确认。

### 风险 4：覆盖面扩大但引入文档规则冲突

控制：

- reviewer 先检查与 `evals/rubric.md`、`agents/leader.md` 的一致性；
- 不在 case 中发明超出当前系统文档的新规则。

## 验收标准

1. 新增 10 个 case 文件全部存在。
2. `tests/test_eval_regression_skeleton.py` 已纳入新增 case 名单。
3. 每个 case 结构完整、主题明确。
4. eval 骨架测试通过。
5. 全量测试通过。
6. reviewer 未指出未解决的高风险遗漏。

## 执行边界

- plan 未批准前，不新增 case 文件，不改测试。
- 不扩展到修改 runtime/workflow 逻辑。
- 不提交 git commit，除非用户明确要求。

## 当前停点

本 plan 等待你确认。确认后，我才开始实际新增 case、更新测试并运行验证。
