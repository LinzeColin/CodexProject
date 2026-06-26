# Quant Behavior Validation System Handoff

本文档用于让独立验证系统与 QuantLab 量化系统完成交接、握手和后续互通。

## 当前握手状态

- 状态码：`QBVS_HANDSHAKE_ACK_RECEIVED_VALID`
- 最后刷新时间：`2026-06-05T17:04:18+10:00`
- QBVS 已生成握手请求：`handoff/qbvs_handshake_request.json`
- QBVS 已生成 QuantLab ACK 模板：`handoff/quantlab_handshake_ack_template.json`
- QuantLab 真实 ACK 已返回：`handoff/quantlab_handshake_ack.json`
- `verify-handshake` 校验结果：`valid=true`，`errors=[]`。
- 新审计输出：`runs/goal_readiness_audit_quantlab_ack_20260605_from_quantlab_thread/goal_readiness_audit.json`、`goal_readiness_audit.csv`、`Goal_Readiness_Audit_Report.pdf`。
- 新恢复包：`handoff/qbvs_resume_after_quantlab_ack_20260605.json`、`handoff/qbvs_resume_after_quantlab_ack_20260605.md`。
- 当前可以声明“QuantLab handshake ACK missing”已解除；`BRK-B` 已通过 Moomoo/OpenD 快照探测确认 provider code 为 `US.BRK.B`，证据为 `runs/moomoo_brk_b_alias_snapshot_probe_20260605.json`；OpenD 历史 K 线额度仍是后续真实数据验证问题。

你在 QuantLab 线程发送完全相同指令时，QuantLab 侧应读取本文件和握手请求，并生成真实 `handoff/quantlab_handshake_ack.json`。QBVS 收到该 ACK 后，必须运行 `verify-handshake`，只有返回 `valid: true` 才能把互通状态升级为完成。

2026-06-05 QuantLab ACK 接收记录：

- ACK 文件：`handoff/quantlab_handshake_ack.json`。
- ACK 来源：QuantLab。
- ACK 内容：`accepted=true`，`consume_mode=external_artifact_read`，`quantlab_entrypoint` 非空。
- QuantLab 边界：ReviewOnly external evidence ingestion；不触发实盘、不写已审批策略库、不把 Yahoo 公开历史当成账户可交易证明。
- 本地验证命令：`PYTHONPATH=. python3 -m qbvs.cli verify-handshake --ack handoff/quantlab_handshake_ack.json`。
- 本地验证结果：`{"valid": true, "errors": []}`。
- 新 readiness audit 中 `quantlab_handshake_ack` 项已通过，证据为 `accepted=True` 和 QuantLab entrypoint；审计得分 `95.00%`，`passed=9`、`partial=1`、`blocked=0`、`missing=0`。
- 旧交接包已刷新：`handoff/quantlab_ack_request_packet_20260605/*` 与 `handoff/ack_readiness_20260605/*` 不应再显示 `ACK missing` 或 `BRK-B unresolved`。
- QBVS 下一步可以恢复：先运行最小 goal-readiness audit / verify-handshake；`BRK-B` alias 已通过快照确认，后续只需在 OpenD 历史 K 线 quota 安全时做单标的历史 K 线确认，不做批量重抓；OpenD quota 未恢复前只执行 quota-safe public-history / replacement-to-200 分片计划或继续 readiness audit；不要恢复无必要策略目录扩张或重复长跑。

2026-06-06 当前阶段 exact 验证新增记录：

- 最新扩展验证：`runs/current_stage_bw99_3candidates_200symbols_20windows_exact_20260605` 已完成 12,000/12,000 个 exact 任务，覆盖 3 个当前候选策略、200 个 Yahoo 公开行情标的、每对最多 20 个滚动窗口。三条候选策略均满足用户硬阈值：平均总收益差均 `>= -8%`，平均年化差均 `>= -3%`，平均回撤改善为正。
- 20-window 结果摘要：`bw99_boll_or_rsi_none_ma_trend_full_none` samples `4000`，pass_rate `0.99850`，avg_total_gap `-0.000827`，avg_annualized_gap `-0.000052`，avg_drawdown_improvement `0.001310`；`bw99_none_none_ma_trend_full_none` pass_rate `0.99775`；`bw98_boll_or_rsi_none_ma_trend_full_none` pass_rate `0.99400`。
- 最新 QuantLab ReviewOnly bundle：`handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_20windows_20260605`；`verify-quantlab-bundle` 返回 `valid=true`，`errors=[]`，`warnings=[]`。
- 最新当前阶段正式报告：`reports/current_stage_20260606/Current_Stage_Strategy_Report_20260606.pdf`；辅助文件包括 `current_stage_strategy_report_20260606.md`、`candidate_summary_12000_exact.csv`、`strategy_rule_card_20260606.json`。报告明确主候选规则、指标口径、12,000 exact 样本结果、ReviewOnly 边界和剩余缺口。
- 最新目标完成度缺口审计：`reports/goal_completion_gap_audit_20260606/Goal_Completion_Gap_Audit_20260606.pdf`；辅助文件包括 `goal_completion_gap_audit.md`、`goal_completion_gap_audit.csv`、`goal_completion_gap_audit.json`。审计状态为 `active_not_complete`，不严格 blocked，readiness `95.00%`；14 项需求中 9 项完成、4 项部分完成、1 项未完成。未完成项仍是每策略百万级/极限规模，部分完成项集中在支付宝真实基金口径、Moomoo/OpenD 真实 200 标的、100 年跨周期和最终完整报告。
- 最新随机压力测试进度：`runs/current_stage_bw99_random_stress_20260606` 已完成 100 个 batch，共 150,000 行结果；3 个当前候选策略各 50,000 条随机路径，覆盖 bull、bear、sideways、crash、highvol、rotation 六类 synthetic regime。主候选 `bw99_boll_or_rsi_none_ma_trend_full_none` 通过率 `100.0000%`，avg_total_gap `-0.0263%`，avg_annualized_gap `-0.0266%`，avg_drawdown_improvement `0.0954%`；三条候选均满足用户硬阈值。各策略/状态组合中最低通过率为 `99.8314%`。正式报告：`reports/random_stress_progress_20260606/Random_Stress_Progress_Report_20260606.pdf`；辅助文件包括 `random_stress_progress_report.md`、`random_stress_progress_report.json`、`random_stress_strategy_summary.csv`、`random_stress_regime_summary.csv`。该项为 100,000 随机路径/策略目标的 `50%` 阶段进度，不代表随机压力目标完成。
- 最新 readiness audit：`runs/goal_readiness_audit_random_stress_50k_20260606`，结果 `readiness_percent=95.00%`，`passed=9`、`partial=1`、`blocked=0`、`missing=0`；唯一 partial 仍为百万级/极限规模目标。
- 新增扩展 manifest：`runs/manifests/current_stage_bw99_3candidates_200symbols_10windows_20260605.csv`，覆盖 3 个当前候选策略、200 个 Yahoo 公开行情标的、每对最多 10 个滚动窗口，共 6,000 个 exact 任务。
- 新增扩展 run：`runs/current_stage_bw99_3candidates_200symbols_10windows_exact_20260605`，`task_status.csv` 显示 `completed=6000`；三条候选策略均满足用户硬阈值：平均总收益差均 `>= -8%`，平均年化差均 `>= -3%`，平均回撤改善为正。
- 扩展结果摘要：`bw99_boll_or_rsi_none_ma_trend_full_none` pass_rate `0.9980`，avg_total_gap `-0.000816`，avg_annualized_gap `-0.000141`，avg_drawdown_improvement `0.001179`；`bw99_none_none_ma_trend_full_none` pass_rate `0.9965`；`bw98_boll_or_rsi_none_ma_trend_full_none` pass_rate `0.9945`。
- 新增 QuantLab ReviewOnly bundle：`handoff/quantlab_bundle_current_stage_bw99_3candidates_200symbols_10windows_20260605`；`verify-quantlab-bundle` 返回 `valid=true`，`errors=[]`，`warnings=[]`。
- 边界未变：不写 QuantLab 源码/数据库/approved strategy library，不触发 OpenD 历史批量重抓，不接实盘交易。

