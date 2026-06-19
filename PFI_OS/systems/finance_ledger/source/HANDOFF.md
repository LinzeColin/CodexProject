# HANDOFF

## Current Goal

把经济放血账单分析能力交付为可重复运行的本地软件工程项目：四年账单入库、固定分类口径、周期 PDF、dashboard、本地交互 UI、标签库、复核工作台、SQLite/API、浏览器验收和 ZIP 交付。

## Current State

- 当前形态：本地静态 UI + SQLite 数据库 + 可选本机只读 HTTP API，不是 online deployed webpage。
- 最新输出目录：`outputs/finance_ledger_20220605_20260603`
- 最新交付包：`outputs/delivery/economic_bleed_delivery_20260605_151300.zip`
- 2026-06-05 system upgrade continuation：已完成消费分析系统 Data Trust Layer v1。新增逐笔可信度审计表 `data_trust_transactions`、来源可信度表 `data_trust_sources`、只读视图 `v_data_trust_transactions` / `v_data_trust_sources` / `v_data_trust_summary`，并生成正式 PDF `outputs/finance_ledger_20220605_20260603/reports/data_trust_audit_report.pdf`。本层不改变生产金额、分类、复核和报告口径，只用于审计、下游只读读取和人工复核优先级。
- 2026-06-05 system upgrade continuation：已完成消费分析系统 Reconciliation Layer v1。新增自动对账表 `reconciliation_checks`、只读视图 `v_reconciliation_checks` / `v_reconciliation_failures` / `v_reconciliation_summary`、机器可读审计 `outputs/finance_ledger_20220605_20260603/audit/reconciliation_checks.json` / `.csv`，并生成正式 PDF `outputs/finance_ledger_20220605_20260603/reports/reconciliation_audit_report.pdf`。本层对比来源 hash、清洗交易、Data Trust、生产分摊、月度汇总、复核隔离、HANDOFF 和关键文件状态；不改变生产金额、分类、复核或报告口径。
- 2026-06-05 system upgrade continuation：已完成消费分析系统 Manual Review Queue v1。新增人工复核队列审计表 `manual_review_queue_audit`、摘要表 `manual_review_queue_audit_summary`、只读视图 `v_manual_review_queue_audit` / `v_manual_review_queue_blockers` / `v_manual_review_queue_summary`、机器可读审计 `outputs/finance_ledger_20220605_20260603/audit/manual_review_queue_audit.json` / `.csv`，并生成正式 PDF `outputs/finance_ledger_20220605_20260603/reports/manual_review_queue_audit_report.pdf`。本层只读取待复核队列、复核候选、Data Trust 和无效确认行，标注优先级、证据分层、决策等级、账本影响和下一步动作；不改变生产金额、分类、复核或报告口径。
- 2026-06-05 system upgrade continuation：已完成消费分析系统 Entity Registry / Alias Map v1。新增实体注册表 `entity_registry`、别名映射表 `alias_map`、摘要表 `entity_registry_summary`、只读视图 `v_entity_registry` / `v_alias_map` / `v_entity_registry_summary` / `v_entity_alias_conflicts`、机器可读审计 `outputs/finance_ledger_20220605_20260603/audit/entity_registry.json` / `.csv` 和 `alias_map.json` / `.csv`，并生成正式 PDF `outputs/finance_ledger_20220605_20260603/reports/entity_registry_report.pdf`。本层统一交易对方、来源平台、支付方式、来源文件、类别、机制和风险标签的稳定 `entity_id` / `alias_id`；不改变生产金额、分类、复核或报告口径。
- 2026-06-05 system upgrade continuation：已完成消费分析系统 Evidence Classification / Decision Grade v1。新增统一证据决策矩阵表 `evidence_decision_matrix`、摘要表 `evidence_decision_summary`、只读视图 `v_evidence_decision_matrix` / `v_evidence_decision_actionable` / `v_evidence_decision_watchlist` / `v_evidence_decision_summary`、机器可读审计 `outputs/finance_ledger_20220605_20260603/audit/evidence_decision_matrix.json` / `.csv` 和 `evidence_decision_summary.json` / `.csv`，并生成正式 PDF `outputs/finance_ledger_20220605_20260603/reports/evidence_decision_matrix_report.pdf`。本层统一 Data Trust、Reconciliation、Manual Review、Entity Registry、Alias Map、控制动作、来源平台、报告登记和固定查询入口的 `FACT` / `INFERENCE` / `OBSERVATION` / `OPINION` 与 `Actionable` / `Watch` / `Observe` / `Reject`；不改变生产金额、分类、复核或报告口径。
- 2026-06-06 system upgrade continuation：已完成消费分析系统 Codex Workflow Layer v1。新增项目级 `AGENTS.md`、Run Contract 模板、工作流契约、`doctor.py`、`setup.sh`、`Makefile` 和工作流测试；生成正式 PDF `outputs/finance_ledger_20220605_20260603/reports/codex_workflow_contract_report.pdf` 与机器可读审计 `outputs/finance_ledger_20220605_20260603/audit/codex_workflow_doctor.json`。本层用于统一每轮 Run 的读取顺序、验证门禁、失败降级、回滚说明和交接规则；不改变生产金额、分类、复核或报告口径。
- 新增用户验收矩阵：`outputs/finance_ledger_20220605_20260603/reports/user_acceptance_matrix_report.pdf`
- 新增用户验收工作台：`outputs/finance_ledger_20220605_20260603/reports/acceptance_workbench.html`，已支持 A/B/C 本地持久化、ChatGPT 对照文件粘贴/选择/导出和审计命令生成
- 新增 ChatGPT 对照摄取报告：`outputs/finance_ledger_20220605_20260603/reports/chatgpt_reference_intake_report.pdf`
- 新增 ChatGPT 对照审计：`outputs/finance_ledger_20220605_20260603/audit/chatgpt_reference_audit.json`
- 新增 ChatGPT 对照差距矩阵：`outputs/finance_ledger_20220605_20260603/audit/chatgpt_reference_gap_matrix.csv`
- 新增目标完成度审计：`outputs/finance_ledger_20220605_20260603/reports/goal_completion_audit_report.pdf`
- 新增开源参考模型工作台：`outputs/finance_ledger_20220605_20260603/reports/reference_model_lab.html`，已包含开源参考吸收度、功能构成、差距边界和 UI/布局模式吸收矩阵
- 新增 UI/布局模式审计：`outputs/finance_ledger_20220605_20260603/audit/reference_ui_patterns.json`、`outputs/finance_ledger_20220605_20260603/audit/reference_ui_patterns.csv`
- 新增报告可视化覆盖审计：`outputs/finance_ledger_20220605_20260603/reports/report_visual_inventory_report.pdf`、`outputs/finance_ledger_20220605_20260603/audit/report_visual_inventory.json`、`outputs/finance_ledger_20220605_20260603/audit/report_visual_inventory.csv`
- 新增微信接入契约：`docs/weixin_ingestion_contract.md`
- 新增系统结构内审 PDF：`outputs/finance_ledger_20220605_20260603/reports/system_structure_internal_audit_20260605.pdf`
- 微信候选入箱已接入现有脚本：`scripts/weixin_alipay_fund_ingest.py` 现在支持文本-only 归档和 `weixin_intake_items` 通用候选状态表，复用微信 API 项目，不复制机器人。

