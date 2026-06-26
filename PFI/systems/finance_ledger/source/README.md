# 经济放血账单分析器

这是一个可重复运行的本地账本分析系统，用于把支付宝/微信 CSV/XLSX 账单按“经济放血机制”分类，并生成周报、月报、季报、半年报、年报、明细 CSV、SQLite、本地交互 dashboard、交易行为分析、标签库编辑、只读本地 API 和审计文件。当前形态是本地静态 UI + SQLite 数据库 + 可选本机只读 HTTP API，不是 online deployed webpage；后续如需在线部署，应另加认证、权限、脱敏、备份和访问日志。

## 快速运行

首次使用建议先安装依赖：

```bash
python3 -m pip install -e .
```

也可以使用项目级启动检查脚本，它会安装本地包并运行 Codex Workflow 体检：

```bash
./setup.sh
```

每次交接或开发前，先运行轻量体检：

```bash
python3 scripts/doctor.py
```

需要同时验证当前正式输出和 SQLite 主库时运行：

```bash
python3 scripts/doctor.py \
  --require-output \
  --write-audit outputs/finance_ledger_20220605_20260603/audit/codex_workflow_doctor.json \
  --write-report outputs/finance_ledger_20220605_20260603/reports/codex_workflow_contract_report.pdf
```

常用命令也已收敛到 `Makefile`：

```bash
make doctor
make doctor-output
make validate
make test
```

每周新增账单时，优先使用周更入口。它会自动导入共享 SQLite、重建 dashboard/PDF/复核工作台、运行验收，并写出本次运行 manifest：

```bash
python3 scripts/weekly_update.py \
  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --output outputs/finance_ledger_latest
```

如果不传 `--input`，脚本会在 `~/Downloads` 自动选择最新的支付宝/微信账单压缩包或账单文件。单笔 `>= ¥10,000` 且未确认的大额交易仍只进入复核队列；候选动作只用于下拉菜单加速，不会自动写入生产统计。

```bash
python3 scripts/run_analysis.py \
  --input "~/Downloads/<YOUR_ALIPAY_BILL>.csv" \
  --output outputs/alipay_analysis_latest
```

打开输出目录里的 `index.html` 进入报告门户；也可以直接打开 `operations_center.html` 查看周更、复核、标签回灌、报告验收和只读 API 的连续工作流，打开 `acceptance_workbench.html` 用 A/B/C 按钮完成用户验收矩阵，打开 `reference_model_lab.html` 查看 GitHub/开源参考模型吸收度和差距，打开 `dashboard.html` 查看总览，打开 `behavior_analysis.html` 做交易行为分析，打开 `transaction_explorer.html` 查询、钻取和导出逐笔明细，打开 `tag_library.html` 编辑标签库，打开 `review/review_workbench.html` 用下拉菜单处理大额复核；周报、月报、季报、半年报、年报会同时输出 `.md` 和 `.pdf`。

如果你已经确认过大额复核交易，带上确认表重跑：

```bash
python3 scripts/run_analysis.py \
  --input "~/Downloads/<YOUR_ALIPAY_BILL>.csv" \
  --review-decisions outputs/alipay_analysis_latest/review/review_decisions_template.csv \
  --output outputs/alipay_analysis_latest
```

如果你在 `tag_library.html` 下载了自定义标签库，带上标签库重跑即可永久写入 SQLite：

```bash
python3 scripts/import_ledger.py \
  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --output outputs/finance_ledger_20220605_20260603 \
  --tag-library outputs/finance_ledger_20220605_20260603/reports/tag_library_custom.json
```

生成可归档交付包：

```bash
python3 scripts/finalize_delivery.py \
  --base-url http://127.0.0.1:8772/ \
  --output-dir outputs/finance_ledger_20220605_20260603 \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --ensure-server \
  --json
```

正式收口脚本会依次运行真实浏览器验收、浏览器 freshness 校验、测试、输出校验和最终 ZIP 打包。底层 `scripts/package_delivery.py` 仍会检查 `audit/browser_visual_acceptance.json`：必须 18 项浏览器验收、0 失败，且验收文件不能早于最新 HTML 页面。只有临时调试包才直接运行 `package_delivery.py --skip-browser-acceptance`；正式交付不要跳过。

## 项目结构