## 本轮互通状态

本轮已把独立验证系统侧的交接与握手协议刷新到可由 QuantLab 直接读取的状态。

QuantLab 侧收到同样指令后，应优先读取：

- `HANDOFF.md`
- `QUANTLAB_INTEGRATION_CONTRACT.json`
- `HANDSHAKE_PROTOCOL.json`
- `handoff/qbvs_handshake_request.json`
- `handoff/quantlab_handshake_ack_template.json`

QuantLab 侧必须回写：

- `handoff/quantlab_handshake_ack.json`

握手成功条件：

- `protocol_version = qbvs-quantlab-handshake-v1`
- `message_type = handshake_ack`
- `source_system = quantlab`
- `target_system = quant_behavior_validation_system`
- `accepted = true`
- `quantlab_entrypoint` 非空，必须写明 QuantLab 将通过哪个命令、页面、模块或 adapter 读取 QBVS 产物。

边界：本线程不修改 QuantLab 源码、不写 QuantLab 数据库、不把候选策略直接写入已审批策略库。QuantLab 侧只能先按 `external_evidence_only` 读取外部证据；任何策略库写入、数据库写入或生产化接入都必须经用户单独确认。

## 当前目标

把独立验证系统作为 QuantLab 的外部策略验证层，用于验证交易行为规律策略，而不是投资组合策略。

核心策略问题：

- 原支付宝式“越跌越买、越涨越卖”在上涨时容易跑输买入持有。
- 用户希望保留下跌保护，同时提高上涨参与度。
- 用户约束：平均总收益相对买入持有不能低 8% 以上，年化不能低 3% 以上。
- 策略测试要围绕行为规则展开，例如 BOLL 下轨补足、RSI 过滤、MA/MACD 趋势持有、ATR 风控、极端事件窗口等。

## 系统边界

独立验证系统路径：

`/Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system`

QuantLab 当前路径提示：

`/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance`

边界规则：

- 独立验证系统不导入 QuantLab 源码。
- 独立验证系统不修改 QuantLab 源码。
- 独立验证系统不写 QuantLab 数据库。
- QuantLab 后续只读取独立验证系统产物，作为策略审批、策略库展示、回测功能增强的外部证据。

## 已完成能力

- 200+ 个交易行为策略族生成。
- 随机压力测试。
- 本地 CSV 验证。
- Yahoo 公开行情只读验证。
- 滚动窗口验证。
- 事件窗口验证。
- 本机多进程随机压力测试。
- 标准 OHLCV 数据缓存。
- 多标的 `cache_index.csv`。
- 可恢复 manifest。
- 每任务 JSON 缓存。
- 断点续跑。
- 跨 run 结果索引。
- SQLite 结果仓库。
- 数据质量评分、质量门禁、manifest 分片和预算估算。
- 快速筛选引擎。
- 快速筛选与精确回测误差对比。
- QuantLab 外部证据包导出与校验。
- QuantLab 只读消费 adapter pack。
- 长任务 campaign 计划、分片命令和校验。
- 候选策略晋级门禁。
- Moomoo/OpenD 可用性探测。
- Moomoo/OpenD 历史行情缓存入口。
- Moomoo SDK 安装与 OpenD 真实行情缓存/回测烟测。
- 220 标的候选 universe seed。
- 220 标的 Moomoo/OpenD 缓存命令计划。
- 220 标的 Yahoo 公开行情 universe。
- 220 标的 Yahoo 公开行情缓存命令计划。
- Yahoo 公开行情 5 标的标准 OHLCV 缓存烟测。
- Yahoo 公开行情 600 个 rolling 精确回测任务烟测。
- 分层抽样 manifest，用于短跑覆盖多标的、多策略和多周期。
- Yahoo 公开行情 1,000 个分层 rolling 精确回测任务烟测。
- 分层抽样 universe，用于公开行情样本覆盖多市场和多资产类别。
- Yahoo 公开行情 40 标的跨市场缓存烟测。
- Yahoo 公开行情 4,000 个跨市场分层 rolling 精确回测任务烟测。
- Yahoo 公开行情 219/220 标的全量 seed 缓存。
- 200 标的 × 200 策略 pair manifest。
- Yahoo 公开行情 4,000 个 200×200 分层 pair 精确回测任务烟测。
- Yahoo 公开行情 40,000 个 200×200 pair 全量精确回测任务已完成并聚合。
- 用户原始目标逐项达成审计命令与 PDF/JSON/CSV 输出。
- 从 40,000 pair 基线自动筛选 top finalist 策略并生成多窗口深度验证 manifest/campaign。
- Top 20 finalist 多窗口深度 campaign 已完成 20,000 个精确验证任务并导出 QuantLab 证据包。
- 支付宝基金净值 CSV 标准化缓存。
- 支付宝基金申购/赎回规则执行口径。
- Moomoo/支付宝可交易 universe 模板。
- PDF 报告输出。
- 策略目录反凑数审计：区分控制组、已验证行为策略、未验证目录候选和低优先级策略。