## Decisions

- 22:00-06:00 睡眠窗口内不发散追问；可本地推进的工作继续执行，待用户判断事项集中到验收矩阵。
- 平台级权限请求不能被业务授权绕过；优先使用已批准命令和本地 headless 验收，确实受沙箱限制时才集中请求。
- 大额待复核交易仍隔离，不自动进入生产统计；确认后用复核 CSV 回灌并重建报告。
- 用户验收现在严格 fail-closed：`audit/user_acceptance_decisions.json` 只有在 `final_acceptance=A` 且所有验收项均为 `A` 时，目标完成度审计才会把“最终目标满足用户预期”标记为 `met`；任一 `B/C`、无效 JSON 或缺少最终验收项都保持 `needs_user_input`。

## Files Changed

- `src/econ_bleed_analyzer/reports.py`
- `src/econ_bleed_analyzer/evidence_decision.py`
- `src/econ_bleed_analyzer/manual_review_audit.py`
- `src/econ_bleed_analyzer/entity_registry.py`
- `src/econ_bleed_analyzer/validate_outputs.py`
- `src/econ_bleed_analyzer/ledger.py`
- `docs/reference_models.md`
- `docs/finance_ledger_data_contract.md`
- `scripts/weekly_update.py`
- `scripts/audit_chatgpt_reference.py`
- `scripts/audit_goal_completion.py`
- `scripts/import_ledger.py`
- `scripts/finalize_delivery.py`
- `scripts/package_delivery.py`
- `scripts/run_browser_visual_acceptance.py`
- `scripts/verify_browser_acceptance.py`
- `tests/test_validate_outputs.py`
- `tests/test_manual_review_audit.py`
- `tests/test_entity_registry.py`
- `tests/test_evidence_decision.py`
- `tests/test_ledger.py`
- `tests/test_chatgpt_reference_audit.py`
- `tests/test_goal_completion_audit.py`
- `tests/test_finalize_delivery.py`
- `tests/test_browser_acceptance.py`
- `tests/test_package_delivery.py`
- `tests/test_weixin_intake_ingest.py`
- `AGENTS.md`
- `docs/codex_workflow_contract.md`
- `docs/run_contract_template.md`
- `scripts/doctor.py`
- `setup.sh`
- `Makefile`
- `tests/test_codex_workflow.py`
- `README.md`
- `HANDOFF.md`

