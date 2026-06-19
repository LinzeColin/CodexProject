# Finance Ledger Data Contract

底层数据库位置：

```text
data/finance_ledger/finance_ledger.sqlite
```

该库面向其他本地系统只读访问，例如赛事分析、量化回测、行研报告、个人预算和自动报告系统。写入入口只保留在本项目的导入脚本中。

## 导入命令

```bash
python3 scripts/import_ledger.py \
  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --output outputs/finance_ledger_20220605_20260603
```

如需永久保存自定义标签库，从 `reports/tag_library.html` 下载 JSON 后重跑：

```bash
python3 scripts/import_ledger.py \
  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --output outputs/finance_ledger_20220605_20260603 \
  --tag-library outputs/finance_ledger_20220605_20260603/reports/tag_library_custom.json
```

## 访问规则

- 下游系统默认只读连接 SQLite：`file:data/finance_ledger/finance_ledger.sqlite?mode=ro`。
- 下游系统也可以使用本地只读 HTTP API：`python3 scripts/serve_ledger.py --host 127.0.0.1 --port 8766`。
- 不要直接修改任何表；新的账单导入必须通过 `scripts/import_ledger.py`。
- 未确认的大额交易不会进入生产支出视图；读取复核队列请用 `v_pending_large_review`。
- 正式统计口径以 `v_production_transactions`、`v_cashflow_*`、`v_category_summary` 和 `v_risk_summary` 为准。
- 自动对账口径以 `v_reconciliation_checks`、`v_reconciliation_failures`、`v_reconciliation_summary` 为准；如果 `v_reconciliation_failures` 非空，下游系统必须把本轮账本降级为不可完全对账。
- 标签库和筛选组合以 `v_tag_library`、`v_tag_filter_presets` 为准；不要直接在 SQLite 里手改。需要调整时，优先在 `tag_library.html` 编辑标签与筛选组合，下载 `tag_library_custom.json` 后通过 `--tag-library` 回灌。

## 稳定视图

