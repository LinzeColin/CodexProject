# PFI v0.2.2 Stage 8 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 8；不复审 Stage 9-13，不做整体项目复审，不重装 app 入口，不同步 GitHub。

复审结论：Stage 8 本地运行 Diff 与 Impacted Metrics 合同通过；原目标测试中的构造财务记录已移除，运行差异输入改为读取真实 `MetaDatabase`、PFI 本地参数、分类、标签和汇率快照。
上线阻塞项：1

剩余阻塞项是全局 legacy 测试/样例/模拟数据审计仍未关闭；Stage 8 本轮已不再用手写交易、手写账本事件或虚构 Interconnection 分组作为验收依据。

## 复审范围

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S8-P1-T1` | 对原始数据、标准化交易、账本事件、interconnection、参数、分类、标签、汇率快照建立 hash。 | 通过 |
| `S8-P1-T2` | 本地运行时比较上一次 hash 与当前 hash。 | 通过 |
| `S8-P1-T3` | 输出变更项和未变更项，不联网、不调用外部 LLM。 | 通过 |
| `S8-P2-T1` | P0 核心指标仅包括净资产、生活现金、投资资产、消费总流出、生活消费、投资收益、现金流窗口、待复核数量、Interconnection 异常数量。 | 通过 |
| `S8-P2-T2` | P1 分析指标与 P0 分离，覆盖分类占比、标签视图、订阅、夜间、大额、商户集中度、投资风格、交易频率、费用拖累、现金拖累。 | 通过 |
| `S8-P2-T3` | P2 展示指标与 P0/P1 分离，覆盖图表排序、趋势图、辅助说明、tooltip、参数中心展示。 | 通过 |
| `S8-P2-T4` | 有 diff 时只重算受影响指标，小 diff 不触发全局重算。 | 通过 |
| `S8-P3-T1` | 无 diff 不联网、不生成 Codex ticket、不触发 LLM。 | 通过 |
| `S8-P3-T2` | 业务语义变化、公式逻辑变化、分类冲突、标签冲突、跨板块不一致、测试无法解释时才生成本地 Codex Review Ticket。 | 通过 |
| `S8-P3-T3` | 本地 ticket 使用中文模板，路径为 `PFI/review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md`。 | 通过 |

## 发现与修复

修复 1：Stage 8 验收不再依赖构造财务事实。

- 问题：`tests/test_v022_stage8_runtime_diff.py` 原来使用 `a-1`、`t-1`、`l-1`、`g-1`、`e-1` 等手写记录验证 hash/diff。这与用户最新硬约束冲突：PFI 交付和验收不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据或虚构财务事实。
- 修复：新增 `load_stage8_runtime_diff_inputs_from_canonical_sources()`，从 canonical 真实来源装载 Stage 8 依赖输入。
- 投资/关联边界：当前 `MetaDatabase/PFI` 只有真实支付宝 raw/processed 数据，没有真实 Interconnection 分组文件；因此 `interconnection` 使用中文真实空态 `暂无真实 Interconnection 分组文件，使用真实空态，不生成模拟分组。`

修复 2：运行差异输入改为真实依赖集合。

- 原始数据：`MetaDatabase/PFI/alipay_daily/raw`，当前真实 raw 文件数 `4`。
- 标准化流水：`MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`，当前真实记录数 `8815`。
- 账本事件：由真实支付宝标准化流水派生，不创建样例交易。
- 参数：`PFI/config/pfi_parameters.yaml`。
- 分类：`PFI/docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md` 与 Stage 5 分类/事件类型表。
- 标签：Stage 6 默认标签和标签规则。
- 汇率快照：`PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json`。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 无 diff 仍触发 agent 时停止 | 未触发；无 diff 报告不联网、不触发 LLM、不生成 ticket。 |
| 小 diff 导致全局重算时停止 | 未触发；标签差异只影响标签视图、辅助说明和 tooltip，不污染 P0 核心指标。 |
| 展示变化被误判为财务核心变化时停止 | 未触发；P0 核心指标、P1 分析指标、P2 展示指标边界分离。 |
| 缺少 hash 来源或 hash 覆盖不完整时停止 | 未触发；8 个依赖 hash key 均生成 64 位 sha256。 |
| 使用测试、样例或模拟数据作为正式验收时停止 | 未触发；Stage 8 目标测试已改为真实 `MetaDatabase` 来源或真实空态。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 8 模块 | `PFI/src/pfi_v02/stage_v022_runtime_diff.py` |
| 原 Stage 8 合同测试 | `PFI/tests/test_v022_stage8_runtime_diff.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage8.py` |
| Stage 8 验收报告 | `PFI/docs/pfi_v022/STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md` |
| Roadmap lock | `PFI/docs/pfi_v022/ROADMAP_LOCK.md` |
| 复核票据模板 | `PFI/review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md` |
| 真实 raw 数据 | `MetaDatabase/PFI/alipay_daily/raw` |
| 真实标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 最新验证结果

- Stage 8 目标 + 复审测试：`11 passed, 44 subtests passed`。
- Stage 0-8 v0.2.2 相关回归：`69 passed, 262 subtests passed`。
- Web shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`ok`。
- 真实浏览器矩阵：`/tmp/pfi_stage8_review_recheck/summary.json` 通过；桌面 15 个一级入口、7 个首页功能按钮、全局搜索 `8815/406`、策略实验室同路由、业务页反馈隔离、禁用词扫描、console errors 均通过；移动端 5 个关键入口可点击，水平溢出 `0px`。截图为 `/tmp/pfi_stage8_review_recheck/desktop.png` 和 `/tmp/pfi_stage8_review_recheck/mobile.png`。

## 剩余风险

- 本轮只证明 Stage 8 已按真实 MetaDatabase 流水、本地合同文件和真实空态完成复审；不能自动证明 Stage 9-13 或整体项目复审完成。
- PFI 仓库仍存在 legacy `demo/sample/synthetic/fixture/mock/fake/测试样例` 命中；后续不能只用完整 pytest 作为产品验收依据。
- 当前没有真实 Interconnection 分组文件；Stage 8 会记录真实空态，不生成模拟分组。
- 本轮不重装 app 入口；整体 pursuing goal 完成后再统一刷新 app 入口。
- 本轮不同步 GitHub；当前 worktree 存在 side thread 和历史混合改动，后续同步前必须先做 PFI-only diff review。