- `configs/classification_rules.json`：分类规则。后续稳定口径主要改这个文件。
- `src/econ_bleed_analyzer/alipay.py`：支付宝/微信 CSV/XLSX 解析、统一交易 schema 和去重。
- `src/econ_bleed_analyzer/classifier.py`：规则匹配、风险标签、消费口径判断。
- `src/econ_bleed_analyzer/reports.py`：周期聚合、报告、dashboard、SQLite 和审计产物生成。
- `src/econ_bleed_analyzer/review.py`：大额复核确认表读取和生产统计回灌。
- `scripts/run_analysis.py`：命令行入口。
- `scripts/import_ledger.py`：把 ZIP/CSV/XLSX 账单导入共享底层 SQLite 数据库；CSV/XLSX 支持支付宝和微信账单，并刷新 ChatGPT 对照审计和目标完成度审计。
- `scripts/weekly_update.py`：每周重复运行入口，串联账单发现、导入、报告重建、验收和 manifest 输出。
- `scripts/finalize_delivery.py`：正式交付门禁，串联真实浏览器验收、freshness 校验、测试、输出校验和最终 ZIP 打包。
- `scripts/package_delivery.py`：把代码、配置、文档、正式报告、SQLite 和审计文件打成 ZIP 交付包；默认要求浏览器验收新鲜且无失败。
- `scripts/query_analysis.py`：只读 SQLite 查询入口，支持月份、周期汇总、分类、风险、交易明细、大额复核和控制动作查询。
- `scripts/serve_ledger.py`：本地只读 HTTP API，默认绑定 `127.0.0.1:8766`，提供固定 endpoint 和报告静态入口。
- `scripts/validate_outputs.py`：自动验收 PDF、HTML、SQLite、主库 views、金额口径和待复核隔离。
- `scripts/doctor.py`：Codex Workflow Layer 体检，检查 `AGENTS.md`、Run Contract、关键脚本、核心数据库表/视图和正式输出。
- `scripts/run_browser_visual_acceptance.py`：调用本机 Chrome 运行 9 个核心页面 x 桌面/移动视口的真实浏览器验收，并写入截图和 `audit/browser_visual_acceptance.json`。
- `scripts/audit_chatgpt_reference.py`：扫描或接收 ChatGPT 版本/代码/要求文件，生成 fail-closed 对照接入审计、差距矩阵 JSON/CSV/PDF。
- `scripts/audit_goal_completion.py`：把 active goal 拆成机器可检查证据项，生成目标完成度 JSON/CSV/PDF，并区分 `met`、`gap`、`needs_user_input`。
- `docs/reference_models.md`：开源参考项目、已吸收功能和暂未覆盖缺口。
- `docs/finance_ledger_data_contract.md`：供其他系统访问底层数据库的数据契约。
- `docs/codex_workflow_contract.md`：Codex 接手、验证、交接和 fail-closed 工作流契约。
- `docs/run_contract_template.md`：每轮修改结束时使用的 Run Contract 模板。
- `AGENTS.md`：项目级 Codex agent 操作规则和边界。
- `Makefile`：常用 doctor、validate、test、weekly、finalize 命令索引。
- `tests/`：基础回归测试。

## Codex Workflow Layer

本项目已补齐 Codex Workflow Layer v1。它的目标是让任何新对话或新 agent 接手时，能快速判断当前系统是否具备可靠交接、可重复验证和低风险运行入口。

工作流层不改变生产金额、分类规则、复核结果或报告统计公式。它只增加：

- 项目级规则：`AGENTS.md`
- 工作流契约：`docs/codex_workflow_contract.md`
- Run Contract 模板：`docs/run_contract_template.md`
- 本地体检：`scripts/doctor.py`
- 快速安装和体检：`setup.sh`
- 命令索引：`Makefile`
- 回归测试：`tests/test_codex_workflow.py`

如果 `scripts/doctor.py` 返回 `warn`，通常表示可继续但需要记录限制；如果返回 `fail`，不要声称交付、打包或跨系统同步已准备完成。

## PDF 报告

每次运行会生成这些 PDF：

- `weekly_report.pdf`
- `monthly_report.pdf`
- `quarterly_report.pdf`
- `half_year_report.pdf`
- `yearly_report.pdf`
- `annual_bill_cycle_report.pdf`
- `delivery_acceptance_report.pdf`
- `report_visual_inventory_report.pdf`
- `visual_quality_acceptance_report.pdf`
- `reference_model_benchmark_report.pdf`
- `chatgpt_reference_intake_report.pdf`
- `classification_rulebook_report.pdf`
- `user_manual_report.pdf`
- `requirements_traceability_report.pdf`
- `completion_audit_report.pdf`
- `goal_completion_audit_report.pdf`
- `user_acceptance_matrix_report.pdf`
- `spending_control_action_report.pdf`
- `manual_review_report.pdf`
- `manual_review_queue_audit_report.pdf`
- `entity_registry_report.pdf`
- `evidence_decision_matrix_report.pdf`
- `data_trust_audit_report.pdf`
- `reconciliation_audit_report.pdf`

如果本机默认 `python3` 没有安装 `Pillow`，请先安装依赖或使用 Codex 工作区 Python 运行。