| 视图 | 用途 |
|---|---|
| `v_production_transactions` | 已进入生产统计的支出分摊明细。 |
| `v_classified_transactions_audit` | 全量逐笔分类审计明细，包含收入、支出、搬运、失败关闭等。 |
| `v_pending_large_review` | 单笔大额且尚未确认的复核队列。 |
| `v_cashflow_weekly` | 周度现金流和支出口径汇总。 |
| `v_cashflow_monthly` | 月度现金流和支出口径汇总。 |
| `v_cashflow_quarterly` | 季度现金流和支出口径汇总。 |
| `v_cashflow_half_year` | 半年度现金流和支出口径汇总。 |
| `v_cashflow_yearly` | 年度现金流和支出口径汇总。 |
| `v_category_summary` | 主类/子类金额、笔数和占比。 |
| `v_risk_summary` | 风险标签金额、笔数和占比。 |
| `v_control_plan` | 消费控制动作和预计可优化金额。 |
| `v_budget_pressure_radar` | 预算压力维度、目标上限、压力分、状态和控制动作；用于下期预算约束和复核优先级。 |
| `v_source_platform_summary` | 来源平台汇总，包含审计交易、源文件、生产支出、占比和待复核笔数。 |
| `v_data_trust_transactions` | 逐笔交易 Data Trust 状态，供下游系统判断是否可作为生产事实、复核候选或拒绝记录。 |
| `v_data_trust_sources` | 原始账单来源 Data Trust 状态、hash、归档路径和账期。 |
| `v_data_trust_summary` | Data Trust 状态分布，适合总系统健康看板读取。 |
| `v_reconciliation_checks` | 自动对账逐项检查，包含 `status`、`evidence_classification`、`decision_grade`、公式、证据路径和下一步动作。 |
| `v_reconciliation_failures` | 只读失败项视图；非空时不得把本轮账本声明为完全可追溯或完全可复核。 |
| `v_reconciliation_summary` | 自动对账状态分布，适合总系统健康看板读取。 |
| `v_entity_registry` | 稳定实体注册库，覆盖交易对方、来源平台、支付方式、来源文件、类别、机制和风险标签。 |
| `v_alias_map` | 原始名称到 `canonical_entity_id` 的别名映射，解决空白、大小写、全半角和符号差异。 |
| `v_entity_registry_summary` | 按实体类型汇总实体数、别名数、冲突数和需复核数。 |
| `v_entity_alias_conflicts` | 别名归一化后指向多个实体的冲突视图；非空时下游必须降级为 `Watch`。 |
| `v_evidence_decision_matrix` | 统一证据分层与决策等级矩阵，覆盖 Data Trust、Reconciliation、Manual Review、Entity、Alias、控制动作、来源平台、报告和固定查询入口。 |
| `v_evidence_decision_actionable` | 只读可用的 `Actionable` 证据项；适合作为下游系统默认输入白名单。 |
| `v_evidence_decision_watchlist` | `Watch`、`Reject` 或 `P0/P1` 项；适合作为人工复核和降级处理入口。 |
| `v_evidence_decision_summary` | 按层、证据等级、决策等级和状态汇总的健康看板输入。 |
| `v_review_status_summary` | 大额复核闭环状态，包含内置规则已确认、人工纳入、人工排除和仍待复核的笔数、金额、占比和生产影响。 |
| `v_review_decision_candidates` | 大额复核候选动作、置信度、建议分类和理由；仅用于辅助确认，不代表已入账。 |
| `v_review_decision_candidate_groups` | 按交易对方、建议分类和月份聚合的候选复核摘要。 |
| `v_manual_review_queue_audit` | 人工复核队列审计层，逐笔标注优先级、证据分层、决策等级、账本影响和下一步动作。 |
| `v_manual_review_queue_blockers` | P0/P1 待复核或无效确认项；非空时，下游系统不得把相关交易当作生产事实。 |
| `v_manual_review_queue_summary` | 人工复核队列状态和优先级摘要，适合总系统健康看板读取。 |
| `v_tag_library` | 持久化标签库，包含标签名、分组、颜色、说明、启停状态和来源。 |
| `v_tag_filter_presets` | 持久化标签组合预设，包含组合名、标签集合、任一/全部命中模式、启停状态和来源。 |
| `v_fact_expense_allocations` | 生产统计支出事实表，金额字段已转为数值，带 `date/month/year`。适合报表、预算、回测现金流出分析。 |
| `v_fact_transactions_audit` | 全量交易审计事实表，金额和小时字段已转为数值，包含分类、风险、机制和布尔标签。适合建模和异常检测。 |
| `v_fact_pending_large_review` | 大额待复核事实表，金额字段已转为数值。适合复核队列管理。 |
| `v_mart_daily_cashflow` | 日度现金流宽表：支出、收入、净现金流、账户搬运、待复核。适合量化回测或资金流时间序列。 |
| `v_mart_counterparty_monthly` | 月度交易对方支出汇总。适合行研、供应商/平台暴露分析。 |
| `v_mart_risk_monthly` | 月度风险标签暴露汇总。适合消费行为控制和风险趋势分析。 |

## 元数据表

| 表 | 用途 |
|---|---|
| `ledger_metadata` | schema version、生成时间、交易数、覆盖日期、输出目录、访问策略。 |
| `source_archives` | 原始 zip、CSV member、内容 hash、账期、解压后的稳定路径。 |
| `reconciliation_checks` | 自动对账基础表，对比来源文件、清洗数据、生产数据、Data Trust、复核隔离、HANDOFF 和关键文件状态。 |
| `entity_registry` | 实体注册基础表，保存稳定 `entity_id`、实体类型、证据等级、决策等级和需复核原因。 |
| `alias_map` | 别名映射基础表，保存 `alias_id`、原始别名、归一化别名、`canonical_entity_id` 和冲突状态。 |
| `entity_registry_summary` | 实体层摘要基础表，供总系统健康看板读取。 |
| `evidence_decision_matrix` | 证据分层和决策等级基础表，字段包括 `evidence_classification`、`decision_grade`、`risk_level`、`source_table`、`evidence_path` 和 `next_action`。 |
| `evidence_decision_summary` | 证据决策矩阵摘要表，供总系统健康看板和报告层读取。 |
| `tag_library` | 标签库基础表。 |
| `tag_filter_presets` | 标签组合预设基础表。 |
| `manual_review_status_summary` | 大额复核闭环状态基础表，和 dashboard/PDF 的复核状态面板同口径。 |
| `manual_review_decision_candidates` | 候选复核动作基础表，不进入生产统计。 |
| `manual_review_decision_candidate_groups` | 候选复核分组摘要基础表，不进入生产统计。 |
| `manual_review_queue_audit` | 人工复核队列审计基础表，标注 `PENDING_REVIEW`、`INVALID_DECISION`、`EMPTY` 等状态。 |
| `manual_review_queue_audit_summary` | 人工复核审计摘要表，按状态和优先级汇总。 |

