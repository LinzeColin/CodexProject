# Stage 9 - 可视化与 UI/UX

版本：`v0.2.2 数据库治理`

本轮目标：生成本地可打开、中文可读、可点击追踪的 Stage 9 可视化审查交付物。Stage 9 不修改 v0.2.1 主 Web Shell UIUX 基线，不实现 Stage 10 报告、建议与复盘，不联网、不调用外部 LLM、不新增真实交易、自动投资、支付或券商提交能力。

## Phase 9.1 - 参数中心

| Task ID | 交付物 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S9-P1-T1` | 参数中心模型与 HTML 模块 | 可查看货币、汇率、分类、标签、阈值、公式、置信度、现金流窗口 | 本轮完成 |
| `S9-P1-T2` | 中文参数说明 | 每个参数显示中文名、当前值、作用、影响范围、是否可修改 | 本轮完成 |
| `S9-P1-T3` | 参数变更影响预览 | 修改阈值前显示可能影响的记录数、标签数、建议数、图表数 | 本轮完成 |

停止条件检查：用户可以人工检查参数；页面没有只显示代码变量名；影响预览使用本地 snapshot，不联网。

## Phase 9.2 - Interconnection 可视化

| Task ID | 交付物 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S9-P2-T1` | `docs/pfi_v022/INTERCONNECTION_MAP.md` | Mermaid 图覆盖 `source -> raw -> normalized -> group -> event -> ledger -> metrics -> UI` | 本轮完成 |
| `S9-P2-T2` | `web/interconnection-map.html` | 本地 HTML 可点击数据源、事件类型、分类、标签、公式、影响板块 | 本轮完成 |
| `S9-P2-T3` | 模块数据状态字段 | 每个图表显示数据来源、参数版本、公式版本、汇率快照、hash、缓存、是否需要重算 | 本轮完成 |

## Phase 9.3 - 现金流可视化

| Task ID | 交付物 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S9-P3-T1` | 现金流阶梯图 | 展示 7/21/30/60/90/180/360 天预测余额 | 本轮完成 |
| `S9-P3-T2` | 现金流瀑布图 | 展示当前现金、收入、退款、固定支出、弹性支出、信用卡、投资入金、投资回流 | 本轮完成 |
| `S9-P3-T3` | 储备金安全带 | 展示绿色、黄色、红色现金安全区间 | 本轮完成 |
| `S9-P3-T4` | 投资入金挤压图 | 显示投资入金对生活现金和储备金的影响 | 本轮完成 |

## Phase 9.4 - Metric Drilldown Debugger

| Task ID | 交付物 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S9-P4-T1` | 首页核心数字 drilldown | 本月消费、投资资产、现金流窗口显示来源记录、公式、参数、排除项、抵消项 | 本轮完成 |
| `S9-P4-T2` | 纳入/排除/调整展示 | 每个核心指标显示 included、excluded、adjusted 中文解释 | 本轮完成 |
| `S9-P4-T3` | 质量状态 | 显示置信度、匹配率、最后更新时间、计算耗时、缓存状态 | 本轮完成 |

## 本地 HTML 审查页

文件：`PFI/web/interconnection-map.html`

必须包含：

- 首页总览
- 参数中心
- Interconnection Map
- Metric Dependency Graph
- 消费分类与标签
- 投资模型
- 消费模型
- 现金流可视化
- Runtime Diff Dashboard
- Agent Review Queue
- 验收清单

每个模块的数据状态字段：

- 数据来源覆盖率
- 最近更新时间
- 参数版本
- 公式版本
- 汇率快照 ID
- ledger_hash
- interconnection_hash
- 是否存在未匹配记录
- 是否存在低置信记录
- 是否存在缓存
- 是否需要重算
- UI 指标是否与报告一致

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage9_visualization_uiux.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_stage9_visualization_uiux.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

浏览器验收：打开 `PFI/web/interconnection-map.html`，点击 `data-map-node` 和 `data-drilldown-metric`，确认右侧详情与 drilldown 内容变化；页面不得依赖 `http://`、`https://`、CDN、远程脚本或远程字体。

## 非目标

- Stage 10 报告、建议与复盘不在本轮实现。
- 不修改 v0.2.1 主 Web Shell UIUX 基线。
- 不联网、不调用外部 LLM、不生成真实 agent 任务。
- 不新增真实交易、自动投资、支付或券商提交。