正式报告位于 `outputs/.../reports/`，同名 Markdown 是辅助源文件。周期 PDF 包含现金流、累计净现金流轨迹、行为桶支出对照、预算压力雷达、主类占比、风险标签、经济放血机制图谱、风险控制矩阵、交易对方集中度、时间行为热力图、主类月度热力矩阵和周期趋势图表；UI 与可视化质量验收报告把页面矩阵、图表矩阵、布局颜色规则和交互控件做成正式 PDF；开源参考对标报告把 GitHub/开源项目、已吸收功能、增强项和缺口做成正式 PDF，`reference_model_lab.html` 则提供可筛选的参考模型吸收度图表和差距矩阵；表格内主类行会标色，子类行会留空主类列以模拟合并相邻同值格。

## Dashboard 可视化

`dashboard.html` 是本地静态交互页，不需要联网，当前包含：

- 月度现金流 SVG 折线图：支出、收入、待复核分离展示。
- 累计净现金流轨迹：最近 12 个月按收入减生产口径支出累计，判断资金是在回血还是失血。
- 主类占比 SVG 环形图：金额和两位小数占比直接标注。
- 主类/子类金额表：主类行标色，子类行合并式留空。
- 行为桶支出对照：真实消费、风险支出、可优化支出、社交支出、金融支出和公司个人混同支出按统一生产口径展示。
- 预算压力雷达：按默认目标上限展示大额复核、可优化、低复购、外卖即时零售、社交家庭、金融资金、信用工具和长期扣费的压力分。
- 风险标签条形图：用于识别信用工具、长期扣费、平台便利等行为暴露。
- 经济放血机制图谱：按机制聚合金额，识别社交场景、信用周转、投资冲动、平台便利等主要流失来源。
- 风险控制矩阵：把风险标签翻译为 P1/P2/P3、控制杠杆和下期动作。
- 数据源平台分布与导入健康：按 `source_platform` 展示平台、源文件、审计交易、生产支出和待复核状态。
- 周度和月度趋势条形图：用于追踪短周期变化。
- 交易对方 Top 12 与交易对方集中度：显示累计占比，识别主要现金流出口。
- 时间行为热力矩阵：按星期和凌晨/上午/下午/晚间定位高风险消费窗口。
- 主类月度热力矩阵：最近 12 个月按主类交叉展示金额，用于发现生活刚需、金融资金、社交家庭、可优化消费的结构漂移。
- 大额待复核和消费控制动作：直接连接复核工作台与行动计划。

## 交易行为分析和标签库

`behavior_analysis.html` 支持用标签组合选择分析范围，并切换图表呈现：

- 标签组合：可选择一个或多个标签，支持 `标签任一命中` 或 `标签全部命中`。
- 筛选范围：支持搜索、日期、主类、金额上下限。
- 图表类型：支持折线图、直方图、环形图和金额分布图。
- 分组方式：支持按月份、星期、小时、主类、交易对方聚合。
- 输出：可导出当前筛选范围的 CSV。

`tag_library.html` 是本地标签库编辑页：

- 可编辑标签名、分组、颜色、说明、启停状态。
- 可新增或删除自定义标签。
- 可新增、删除、启停筛选组合，并用下拉多选维护组合内标签。
- 可下载 `tag_library_custom.json`。
- 使用 `--tag-library` 重跑后，标签库和筛选组合会写入 `tag_library`、`tag_filter_presets` 表以及 `v_tag_library`、`v_tag_filter_presets` 只读视图，并被交易明细和行为分析页读取。

## 输出目录