## 当前四年账单导入结果

当前导入结果：

- 源文件：4 个支付宝 CSV，从本地私有账单源解压。
- 去重后交易：8808 笔。
- 实际交易日期：2022-06-06 至 2026-06-03。
- 生产统计分摊：5414 行。
- 大额待复核：92 行。

## 多源账单字段

- `source_platform`：账单平台，当前取值为 `alipay` 或 `wechat`。
- `source_file`：原始 CSV 或归档后 CSV 路径，用于审计和溯源。
- `v_fact_transactions_audit`、`v_fact_expense_allocations`、`v_fact_pending_large_review` 均暴露 `source_platform`。
- 生产统计口径不因平台变化而改变；支付宝/微信 CSV/XLSX 会先映射到统一交易 schema，再复用同一套分类规则、复核规则和报告管线。

## 查询示例

```bash
sqlite3 data/finance_ledger/finance_ledger.sqlite \
  "select period,total_expense,total_income,pending_review from v_cashflow_monthly order by period_start desc limit 6;"
```

```bash
sqlite3 data/finance_ledger/finance_ledger.sqlite \
  "select priority,dimension,current_pct,target_pct,pressure_score,status from v_budget_pressure_radar order by priority,cast(pressure_score as real) desc;"
```

```bash
python3 scripts/query_analysis.py \
  --db data/finance_ledger/finance_ledger.sqlite \
  transactions --month 2026-06 --limit 10 --json
```

固定问题模板查询，不开放任意 SQL：

```bash
python3 scripts/query_analysis.py \
  --db data/finance_ledger/finance_ledger.sqlite \
  ask "本月现金流怎么样" --json
```

## 本地只读 API

启动命令：

```bash
python3 scripts/serve_ledger.py \
  --db data/finance_ledger/finance_ledger.sqlite \
  --reports outputs/finance_ledger_20220605_20260603/reports \
  --host 127.0.0.1 \
  --port 8766
```

稳定 endpoint：

| Endpoint | 用途 |
|---|---|
| `/api/health` | 健康状态、schema、交易数和日期范围。 |
| `/api/metadata` | `ledger_metadata` 键值。 |
| `/api/stats?period=month&limit=12` | 周/月/季/半年/年度现金流汇总。 |
| `/api/categories?limit=30` | 主类/子类汇总。 |
| `/api/risks?limit=20` | 风险标签汇总。 |
| `/api/control-plan?limit=20` | 消费控制动作。 |
| `/api/review?limit=30` | 大额待复核队列。 |
| `/api/review-status` | 大额复核闭环状态。 |
| `/api/review?limit=30` | 当前仍待复核队列。 |
| `/api/review-candidates?limit=100` | 大额复核候选动作。 |
| `/api/review-candidate-groups?limit=100` | 大额复核候选分组摘要。 |
| `/api/source-platforms` | 数据源平台健康。 |
| `/api/daily-cashflow?limit=90` | 日度现金流。 |
| `/api/question-templates` | 固定只读问题模板清单。 |
| `/api/ask?q=本月现金流如何&limit=10` | 按问题模板查询，返回匹配模板、视图和结果。 |
| `/api/transactions?month=2026-06&limit=50` | 生产统计支出明细。 |
| `/reports/index.html` | 报告门户静态入口。 |