## QuantLab 应读取的核心文件

- `QUANTLAB_INTEGRATION_CONTRACT.json`
- `HANDOFF.md`
- `HANDSHAKE_PROTOCOL.json`
- `handoff/qbvs_handshake_request.json`
- `handoff/quantlab_handshake_ack_template.json`
- `runs/**/strategy_summary.csv`
- `runs/**/validation_results.csv`
- `runs/**/task_status.csv`
- `runs/**/Behavior_Strategy_*.pdf`
- `data_cache/**/cache_index.csv`
- `runs/**/fast_validation_results.csv`
- `runs/**/fast_strategy_summary.csv`
- `runs/**/fast_exact_comparison.csv`
- `warehouse/qbvs_results.sqlite`
- `warehouse/export/*.csv`
- `handoff/**/quantlab_bundle_manifest.json`
- `handoff/**/quantlab_ingestion_payload.json`
- `handoff/**/quantlab_candidate_strategies.csv`
- `handoff/**/QuantLab_Integration_Bundle_Report.pdf`
- `runs/**/moomoo_opend_probe.json`
- `config/tradable_universe_template.csv`
- `config/tradable_universe_seed_220.csv`
- `config/tradable_universe_seed_220.summary.json`
- `campaigns/seed_220_cache_plan/seed_cache_plan.csv`
- `campaigns/seed_220_cache_plan/seed_cache_commands.sh`
- `config/tradable_universe_seed_220_yahoo.csv`
- `config/tradable_universe_seed_220_yahoo.summary.json`
- `config/tradable_universe_seed_yahoo_balanced_40.csv`
- `config/tradable_universe_seed_yahoo_balanced_40.summary.json`
- `campaigns/seed_220_yahoo_cache_plan/yahoo_seed_cache_plan.csv`
- `campaigns/seed_220_yahoo_cache_plan/yahoo_seed_cache_commands.sh`
- `campaigns/seed_220_yahoo_cache_plan/yahoo_seed_cache_plan.summary.json`
- `data_cache_seed_yahoo_smoke/cache_index.csv`
- `data_cache_seed_yahoo_220_public/cache_index.csv`
- `data_cache_seed_yahoo_220_public/cache_errors.csv`
- `config/yahoo_220_public_balanced_200_cache_index.csv`
- `config/yahoo_220_public_balanced_200_cache_index.summary.json`
- `runs/manifests/seed_yahoo_smoke_manifest.csv`
- `runs/manifests/seed_yahoo_stratified_1000_manifest.csv`
- `runs/manifests/seed_yahoo_stratified_1000_manifest.summary.json`
- `runs/manifests/seed_yahoo_balanced_40_manifest.csv`
- `runs/manifests/seed_yahoo_balanced_40_stratified_4000_manifest.csv`
- `runs/manifests/seed_yahoo_balanced_40_stratified_4000_manifest.summary.json`
- `runs/manifests/yahoo_public_200x200_pair_manifest.csv`
- `runs/manifests/yahoo_public_200x200_pair_manifest.summary.json`
- `runs/manifests/yahoo_public_200x200_pair_stratified_4000_manifest.csv`
- `runs/manifests/yahoo_public_200x200_pair_stratified_4000_manifest.summary.json`
- `runs/seed_yahoo_smoke_exact_qg/strategy_summary.csv`
- `runs/seed_yahoo_smoke_exact_qg/validation_results.csv`
- `runs/seed_yahoo_smoke_exact_qg/Behavior_Strategy_Task_Run_Report.pdf`
- `runs/seed_yahoo_stratified_1000_exact/strategy_summary.csv`
- `runs/seed_yahoo_stratified_1000_exact/validation_results.csv`
- `runs/seed_yahoo_stratified_1000_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `runs/seed_yahoo_balanced_40_stratified_4000_exact/strategy_summary.csv`
- `runs/seed_yahoo_balanced_40_stratified_4000_exact/validation_results.csv`
- `runs/seed_yahoo_balanced_40_stratified_4000_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `runs/yahoo_public_200x200_pair_stratified_4000_exact/strategy_summary.csv`
- `runs/yahoo_public_200x200_pair_stratified_4000_exact/validation_results.csv`
- `runs/yahoo_public_200x200_pair_stratified_4000_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `runs/yahoo_public_200x200_pair_full_40000_exact/strategy_summary.csv`
- `runs/yahoo_public_200x200_pair_full_40000_exact/validation_results.csv`
- `runs/yahoo_public_200x200_pair_full_40000_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `handoff/quantlab_bundle_seed_yahoo_smoke/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_seed_yahoo_smoke/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_seed_yahoo_smoke/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_seed_yahoo_smoke/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_seed_yahoo_stratified_1000/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_seed_yahoo_stratified_1000/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_seed_yahoo_stratified_1000/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_seed_yahoo_stratified_1000/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_seed_yahoo_balanced_40_stratified_4000/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_seed_yahoo_balanced_40_stratified_4000/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_seed_yahoo_balanced_40_stratified_4000/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_seed_yahoo_balanced_40_stratified_4000/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_yahoo_public_200x200_stratified_4000/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_stratified_4000/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_stratified_4000/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_yahoo_public_200x200_stratified_4000/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_3493/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_3493/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_3493/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_3493/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_10000/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_10000/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_10000/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_10000/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_20000/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_20000/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_20000/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_partial_20000/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_40000/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_40000/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_40000/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_yahoo_public_200x200_full_40000/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/promotion_candidates_seed_yahoo_smoke.csv`
- `handoff/promotion_candidates_seed_yahoo_stratified_1000.csv`
- `handoff/promotion_candidates_seed_yahoo_balanced_40_stratified_4000.csv`
- `handoff/promotion_candidates_yahoo_public_200x200_stratified_4000.csv`
- `handoff/promotion_candidates_yahoo_public_200x200_full_40000.csv`
- `runs/goal_readiness_audit_iteration23/goal_readiness_audit.json`
- `runs/goal_readiness_audit_iteration23/goal_readiness_audit.csv`
- `runs/goal_readiness_audit_iteration23/Goal_Readiness_Audit_Report.pdf`
- `runs/manifests/yahoo_public_200x200_pair_million_scale_budget_8w.json`
- `runs/manifests/yahoo_public_top20_finalist_200symbols_5windows_manifest.csv`
- `runs/manifests/yahoo_public_top20_finalist_200symbols_5windows_manifest.finalists.csv`
- `runs/manifests/yahoo_public_top20_finalist_200symbols_5windows_manifest.summary.json`
- `runs/manifests/yahoo_public_top20_finalist_200symbols_5windows_budget_8w.json`
- `campaigns/yahoo_public_top20_finalist_200symbols_5windows_campaign/campaign_plan.json`
- `campaigns/yahoo_public_top20_finalist_200symbols_5windows_campaign/run_commands.sh`
- `runs/yahoo_public_top20_finalist_200symbols_5windows_exact/strategy_summary.csv`
- `runs/yahoo_public_top20_finalist_200symbols_5windows_exact/validation_results.csv`
- `runs/yahoo_public_top20_finalist_200symbols_5windows_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `runs/moomoo_opend_probe_iteration26_after_sdk.json`
- `data_cache_moomoo_smoke/cache_index.csv`
- `data_cache_moomoo_smoke/US/US.SPY.csv`
- `data_cache_moomoo_smoke/US/US.SPY.metadata.json`
- `runs/manifests/moomoo_spy_smoke_5strategy_manifest.csv`
- `runs/moomoo_spy_smoke_5strategy_exact/strategy_summary.csv`
- `runs/moomoo_spy_smoke_5strategy_exact/validation_results.csv`
- `runs/goal_readiness_audit_iteration26/goal_readiness_audit.json`
- `runs/goal_readiness_audit_iteration26/goal_readiness_audit.csv`
- `runs/goal_readiness_audit_iteration26/Goal_Readiness_Audit_Report.pdf`
- `data_cache_moomoo_batch10/cache_index.csv`
- `runs/manifests/moomoo_batch10_top20_finalist_3windows_manifest.csv`
- `runs/manifests/moomoo_batch10_top20_finalist_3windows_manifest.summary.json`
- `runs/manifests/moomoo_batch10_top20_finalist_3windows_budget.json`
- `runs/moomoo_batch10_top20_finalist_3windows_exact/strategy_summary.csv`
- `runs/moomoo_batch10_top20_finalist_3windows_exact/validation_results.csv`
- `runs/moomoo_batch10_top20_finalist_3windows_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `handoff/quantlab_bundle_moomoo_batch10_top20_finalist_3windows/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_moomoo_batch10_top20_finalist_3windows/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_moomoo_batch10_top20_finalist_3windows/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_moomoo_batch10_top20_finalist_3windows/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/promotion_candidates_moomoo_batch10_top20_finalist_3windows.csv`
- `config/moomoo_batch30_cache_index.csv`
- `config/moomoo_batch30_cache_index.summary.json`
- `runs/manifests/moomoo_batch30_top20_finalist_3windows_manifest.csv`
- `runs/manifests/moomoo_batch30_top20_finalist_3windows_manifest.summary.json`
- `runs/manifests/moomoo_batch30_top20_finalist_3windows_budget.json`
- `runs/moomoo_batch30_top20_finalist_3windows_exact/strategy_summary.csv`
- `runs/moomoo_batch30_top20_finalist_3windows_exact/validation_results.csv`
- `runs/moomoo_batch30_top20_finalist_3windows_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `handoff/quantlab_bundle_moomoo_batch30_top20_finalist_3windows/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_moomoo_batch30_top20_finalist_3windows/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_moomoo_batch30_top20_finalist_3windows/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_moomoo_batch30_top20_finalist_3windows/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/promotion_candidates_moomoo_batch30_top20_finalist_3windows.csv`
- `config/moomoo_batch80_cache_index.csv`
- `config/moomoo_batch80_cache_index.summary.json`
- `runs/manifests/moomoo_batch80_top20_finalist_3windows_manifest.csv`
- `runs/manifests/moomoo_batch80_top20_finalist_3windows_manifest.summary.json`
- `runs/manifests/moomoo_batch80_top20_finalist_3windows_budget.json`
- `runs/moomoo_batch80_top20_finalist_3windows_exact/strategy_summary.csv`
- `runs/moomoo_batch80_top20_finalist_3windows_exact/validation_results.csv`
- `runs/moomoo_batch80_top20_finalist_3windows_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `handoff/quantlab_bundle_moomoo_batch80_top20_finalist_3windows/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_moomoo_batch80_top20_finalist_3windows/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_moomoo_batch80_top20_finalist_3windows/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_moomoo_batch80_top20_finalist_3windows/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/promotion_candidates_moomoo_batch80_top20_finalist_3windows.csv`
- `config/moomoo_batch100_cache_index.csv`
- `config/moomoo_batch100_cache_index.summary.json`
- `runs/manifests/moomoo_batch100_top20_finalist_3windows_manifest.csv`
- `runs/manifests/moomoo_batch100_top20_finalist_3windows_manifest.summary.json`
- `runs/manifests/moomoo_batch100_top20_finalist_3windows_budget.json`
- `runs/moomoo_batch100_top20_finalist_3windows_exact/strategy_summary.csv`
- `runs/moomoo_batch100_top20_finalist_3windows_exact/validation_results.csv`
- `runs/moomoo_batch100_top20_finalist_3windows_exact/Behavior_Strategy_Task_Run_Report.pdf`
- `handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/promotion_candidates_moomoo_batch100_top20_finalist_3windows.csv`
- `handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows/quantlab_bundle_manifest.json`
- `handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows/quantlab_ingestion_payload.json`
- `handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows/quantlab_candidate_strategies.csv`
- `handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows/QuantLab_Integration_Bundle_Report.pdf`
- `handoff/promotion_candidates_yahoo_public_top20_finalist_200symbols_5windows.csv`
- `campaigns/seed_yahoo_stratified_1000_campaign/campaign_plan.json`
- `campaigns/seed_yahoo_balanced_40_stratified_4000_campaign/campaign_plan.json`
- `campaigns/yahoo_public_200x200_stratified_4000_campaign/campaign_plan.json`
- `campaigns/yahoo_public_200x200_full_40000_campaign/campaign_plan.json`
- `data_cache/ALIPAY_FUND/*.csv`
- `data_cache/ALIPAY_FUND/*.metadata.json`
- `config/alipay_fund_rule_template.json`
- `runs/**/fund_validation_results.csv`
- `runs/**/fund_strategy_summary.csv`
- `runs/**/fund_trading_rule.json`
- `runs/**/Alipay_Fund_Strategy_Validation_Report.pdf`
- `campaigns/**/campaign_plan.json`
- `campaigns/**/campaign_status.csv`
- `campaigns/**/run_commands.sh`
- `handoff/**/promotion_candidates.csv`
- `handoff/**/adapter_pack_manifest.json`
- `handoff/**/quantlab_qbvs_readonly_adapter.py`
- `handoff/**/sample_ingestion_request.json`
- `handoff/**/adapter_pack_verification.json`