- `index.html`：本地报告门户，汇总 KPI、工作台入口、PDF 报告、数据和审计入口。
- `operations_center.html`：本地运行控制台，按按钮式步骤组织周更、复核、标签回灌、报告验收和只读 API 启动。
- `reference_model_lab.html`：GitHub/开源参考模型工作台，支持搜索、许可筛选、吸收度筛选、吸收度条形图、功能环形图、差距矩阵和 CSV 导出。
- `reports/`：正式 PDF 报告、辅助 Markdown、`index.html`、`operations_center.html`、`reference_model_lab.html`、`dashboard.html`、`behavior_analysis.html`、`transaction_explorer.html`、`tag_library.html`。
- `reports/review_workbench.html`：复核工作台副本，方便和报告一起归档。
- `data/classified_transactions.csv`：逐笔分类审计明细。
- `data/production_expense_allocations.csv`：真正进入生产统计的支出分摊表。
- `data/spending_control_plan.csv`：按金额、占比、趋势和风险标签生成的消费控制动作表。
- `data/budget_pressure_radar.csv`：预算压力维度、目标上限、压力分、状态和控制动作。
- `data/source_platform_summary.csv`：按来源平台汇总审计交易、源文件、生产支出、占比和待复核笔数。
- `data/data_trust_transactions.csv`：逐笔 Data Trust Layer 审计表，区分 `PARSED_CANDIDATE`、`NEEDS_REVIEW`、`USER_CONFIRMED`、`RECONCILED`、`REJECTED` 等状态。
- `data/entity_registry.csv` / `data/alias_map.csv`：实体注册库和别名映射，给交易对方、来源平台、支付方式、来源文件、类别、机制和风险标签生成稳定 `entity_id`。
- `data/evidence_decision_matrix.csv` / `data/evidence_decision_summary.csv`：统一证据分层和决策等级矩阵，汇总 Data Trust、自动对账、人工复核、实体、别名、控制动作、来源平台、报告登记和固定查询入口。
- `audit/reconciliation_checks.csv` / `audit/reconciliation_checks.json`：自动对账层检查结果，覆盖来源 hash、清洗交易、Data Trust、生产分摊、月度汇总、复核隔离、HANDOFF 和关键文件状态。
- `audit/entity_registry.csv` / `audit/entity_registry.json` / `audit/alias_map.csv` / `audit/alias_map.json`：实体层机器可读审计文件。
- `audit/evidence_decision_matrix.csv` / `audit/evidence_decision_matrix.json`：下游系统统一读取的 Evidence Classification / Decision Grade 机器可读矩阵。
- `audit/manual_review_queue_audit.csv` / `audit/manual_review_queue_audit.json`：人工复核队列审计层，给每个待复核项标注优先级、证据分层、决策等级、账本影响和下一步动作。
- `data/manual_review_status_summary.csv`：大额复核闭环状态，包含内置规则已确认、人工纳入、人工排除和仍待复核的笔数、金额与占比。
- `data/manual_review_decision_candidates.csv`：大额复核候选动作、置信度、建议分类和理由；仅用于加速确认，不会自动入账。
- `data/manual_review_decision_candidate_groups.csv`：按交易对方、建议分类和月份聚合的候选复核摘要。
- `data/consumption.sqlite`：本地 SQLite 数据库，包含审计交易、生产分摊、分类汇总、风险标签、标签库、筛选组合、周期汇总、复核队列、复核状态和复核确认表。
- `review/manual_review_queue.csv`：仍未确认的大额交易。
- `review/manual_review_status_summary.csv`：给复核工作流使用的状态总览，和 SQLite `manual_review_status_summary` 表一致。
- `review/review_decision_candidates.csv`：候选复核决策，不是正式确认文件。
- `review/review_decision_candidate_groups.csv`：候选复核分组摘要，用于批量处理。
- `review/review_decisions_template.csv`：给你确认用的模板。
- `review/review_workbench.html`：下拉菜单式本地复核工作台，可下载 `review_decisions_confirmed.csv`。
- `review/review_decisions_loaded.csv`：本次运行读取到的有效确认。
- `review/review_decisions_invalid.csv`：确认表里无法识别的行。
- `audit/`：输入文件 hash、规则版本、运行清单、报告清单、假设和缺口。
- `audit/reference_models.json`：本次版本参考的开源项目和功能吸收矩阵。
- `audit/reference_ui_patterns.json` / `.csv`：开源项目启发的 UI/布局模式、落地页面、实现证据和复用边界。
- `audit/report_visual_inventory.json` / `.csv`：逐份周期 PDF 的可视化章节覆盖审计，证明周/月/季/半年/年/账期年报均含固定图表。
- `audit/browser_visual_acceptance.json`：本地浏览器验收结果，覆盖核心页面的桌面/移动视口、DOM 标记、图表尺寸、响应式 CSS、配色和横向溢出检查。
- `outputs/delivery/`：由 `scripts/package_delivery.py` 生成的 ZIP 交付包目录。

## Data Trust Layer

系统会在每次报告生成时写出 `data/data_trust_transactions.csv`、SQLite 表 `data_trust_transactions` 和正式 PDF `reports/data_trust_audit_report.pdf`。状态口径如下：

- `RAW_IMPORTED`：原始账单文件进入来源归档层，仅作为源证据。
- `PARSED_CANDIDATE`：交易已解析和分类，但尚未成为生产支出分摊事实。
- `NEEDS_REVIEW`：大额、默认规则或无法识别交易，必须人工复核。
- `USER_CONFIRMED`：用户复核文件已确认纳入或排除。
- `RECONCILED`：交易已进入生产分摊，可与月度汇总对账。
- `ARCHIVED`：来源文件已稳定归档并保留 hash。
- `REJECTED`：失败、关闭或明确排除的交易，不进入生产统计。

金额公式不变：生产支出仍以 `sum(production_expense_allocations.allocated_amount_cents) / 100` 为准；Data Trust 状态只用于审计、下游读取和人工复核优先级，不自动执行任何支付、投资或交易。