## Verification

- 浏览器验收：18/18 checked, 0 failures, `audit/browser_visual_acceptance.json` generated at `2026-06-05T12:54:37+1000`，已晚于最新 HTML
- 测试：`49 passed in 107.57s`（finalize 内）；目标审计严格用户验收测试 `4 passed in 32.94s`，相关门禁测试 `11 passed in 0.15s`
- 输出验收：通过，`validate_outputs.py` 123 ok / 0 warn / 0 fail，新增 `report_visual_inventory.json/csv/pdf`、`reference_ui_patterns.json/csv`、`chatgpt_reference_gap_matrix.csv`、`goal_completion_audit.json/csv/pdf` schema 和验收工作台 ChatGPT 接入标记均通过
- Browser 插件实测：`acceptance_workbench.html` 经本机 HTTP 打开后，ChatGPT 文本区、文件入口、审计命令区均存在；填入对照文本后能生成 `audit_chatgpt_reference.py` 与 `finalize_delivery.py` 命令；无横向溢出
- Browser 插件实测：`reference_model_lab.html` 经本机 HTTP 打开后，UI/布局模式矩阵 7 张卡片可见，dashboard 和复核模式可搜索/呈现，无横向溢出
- ChatGPT 对照审计：`status=missing`，`candidate_count=0`，`gap_summary={'blocked_missing_chatgpt_source': 10}`，策略为 `fail_closed_no_reference_fabrication`；用户已确认该 ZIP 是其他系统参考包，不作为本消费系统硬性 ChatGPT 对照源，验收矩阵第 8 项为 A
- 目标完成度审计：`goal_complete=False`，机器可验证项 8/8 已满足，剩余 1 项为用户最终验收 `final_acceptance=B`，表示需要一轮局部精修后再关闭
- 报告可视化覆盖审计：6 份周期报告全部通过，`pass_count=6`、`gap_count=0`、每份必需 14 个图表章节，覆盖率 100.00%；账期年报已补月度趋势图
- 打包：通过，最新 ZIP `outputs/delivery/economic_bleed_delivery_20260605_125852.zip`，大小 27,900,168 bytes，包含 274 个文件
- 清理：本轮临时启动的本地 HTTP 服务已停止，`lsof -nP -iTCP:8772 -sTCP:LISTEN` 无监听进程
- 微信 API 状态：OpenClaw Gateway loopback `127.0.0.1:18789` running，connectivity probe OK；Weixin channel enabled/configured/running
- 微信候选入箱验证：`tests/test_weixin_intake_ingest.py tests/test_bill_import.py tests/test_package_delivery.py tests/test_finalize_delivery.py` 16 passed in 7.86s
- 系统结构内审 PDF：`outputs/finance_ledger_20220605_20260603/reports/system_structure_internal_audit_20260605.pdf` 已生成，321 KB
- Manual Review Queue v1 验证：`scripts/weekly_update.py` 重建输出成功，`validation: ok=168 warn=0 fail=0`；`scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger` 全 OK；新增 PDF `manual_review_queue_audit_report.pdf` 624,098 bytes；新增 SQLite 审计表 92 行、摘要表 2 行、P1/P2 分布为 P1=30、P2=62，`v_manual_review_queue_blockers` 30 行。测试：相关测试 23 passed，全量测试 `64 passed in 47.11s`。本轮未重建正式 ZIP，因为目标是 Manual Review Queue 增量，不触发最终打包门禁。
- Entity Registry / Alias Map v1 验证：`scripts/weekly_update.py` 重建输出成功，`validation: ok=185 warn=0 fail=0`；`scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger` 全 OK；新增 PDF `entity_registry_report.pdf` 907,191 bytes；新增 `entity_registry` 1674 行、`alias_map` 1674 行、`entity_registry_summary` 7 行，`v_entity_alias_conflicts` 0 行。实体类型分布：category=19、counterparty=1492、mechanism=20、payment_method=122、risk_tag=16、source_file=4、source_platform=1。测试：定向测试 16 passed，全量测试 `66 passed in 49.49s`。本轮未重建正式 ZIP，因为目标是 Entity Registry / Alias Map 增量。
- Evidence Classification / Decision Grade v1 验证：`scripts/weekly_update.py` 重建输出成功，`validation: ok=201 warn=0 fail=0`；`scripts/validate_outputs.py --output outputs/finance_ledger_20220605_20260603 --db data/finance_ledger/finance_ledger.sqlite --require-ledger` 全 OK；新增 PDF `evidence_decision_matrix_report.pdf` 688,709 bytes；新增 `evidence_decision_matrix` 12,323 行、`evidence_decision_summary` 16 行，`v_evidence_decision_watchlist` 541 行。决策等级分布：Actionable=8613、Observe=3169、Watch=272、Reject=269；证据等级分布：FACT=7268、INFERENCE=4850、OBSERVATION=205。测试：定向测试 `tests/test_evidence_decision.py tests/test_ledger.py tests/test_validate_outputs.py` 6 passed，全量测试 `68 passed in 29.17s`。本轮未重建正式 ZIP，因为目标是 Evidence/Decision 增量，不触发最终打包门禁。
- Codex Workflow Layer v1 验证：系统 `python3` 缺少 `pytest`，已改用 Codex bundled Python `<CODEX_BUNDLED_PYTHON>`。语法检查 `py_compile scripts/doctor.py tests/test_codex_workflow.py` 通过；`scripts/doctor.py --require-output --write-audit ... --write-report ... --json` 输出 `37 ok / 1 warn / 0 fail`，唯一 warning 为项目内未发现升级总报告或 taskpack 本地副本；`scripts/validate_outputs.py --require-ledger --json` 输出 `201 ok / 0 warn / 0 fail`；定向测试 `tests/test_codex_workflow.py tests/test_weekly_update.py tests/test_validate_outputs.py` 7 passed；全量测试 `tests` 71 passed；`make doctor` 与 `make validate` 均通过。已清理 `__pycache__`、`.pytest_cache` 和临时 pycache。

