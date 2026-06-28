# PFI v0.2.2 Stage 9 复审并解决

日期：2026-06-28 Australia/Sydney

本轮只复审解决 Stage 9；不复审 Stage 10-13，不做整体项目复审，不重装 app 入口，不同步 GitHub。

复审结论：Stage 9 可视化与 UI/UX 审查交付物保留为本地审查 HTML，不替代 v0.2.1 主 Web Shell；原先 HTML 与测试中的固定假金额、固定假匹配率、模拟耗时和旧构造计数参数已移除。Stage 9 现在从真实 `MetaDatabase`、Stage 8 依赖 hash、Stage 7 真实公式输入和真实空态派生可视化状态。
上线阻塞项：1

剩余阻塞项是全局 legacy 测试/样例/模拟数据审计仍未关闭；Stage 9 本轮已不再使用固定假金额、固定假匹配率或模拟耗时作为验收依据。

## 复审范围

| Task ID | 复审点 | 结论 |
| --- | --- | --- |
| `S9-P1-T1` | 参数中心覆盖货币、汇率、分类、标签、阈值、公式、置信度、现金流窗口。 | 通过 |
| `S9-P1-T2` | 每个参数显示中文名、当前值、作用、影响范围、是否可修改。 | 通过 |
| `S9-P1-T3` | 参数变更影响预览显示记录数、标签数、建议数、图表数。 | 通过 |
| `S9-P2-T1` | `INTERCONNECTION_MAP.md` 覆盖 `source -> raw -> normalized -> group -> event -> ledger -> metrics -> UI`。 | 通过 |
| `S9-P2-T2` | `web/interconnection-map.html` 可点击追踪数据源、事件类型、分类、标签、公式和影响板块。 | 通过 |
| `S9-P2-T3` | 每个图表和模块显示数据来源、参数版本、公式版本、汇率快照、hash、缓存和是否需要重算。 | 通过 |
| `S9-P3-T1` | 现金流阶梯图覆盖 `7/21/30/60/90/180/360`。 | 通过 |
| `S9-P3-T2` | 现金流瀑布图覆盖当前现金、收入、退款、固定支出、弹性支出、信用卡、投资入金、投资回流。 | 通过 |
| `S9-P3-T3` | 储备金安全带区分绿色、黄色、红色。 | 通过 |
| `S9-P3-T4` | 投资入金挤压图说明投资入金对生活现金和储备金的影响。 | 通过 |
| `S9-P4-T1` | 首页核心数字 drilldown 展示来源、公式、参数、排除项、抵消项。 | 通过 |
| `S9-P4-T2` | Drilldown 展示纳入、排除、调整。 | 通过 |
| `S9-P4-T3` | Drilldown 展示置信度、匹配率、最后更新时间、计算耗时、缓存状态；无真实测量时显示中文空态。 | 通过 |

## 发现与修复

修复 1：Stage 9 可视化不再展示固定假金额。

- 问题：`PFI/web/interconnection-map.html` 原来展示多个固定金额。这些不是当前真实持仓或账户余额。
- 修复：首页和现金流区域改为真实支付宝流水派生值或真实空态：真实流水 `8815` 条、消费总流出 `CNY 1,727,278.37`、生活消费 `CNY 1,545,600.44`、待复核 `406` 条；投资资产显示 `暂无真实持仓快照`。

修复 2：Stage 9 影响预览不再使用构造计数。