## Reconciliation Layer

系统会在共享主库写出 SQLite 表 `reconciliation_checks`，并生成正式 PDF `reports/reconciliation_audit_report.pdf`、机器可读 `audit/reconciliation_checks.csv` 和 `audit/reconciliation_checks.json`。

本层用于回答“当前账本是否能被下游系统安全读取为可对账事实”，不改变任何生产金额、分类或复核结果。核心检查包括：

- 来源文件存在且可校验时，`sha256(extracted_path) == source_archives.member_sha256`。
- `count(classified_transactions_audit) == count(data_trust_transactions)`。
- `sum(production_expense_allocations.allocated_amount_cents) / 100 == sum(summary_by_month.total_expense)`，容差 `0.05` 元。
- `manual_review_queue` 的 pending key 不得出现在 `production_expense_allocations.review_key`。
- `count(data_trust_transactions where data_trust_status='RECONCILED') == count(distinct production_expense_allocations.review_key)`。
- `HANDOFF.md` 必须存在，并尽量指向当前输出目录。

对账状态含义：

- `pass`：可作为当前事实证据读取。
- `warn`：证据不足或 fixture/旧库缺少字段，需要下游降级为观察，不阻断现有统计。
- `fail`：关键对账失败，不应把本次账本声明为完全可追溯或完全可复核。

## Manual Review Queue

系统会在每次报告生成时写出 `data/manual_review_queue_audit.csv`、`audit/manual_review_queue_audit.csv`、`audit/manual_review_queue_audit.json`、SQLite 表 `manual_review_queue_audit` / `manual_review_queue_audit_summary` 和正式 PDF `reports/manual_review_queue_audit_report.pdf`。

本层用于回答“哪些交易必须先人工确认，为什么，优先级是什么，确认前对账本有什么影响”。它只读取待复核队列、复核候选、Data Trust 和无效确认行，不改变生产金额、分类、报告总支出或复核确认逻辑。

核心口径：

- `queue_status=PENDING_REVIEW`：仍待人工确认，确认前保持隔离。
- `queue_status=INVALID_DECISION`：复核确认文件存在无效行，必须修正后重建。
- `priority=P0/P1/P2/P3`：按金额、Data Trust 状态和候选置信度决定复核优先级。
- `evidence_classification=OBSERVATION`：来自待复核队列的观察，不是已确认事实。
- `decision_grade=Watch`：只能进入复核观察，不能直接进入生产统计。
- `ledger_effect=blocked_until_manual_review`：确认前不进入生产支出事实表。

## Entity Registry / Alias Map

系统会在每次报告生成时写出 `data/entity_registry.csv`、`data/alias_map.csv`、`audit/entity_registry.csv`、`audit/entity_registry.json`、`audit/alias_map.csv`、`audit/alias_map.json`、SQLite 表 `entity_registry` / `alias_map` / `entity_registry_summary` 和正式 PDF `reports/entity_registry_report.pdf`。

本层用于回答“同一个交易对象、来源平台、类别或风险标签在不同文件和系统里应该如何稳定引用”。它只生成稳定 `entity_id` 和 `alias_id`，不改变交易分类、生产金额或报告口径。

核心口径：

- `entity_type=counterparty`：交易对方实体，来自账单字段，证据等级为 `FACT`。
- `entity_type=source_platform/payment_method/source_file`：来源、支付方式和文件实体，证据等级为 `FACT`。
- `entity_type=category/risk_tag/mechanism`：本地规则生成的分类实体，证据等级为 `INFERENCE`。
- `alias_map`：把原始名称、大小写、全半角、空白和符号归一化后映射到 `canonical_entity_id`。
- `v_entity_alias_conflicts`：别名归一化后指向多个实体时进入冲突视图，下游系统必须降级为 `Watch`。

## Evidence Classification / Decision Grade

系统会生成正式 PDF `reports/evidence_decision_matrix_report.pdf`，并写出 `audit/evidence_decision_matrix.csv`、`audit/evidence_decision_matrix.json`、`audit/evidence_decision_summary.csv`、`audit/evidence_decision_summary.json`、SQLite 表 `evidence_decision_matrix` / `evidence_decision_summary`。

本层用于回答“哪些结论是事实、哪些只是推断、哪些只能观察、哪些必须拒绝”。它统一使用：

- `evidence_classification=FACT`：可由文件、SQLite 表、hash、报告或审计文件直接验证。
- `evidence_classification=INFERENCE`：来自规则、标签、控制动作或别名归一化的推断。
- `evidence_classification=OBSERVATION`：仍需人工观察、复核或补证据。
- `evidence_classification=OPINION`：主观意见；当前不作为机器事实。
- `decision_grade=Actionable`：可作为只读下游输入。
- `decision_grade=Watch`：需要复核或观察。
- `decision_grade=Observe`：仅作背景。
- `decision_grade=Reject`：不得用于结论或下游决策。

