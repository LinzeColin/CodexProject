# PFI v0.2.3 Stage 4-6 Group Review

## Scope

本文件覆盖第二阶段第二组整体复审：Stage 4、Stage 5、Stage 6。

本轮只复审二级页面差异化、首页人类任务流、核心指标真实 read model
在当前 `pfi` 项目级 worktree 和真实 localhost app 中是否一致。
本轮不进入 Stage 7-11，不执行最终项目级 closeout，不清理用户数据。

## Review Basis

- Stage 4：每个正式一级入口必须有 3-5 个差异化二级页面，URL、state、
  breadcrumb、title、主对象、主操作、空状态和错误状态都要变化。
- Stage 5：首页只展示个人经济总览、数据健康、下一步动作、最近变化和报告入口；
  首页不得暴露 Task Pack、运行边界、AI 控制台、反馈控制台或证据抽屉。
- Stage 6：净资产、现金余额、投资市值、生活消费、消费总流出、数据健康等核心指标
  必须来自真实 read model 或明确中文阻断状态，缺失时不得回退为 0。

## Finding Fixed

复审发现：

- Stage 4 的 10 个正式一级入口和 45 个二级页面合同仍成立。
- Stage 5 首页在真实 localhost 中不再显示说明/证据抽屉按钮，下一步动作来自数据状态和待复核任务。
- Stage 6 的净资产、现金余额和投资市值已显示中文缺失状态。
- 消费页仍把未配置固定支出规则的 `fixed_spend_cny=0` 显示为
  `固定/弹性 = CNY 0.00 / CNY 7,153.98`，并在趋势图中展示固定支出 0 线。
  这不是已确认真实固定支出为 0，而是规则未配置，应显示为未配置状态。

修复：

- `PFI/web/app/shell.js` 新增可选 CNY 金额格式化逻辑。
- 固定支出规则未配置时，消费页显示 `未配置 / CNY 7,153.98`。
- 固定支出和预算规则未配置时，不再把对应 0 序列画入消费趋势图。

## Evidence

- Group review evidence：
  `PFI/reports/pfi_v023/group_reviews/stage_4_6/evidence.json`
- Browser audit：
  `PFI/reports/pfi_v023/group_reviews/stage_4_6/browser_audit.json`
- Review audit：
  `PFI/reports/pfi_v023/group_reviews/stage_4_6/review_audit.json`
- Terminal log：
  `PFI/reports/pfi_v023/group_reviews/stage_4_6/terminal.log`

## Validation

本轮验证集：

```bash
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_stage4_subpage_differentiation.py PFI/tests/test_v023_stage5_home_experience.py PFI/tests/test_v023_stage6_core_metrics.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_regression.py -q
PYTHONPATH=PFI/src PFI/.venv/bin/python -m pytest PFI/tests/test_v023_*.py -q
PATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH node --check PFI/web/app/shell.js
PFI/scripts/macosAppAcceptanceLite.sh --project-root /Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI --summary-json
```

## Remaining Work

第二阶段仍需继续：

- Stage 7-9 分组整体复审。
- Stage 10-11 分组整体复审。
- 第三阶段 v0.2.3 项目级整体复审、同步 GitHub、备份和非必要文件清理。