## Open Issues

- 当前工作区仍未发现单独的 ChatGPT 版本/代码/要求文件；如用户要求严格逐项对照，需要补充该文件后再审计。审计脚本和验收工作台现已能在补文件后生成需求关键词命中、实现状态、证据路径和下一步动作的差距矩阵。
- “满足我的预期”仍是用户主观验收项；工程门禁已通过，但总目标是否关闭需用户按验收矩阵确认。
- 当前目录不是 Git 仓库，无法提供 `git status` 或 commit 级 diff；以文件系统产物和审计报告作为交付证据。
- Codex Workflow doctor 当前有 1 个非阻塞 warning：项目目录内没有发现升级总报告或 `system_upgrade_taskpack` 本地副本；当前权威来源为 active goal、`HANDOFF.md`、`AGENTS.md` 和真实文件状态。

## Next Steps

- 用户打开 `acceptance_workbench.html` 或 `user_acceptance_matrix_report.pdf`，按 A/B/C 选择是否接受当前工程基线、局部精修或补 ChatGPT 对照文件；也可在工作台粘贴/选择 ChatGPT 对照内容并导出 `chatgpt_reference_requirements.md`。
- 用户可打开 `reference_model_lab.html` 查看 GitHub/开源参考模型、吸收度、已实现功能和剩余差距。
- 后续每周新增账单时，优先运行 `scripts/weekly_update.py`，复核确认后再跑 `scripts/finalize_delivery.py`。
- 系统升级下一轮建议：进入消费分析系统 Report Layer Manifest Integration v1，把新增工作流 PDF/doctor 审计纳入正式报告索引和交付包策略；仍保持不改生产金额口径。
- 系统升级下一轮建议：开始 AI-Research-System Data Trust Layer v1，按同一标准补齐来源可信度、证据等级、人工复核和跨系统只读同步契约。