该层不改变生产金额、分类、复核或周期报告口径；它只给总系统、PFIOS、行研系统和后续报告层提供可追溯的证据等级矩阵。

## 共享底层数据库

四年账单或多文件账单应导入到共享底层库：

```bash
python3 scripts/import_ledger.py \
  --input ~/Downloads/<YOUR_ALIPAY_OR_WECHAT_BILL>.zip \
  --ledger-db data/finance_ledger/finance_ledger.sqlite \
  --output outputs/finance_ledger_20220605_20260603
```

主库路径：

```text
data/finance_ledger/finance_ledger.sqlite
```

下游系统建议只读访问该库，优先读取稳定视图：

- `v_production_transactions`
- `v_classified_transactions_audit`
- `v_pending_large_review`
- `v_review_status_summary`
- `v_manual_review_queue_audit`
- `v_manual_review_queue_blockers`
- `v_manual_review_queue_summary`
- `v_cashflow_monthly` / `v_cashflow_yearly`
- `v_category_summary`
- `v_risk_summary`
- `v_control_plan`
- `v_budget_pressure_radar`
- `v_source_platform_summary`
- `v_data_trust_transactions`
- `v_data_trust_sources`
- `v_data_trust_summary`
- `v_reconciliation_checks`
- `v_reconciliation_failures`
- `v_reconciliation_summary`
- `v_entity_registry`
- `v_alias_map`
- `v_entity_registry_summary`
- `v_entity_alias_conflicts`
- `v_evidence_decision_matrix`
- `v_evidence_decision_actionable`
- `v_evidence_decision_watchlist`
- `v_evidence_decision_summary`
- `v_tag_library`
- `v_tag_filter_presets`
- `v_fact_expense_allocations`
- `v_fact_transactions_audit`
- `v_fact_pending_large_review`
- `v_mart_daily_cashflow`
- `v_mart_counterparty_monthly`
- `v_mart_risk_monthly`

详细字段和访问约束见 `docs/finance_ledger_data_contract.md`。

## 本地明细查询

`transaction_explorer.html` 是静态本地多维钻取页面，不需要启动服务。它分成两套数据：

- `生产统计`：只展示已经进入总支出、占比、报告和 SQLite 的支出分摊。
- `大额待复核`：只展示单笔 `>= ¥10,000` 且尚未确认的交易，不混入生产统计。

支持按交易对方/说明/风险标签搜索，搜索包含精确匹配、去符号模糊匹配和字符顺序模糊匹配；输入关键词后会反馈命中的交易对方、说明对象、分类、标签和命中字段。也支持按主类、子类、标签组合、日期、金额筛选。标签组合支持任一命中或全部命中，并读取 SQLite 持久化标签库。快捷按钮可查看 `1 万以上`、`信用工具`、`可优化消费`、`社交家庭`、`金融资金`，并导出当前筛选结果 CSV。筛选后会同步更新主类分布、风险标签、月份趋势和对手方排行，用于定位某一类支出的具体来源；明细列表可折叠，方便只看上方统计和反馈。

## 只读命令行查询

生成 SQLite 后，可以用固定查询命令快速检查，不开放任意 SQL：

```bash
python3 scripts/query_analysis.py \
  --db data/finance_ledger/finance_ledger.sqlite \
  stats --period month --limit 6
```

常用命令：

- `months`：查看数据库内有哪些月份。
- `stats --period month|week|quarter|half|year`：查看周期现金流汇总。
- `categories`：查看主类/子类金额和占比。
- `risks`：查看风险标签金额。
- `transactions --month 2026-06 --main-category 生活刚需 --risk-tag 餐饮日用`：查询生产统计明细。
- `review`：查看大额待复核队列。
- `control-plan`：查看消费控制动作。
- `ask "本月现金流怎么样"`：用固定只读问题模板查询，不开放任意 SQL。
- `--json`：输出 JSON，方便后续接入其他工具。

## 本地只读 API

如果赛事分析、量化回测、行研报告或其他本地系统不想直接连接 SQLite，可以启动本机只读服务：

```bash
python3 scripts/serve_ledger.py \
  --db data/finance_ledger/finance_ledger.sqlite \
  --reports outputs/finance_ledger_20220605_20260603/reports \
  --host 127.0.0.1 \
  --port 8766
```

常用 endpoint：

