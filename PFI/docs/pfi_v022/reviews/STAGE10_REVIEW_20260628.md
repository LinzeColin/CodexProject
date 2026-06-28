# PFI v0.2.2 Stage 10 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 10；不复审 Stage 11-13，不做整体项目复审，不重装 app 入口，不同步 GitHub。

复审结论：Stage 10 报告、建议与复盘仍保留为本地合同和 read model 层，不替代 v0.2.1 主 Web Shell；原先行动建议中的构造交易 ID、构造金额、构造订阅和构造投资行为建议已移除。Stage 10 现在从真实 `MetaDatabase`、Stage 9 真实可视化上下文、Stage 7 真实公式输入和中文真实空态派生报告口径与行动建议。

上线阻塞项：1

剩余阻塞项是全局 legacy 测试/样例/模拟数据审计仍未关闭；Stage 10 本轮已不再把构造交易 ID、假建议或模拟投资行为作为验收依据。

硬边界：不得使用构造交易 ID、构造建议标题、构造金额、构造订阅或构造投资行为建议作为 Stage 10 正式验收依据。

## 复审范围

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S10-P1-T1` | 月报同时显示消费总流出和生活消费。 | 通过 |
| `S10-P1-T2` | 投资报告显示收益、成本、费用、汇率、交易频率、风格、现金拖累。 | 通过，当前无真实持仓时显示中文空态。 |
| `S10-P1-T3` | 数据质量报告显示未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff。 | 通过 |
| `S10-P2-T1` | 推荐解释为行动建议与复盘，不是自动投资建议。 | 通过 |
| `S10-P2-T2` | 建立行动建议评分公式。 | 通过 |
| `S10-P2-T3` | 建立建议生命周期。 | 通过 |

## 真实输入

| 项目 | 当前值 |
| --- | --- |
| 真实标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |
| 标准化流水数量 | `8815` |
| 待复核记录 | `406` |
| 待复核金额覆盖面 | `CNY 3,082,013.96` |
| 大额生活消费记录 | `181` |
| 大额生活消费金额 | `CNY 1,213,978.31` |
| 消费总流出 | `CNY 1,727,278.37` |
| 生活消费 | `CNY 1,545,600.44` |
| 投资行为复盘 | `暂无真实持仓快照或可确认卖出交易` |
| 订阅优化 | `暂无真实订阅候选文件或订阅规则运行结果` |

## 发现与修复

修复 1：行动建议不再使用构造交易 ID。

- 问题：原 `build_action_review_recommendations()` 手写交易 ID、标题、影响金额和评分输入。
- 修复：新增 `load_stage10_real_report_advice_context()`，只从真实 `MetaDatabase` 和真实空态派生建议。

修复 2：真实触发建议与中文空态分离。

- 当前真实触发建议包括：数据修复建议、消费复盘建议、现金流风险建议、参数调整建议。
- 当前没有真实持仓快照或可确认卖出交易，因此投资行为复盘建议进入中文真实空态。
- 当前没有真实订阅候选文件或订阅规则运行结果，因此订阅优化建议进入中文真实空态。

修复 3：建议评分增加真实依据说明。

- 每条真实触发建议包含 `score_basis_zh`。
- 分数来自真实记录数、金额覆盖面、平均置信度、阈值命中比例或现金流输入；不再使用手写评分样本。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 报告只显示一个消费口径 | 未触发 |
| 投资报告只有收益 | 未触发；无真实持仓时显示空态，不伪造收益。 |
| 数据质量报告不含 Interconnection 关联指标 | 未触发 |
| 推荐被误解成买卖指令 | 未触发；交易、支付、券商提交均为 false。 |
| 建议没有排序依据 | 未触发；真实触发建议按 Stage 10 评分排序。 |
| 建议无法复盘效果 | 未触发；生命周期保留 `reviewed -> effect_measured`。 |
| 出现构造交易 ID、构造建议或构造金额 | 未触发；复审测试扫描源码和目标测试。 |
| Stage 11 测试与验证被提前实现 | 未触发 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 10 模块 | `PFI/src/pfi_v02/stage_v022_report_advice_review.py` |
| 原 Stage 10 合同测试 | `PFI/tests/test_v022_stage10_report_advice_review.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage10.py` |
| Stage 10 验收报告 | `PFI/docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md` |
| 真实标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage10_report_advice_review.py tests/test_v022_review_stage10.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_review_stage9.py tests/test_v022_stage10_report_advice_review.py tests/test_v022_review_stage10.py -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
curl -fsS http://127.0.0.1:8501/_stcore/health
```

## 最新验证结果

- Stage 10 目标 + 复审测试：`11 passed, 18 subtests passed`。
- Stage 0-10 v0.2.2 相关回归：`93 passed, 348 subtests passed`。
- 构造建议残留扫描：无构造交易 ID、构造订阅、构造投资行为建议或旧手写评分输入命中。
- 真实 8501 浏览器矩阵：`/tmp/pfi_stage10_review_recheck/summary.json` 通过；桌面关键入口可见，`建议与复盘`、`报告与洞察` 可点击，全局搜索 `406/8815` 命中；移动端关键入口可点击且水平溢出 `0px`；禁用可见词、console errors、page errors 均为 `0`；截图 `/tmp/pfi_stage10_review_recheck/desktop.png` 和 `/tmp/pfi_stage10_review_recheck/mobile.png`。
- Web shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`python3 scripts/validate_project_governance.py --project PFI` 返回 `errors 0 / warnings 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`curl -fsS http://127.0.0.1:8501/_stcore/health` 返回 `ok`。

## 剩余风险

- 本轮只证明 Stage 10 已按真实 MetaDatabase 派生值和真实空态完成复审；不能自动证明 Stage 11-13 或整体项目复审完成。
- 当前没有真实持仓快照，因此投资收益、交易频率、风格和现金拖累不得显示伪造结论。
- 当前没有真实订阅候选文件或订阅规则运行结果，因此订阅优化不得生成假建议。
- 本轮不重装 app 入口；整体 pursuing goal 完成后再统一刷新 app 入口。
- 本轮不同步 GitHub；当前 worktree 存在 side thread 和历史混合改动，后续同步前必须先做 PFI-only diff review。