- 问题：`tests/test_v022_stage9_visualization_uiux.py` 原来使用构造计数字典。
- 修复：新增 `load_stage9_real_visualization_context()`，从 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`、Stage 8 dependency hash、Stage 7 真实公式输入和 Stage 6 默认标签库派生影响计数。
- 当前真实上下文：raw 文件 `4` 个、标准化流水 `8815` 条、待复核 `406` 条、默认标签 `56` 个、行动建议 `0` 条、Interconnection 分组 `0` 个。

修复 3：Stage 9 不再模拟匹配率或耗时。

- 问题：HTML/JS 原来写死多组匹配率和计算耗时。
- 修复：当前没有真实 Interconnection 分组文件，页面显示 `暂无真实 Interconnection 分组文件`；当前没有真实浏览器性能测量，页面显示 `本轮未测量，不显示模拟耗时`。

## 停止条件复核

| 停止条件 | 复核结果 |
| --- | --- |
| 用户无法人工检查参数时停止 | 未触发；参数中心保留 8 个参数域和中文说明。 |
| 只有代码变量名、没有中文解释时停止 | 未触发；可见内容为中文解释，必要英文专名保留中文语境。 |
| 参数变更无法预估影响时停止 | 未触发；影响预览使用真实上下文派生记录数、标签数、建议数、图表数。 |
| Interconnection 只有文字没有 graph 时停止 | 未触发；Mermaid 文档和 HTML 可点击节点均保留。 |
| HTML 图不可点击或不可追踪时停止 | 未触发；浏览器验收点击 `data-map-node` 与 `data-drilldown-metric`。 |
| 图表无法证明数据新鲜度时停止 | 未触发；每个模块显示真实数据来源、hash、快照、缓存和重算状态。 |
| HTML 依赖外部 CDN 或网络时停止 | 未触发；HTML 单文件无外部脚本、远程字体、CDN 或网络请求。 |
| UI 只显示结果、不显示公式、参数和数据来源时停止 | 未触发；drilldown 显示纳入、排除、调整、质量、参数和数据状态。 |
| 不得使用固定假金额、固定假匹配率或模拟耗时 | 未触发；相关固定值已移除。 |

## 证据来源

| 证据 | 路径 |
| --- | --- |
| Stage 9 模块 | `PFI/src/pfi_v02/stage_v022_visualization_uiux.py` |
| 原 Stage 9 合同测试 | `PFI/tests/test_v022_stage9_visualization_uiux.py` |
| 本轮复审测试 | `PFI/tests/test_v022_review_stage9.py` |
| Stage 9 验收报告 | `PFI/docs/pfi_v022/STAGE9_VISUALIZATION_UIUX.md` |
| 本地审查 HTML | `PFI/web/interconnection-map.html` |
| Interconnection Mermaid | `PFI/docs/pfi_v022/INTERCONNECTION_MAP.md` |
| 真实标准化流水 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` |

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage9_visualization_uiux.py tests/test_v022_review_stage9.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_review_stage9.py -q -p no:cacheprovider
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 最新验证结果

- Stage 9 目标 + 复审测试：`13 passed, 68 subtests passed`。
- Stage 0-9 v0.2.2 相关回归：`82 passed, 330 subtests passed`。
- Stage 9 本地 HTML 浏览器验收：`/tmp/pfi_stage9_review_recheck/stage9-html-summary.json` 通过；关系图节点 `12` 个、drilldown 指标 `3` 个、缺失项 `0`、禁用固定假值 `0`、外部网络请求 `0`、console/page errors `0`；截图 `/tmp/pfi_stage9_review_recheck/stage9-html.png`。
- 真实 8501 浏览器矩阵：`/tmp/pfi_stage9_review_recheck/summary.json` 通过；桌面 `15/15` 个一级入口可见且可点击、`7` 个首页功能按钮可点击、全局搜索 `8815/406` 命中真实支付宝流水、策略实验室一级入口和投资内入口同路由、设置反馈与业务页隔离、禁用可见词 `0`、console/page errors `0`；移动端关键入口 `5/5` 可点击且水平溢出 `0px`；截图 `/tmp/pfi_stage9_review_recheck/desktop.png` 和 `/tmp/pfi_stage9_review_recheck/mobile.png`。
- Web shell 语法：`node --check PFI/web/app/shell.js` 通过。
- 项目治理：`python3 scripts/validate_project_governance.py --project PFI` 返回 `errors 0 / warnings 0`。
- 空白检查：`git diff --check -- PFI` 通过。
- 8501 health：`curl -fsS http://127.0.0.1:8501/_stcore/health` 返回 `ok`。

## 剩余风险

- 本轮只证明 Stage 9 已按真实 MetaDatabase 派生值和真实空态完成复审；不能自动证明 Stage 10-13 或整体项目复审完成。
- 当前没有真实持仓快照，因此投资资产、收益和持仓图不得显示伪造数值。
- 当前没有真实 Interconnection 分组文件，因此匹配率和未匹配数量不得伪造。
- 本轮不重装 app 入口；整体 pursuing goal 完成后再统一刷新 app 入口。
- 本轮不同步 GitHub；当前 worktree 存在 side thread 和历史混合改动，后续同步前必须先做 PFI-only diff review。