- `GET /api/health`：数据库、报告目录、schema、交易数和日期范围。
- `GET /api/stats?period=month&limit=12`：周期现金流。
- `GET /api/categories?limit=30`：主类/子类汇总。
- `GET /api/risks?limit=20`：风险标签汇总。
- `GET /api/control-plan?limit=20`：消费控制动作。
- `GET /api/review?limit=30`：大额待复核队列。
- `GET /api/review-status`：大额复核闭环状态。
- `GET /api/review-candidates?limit=100`：大额复核候选动作。
- `GET /api/review-candidate-groups?limit=100`：大额复核候选分组摘要。
- `GET /api/source-platforms`：数据源平台健康。
- `GET /api/daily-cashflow?limit=90`：日度现金流。
- `GET /api/question-templates`：可用的固定只读问题模板。
- `GET /api/ask?q=本月现金流如何&limit=10`：按问题模板返回查询结果；不会执行任意 SQL。
- `GET /api/transactions?month=2026-06&limit=50`：生产统计明细。
- `GET /reports/index.html`：报告门户静态文件。

该服务不开放任意 SQL、不写数据库，默认只绑定本机。若要开放到局域网或公网，需要先增加认证、脱敏、访问日志和备份策略。

## 自动验收

周更入口默认已经自动运行下面的验收。需要单独复查时再手动执行：

每次导入或周更后运行：

```bash
python3 scripts/validate_outputs.py \
  --output outputs/finance_ledger_20220605_20260603 \
  --db data/finance_ledger/finance_ledger.sqlite \
  --require-ledger
```

浏览器页面验收完成后，再检查浏览器审计 JSON：

```bash
python3 scripts/run_browser_visual_acceptance.py \
  --base-url http://127.0.0.1:8772/ \
  --output-dir outputs/finance_ledger_20220605_20260603 \
  --json

python3 scripts/verify_browser_acceptance.py \
  --audit outputs/finance_ledger_20220605_20260603/audit/browser_visual_acceptance.json \
  --html-root outputs/finance_ledger_20220605_20260603
```

验证器会检查：

- 所有正式 PDF 是否存在、非空且是 PDF。
- `index.html`、`reference_model_lab.html`、`dashboard.html`、`transaction_explorer.html`、`review_workbench.html` 是否存在并包含脚本。
- 周/月/季/半年/年/账期报告是否包含现金流、累计净现金流轨迹、行为桶支出对照、预算压力雷达、主类占比、风险标签、经济放血机制图谱、风险控制矩阵、交易对方集中度、时间行为热力图、主类月度热力矩阵和趋势公式。
- dashboard 是否包含月度现金流、累计净现金流轨迹、主类环形图、行为桶支出对照、预算压力雷达、经济放血机制图谱、风险控制矩阵、交易对方集中度、时间行为热力矩阵和主类月度热力矩阵。
- transaction explorer 是否包含筛选主类分布、筛选风险标签、筛选月份趋势和筛选对手方排行。
- `report_manifest.json` 是否登记所有正式入口。
- `report_visual_inventory.json`、`report_visual_inventory.csv` 和 `report_visual_inventory_report.pdf` 是否证明 6 份周期报告图表覆盖率为 100%。
- `reference_models.json`、`reference_source_log.json`、`reference_source_log.csv`、`reference_ui_patterns.json`、`reference_ui_patterns.csv` 是否存在并包含来源证据字段。
- reference model lab 是否包含开源项目搜索、吸收度图表、功能构成图、UI/布局模式矩阵、差距矩阵和 CSV 导出函数。
- `chatgpt_reference_audit.json`、`chatgpt_reference_audit.csv`、`chatgpt_reference_gap_matrix.csv` 和 `chatgpt_reference_intake_report.pdf` 是否存在；无 ChatGPT 对照文件时必须明确记录 missing，不伪造来源；有文件时生成 PDF/dashboard/UI/开源参考/分类/复核/标签库/SQLite/API/验收打包等维度的差距矩阵。
- `goal_completion_audit.json`、`goal_completion_audit.csv` 和 `goal_completion_audit_report.pdf` 是否存在；目标完成度审计必须明确哪些项已由证据证明，哪些仍需用户验收或 ChatGPT 对照文件。`audit/user_acceptance_decisions.json` 只有在 `final_acceptance=A` 且所有验收项均为 `A` 时，才会让“最终目标满足用户预期”进入 `met`；存在 `B/C`、无效 JSON 或缺少最终验收项时一律保留为 `needs_user_input`。
- `reconciliation_checks.json`、`reconciliation_checks.csv` 和 `reconciliation_audit_report.pdf` 是否存在；真实账本中 `reconciliation_checks.status='fail'` 必须为 0。
- SQLite 必要表和共享主库 views 是否存在。
- 生产统计分摊金额是否等于月度总支出汇总。
- 大额待复核交易是否没有混入生产统计。
- `verify_browser_acceptance.py` 会检查 9 个核心页面 x 桌面/移动视口的浏览器验收结果是否为 18 项、0 失败；带 `--html-root` 时还会检查浏览器验收文件不能早于最新 HTML 页面，避免旧验收误覆盖新构建。