## 握手流程

第一步，在独立验证系统侧生成握手请求：

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system
PYTHONPATH=. python3 -m qbvs.cli create-handshake \
  --output-dir handoff \
  --quantlab-root /Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance
```

第二步，在 QuantLab 侧读取：

- `HANDOFF.md`
- `QUANTLAB_INTEGRATION_CONTRACT.json`
- `handoff/qbvs_handshake_request.json`
- `handoff/quantlab_handshake_ack_template.json`

第三步，QuantLab 侧生成：

`handoff/quantlab_handshake_ack.json`

要求：

- `protocol_version` 必须等于 `qbvs-quantlab-handshake-v1`
- `message_type` 必须为 `handshake_ack`
- `source_system` 必须为 `quantlab`
- `target_system` 必须为 `quant_behavior_validation_system`
- `accepted` 必须为 `true`
- `quantlab_entrypoint` 写明 QuantLab 将通过哪个命令、页面或模块读取独立验证系统产物

第四步，在独立验证系统侧校验 ack：

```bash
PYTHONPATH=. python3 -m qbvs.cli verify-handshake \
  --ack handoff/quantlab_handshake_ack.json
```

返回 `valid: true` 即表示握手成功。

## 推荐互通方式

短期推荐：外部产物读取。

QuantLab 不直接调用独立验证系统内部函数，而是读取以下文件：

- `strategy_summary.csv`
- `validation_results.csv`
- `task_status.csv`
- `Behavior_Strategy_Task_Run_Report.pdf`
- `Behavior_Strategy_Run_Index_Report.pdf`

中期推荐：QuantLab 增加“外部验证证据”入口。

建议入口：

- 策略库 Strategy Library：展示外部验证摘要。
- 单标的回测页面：展示该策略是否通过独立验证。
- 策略审批页面：把独立验证报告作为审批证据。
- 报告中心：展示 QBVS 生成的 PDF。

长期推荐：QuantLab 触发独立验证系统 CLI。

QuantLab 可触发：

```bash
PYTHONPATH=. python3 -m qbvs.cli cache-csv ...
PYTHONPATH=. python3 -m qbvs.cli build-cache-manifest ...
PYTHONPATH=. python3 -m qbvs.cli build-cache-pair-manifest ...
PYTHONPATH=. python3 -m qbvs.cli run-manifest ...
PYTHONPATH=. python3 -m qbvs.cli index-runs ...
PYTHONPATH=. python3 -m qbvs.cli fast-screen-csv ...
PYTHONPATH=. python3 -m qbvs.cli fast-benchmark-csv ...
PYTHONPATH=. python3 -m qbvs.cli warehouse-import-runs ...
PYTHONPATH=. python3 -m qbvs.cli export-quantlab-bundle ...
PYTHONPATH=. python3 -m qbvs.cli verify-quantlab-bundle ...
PYTHONPATH=. python3 -m qbvs.cli probe-moomoo-opend ...
PYTHONPATH=. python3 -m qbvs.cli cache-moomoo-history ...
PYTHONPATH=. python3 -m qbvs.cli cache-alipay-fund-nav ...
PYTHONPATH=. python3 -m qbvs.cli create-tradable-universe-template ...
PYTHONPATH=. python3 -m qbvs.cli create-seed-universe ...
PYTHONPATH=. python3 -m qbvs.cli verify-seed-universe ...
PYTHONPATH=. python3 -m qbvs.cli build-seed-cache-plan ...
PYTHONPATH=. python3 -m qbvs.cli build-seed-yahoo-universe ...
PYTHONPATH=. python3 -m qbvs.cli build-seed-yahoo-cache-plan ...
PYTHONPATH=. python3 -m qbvs.cli sample-universe ...
PYTHONPATH=. python3 -m qbvs.cli sample-manifest ...
PYTHONPATH=. python3 -m qbvs.cli create-fund-rule-template ...
PYTHONPATH=. python3 -m qbvs.cli validate-fund-csv ...
PYTHONPATH=. python3 -m qbvs.cli build-campaign ...
PYTHONPATH=. python3 -m qbvs.cli verify-campaign ...
PYTHONPATH=. python3 -m qbvs.cli promote-candidates ...
PYTHONPATH=. python3 -m qbvs.cli build-quantlab-adapter-pack ...
PYTHONPATH=. python3 -m qbvs.cli verify-quantlab-adapter-pack ...
```

快速筛选层只能用于候选压缩。QuantLab 如果读取 `fast_strategy_summary.csv`，必须把对应策略重新放入精确回测、滚动窗口和事件窗口验证，不能直接写入已审批策略库。

当前推荐 QuantLab 优先读取证据包：

- `quantlab_bundle_manifest.json`
- `quantlab_ingestion_payload.json`
- `quantlab_candidate_strategies.csv`
- `QuantLab_Integration_Bundle_Report.pdf`

证据包的 `ingestion_mode` 固定为 `external_evidence_only`，`writes_quantlab_database` 和 `writes_quantlab_source` 固定为 `false`。

支付宝基金策略应优先使用 `validate-fund-csv` 生成的基金执行口径结果，而不是普通股票/ETF 目标仓位回测结果。该口径会纳入申购费、赎回费、买入确认延迟、卖出到账延迟、最短持有期等规则。

长任务使用 `build-campaign` 生成 campaign。该命令只写计划、分片、状态和 `run_commands.sh`，不会自动启动后台任务。真正执行需要用户或外部调度器显式运行命令。

QuantLab 侧建议优先读取 `handoff/quantlab_readonly_adapter_pack`。该包提供只读解析器和测试，可把 QBVS bundle/campaign/promotion 转成 QuantLab 的 `ReviewOnly` 外部验证记录；不能绕过精确复验和用户批准。

当前 220 标的 seed 位于 `config/tradable_universe_seed_220.csv`，覆盖 US ETF、US 股票、港股、A 股 ETF、债券、商品、FX 等类别。它是候选池，不是已确认可交易池；必须经过 Moomoo/OpenD 权限、数据质量和账户可交易性确认。

当前 Yahoo 公开行情回退 universe 位于 `config/tradable_universe_seed_220_yahoo.csv`。它已经成功缓存 219/220 个公开行情标的到 `data_cache_seed_yahoo_220_public/cache_index.csv`，唯一失败项是 `SQ` 的 Yahoo 404。当前已从 219 个成功缓存中抽取 `config/yahoo_220_public_balanced_200_cache_index.csv`，并生成 `runs/manifests/yahoo_public_200x200_pair_manifest.csv`，覆盖 200 标的、200 策略、4 个市场和 5 类资产。`runs/yahoo_public_200x200_pair_stratified_4000_exact` 已完成 4,000 个分层 pair 精确回测任务，覆盖 200 标的和 200 策略。`runs/yahoo_public_200x200_pair_full_40000_exact` 已完成完整 40,000 个 pair 精确回测任务，状态表和结果表均为 40,000 行，覆盖 200 标的、200 策略、4 个市场和 5 类资产；对应 QuantLab 完整证据包位于 `handoff/quantlab_bundle_yahoo_public_200x200_full_40000`，晋级候选表位于 `handoff/promotion_candidates_yahoo_public_200x200_full_40000.csv`。该结果可作为 QuantLab 互通样本和真实历史数据链路验证，但不能替代 Moomoo/支付宝账户级可交易性确认。

当前用户原始目标逐项达成审计位于 `runs/goal_readiness_audit_iteration23`。审计结论：10 个验收项中 7 项 passed、1 项 partial、1 项 blocked、1 项 missing，目标达成审计分数为 77.50%。其中 200 策略、200 标的、40,000 pair 基线、收益底线、回撤保护、正式产物、只读 QuantLab 边界已经通过；Moomoo/OpenD 真实可交易数据门禁 blocked，原因是 `moomoo_or_futu_sdk_not_installed`；QuantLab 真实 handshake ack missing；百万级执行为 partial。

当前最新目标逐项达成审计位于 `runs/goal_readiness_audit_iteration26`。审计结论：10 个验收项中 8 项 passed、1 项 partial、1 项 missing，目标达成审计分数为 85.00%。Moomoo/OpenD 门禁已从 blocked 变为 passed：本机 OpenD socket 可达，`moomoo-api 10.7.6708` 已安装到 QBVS 使用的 Codex Python runtime，`runs/moomoo_opend_probe_iteration26_after_sdk.json` 显示 `ready_for_fetch=true`。

Moomoo/OpenD 真实行情链路已从单标的烟测推进到 batch100 验证：当前已完成 100 个 Moomoo seed 标的的 2020-01-02 至 2026-06-04 日线缓存，合并索引位于 `config/moomoo_batch100_cache_index.csv`，覆盖 82 个 US_ETF 和 18 个 US_STOCK；资产类别为 57 个 ETF、18 个 STOCK、12 个 BOND、10 个 COMMODITY、3 个 FX；质量等级为 98 个 A、2 个 B。第 81-140 批缓存尝试中，20 个成功、40 个失败；失败主因是 Moomoo/OpenD 历史 K 线额度不足，另有 `BRK-B` 符号不被识别。随后使用 `runs/manifests/moomoo_batch100_top20_finalist_3windows_manifest.csv` 完成 100 个 Moomoo 标的、20 个 finalist 策略、3 个滚动窗口的 6,000 个精确验证任务，结果位于 `runs/moomoo_batch100_top20_finalist_3windows_exact`。该 run 的当前第一名为 `bw92_boll_or_rsi_none_ma_trend_full_atr_96`，样本数 300，通过率 93.00%，平均总收益差 -2.18%，平均年化差 -0.78%，平均回撤改善 +0.89%。对应 QuantLab 证据包位于 `handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows`，晋级候选表位于 `handoff/promotion_candidates_moomoo_batch100_top20_finalist_3windows.csv`。这证明真实 OpenD 数据链路可被 QuantLab 只读消费，并且真实样本覆盖已从 80 标的扩展到 100 标的；但还不能替代 200 标的批量真实可交易验证。

第 81-140 批失败已整理为可执行重试计划：`runs/moomoo_batch81_140_retry_plan_20260605.csv`、`runs/moomoo_batch81_140_retry_plan_20260605.json`、`runs/Moomoo_Batch81_140_Retry_Plan_20260605.pdf`。结论：60 个尝试中 20 个已成功缓存、39 个属于 `opend_quota_exhausted`，建议等 OpenD 历史 K 线额度释放后再重试，1 个属于 `symbol_mapping_required`，应先修正 `BRK-B` 这类 class-share 符号映射再单标的探测。当前不建议同日盲目重跑 39 个额度失败项；更高 ROI 的路径是等待额度恢复或用未使用 seed universe 里的替代标的补齐到 200 个真实可交易样本，并且所有新增标的必须先通过 cache index 和质量门禁。

已生成补齐 200 个真实可交易样本的替代标的计划：`config/moomoo_replacement_universe_to_200_20260605.csv`、`runs/moomoo_replacement_to_200_plan_20260605.csv`、`runs/moomoo_replacement_to_200_plan_20260605.json`、`runs/Moomoo_Replacement_To_200_Plan_20260605.pdf`，手动分片命令位于 `campaigns/moomoo_replacement_to_200_20260605/cache_commands.sh`。该计划从未缓存的 seed universe 中选出 100 个候选：CN_ETF 39 个、HK 30 个、US_STOCK 31 个；`BRK-B` 因符号映射问题被排除到修正队列。该计划不自动执行、不启动后台任务、不写 QuantLab；只有在 OpenD 历史 K 线额度可用时，才建议按每片 20 个候选逐片缓存，并在每片后检查质量门禁和 attempts summary。

策略目录已完成反凑数审计，产物为 `runs/behavior_strategy_catalog_audit_20260605.csv`、`runs/behavior_strategy_catalog_audit_20260605.json`、`runs/Behavior_Strategy_Catalog_Anti_Waste_Audit_20260605.pdf`。当前目录共有 240 个交易行为策略组合，其中 200 个已进入 Yahoo 公开行情 200×200 full 验证，20 个进入 top finalist 深度验证，20 个进入 Moomoo batch100 真实数据验证，40 个仍是 `catalog_only_not_yet_validated`。后续结论不得把 240 个目录组合全部当作已验证策略；最终策略描述必须按证据层级区分：目录候选、公开历史全量验证、公开深度验证、Moomoo 真实数据验证。

百万级预算估算位于 `runs/manifests/yahoo_public_200x200_pair_million_scale_budget_8w.json`。按当前 40,000 pair manifest、每 pair 乘以 1,000,000、8 workers、每任务 0.05 秒估算，effective_tasks 为 40,000,000,000，约 69,444.44 小时 wall time。该数值说明最终百万级目标不能靠当前单机逐任务精确回测硬跑完成，必须先用快速筛选压缩候选、再做分布式/分片长跑和真实可交易数据门禁。

当前 finalist 深度验证已完成：`runs/yahoo_public_top20_finalist_200symbols_5windows_exact`。该结果从完整 40,000 pair 基线中按收益底线、通过率和回撤改善筛选 top 20 策略，对 200 标的执行每个标的/策略 5 个代表窗口的深度验证任务，共 20,000 个任务，覆盖 4 个市场和 5 类资产。四个 campaign 分片均为 completed，失败任务为 0。深度复验后的当前第一名为 `bw92_rsi_35_none_ma_trend_full_none`，样本数 1,000，通过率 94.60%，平均总收益差 -0.39%，平均年化差 +0.10%，平均回撤改善 +0.90%。对应 QuantLab 深度证据包位于 `handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows`，晋级候选表位于 `handoff/promotion_candidates_yahoo_public_top20_finalist_200symbols_5windows.csv`。

## 数据契约

标准 OHLCV 必备字段：

- `datetime`
- `symbol`
- `market`
- `open`
- `high`
- `low`
- `close`
- `volume`

核心验证结果字段：

- `strategy_id`
- `symbol`
- `market`
- `start`
- `end`
- `bars`
- `strategy_total_return`
- `strategy_annualized_return`
- `strategy_max_drawdown`
- `strategy_var_5`
- `strategy_cvar_5`
- `buy_hold_total_return`
- `buy_hold_annualized_return`
- `buy_hold_max_drawdown`
- `total_return_gap`
- `annualized_return_gap`
- `drawdown_improvement`
- `passes_user_floor`

## 策略准入规则

策略进入 QuantLab 候选策略库前，建议同时满足：

- 不是凑数策略，必须有明确交易行为逻辑。
- 能解释收益来源、失效环境和参数意义。
- 在随机压力测试中不明显劣化。
- 在真实标的滚动窗口中通过用户收益底线。
- 在事件窗口中没有不可接受的极端亏损。
- 对真实可交易标的有效，而不仅是海外强趋势样本有效。

## 给 QuantLab 的同样指令

如果你在 QuantLab 那边发送同样指令，QuantLab 应执行以下动作：

1. 读取本 `HANDOFF.md`。
2. 读取 `QUANTLAB_INTEGRATION_CONTRACT.json`。
3. 读取 `HANDSHAKE_PROTOCOL.json`。
4. 读取 `handoff/qbvs_handshake_request.json`。
5. 按 `handoff/quantlab_handshake_ack_template.json` 生成 `handoff/quantlab_handshake_ack.json`。
6. 读取推荐证据包中的 `quantlab_bundle_manifest.json` 和 `quantlab_ingestion_payload.json`。
7. 明确 QuantLab 将通过哪个模块读取独立验证系统产物，例如 `quantlab.integrations.independent_validation`、现有报告中心、策略审批页或外部 artifact reader。
8. 不要修改独立验证系统产物，除非用户明确授权。
9. 不要把未通过 QuantLab 侧复核和用户批准的策略直接写入已审批策略库。

## 当前未完成

- 尚未完成 200 标的 Moomoo/OpenD 真实批量行情抓取；当前已完成 SDK/OpenD 小样本烟测、100 标的 batch 缓存和 6,000 任务真实数据精确验证，并已提供 220 标的候选 seed、逐标的缓存命令计划和 `cache-moomoo-batch` 批量缓存命令。当前主要限制是 OpenD 历史 K 线额度，不是本地回测系统能力。
- 尚未完成支付宝自动抓取；当前支持用户导出的支付宝基金净值 CSV 进入标准缓存。
- 尚未完成逐基金条款自动识别；当前已有默认支付宝基金执行规则模板，可手动覆盖申赎费率、确认日、到账延迟和持有约束。
- 尚未完成真正的百万级分布式/长任务执行调度；当前已有快速筛选层、manifest 分片、断点续跑、SQLite 汇总仓库、分层抽样 universe、分层抽样 manifest、200×200 pair manifest，并已完成 4,000 个分层代表性任务和完整 40,000 个 200 标的 × 200 策略真实公开行情 pair 精确任务。
- 尚未完成 QuantLab 源码侧消费接口；当前已提供 QBVS 侧证据包 schema、campaign schema、adapter pack、导出命令和校验命令。
- 尚未完成最终全量策略研究 PDF。

## 当前进度估算

按系统工程交付进度估算：约 99.25%。

按用户原始最终目标逐项验收审计：85.00%。

当前系统已完成“结构化互通基础 + 可恢复批处理 + 结果仓库 + 快速筛选层 + QuantLab 可消费证据包 + QuantLab 只读 adapter pack + 握手请求/ACK 模板 + 真实可交易数据接入前置层 + Moomoo batch100 缓存和精确验证 + 220 标的候选 seed + Yahoo 公开行情 219 标的缓存 + 200 标的 × 200 策略 pair manifest + 跨市场分层代表性短跑 + 支付宝基金执行规则层 + 长任务 campaign 层 + 40,000 个完整 pair 精确回测基线 + top finalist 多窗口深度验证执行与证据包”。但还没有达到“每策略百万级测试”的最终生产能力；下一阶段重点是 QuantLab 侧真实 ACK、OpenD K 线额度恢复后的 200 标的 Moomoo 批量缓存、逐基金规则覆盖、百万级分片调度和 QuantLab 侧落地接入。

## System Coordination ACK 2026-06-05

当前 active goal：独立验证系统继续主导交易行为规律策略的大规模验证、manifest/campaign/worker 和 QuantLab 外部证据包；QuantLab 主导读取 ACK、审批、报告展示和 ResearchBus 主 schema。最新验证规模：Yahoo 公开行情已完成 200 标的 × 200 策略 full 40,000 pair、top 20 finalist 深度 20,000 任务、Moomoo batch100 真实数据 20 策略 × 100 标的 × 3 窗口共 6,000 样本；40 个目录候选已生成 8,000 任务 manifest，并完成 800 任务 sample。QuantLab 真实 ACK 已返回并校验通过：`handoff/quantlab_handshake_ack.json`。当前不可消耗资源/额度：OpenD 历史 K 线额度受限，第 81-140 批仍有 39 个 `opend_quota_exhausted`；`BRK-B` provider code 已由快照确认是 `US.BRK.B`，但历史 K 线仍需在 quota 安全时单标的确认。应交给 QuantLab 的只读证据包优先级：`handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows`、`handoff/quantlab_bundle_yahoo_public_top20_finalist_200symbols_5windows`、`handoff/quantlab_bundle_yahoo_public_200x200_full_40000`、`handoff/quantlab_readonly_adapter_pack`、`handoff/qbvs_handshake_request.json`。建议暂停：继续扩充策略目录数量、重复长跑、非必要 PDF、OpenD 额度未恢复前的批量重抓。下一轮最高优先级：按非 approval 路径恢复最小 goal-readiness audit，并仅在 quota 安全时对 `US.BRK.B` 做单标的历史 K 线确认或按 replacement-to-200 plan 分片推进。

ResearchBus 只读 schema 映射已生成：`handoff/researchbus_schema_mapping_20260605/qbvs_to_quantlab_researchbus_mapping.json` 和 `handoff/researchbus_schema_mapping_20260605/qbvs_to_quantlab_researchbus_field_map.csv`。用途：供 QuantLab 将 QBVS evidence bundle 作为 `independent_validation_runs` / `independent_validation_candidates` 的 `ReviewOnly` 记录读取；硬边界仍是 QBVS 不写 QuantLab 源码/数据库，策略库写入必须等待 QuantLab ACK、QuantLab 侧复核和用户批准。

ResearchBus `ReviewOnly` 样例记录已生成：`handoff/researchbus_schema_mapping_20260605/sample_independent_validation_run_reviewonly.json` 和 `handoff/researchbus_schema_mapping_20260605/sample_independent_validation_candidates_top5.csv`。该样例基于 `handoff/quantlab_bundle_moomoo_batch100_top20_finalist_3windows`，仅供 QuantLab 侧读取/展示/审批流对齐，不代表策略库写入授权。

QuantLab ACK readiness 审计已生成：`handoff/ack_readiness_20260605/qbvs_quantlab_ack_readiness.json` 和 `handoff/ack_readiness_20260605/qbvs_quantlab_ack_readiness_checks.csv`。该产物是 ACK 返回前的历史 readiness 记录；当前已被真实 `handoff/quantlab_handshake_ack.json` 和 `runs/goal_readiness_audit_quantlab_ack_20260605_rerun/` 覆盖。剩余阻塞项不再是 ACK 缺失，而是 OpenD 历史 K 线额度限制；`BRK-B` 的 `US.BRK.B` 快照 provider code 已确认，但历史 K 线仍需 quota 安全后单标的确认。

QuantLab ACK 请求包已生成：`handoff/quantlab_ack_request_packet_20260605/quantlab_ack_request_packet.json` 和 `handoff/quantlab_ack_request_packet_20260605/quantlab_ack_request_packet.md`。用途：给 QuantLab 线程最小化读取清单、ACK 必填字段、只读证据包优先级和硬边界，避免 QuantLab 侧重复建设或误触发 QBVS 长跑/抓取。

2026-06-05 QuantLab 协调线程恢复处理：重新运行 `verify-handshake` 通过，并生成 `runs/goal_readiness_audit_quantlab_ack_20260605_rerun/`。新增 Moomoo/OpenD 符号映射模块 `qbvs/symbol_aliases.py`，`BRK-B` 从 `US.BRK-B` 规范化为 `US.BRK.B`；`qbvs/moomoo_batch.py`、`qbvs/universe_seed.py`、`qbvs/cli.py` 已接入同一规则，当前 seed 和 seed cache plan 已更新。`runs/moomoo_brk_b_alias_snapshot_probe_20260605.json` 显示 `US.BRK.B` 快照返回 1 行，`name=Berkshire Hathaway-B`，未请求历史 K 线。结构化恢复记录：`runs/qbvs_resume_resolution_20260605.json`。仍不能声明 OpenD 批量真实数据验证完成，除非后续历史 K 线额度检查通过。