## Boundaries

- 不自动执行支付、投资、转账、交易或真实资金操作。
- 不开放远程部署、认证、多用户和公网访问，除非另起安全设计任务。

## System Coordination ACK 2026-06-05

- 当前 active goal：经济放血账单分析系统交付，覆盖账单分类、经济放血机制、周期 PDF、dashboard、本地 UI、标签库、复核工作台、SQLite/API、浏览器验收和 ZIP 交付。
- 当前工程状态：机器可验证项 7/7，目标审计 `goal_complete=false`；阻塞项为缺少 ChatGPT 对照源文件和用户 A/B/C 最终验收。
- 对外同步边界：本系统向 PFIOS/ResearchBus 同步消费行为状态、现金流视图、分类/风险标签、待复核隔离和周期统计；不主导 ResearchBus schema、投资/回测、行研报告生成或政策采集。
- 暂停项：在用户未提供 ChatGPT 对照和验收 A/B/C 前，暂停新增大型 UI、继续打包、多版本报告扩张和跨系统 schema 设计。
- 下一轮最高优先级：用户完成验收矩阵或补充 ChatGPT 对照文件后，只做差距审计、必要精修、复核回灌和最终门禁。
- 2026-06-05 continuation：仅收口上一轮暂停前的 `package_delivery.py` / `audit_goal_completion.py` 中间改动，使目标完成度审计可引用本次打包 ZIP；未重建正式 ZIP。轻量验证：`tests/test_package_delivery.py tests/test_goal_completion_audit.py` 6 passed，`tests/test_finalize_delivery.py` 7 passed。
- 2026-06-05 Weixin intake continuation：参考 `codex_system_upgrade_package_20260605.zip` 但不作为本系统硬性 ChatGPT 对照源；内审后确认消费系统只主导账单分类、经济放血机制、周期报告和消费行为状态。新增 `weixin_intake_items` 候选入箱、文本-only 归档、微信接入契约和系统结构内审 PDF；不主导 ResearchBus schema、投资/回测、行研报告或政策采集。
- 2026-06-05 user acceptance：用户口头确认验收矩阵选择为 1-8 全部 A，最后总目标为 B；已写入 `outputs/finance_ledger_20220605_20260603/audit/user_acceptance_decisions.json`。目标审计更新为 8 met / 1 needs_user_input，唯一剩余项是按 final B 做一轮局部精修。验证：`tests/test_goal_completion_audit.py` 5 passed。
- 2026-06-05 acceptance workbench refinement：针对“导出 JSON 没反应”完成最小精修。`acceptance_workbench.html` 新增 JSON 预览、复制验收 JSON、下载状态反馈、一键套用“1-8 A，最后 B”和 B 项精修提示；输出已重建，`validate_outputs.py` 123 ok / 0 warn / 0 fail，目标审计仍为 8 met / 1 needs_user_input。Browser 实测按钮点击成功：套用后完成度 89%，仅总目标 B，复制按钮给出可见 fallback 提示。未重建正式 ZIP。
- 2026-06-05 final acceptance all A：用户确认“全 A”。已更新 `audit/user_acceptance_decisions.json`，目标完成度审计为 9 met / 0 gap / `goal_complete=true`。完整最终门禁通过：浏览器验收 18/18 checked、0 failures，`pytest` 53 passed，输出校验通过，正式 ZIP 已重建为 `outputs/delivery/economic_bleed_delivery_20260605_151300.zip`，大小 28,155,678 bytes，280 files。
- 2026-06-05 Data Trust Layer v1：新增 `src/econ_bleed_analyzer/data_trust.py`，接入 `reports.py`、`ledger.py`、`validate_outputs.py`、README 和 `docs/finance_ledger_data_contract.md`。状态口径覆盖 `RAW_IMPORTED`、`PARSED_CANDIDATE`、`NEEDS_REVIEW`、`USER_CONFIRMED`、`RECONCILED`、`ARCHIVED`、`REJECTED`；交易层当前分布为 `RECONCILED=5316`、`PARSED_CANDIDATE=3110`、`REJECTED=269`、`NEEDS_REVIEW=113`，总计 8808 笔，与 `classified_transactions_audit` 对齐。正式输出重建命令：`PYTHONPATH=src <CODEX_BUNDLED_PYTHON> scripts/weekly_update.py --input data/finance_ledger/sources --ledger-db data/finance_ledger/finance_ledger.sqlite --output outputs/finance_ledger_20220605_20260603`，结果 `validation: ok=128 warn=0 fail=0`。补充验证：`scripts/validate_outputs.py --require-ledger` 全 OK；`pytest tests` 全量 59 passed in 347.77s。正式 ZIP 未在本轮重建，因为本轮目标是 Data Trust Layer 增量，不触发浏览器最终打包门禁。
- 2026-06-05 Reconciliation Layer v1：新增 `src/econ_bleed_analyzer/reconciliation.py`，接入 `ledger.py`、`validate_outputs.py`、README、`docs/finance_ledger_data_contract.md` 和测试。对账公式包括：`count(classified_transactions_audit) == count(data_trust_transactions)`；`sum(production_expense_allocations.allocated_amount_cents)/100 == sum(summary_by_month.total_expense)`，容差 0.05 元；`manual_review_queue` pending key 不得进入 `production_expense_allocations.review_key`；`count(data_trust_transactions where data_trust_status='RECONCILED') == count(distinct production_expense_allocations.review_key)`；可校验来源文件 hash 必须匹配。正式输出重建命令同上，本轮结果 `weekly_update_manifest.json` 为 155 ok / 0 warn / 0 fail，`validation.failed=false`；`reconciliation_checks` 9 行全部 `pass`，`v_reconciliation_failures` 为 0；最终全量测试 `61 passed in 59.61s`。正式 ZIP 未在本轮重建，因为本轮目标是 Reconciliation Layer 增量，不触发浏览器最终打包门禁。
- 2026-06-05 Manual Review Queue v1：新增 `src/econ_bleed_analyzer/manual_review_audit.py`，接入 `reports.py`、`ledger.py`、`validate_outputs.py`、README、`docs/finance_ledger_data_contract.md` 和测试。队列审计字段包括 `queue_status`、`priority`、`evidence_classification`、`decision_grade`、`ledger_effect`、`next_action`、候选动作、候选置信度和 Data Trust 状态；状态覆盖 `PENDING_REVIEW`、`INVALID_DECISION`、`EMPTY`。正式输出重建后 `validation: ok=168 warn=0 fail=0`，`manual_review_queue_audit` 为 92 行，`v_manual_review_queue_blockers` 为 30 行，`manual_review_queue_audit_report.pdf` 已生成。验证：`PYTHONPATH=src:. pytest tests -q -p no:cacheprovider` 64 passed。正式 ZIP 未在本轮重建，因为本轮目标是 Manual Review Queue 增量。
- 2026-06-05 Entity Registry / Alias Map v1：新增 `src/econ_bleed_analyzer/entity_registry.py`，接入 `reports.py`、`ledger.py`、`validate_outputs.py`、README、`docs/finance_ledger_data_contract.md` 和测试。实体范围覆盖交易对方、来源平台、支付方式、来源文件、类别、机制和风险标签；别名规则为 Unicode NFKC、casefold、去空白和常见符号。正式输出重建后 `validation: ok=185 warn=0 fail=0`，`entity_registry` 1674 行，`alias_map` 1674 行，`v_entity_alias_conflicts` 0 行，`entity_registry_report.pdf` 已生成。验证：`PYTHONPATH=src:. pytest tests -q -p no:cacheprovider` 66 passed。正式 ZIP 未在本轮重建，因为本轮目标是 Entity Layer 增量。
- 2026-06-05 Evidence Classification / Decision Grade v1：新增/接入 `src/econ_bleed_analyzer/evidence_decision.py`，集成 `reports.py`、`ledger.py`、`validate_outputs.py`、README、`docs/finance_ledger_data_contract.md` 和测试。统一矩阵覆盖 Data Trust、Reconciliation、Manual Review、Entity Registry、Alias Map、控制动作、来源平台、报告登记和固定查询入口；输出 `audit/evidence_decision_matrix.json/.csv`、`audit/evidence_decision_summary.json/.csv`、`data/evidence_decision_matrix.csv`、`data/evidence_decision_summary.csv`、SQLite 表和只读视图，并生成正式 PDF `reports/evidence_decision_matrix_report.pdf`。正式输出重建后 `validation: ok=201 warn=0 fail=0`，矩阵 12,323 行、摘要 16 行、watchlist 541 行；`validate_outputs.py --require-ledger` 全 OK；全量测试 `68 passed in 29.17s`。正式 ZIP 未在本轮重建，因为本轮目标是 Evidence/Decision 增量。
- 2026-06-05 V2 usability/report upgrade：已把入口定位为“本地记账分析系统”，新增自定义问题查询控制台、本地证据回答、问题历史、证据区、报告中心筛选/选中查看、报告默认新标签页打开、全模块全局导航和正式 PDF `reports/finance_ledger_system_improvement_report.pdf`。新增机器可读文件 `audit/question_answer_index.json`、`audit/finance_ledger_system_improvement_source_log.json/.csv`、`audit/system_improvement_gap_matrix.csv`。最终门禁通过：浏览器验收 18/18 checked、0 failures，`pytest` 61 passed，`validate_outputs.py --require-ledger` 155 ok / 0 warn / 0 fail，目标审计 `goal_complete=true`。正式 ZIP 已重建为 `outputs/delivery/economic_bleed_delivery_20260605_203726.zip`，大小 30,817,644 bytes，305 files。
- 2026-06-05 Data access/backtest-style entrance：新增 `data_access_hub.html`，作为类似量化回测系统的一级入口，供 PFIOS、ResearchBus、赛事分析和微信候选入箱复用同一 SQLite/报告产物；页面列出 `v_mart_daily_cashflow`、`v_fact_expense_allocations`、`v_data_trust_transactions`、`v_reconciliation_checks` 等推荐只读视图、API 启动命令和快速查询样例。已接入首页卡片、全局导航、运行控制台、`report_manifest.json`、输出校验和浏览器验收。验证：`weekly_update.py` 通过，`validate_outputs` 158 ok / 0 warn / 0 fail；浏览器验收 20 checked / 0 failures，验收新鲜度 OK；定向测试 `tests/test_validate_outputs.py tests/test_browser_visual_acceptance_runner.py` 4 passed。
- 2026-06-05 macOS app launchers：用户澄清“新增入口”指 Desktop、Downloads、Applications 三处 app 样式点击入口，不是 HTML/MD。已创建 `~/Desktop/本地记账分析系统.app`、`~/Downloads/本地记账分析系统.app`、`/Applications/本地记账分析系统.app`，三者复用 `scripts/launch_finance_ledger_app.sh`；双击后自动复用或启动本地 `127.0.0.1` 静态服务并打开系统首页。验证：三份 `Info.plist` 均 `plutil -lint OK`，可执行权限已设置，`open ~/Desktop/本地记账分析系统.app` 成功，`curl http://127.0.0.1:8765/index.html` 命中“本地记账分析系统”和“数据接入与回测入口”。安装清单：`outputs/finance_ledger_20220605_20260603/audit/app_launchers.json`。
- 2026-06-05 guided UI upgrade：新增全局右侧“使用说明 / 术语”抽屉，所有 HTML 页面通过全局导航注入，可边看指导边操作；内容覆盖推荐操作路径、账本工作流可视化、页面用法、专业术语（生产口径、待复核隔离、真实消费、风险支出、现金流视图、同比/环比、Data Trust、Reconciliation 等）和使用边界。运行控制台新增 `workflowMap` / `workflowVisual` / `reviewPressureBar`，展示账单导入、规则分类、大额复核、生产统计、报告查看、行动回灌的流程及待复核压力。验证：`weekly_update.py` 通过，输出校验 158 ok / 0 warn / 0 fail；浏览器验收 20 checked / 0 failures 且新鲜度 OK；定向测试 `tests/test_validate_outputs.py tests/test_browser_visual_acceptance_runner.py` 4 passed。浏览器插件路由本轮不可用，已用项目 headless 验收和 DOM 内容检查替代。
- 2026-06-05 app icon polish：新增可爱专业风格应用图标资产 `assets/app_icon/finance_ledger_icon_1024.png` 和 `assets/app_icon/finance_ledger.icns`，视觉为 mint 圆角底、账本、折线图和金币元素。三个 macOS app 入口均已复制 `Contents/Resources/finance_ledger.icns` 并设置 `CFBundleIconFile=finance_ledger`；网页输出已复制 `favicon.png` 并在全局注入层加入 `<link rel="icon">`。验证：三份 `Info.plist` OK，`pytest tests/test_validate_outputs.py` 2 passed，app 启动后 `127.0.0.1:8765/index.html` 可访问，图标 PNG 已人工视觉检查。
- 2026-06-06 app click fix：用户反馈 `.app` 点击无反应。已从 shell/AppleScript app 改为原生 Mach-O 启动器 `src/native/finance_ledger_launcher.c`，编译产物 `build/native/FinanceLedgerLauncher` 写入 Desktop、Downloads、Applications 三个 app bundle；启动脚本 `scripts/launch_finance_ledger_app.sh` 加锁、固定使用 `127.0.0.1:8765`、健康检查改为 ASCII 标记，避免 locale 和旧端口干扰。验证：`zsh -n scripts/launch_finance_ledger_app.sh` 通过；`open -n` 三处 app 均写入 `open http://127.0.0.1:8765/index.html` 日志；`curl http://127.0.0.1:8765/index.html` 命中页面标题。清单 `outputs/finance_ledger_20220605_20260603/audit/app_launchers.json` 已更新。
- 2026-06-06 Codex Workflow Layer v1：新增项目级 `AGENTS.md`、`docs/codex_workflow_contract.md`、`docs/run_contract_template.md`、`scripts/doctor.py`、`setup.sh`、`Makefile` 和 `tests/test_codex_workflow.py`。工作流 doctor 支持只读检查关键文件、SQLite 表/视图、输出文件、正式 PDF 和 `validate_outputs` 集成，可写出 `audit/codex_workflow_doctor.json` 与 `reports/codex_workflow_contract_report.pdf`。验证：doctor require-output 为 37 ok / 1 warn / 0 fail；输出校验 201 ok / 0 warn / 0 fail；全量测试 71 passed。唯一 warning 为项目内无升级总报告或 taskpack 本地副本，不阻塞当前消费系统工作流层。
- 2026-06-15 handoff/evaluation package：按用户要求生成可外发给 ChatGPT、新开发者和使用者的交接审核包，脚本为 `scripts/generate_handoff_package.py`，输出目录 `outputs/handoff/finance_ledger_handoff_20260615/`，ZIP 为 `outputs/handoff/finance_ledger_handoff_20260615.zip`。包内包含开发进度 PDF/MD、功能清单 CSV、任务清单 CSV、ChatGPT 审核说明、开发者上手、用户快速使用、证据索引 JSON 和审核问题清单；为降低隐私风险，未复制原始账单、SQLite 数据库或交易明细。包内当前验证摘要为 `201 ok / 0 warn / 0 fail`，ZIP 完整性通过；当前文件态 `goal_completion_audit.json` 仍显示 8/9、`goal_complete=false`，需下一轮优先复核验收漂移或重跑最终审计。