任一关键检查失败时命令返回非零状态。

## 大额复核闭环

单笔 `>= ¥10,000` 的支出默认只进入 `review/manual_review_queue.csv`，不进入生产统计、分类占比和总支出。你确认后，把 `review/review_decisions_template.csv` 另存为自己的确认表并填写：

- `decision`：填 `include` 表示纳入生产统计，填 `exclude` 表示确认排除且不再待复核。
- `main_category` / `sub_category`：最终归属分类。
- `allocation_pct`：分摊比例。单笔拆分时复制同一个 `review_key` 多行，例如 `50`、`25`、`25`。
- `allocation_amount`：也可以填固定分摊金额；和比例二选一即可。
- `risk_tags`：用 `|` 分隔；为空时沿用系统原始风险标签。
- `note`：确认说明。

确认后带 `--review-decisions` 重跑，所有周报/月报/季报/半年报/年报、dashboard、SQLite 和审计文件都会更新。

也可以打开 `review/review_workbench.html` 用下拉菜单处理，尽量不手填自由文本：

- `复核决定`：下拉选择 `纳入统计`、`排除` 或保持未选择。
- `主类/子类`：下拉选择现有分类体系里的分类组合，保持分类简洁一致。
- `风险标签`：下拉选择已有风险标签，避免自由文本漂移。
- `筛选`：按搜索、建议分类、复核状态、最小金额和排序缩小当前工作集。
- `应用到当前筛选`：把批量决定、批量主类/子类和批量风险标签一次应用到当前筛选结果。
- `分组矩阵`：按交易对方、建议分类或月份聚合当前筛选结果，整组执行按建议纳入、套用批量栏、50/25/25 拆分或排除。
- `影响预览`：实时显示当前筛选金额、已决策笔数、纳入影响金额和仍未决策金额。
- `候选决策`：系统按商户/机构/个人转账特征生成建议纳入或保持人工复核，并标注 high/medium/low 置信度；点击套用候选后仍需下载确认 CSV 并回灌才会进入生产统计。
- `50/25/25 拆分`：作为特殊辅助按钮，生成教育医疗 50%、住房缴费 25%、餐饮日用 25% 三行确认，适合家庭/共同支出类大额。

复核状态会同步写入 `data/manual_review_status_summary.csv`、SQLite `manual_review_status_summary` 表和 `v_review_status_summary` 视图；dashboard 与每份 PDF 报告的“大额复核闭环状态”面板读取同一口径。当前仍待复核的金额继续隔离，不进入生产统计。
- `下载复核确认 CSV`：生成可直接传给 `--review-decisions` 的确认表。

## 当前统计口径

- `总支出`：生产统计口径下的所有支出分摊，金融资金参与总支出占比；未确认大额支出不计入。
- `真实消费`：生活刚需、可优化消费、社交家庭等实际现金流消费视角；公司个人混同支出进入对应主类/子类后再提示核对。
- `风险支出`：行为控制视角，所有支出都有风险标签；风险标签可与主类/子类重叠。
- `可优化支出`：高频小额、平台便利溢价、低复购价值、部分长期订阅等。
- `金融资金`：花呗/信用借还、基金买入、保险、理财、备用金等作为主类参与总支出占比；基金卖出/赎回计收入。
- `账户搬运`：余额宝转入转出、银行卡转账、提现、账户存取等，进入现金流视图但不计入支出占比。
- 百分比：主类占比 = 主类金额 / 本期总支出金额；子类占比 = 子类金额 / 所属主类金额；统一保留两位小数。

这些口径会写入 `audit/assumptions.json`，后续可以通过分类规则和复核确认表逐步校准。

## 消费控制动作

每份 PDF 报告都会生成“消费控制动作”表，字段包括：

- `优先级`：P0 为必须先处理的大额复核；P1 为下期应立即控额的主类/子类；P2 为需要制度化约束的风险机制。
- `触发证据`：金额、占比、风险标签或趋势变化。
- `建议动作`：下期执行动作，例如设置上限、延迟购买、固定投资窗口、订阅清理。
- `建议上限` / `预计可优化`：按当前期金额自动估算，进入 `data/spending_control_plan.csv` 和 SQLite 的 `spending_control_plan` 表。

## 每周持续更新

把新的支付宝 CSV 下载到本地后，重新运行命令即可。也可以一次传入多个文件：

```bash
python3 scripts/run_analysis.py --input data/*.csv --output outputs/alipay_analysis_latest
```

系统会按交易订单号、时间、金额和方向去重。