API 不开放任意 SQL、不写库，默认绑定 `127.0.0.1`。如需远程访问，必须另加认证、脱敏、访问日志和备份策略。

## 自动验收

导入后必须运行：

```bash
python3 scripts/validate_outputs.py \
  --output outputs/finance_ledger_20220605_20260603 \
  --db data/finance_ledger/finance_ledger.sqlite \
  --require-ledger
```

验收项：

- PDF 报告存在、非空且文件头为 PDF。
- HTML 入口和工作台存在。
- 交易行为分析页、标签库编辑页存在且包含标签组合和图表切换逻辑。
- `report_manifest.json` 登记正式报告和 HTML 入口。
- 主库必要表、稳定 views、`ledger_metadata`、`source_archives` 存在。
- `production_expense_allocations` 金额与 `summary_by_month.total_expense` 汇总一致。
- `manual_review_queue` 中的未确认大额交易不出现在 `production_expense_allocations`。
- `reconciliation_checks` 存在且行数大于 0，`status='fail'` 行数必须为 0。
- `manual_review_status_summary` 和 `v_review_status_summary` 存在，用于核对大额复核闭环状态。
- `manual_review_decision_candidates` 和分组摘要存在，但不会被生产统计读取。
- `manual_review_queue_audit`、`v_manual_review_queue_audit`、`v_manual_review_queue_blockers` 和 `v_manual_review_queue_summary` 存在，用于证明待复核项已经被标注证据等级、决策等级和下一步动作。
- `entity_registry`、`alias_map`、`entity_registry_summary` 以及 `v_entity_registry`、`v_alias_map`、`v_entity_alias_conflicts` 存在，用于证明交易对象和标签可以被跨系统稳定引用。
- `evidence_decision_matrix`、`evidence_decision_summary` 以及 `v_evidence_decision_matrix`、`v_evidence_decision_actionable`、`v_evidence_decision_watchlist`、`v_evidence_decision_summary` 存在，用于证明所有关键结论都有证据等级和决策等级。

## 下游系统推荐入口

| 使用场景 | 推荐视图 |
|---|---|
| 量化回测资金流 | `v_mart_daily_cashflow` |
| 行研/平台消费暴露 | `v_mart_counterparty_monthly` |
| 消费行为风险趋势 | `v_mart_risk_monthly` |
| 标签库和筛选组合 | `v_tag_library`、`v_tag_filter_presets` |
| 预算控制优先级 | `v_budget_pressure_radar` |
| 多源平台审计 | `v_source_platform_summary`、`v_fact_transactions_audit.source_platform`、`v_fact_expense_allocations.source_platform` |
| 数据可信度审计 | `v_data_trust_transactions`、`v_data_trust_sources`、`v_data_trust_summary` |
| 自动对账审计 | `v_reconciliation_checks`、`v_reconciliation_failures`、`v_reconciliation_summary` |
| 人工复核审计 | `v_manual_review_queue_audit`、`v_manual_review_queue_blockers`、`v_manual_review_queue_summary` |
| 实体注册与别名映射 | `v_entity_registry`、`v_alias_map`、`v_entity_registry_summary`、`v_entity_alias_conflicts` |
| 证据分层与决策等级 | `v_evidence_decision_matrix`、`v_evidence_decision_actionable`、`v_evidence_decision_watchlist`、`v_evidence_decision_summary` |
| 逐笔生产支出 | `v_fact_expense_allocations` |
| 全量审计与建模 | `v_fact_transactions_audit` |
| 大额交易复核 | `v_fact_pending_large_review` |
| 复核闭环状态 | `v_review_status_summary` |
| 复核候选批量处理 | `v_review_decision_candidates`、`v_review_decision_candidate_groups` |

## 待确认口径

- 其他系统是否需要把 `金融资金` 与投资回测资金流进一步拆分为现金、权益、基金、保险等账户维度。
- 支付宝/微信 CSV/XLSX 已通过统一 `source_platform` 字段接入；银行卡账单、券商流水后续仍需补充 `account_id`、`asset_type` 等账户/资产维度。
- 当前已提供本地只读 HTTP API；是否需要远程部署版仍待确认。
