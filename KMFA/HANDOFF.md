# KMFA Handoff

更新时间: 2026-07-08

## S19 当前状态

- `每日早晚钉钉考勤检查` 已切换为 DWS live backend，并完成 2026-07-07 live 验证。
- 当前可见组织 44 人；record 成功 44 人，summary 成功 44 人；42 人当天有打卡记录。
- 张霖泽、林全意为已知无考勤记录，record 成功返回空列表，不作为异常。
- 私有归档目录为 `/Users/linzezhang/OneDrive/dingtalk_attendance/202607/`，本轮 raw 文件为 `s19_evening_20260707_095119.raw.jsonl.gz`，SHA256 为 `aabfb6415d95f55d76890d74ef60d3430785f404210679631be470eb47f3a811`。
- Git 只保存 DWS backend 代码、报告模板、路径/统计证据和安全扫描；不保存真实员工考勤明文、raw JSONL、SQLite、机器人地址、应用密钥或访问凭证。
- S19 钉钉通知已升级为多目标路由表：`notification_targets.local.json` / `notification_targets_resolved.json` 仅保存在 ignored private runtime，公开 `notification_targets_manifest.json` 只保留脱敏状态；旧 `notification_channel_resolved.json` 仍兼容迁移。
- 张霖泽目标已迁移并验证为 `dws_open_dingtalk_id_chat` 个人单聊：`notification_probe.py --all-targets` 已发送验证消息 `SENT`；DWS userId 单聊历史失败为 `chat/business_error/系统错误`，openDingTalkId fallback 保持生效。
- S19 通知发送已统一到唯一“考勤通知模板”：`send_latest_report.py --channel auto --targets all` 不重新取考勤，通过多目标路由发送一条 `attendance_notification`；钉钉正文只展示当天命中的“今日异常 / 无考勤”、连续异常和需要休息人员，`缺卡/未打卡/旷工/迟到/早退` 只有当天 summary child row 命中 `work_date` 才进入今日异常；当前自然月累计次数只作为今天命中人员注释，不反向制造今天异常；空板块完全不渲染；当天无异常且取数完整时输出 `本次 N 人全部考勤正常`；`待审批 / 待补卡 / 待核查` 用户可见板块已删除。
- 指定日期个人测试必须使用 `run_attendance.py --work-date YYYY-MM-DD --notification-targets personal`，不得触达生产管理群；默认生产发送目标仍为 `all`。
- 2026-07-08 指定日期测试结果：`2026-07-06` 晨报用 personal target 发送张霖泽成功，dispatch 只含个人目标，正文无 pending 板块和后台诊断；`2026-07-06` 晚报被 DWS gateway timeout/code 6 阻断在 department discovery，未生成报告、未发送个人或群，recovery event `evt_1783485085139817000` 已 finalize failed。
- run_id、北京时间、OneDrive 报告路径和后台取数/权限诊断只保留在 dispatch receipt / manifest / automation JSON，不进入钉钉正文或用户面向管理/HR 报告；automation JSON 输出 `notification_template_text` 和 `notification_delivery_table`。
- S19 需要休息口径：自然月第 23 个有效考勤日开始提醒；丁春法、李永占只从“需要休息人员”和私有 ledger `rest_required_snapshots` 中排除，其他状态仍照常统计。

## S20 当前状态｜钉钉工作检查 daily routine check

- `Dingtalk-routine-check / 钉钉工作检查` 是唯一 S20 automation，时间统一 `Asia/Shanghai`，窗口为 `11:35 -> morning_1135` 和 `17:05 -> evening_1705`。
- 公开代码/规则/测试位于 `KMFA/daily_routine_check_skill/`、`KMFA/metadata/daily_routine_check/`、`KMFA/tools/daily_routine_check/`、`KMFA/tests/test_daily_routine_check.py`。
- 运行输入主路径为 `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip`；reader 流式读取 zip 内 `付款请示群` / `生产管理群` 的 `chat_records/chat_records.csv` 与 `_manifest/manifest.csv`，不解压大包到本机。直接 `DWS_Outputs/` 群目录只作为兼容 fallback；zip 占位或损坏时 healthcheck 输出 `ZIP_INPUT_UNREADABLE`，缺失或过期数据降级为 `SOURCE_MISSING` / `SOURCE_STALE`，不崩溃、不删除源数据。
- 例行异常类型固定为 `missing/late/review/wrong/merged`，提醒等级固定为 `P0/P1/P2`，通知事件包含 `abnormal_type`、`reminder_level`、matched message、confidence 和 reason。
- `morning_1135` 生成杨婷现金 `cash_risk_result`；当前 public-safe 离线实现只从 DWS 消息文本按 `cash_monitor.public.yaml` 配置化金额锚点提取 `total_available_cash`，图片/附件候选无结构化金额时输出 `CASH_NEEDS_REVIEW`，不伪造 OCR。
- SQLite 私有 ledger 写入 `run_log`、`routine_check_results`、`cash_risk_results`、`cash_account_snapshots`、`notification_events`、`data_quality_issues`；`--cleanup --apply` 执行 WAL checkpoint、VACUUM 并写 `cleanup_events`。
- 真实钉钉发送仍需 ignored private runtime 通知配置；缺配置时必须返回 `CONFIG_MISSING`，不得伪造已发送。

## S21 当前状态｜资金与税费管理周报 Skill

- Codex App automation `kmfa` 当前契约为 `Australia/Sydney` 本地每周一、周六 11:00，repo contract 与本机 automation drift check 已纳入验证。
- 默认只读输入为 `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群`；scheduled shell 先跑 `check_source_readiness.py`，非 `READY` 不启动 runner。
- `run_daily_local.sh` 支持 validation-only `KMFA_FUND_RUN_ID`、`KMFA_FUND_VISION_LIMIT` 和 `KMFA_SKIP_CODEX_EXEC=1`，用于固定 run id、小批量 OCR 验收真实 runner/OCR 路径并避免递归 Codex CLI；默认 automation 不设置这些变量。
- runner 现在生成 `automation_readiness.csv`，只读核对 tracked contract 与本机 Codex automation TOML；`schedule_ready=true` 需要 contract `Australia/Sydney`、周一/周六 11:00 rrule 匹配，且 live TOML 如显式写 timezone 不得漂移。S58 真实复跑 `s55_scheduled_entrypoint_real_run_20260708` 后 `CODEX_AUTOMATION_READY`、mismatch=0，automation schedule audit/gate 已 pass/ready；该证据只解除 automation schedule 外部检查，不放行管理结论。
- scheduled Vision OCR 对 timeout 行默认执行 `--retry-timeout-seconds 30 --retry-batch-size 1`；可用 `KMFA_FUND_VISION_RETRY_TIMEOUT_SECONDS` / `KMFA_FUND_VISION_RETRY_BATCH_SIZE` 覆盖。retry 仍只写 private runtime OCR sidecar，不改源、不晋升事实。
- scheduled Vision OCR retry 现在默认 `--retry-max-rows 24`，可用 `KMFA_FUND_VISION_RETRY_MAX_ROWS` 覆盖；generator 每次写 `screenshot_ocr_sidecar_generation_progress.jsonl`，只记录批次状态/计数，不包含 OCR 原文。超预算 timeout 行标记 `ocr_retry_deferred_due_retry_budget`，后续 run 可继续处理。
- S56 真实 retry 已将 `s55_scheduled_entrypoint_real_run_20260708` 的截图 OCR 覆盖从 216/272 提升到 272/272；二次 runner 输出 272 条 OCR 文本候选、2852 条 OCR 值候选、235 条 OCR 资金事实候选，`fund_ledger.csv` / `funding_forecast.csv` 仍只有表头，`management_conclusion_allowed=false`。
- S57 基于同一真实 run_id 复跑 runner 后输出 `fact_promotion_owner_review_batch.csv`：batch=6、authorization-required=4、blocking=4；OCR staging 235 blocked、chat value 55 blocked、attachment 293/290 ready/3 blocked、workbook quality 6 ready；`fund_ledger.csv` / `funding_forecast.csv` 仍 0 行，`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- 当前 runner 对真实结构化 CSV 必需列 `date/company/bank/account_alias/liquidity_tier/inflow/outflow/ending_balance/flow_type` 执行 Decimal 抽取，产出 `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW` 的资金事实、净流、公司银行矩阵和税费/保证金/借款/项目成本风险。
- 当存在结构化事实时，runner 以 OOXML cell patch 写入原生 `.xlsx`：`01_首页总览` 4+4 卡片、`02_资金趋势预测` 已知到期项 projection、`03_三层净流余额`、`04_税费融资风险`、`05_公司银行矩阵`、隐藏 `H01/H02/H03/H05`；不重写图表包，保留首页最近 15 天/30 天两张原生折线图。
- runner 现在从真实结构化 CSV 的 `due_date` 税费/保证金/借款/项目成本风险/机会行生成 `funding_forecast.csv`，并写入 `02_资金趋势预测`；这些 projection 只按 `known_due_date_structured_csv` 进入待复核，不生成无证据预测、付款动作或管理结论。
- runner 现在生成 `cashflow_validation.csv`，逐资金行校验余额连续性、经营现金流影响和内部调拨排除；连续性失败追加 `BALANCE_CONTINUITY_GAP` 异常任务，并写入隐藏 `H05_复审检查`。
- runner 现在生成 `workbook_quality_checks.csv`，对生成后的原生 Excel 检查 sheet 顺序、隐藏审计页、可见 row 2 清理、图表尺寸、公式错误标记和可见敏感值形态；失败会写异常任务并阻断管理结论。
- runner 现在在 workbook quality 检查前写入隐藏 `H06_配置规则` 运行时规则表，记录 `run_id`、`source_input_dir`、Sydney 调度 rrule、no-hallucination policy、事实晋升/账本/管理结论 fail-closed 标志和 private runtime 边界；该表只做审计，不授权事实晋升或管理结论。
- runner 现在生成 `goal_completion_audit.csv`，按最终目标逐项记录证据状态和下一步；正式事实晋升、管理结论和 automation 本地状态仍需独立授权/外部检查，不因审计存在而自动放行。
- runner 现在生成 `fact_promotion_review_packet.csv`，汇总结构化事实、OCR ledger staging、聊天金额候选、附件证据完整性、workbook quality 和目标审计，作为 owner 复核/授权准备包；所有行仍 no-write/no-promote。
- runner 现在生成 `fact_promotion_owner_review_batch.csv`，从复核包派生六个 owner-review 批次，汇总 candidate/ready/blocker 计数、`owner_review_status` 和 recommended owner action；所有行仍 `financial_fact_promotion_allowed=false`、`fund_ledger_write_allowed=false`、`financial_fact_promoted=false`、`management_conclusion_allowed=false`，不执行授权、不晋升事实、不写正式账本。
- runner 现在生成 `fact_promotion_authorization_template.json`，从复核包逐行生成默认 `authorized=false` 的 owner-review 授权草稿；scope 为 `fact_promotion_review_packet_validation_only`，仍不允许事实晋升、正式账本写入或管理结论。
- runner 现在生成 `fact_promotion_authorization_preview.csv`，只验证 private `fact_promotion_authorizations/<run_id>.json` 对复核包行的覆盖情况；有效行最多进入 `ready_for_owner_review_no_fact_promotion`，仍不允许事实晋升、正式账本写入或管理结论。
- runner 现在生成 `fact_promotion_execution_gate.csv`，合并 owner 授权覆盖和 review blockers；`authorization_required=false` 的 review area 输出 `not_required_*` no-op 审计行且不计 blocked，ready 行最多进入 `ready_for_controlled_fact_promotion_execution`；本轮仍不允许执行事实晋升、写正式账本或生成管理结论。
- runner 现在生成 `fact_promotion_execution_dry_run.csv`，从执行门禁派生 no-write 影响预览；ready 行最多进入 `ready_for_controlled_execution_preview_no_write` 并显示 `dry_run_impact_count`，所有行仍 `fact_promotion_execution_allowed=false`、`fund_ledger_write_allowed=false`、`financial_fact_promoted=false`、`management_conclusion_allowed=false`。
- runner 现在生成 `fact_promotion_execution_plan.csv`，从 dry-run 行派生 owner-facing 执行计划；ready 行最多进入 `ready_for_owner_execution_authorization_no_write` 并声明 `required_authorization_scope=controlled_fact_promotion_execution`，所有行仍 `source_mutation_allowed=false`、`fact_promotion_execution_allowed=false`、`fund_ledger_write_allowed=false`、`financial_fact_promoted=false`、`management_conclusion_allowed=false`。
- runner 现在生成 `fact_promotion_execution_authorization_template.json` 和 `fact_promotion_execution_authorization_preview.csv`，只验证 private `fact_promotion_execution_authorizations/<run_id>.json` 对 execution plan 行的覆盖情况；有效行最多进入 `ready_for_controlled_execution_run_no_write`，所有行仍 `source_mutation_allowed=false`、`fact_promotion_execution_allowed=false`、`fund_ledger_write_allowed=false`、`financial_fact_promoted=false`、`management_conclusion_allowed=false`。
- runner 现在生成 `fact_promotion_execution_apply_gate.csv`，从 execution authorization preview 派生正式写账前最后 no-write 门禁；ready 行最多进入 `ready_for_controlled_execution_apply_no_write` 并显示 `planned_apply_count`，所有行仍 `source_mutation_allowed=false`、`fact_promotion_execution_allowed=false`、`fund_ledger_write_allowed=false`、`financial_fact_promoted=false`、`management_conclusion_allowed=false`。
- runner 现在生成 `management_conclusion_gate.csv`，把源就绪、Workbook 质量、正式事实晋升执行、正式账本、现金流校验、证据复核和 automation 外部检查汇总为 C-level 结论前门禁；所有行仍 `management_conclusion_allowed=false`。
- runner 现在生成 `owner_action_queue.csv`，从阻断/外部检查门禁派生 owner 下一步动作；所有行仍 `automation_safe=false`、`source_mutation_allowed=false`、`fact_promotion_allowed=false`、`fund_ledger_write_allowed=false`、`management_conclusion_allowed=false`，不执行授权、不改源、不晋升事实、不写正式账本。
- `tools/materialize_fund_source.py` 现在支持显式 ZIP materialization：目录候选用 `--source-dir`，`DWS_Outputs.zip` 候选用 `--source-zip --zip-prefix 付款请示群`；dry-run 不建目标目录，apply 只复制该群 prefix 下缺失文件，hash 冲突、坏 ZIP 或 unsafe member fail-closed。
- ZIP materialization 现在兼容真实 `DWS_Outputs.zip` 的 `DWS_Outputs/付款请示群/...` 外层目录布局；S25 已 dry-run 验证 297 个付款请示群文件后显式 apply 到 `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群`，`check_source_readiness.py` 返回 `READY`、file_count=297、unreadable_count=0。
- S25 已基于该真实热目录运行 `run_fund_weekly_analysis.py --run-id s25_real_input_index_20260708`，状态为 `INDEXED_PENDING_EXTRACTION`；输出包索引 297 个真实源文件，生成原生 Excel 母版副本，`management_conclusion_allowed=false`，`fund_ledger.csv` 和 `funding_forecast.csv` 仍为空，未生成虚构金额或管理结论。
- runner 现在将截图相邻真实 `.ocr.txt` 文本侧车写入 `ocr_text_candidates.csv`，并从该文本抽取日期/金额候选到 `ocr_value_candidates.csv`，关联原截图 evidence 并追加 `OCR_TEXT_PENDING_REVIEW` / `OCR_VALUE_PENDING_REVIEW` 任务；OCR 文本和值候选只进入待复核链路，`financial_fact_promoted=false`，不自动生成金额或管理结论。
- runner 现在将真实 `chat_records/chat_records.csv` 的 `content` / `quoted_content` 资金相关文本写入 `chat_text_candidates.csv`，并从该文本抽取日期/金额候选到 `chat_value_candidates.csv`，追加 `CHAT_TEXT_PENDING_REVIEW` / `CHAT_VALUE_PENDING_REVIEW` 任务；聊天文本和值候选只进入待复核链路，`financial_fact_promoted=false`，不自动生成金额或管理结论。
- S26 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s26_real_chat_candidates_20260708`，索引 295 个真实源文件，生成 `chat_text_candidates.csv` 136 行、`chat_value_candidates.csv` 55 行；其中日期候选 9、金额候选 46，`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`management_conclusion_allowed=false`，workbook quality 6/6 PASS。
- runner 现在使用真实 `_manifest/manifest.csv` 的 `message_id/output_path` 将聊天文本/值候选关联到附件 evidence，写入 `chat_evidence_links.csv` 和 `CHAT_EVIDENCE_LINK_PENDING_REVIEW` 任务；这些链接只用于 cross-review，`financial_fact_promoted=false`，不写入 `fund_ledger.csv` 或形成管理结论。
- S27 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s27_real_chat_evidence_links_20260708`，索引 295 个真实源文件，生成聊天-附件证据链路 36 行，其中 35 行命中 evidence index、1 行 evidence missing 待复核；`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`generated_financial_amount_count=0`，`management_conclusion_allowed=false`，workbook quality 6/6 PASS。
- runner 现在将真实 `_manifest/manifest.csv` 的每条附件资源行全量核对到 evidence index，写入 `attachment_evidence_reconciliation.csv`；缺 output path、缺 evidence、SHA 不一致会写 `ATTACHMENT_EVIDENCE_RECONCILIATION_FAIL` 阻断任务，不允许事实提升。
- S28 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s28_real_attachment_reconciliation_20260708`，索引 295 个真实源文件，核对 293 条 manifest 附件资源行，其中 290 条 evidence 命中待复核、1 条 evidence missing 阻断、2 条 manifest output path missing 阻断；`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`generated_financial_amount_count=0`，`management_conclusion_allowed=false`，workbook quality 6/6 PASS。
- runner 现在将附件 evidence 阻断行转换为 `attachment_reconciliation_remediation.csv` operator action queue；这些 action 只给人工/受控修复路由使用，`automation_safe=false`、`formal_fact_allowed=false`，不修改源文件、不生成资金事实。
- S29 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s29_real_attachment_remediation_20260708`，索引 295 个真实源文件，生成 3 条 remediation，其中 `restore_or_materialize_output_file=1`、`rerun_dws_attachment_download=2`；`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`generated_financial_amount_count=0`，`management_conclusion_allowed=false`。
- runner 现在为附件修复队列输出 `attachment_remediation_dry_run.csv`，只评估下一步状态；所有 dry-run 行保持 `safe_to_apply=false`、`apply_performed=false`、`formal_fact_allowed=false`。
- S30 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s30_real_attachment_remediation_dry_run_20260708`，索引 295 个真实源文件，生成 3 条 dry-run，其中 `source_restore_required=1`、`dws_rerun_required=2`；`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`generated_financial_amount_count=0`，`management_conclusion_allowed=false`。
- runner 现在将附件修复 dry-run 转换为 `attachment_repair_plan.csv` plan-only 步骤，记录 command family 和人工确认要求；所有 plan 行保持 `operator_confirmation_required=true`、`source_mutation_allowed=false`、`apply_performed=false`。
- S31 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s31_real_attachment_repair_plan_20260708`，索引 295 个真实源文件，生成 3 条 repair plan，其中 `source_materialization_plan=1`、`dws_archive_controlled_rerun=2`；`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`generated_financial_amount_count=0`，`management_conclusion_allowed=false`。
- runner 现在将附件修复计划转换为 `attachment_repair_apply_gate.csv` fail-closed 授权闸门；无 private operator authorization manifest 时所有 gate 行保持 `operator_authorization_present=false`、`apply_allowed=false`、`source_mutation_allowed=false`、`apply_performed=false`。
- S32 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s32_real_attachment_apply_gate_20260708`，索引 295 个真实源文件，生成 3 条 apply gate，全部 `blocked_missing_operator_authorization`；`attachment_repair_apply_allowed_count=0`，`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`generated_financial_amount_count=0`，`management_conclusion_allowed=false`。
- runner 现在支持 private `attachment_repair_authorizations/<run_id>.json` validation-only 授权 manifest schema；只验证 `authorization_manifest_version=1`、匹配 `run_id`、`authorization_scope=attachment_repair_plan_validation_only`、`source_mutation_allowed=false`、`apply_execution_allowed=false` 和 row-level `repair_plan_authorizations`。有效授权行只写 `authorization_validation_status=valid_manifest_validation_only`，仍不执行修复、不允许 source mutation。
- S33 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s33_real_authorization_manifest_schema_20260708`，索引 295 个真实源文件，生成 3 条 apply gate，全部 `missing_authorization_manifest` / `blocked_missing_operator_authorization`；`attachment_repair_authorization_valid_count=0`，`attachment_repair_apply_allowed_count=0`，`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`management_conclusion_allowed=false`。
- runner 现在在每次 run 目录输出 `attachment_repair_authorization_template.json` 草稿，供人工审阅后另存为 private authorization manifest；模板行默认 `authorized=false`，生成模板本身不会改变 apply gate 状态。
- S34 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s34_real_authorization_template_20260708`，索引 295 个真实源文件，生成 3 行 authorization template，`authorized=true` 为 0；3 条 apply gate 仍全部阻断，`attachment_repair_apply_allowed_count=0`，`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`management_conclusion_allowed=false`。
- runner 现在输出 `attachment_repair_authorization_preview.csv`，从 apply gate 派生授权覆盖影响；有效授权最多进入 `ready_for_operator_review_no_apply`，仍不执行修复、不允许 source mutation、不解锁正式事实。
- S35 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s35_real_authorization_preview_20260708`，索引 295 个真实源文件，生成 3 条 authorization preview，全部 `missing_authorization_manifest` / `blocked_missing_operator_authorization`；`attachment_repair_authorization_preview_ready_count=0`、`attachment_repair_authorization_preview_blocked_count=3`、`attachment_repair_apply_allowed_count=0`，`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`management_conclusion_allowed=false`。
- 本地 Codex automation `kmfa` 已重新与 repo mirror 对齐：tracked `weekly_1100_sydney.prompt.md` 和 `codex_app_automation.contract.toml` 反映当前本机 symlink alias cwds、周一/周六 11:00 本地排程与上游 DWS zip 优先级，`check_codex_app_automation.py` 返回 `CODEX_AUTOMATION_READY`。
- runner 现在输出 `screenshot_ocr_coverage.csv`，逐张 screenshot evidence 审计真实 OCR sidecar 覆盖状态；缺侧车的截图写 `SCREENSHOT_OCR_MISSING` 阻断任务，不调用 OCR、不读取图片内容、不生成金额事实。
- S36 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s36_real_screenshot_ocr_coverage_20260708`，索引 295 个真实源文件，生成 272 条 screenshot OCR coverage，全部 `ocr_text_sidecar_missing`；`screenshot_ocr_ready_count=0`、`screenshot_ocr_missing_count=272`、`ocr_text_candidate_count=0`、`ocr_value_candidate_count=0`，`fund_ledger.csv` / `funding_forecast.csv` 仍为空，`management_conclusion_allowed=false`。
- scheduled shell 现在在 runner 成功后调用 `generate_screenshot_ocr_sidecars.py` 生成私有 OCR sidecar generation plan；默认 dry-run，不修改 OneDrive 源目录，不写空 OCR sidecar，不生成金额事实。
- S37 已基于最新真实热目录运行 `run_fund_weekly_analysis.py --run-id s37_real_ocr_sidecar_generation_plan_20260708`，随后执行 `generate_screenshot_ocr_sidecars.py --engine mdls` dry-run；计划 272 条截图 OCR sidecar 生成行，全部 `no_text_from_engine`，`generated_sidecar_count=0`、`text_available_count=0`、`financial_fact_promoted=false`，未写入 `private_runtime/ocr_sidecars/` 文件。
- S38 已按用户最新指令将 live Codex App automation `kmfa`、repo contract、prompt 和 launchd fallback 从旧时间改为每周一/周六 11:00 悉尼本地时间；`check_codex_app_automation.py` 返回 `CODEX_AUTOMATION_READY`。真实运行 `run_fund_weekly_analysis.py --run-id s38_schedule_update_real_run_20260708` 索引 295 个真实源文件，生成 workbook `资金与税费管理母版_s38_schedule_update_real_run_20260708.xlsx`，状态仍为 `INDEXED_PENDING_EXTRACTION`，`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S39 已将 repo mirror 追平 live automation 的干净显示入口：`/Users/linzezhang/Documents/Codex/workspaces/dws-kmfa-automation/dws-archive` 和 `.../kmfa-codexproject` 均为 symlink alias，分别指向真实 DWS 归档项目与 `/Users/linzezhang/CodexProject`；不是新的 worktree。repo contract、prompt 与 live automation 再次一致。真实运行 `run_fund_weekly_analysis.py --run-id s39_alias_sync_real_run_20260708` 通过 alias cwd 执行，索引 295 个真实源文件，生成 workbook `资金与税费管理母版_s39_alias_sync_real_run_20260708.xlsx`，`workbook_quality_check_count=6`、`workbook_quality_blocking_count=0`、`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S40 已接入本机 Apple Vision OCR：`generate_screenshot_ocr_sidecars.py` 支持 `--engine vision`、`--vision-batch-size` 和 per-batch `--timeout-seconds`，scheduled shell 默认 `--engine vision --apply` 写入 private runtime OCR sidecars。真实运行 `s40_vision_ocr_sidecars_20260708` 已补齐 272/272 个 screenshot private OCR sidecar；runner 以同一 `run_id` 二次索引后输出 `ocr_text_candidate_count=272`、`ocr_value_candidate_count=2352`、`screenshot_ocr_missing_count=0`，但 `fund_ledger.csv` 仍为空、`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。plan 只含 path/length/hash，不含 OCR 原文，sidecar 与 plan 均被 `private_runtime/` gitignore 排除，`financial_fact_promoted=false`。
- S41 已修复 private OCR generation plan 的续跑覆盖风险：生成器保留已成功 apply 的 plan 行，新批次追加下一个 generation id；`run_daily_local.sh` 在新增 private sidecar 后用同一 `run_id` 再跑一次 runner，把 private Vision OCR sidecar 纳入待复核候选链路，不写回 OneDrive 源目录、不自动晋升事实。
- S42 已新增 `ocr_financial_fact_candidates.csv`：runner 从 OCR 文本中按公司、银行、资金类别和金额关键词生成可复核资金事实候选，并写入 `OCR_FACT_CANDIDATE_PENDING_REVIEW` 异常任务。真实运行 `s40_vision_ocr_sidecars_20260708` 生成 273 条 OCR 资金事实候选，其中 `payment_outflow=247`、`bank_deposit=7`、`electronic_bill=4`、`tax_payment=9`、`deposit_release=1`、`loan=5`；所有行 `financial_fact_promoted=false`，`fund_ledger.csv` 仍为空，`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S43 已新增 OCR fact review 授权门禁：runner 输出 `ocr_fact_review_apply_gate.csv`、`ocr_fact_review_authorization_template.json` 和 `ocr_fact_review_authorization_preview.csv`；private `ocr_fact_review_authorizations/<run_id>.json` 只做 validation-only 覆盖检查。真实运行 `s40_vision_ocr_sidecars_20260708` 生成 273 条 gate rows，全部 `blocked_missing_operator_authorization`；模板 273 行全部 `authorized=false`；preview 273 行全部 blocked；`fund_ledger.csv` 仍为空，`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S44 已新增 `ocr_fact_cross_review.csv`：runner 按 OCR 资金事实候选 metric 聚合候选数、金额合计、证据数、公司/银行缺失数和授权阻断数，供人工 cross-review 使用。真实运行 `s40_vision_ocr_sidecars_20260708` 生成 6 个 cross-review groups：`bank_deposit=7`、`deposit_release=1`、`electronic_bill=4`、`loan=5`、`payment_outflow=247`、`tax_payment=9`；所有 group `operator_authorized_count=0`、`fund_ledger_write_allowed=false`、`financial_fact_promoted=false`，`fund_ledger.csv` 仍为空，`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S45 已新增 `ocr_fact_ledger_staging_preview.csv`：runner 将 OCR fact 候选映射为 ledger-like 人工复核行，标注 `proposed_amount_role`、`proposed_liquidity_tier`、`proposed_flow_type` 和授权状态。真实运行 `s40_vision_ocr_sidecars_20260708` 生成 273 条 preview，全部 `blocked_missing_operator_authorization`；role 分布为 `outflow=256`、`balance=11`、`financing_or_balance_review=5`、`inflow=1`；所有行 `fund_ledger_write_allowed=false`、`financial_fact_promoted=false`，`fund_ledger.csv` 仍为空，`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S69 已将 `screenshot_ocr_coverage.csv` 汇总追加到 `fact_promotion_review_packet.csv` 第 7 行 `screenshot_ocr_coverage`，保持原 `FPRP-*-00001` 至 `00006` 授权 ID 稳定；真实运行 `s69_ocr_coverage_review_packet_real_run_20260708` 显示截图 272、OCR ready 0、missing 272，`authorization_required=false`，只暴露 OCR sidecar 前置阻断，不授权事实晋升、不写正式账本、不生成管理结论。
- S70 已为 scheduled entrypoint 增加 validation-only `KMFA_FUND_VISION_LIMIT`。完整未限流 OCR 验收曾在 Vision retry 路径超过 9 分钟无 sidecar 输出后中断；小批量真实验收 `s70_scheduled_ocr_limit4_same_run_20260708` 生成 4 条 private OCR sidecar 并同 run_id 二次索引，得到 OCR ready 4、missing 268、OCR text 4、OCR value 19、OCR financial fact 0，`management_conclusion_allowed=false`。
- S71 已为 OCR retry 增加预算和 progress JSONL，避免 timeout 行按 30 秒逐个重试时 scheduled entrypoint 长时间无落盘进度；默认 retry 最多 24 行，剩余 timeout 行 deferred。真实验收 `s71_scheduled_retry_budget_progress_20260708` 在 `KMFA_FUND_VISION_LIMIT=2`、retry max 1 下生成 2 条 private sidecar，同 run_id 二次索引后 OCR ready 2、missing 270、OCR text 2、OCR value 17、OCR financial fact 0，progress 4 行且不含 OCR 原文；仍不晋升事实、不写正式账本、不生成管理结论。
- S72 已完成不设 `KMFA_FUND_VISION_LIMIT` 的完整 scheduled entrypoint 验收 `s72_scheduled_full_retry_budget_20260708`：source readiness `READY`、file_count=295；OCR planned 272、generated sidecar 240、retry attempted/generated 24/24、deferred 32；progress JSONL 117 行且不含 OCR 原文。同 run_id 二次索引后 OCR ready 240、missing 32、OCR text 240、OCR value 1652、OCR financial fact 248；`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S73 已用同一 run_id `s72_scheduled_full_retry_budget_20260708` 做 OCR resume，受控设置 `KMFA_FUND_VISION_RETRY_MAX_ROWS=32` 处理剩余 deferred 行；最终 OCR plan 272/272 generated，coverage ready 272、missing 0，OCR text 272、OCR value 2627、OCR financial fact 259。`screenshot_ocr_coverage` review packet 行已 pass、blocked 0，但仍 `fund_ledger_write_allowed=false`、`financial_fact_promoted=false`、`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。
- S74 已新增 `ocr_fact_owner_review_batch.csv`，把 OCR fact cross-review 的 6 个 metric 分组转成 owner 批次；真实复跑 `s72_scheduled_full_retry_budget_20260708` 后 6 行全部 P0 / `blocked_metric_review_required`，覆盖 `payment_outflow=235`、`bank_deposit=7`、`tax_payment=6`、`loan=6`、`electronic_bill=4`、`deposit_release=1`；仍 no-write/no-promote/no-conclusion。
- S75 已验证 OCR fact owner batch validation-only 授权覆盖链路：单测覆盖 private 授权后 ready/blocked 混合状态；真实 run_id `s72_scheduled_full_retry_budget_20260708` 的 ignored validation fixture 仅授权 `deposit_release` 候选，复跑后该 batch 为 `ready_for_owner_review_no_ledger_promotion`，其余 5 个 batch 仍 blocked；`fund_ledger.csv` 0 行、`generated_financial_amount_count=0`、`management_conclusion_allowed=false`。该 fixture 不是 owner 业务批准。
- S76 已新增管理结论 release 授权模板/预览 sidecar：真实复跑 `s72_scheduled_full_retry_budget_20260708` 后 `management_conclusion_authorization_template.json` / `management_conclusion_authorization_preview.csv` 存在，pre-release gates ready=3、blocking=4，preview 为 `blocked_release_preconditions_not_ready`，release auth valid=0，`management_conclusion_allowed=false`。该链路只做 validation-only 发布授权预览，不生成管理结论、不写账、不改源。
- S77 已新增 `evidence_cross_review_resolution_plan.csv`：真实复跑 `s72_scheduled_full_retry_budget_20260708` 后输出 3 个 owner resolution plan 分组，分别为 OCR ledger staging 258、chat value 55、attachment evidence 3，合计 blocker 316；所有行 no-write/no-promote/no-conclusion，evidence gate 仍 blocked。
- S78 已新增 `attachment_repair_source_locator.csv`：真实复跑 `s72_scheduled_full_retry_budget_20260708` 后 3 个 attachment remediation blocker 中，1 个缺失 output 文件在当前 input dir 与 `DWS_Outputs.zip` 均未找到，2 个 manifest output_path 缺失只能进入 DWS attachment rerun/manifest repair；locator candidate=0、apply allowed=0，所有行 no-write/no-apply/no-conclusion。
- runner 现在承接 public-safe KMFA metadata 信号：资金压力、项目成本事实层、报告等级、scope reconciliation，输出 `kmfa_metadata_signals.csv` 并写入 `04_税费融资风险` / `H02_异常任务池`；这些只用于待复核路由，不生成金额、预测或正式动作。
- 所有结构化 CSV 金额仍是待复核事实，`management_conclusion_allowed=false`；不得把 workbook 首页卡片解释为最终 C-level 管理结论。
- 当前真实 OneDrive 热目录已 materialized 并达到 `READY`。若后续目标目录再次缺失或 OneDrive cloud-only/dataless，仍保持 `SOURCE_MISSING` / `SOURCE_UNREADABLE` fail-closed，不生成局部生产包。

## 当前目标

v1.2 FULL_HTML_NO_OMISSION 完整任务包已成为 KMFA 后续开发基线。Stage 1-18 均已完成本地实现、验证、整体复审和 GitHub main 上传；Post-S18 Part 1-6 已在 canonical worktree 本地通过并生成 validator/evidence/local-governance 记录。Post-S18 第二阶段全项目本地复审已完成：新增 task pack zero-delta synthetic fixture、lineage completeness 阻断 validator、whole-project final review validator 和当前全项目 Go/No-Go。当前 `STAGE18_GITHUB_UPLOAD_PENDING` 已从最新全项目 Go/No-Go blocker 中移除并记录为 resolved，但项目仍为 `NO_GO`，`delivery_allowed=false`。随后已独立完成 KMFA worktree cleanup：只保留 canonical `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`，确认无遗留 `kmfa-s*` worktree，删除空旧目录 `/Users/linzezhang/Documents/KMFA v0.1`。Lineage / Report Gate 已独立锁定：0 条 actual lineage rows、2 条 D 级 report runtime、12 条 pending reconciliation 继续阻断正式报告、经营决策依据、release claim 和 delivery claim。Final GitHub backup evidence 已按 `NO_GO governance backup only` 生成并基于最新 `origin/main` rebase；本轮仍未执行 lineage full check completion、正式报告、live connector、OpMe 深度耦合、生产恢复或业务动作。

## v0.1.3 当前续跑状态

- 当前本地分支: `codex/kmfa`
- 当前版本: `0.1.3-stage1-10-github-upload`
- 当前已完成: `v0.1.3 Stage 1-10 GitHub upload gate local validation`
- 证据目录: `KMFA/stage_artifacts/V013_STAGE1_10_GITHUB_UPLOAD/`
- Stage 7 复审结论: S07-P1/S07-P2/S07-P3 replay validators 全部 PASS；legacy S07-P1 finance adapter validator/unit、legacy S07-P2 WPS adapter validator/unit、legacy S07-P3 Redcircle postponement validator/unit 均 PASS；Stage 7 review validator 和 focused unit test PASS。复审确认 phase_results=`S07-P1=PASS, S07-P2=PASS, S07-P3=PASS`、open findings=`0`、Q5 allowed count=`0`、formal report allowed count=`0`、Redcircle automatic connector allowed=`false`、data quality=`Q4`、report grade=`D`、release permission=`blocked`、`s08_p1_performed=false`、`github_upload_performed=false`。
- upload policy: v1.3 不按单个 Stage 做 GitHub upload gate；Stage 1-10 已全部完成并完成 batch overall review，当前只允许执行一次性 Stage 1-10 GitHub upload gate。不得把 Stage 4、Stage 5、Stage 6、Stage 7、Stage 8、Stage 9 或 Stage 10 单独 upload 作为 active next step。
- S08-P1 结论: 已重放既有 public-safe 项目组合键能力，锁定 8 个 hash-only 组件、4 个 profiles、3 个 match results、2 条人工复核队列、1 条 strong auto match、10000 bps 权重总和、8500/7000/5000 bps 阈值。
- S08-P2 结论: 已重放既有 public-safe 业务实体模型能力，锁定 8 类实体、14 条关系、32 条 lifecycle statuses、每类实体 4 个状态；实体值保持 hash/ref only，关系保持 schema-only，生命周期保持 status-only；S08-P3 已由后续 phase 完成，GitHub upload 未执行。
- S08-P3 结论: 已重放既有 public-safe 匹配质量能力，锁定 4 类质量场景、4 条 quality cases、3 条 manual review queue、1 份 entity_matching_report 和 high=2/medium=1/low=1 风险汇总；人工复核队列 `auto_merge_allowed=false`，Stage 8 review 已由本轮完成，GitHub upload 未执行。
- Stage 8 review 结论: S08-P1/S08-P2/S08-P3 replay validators 全部 PASS；focused unit test 和 Stage 8 review validator PASS；phase_results=`S08-P1=PASS, S08-P2=PASS, S08-P3=PASS`、open findings=`0`、fixed findings=`1`、Q5 allowed count=`0`、formal report allowed count=`0`、legacy Stage 8 upload artifacts current gate=`false`、data quality=`Q4`、report grade=`D`、release permission=`blocked`、`s09_p1_performed=false`、`github_upload_performed=false`。
- S09-P1 结论: 已重放既有 public-safe 项目成本事实层能力并验证 v0.1.3 Stage 8 review dependency；锁定 required metrics=`6`、cost categories=`9`、fact records=`4`、unallocated pool=`9`、authority locked fields=`40`、excluded fields=`5`、business entity types=`8`、project identity profiles=`4`、manual review queue=`3`、unresolved differences=`1`、blocked quality results=`2`；metric/cost category value 均保持 hash/private-ref only，formal calculation allowed=`0`，report grade=`D`，release permission=`blocked`，`s09_p2_performed=false`、`s09_p3_performed=false`、`stage9_review_performed=false`、`github_upload_performed=false`。
- S09-P2 结论: 已重放既有 public-safe 毛利与现金毛利层能力并验证 v0.1.3 S09-P1 dependency；锁定 required margin metrics=`4`、project cost fact records=`4`、margin records=`4`、scope difference summary records=`12`、authority field groups=`8`、manual review queue=`3`、unresolved differences=`1`、zero-delta fail count=`1`、blocked quality results=`2`；authority/system/cash value 均保持 hash/private-ref only，authority/system overwrite allowed=`0`，public amount values committed=`0`，formal report allowed=`false`，`s09_p3_performed=false`、`stage9_review_performed=false`、`github_upload_performed=false`。
- S09-P3 结论: 已重放既有 public-safe 口径转换与差异核对层能力并验证 v0.1.3 S09-P2 dependency；锁定 reconciliation records=`12`、domain controls=`6`、required reconciliation domains=`6`、required human fields=`8`、confirmed resolutions=`0`、pending resolutions=`12`、authority/system recomputed domain records=`8`、bank/receivable aging domain records=`4`；derived metric rerun allowed=`false`、formal report rerun allowed=`false`、formal report allowed=`false`、stage9_review_performed=`false`、github_upload_performed=`false`。
- Stage 9 review 结论: 已本地完成 v0.1.3 Stage 9 overall review；S09-P1/S09-P2/S09-P3 replay validators、legacy S09 validators、Stage 9 review validator 和 focused unit test 均 PASS；phase_results=`S09-P1=PASS, S09-P2=PASS, S09-P3=PASS`、open findings=`0`、fixed findings=`1`、pending resolutions=`12`、confirmed resolutions=`0`、legacy Stage 9 upload artifacts current gate=`false`、data quality=`Q4`、report grade=`D`、release permission=`blocked`、`s10_p1_performed=false`、`github_upload_performed=false`。
- S10-P1 结论: 已本地完成 v0.1.3 report templates replay；验证 v0.1.3 Stage 9 review dependency 并复用 legacy S10-P1 public-safe artifacts，锁定 template_count=`2`、section_count=`11`、project_cost_section_count=`4`、business_overview_section_count=`7`、pending_reconciliation_count=`12`、formal_report_count=`0`、export_artifact_count=`0`；`trusted_grade_assignment_allowed=false`、`report_runtime_scope_count=0`、`s10_p2_performed=false`、`s10_p3_performed=false`、`stage10_review_performed=false`、`github_upload_performed=false`。
- S10-P2 结论: 已本地完成 v0.1.3 report grade runtime replay；验证 v0.1.3 S10-P1 dependency 并复用 legacy S10-P2 public-safe report grade artifacts，锁定 report_grade_record_count=`2`、grade_distribution=`D:2`、pending_reconciliation_count=`12`、confirmed_resolution_count=`0`、source_quality_grade=`Q4`、zero_delta_passed=`false`、full_trusted_report_allowed_count=`0`、formal_report_count=`0`、export_artifact_count=`0`；record/template/formula/mapping/field mapping/grade policy/release gate versions 已绑定；`s10_p3_performed=false`、`stage10_review_performed=false`、`github_upload_performed=false`。
- S10-P3 结论: 已本地完成 v0.1.3 report export replay；验证 v0.1.3 S10-P2 dependency 并复用 legacy S10-P3 public-safe report export artifacts，锁定 report_export_record_count=`2`、html_export_count=`2`、csv_appendix_count=`2`、excel_compatible_download_count=`2`、committed_pdf_file_count=`0`、committed_excel_file_count=`0`、formal_report_count=`0`、business_decision_basis_count=`0`、pending_reconciliation_count=`12`、grade_distribution=`D:2`；HTML 继承蓝色商务样板，Excel 下载保持 compatible CSV，PDF 仅 private-runtime-only policy；`stage10_review_performed=false`、`github_upload_performed=false`。
- Stage 10 review 结论: 已本地完成 v0.1.3 Stage 10 overall review；复跑 S10-P1/S10-P2/S10-P3 replay validators、legacy S10 validators、legacy Stage 10 review validator、v0.1.3 Stage 10 review validator 和 focused unit test，phase_results=`S10-P1=PASS, S10-P2=PASS, S10-P3=PASS`，open findings=`0`，fixed findings=`2`，report_template_count=`2`，report_grade_record_count=`2`，report_export_record_count=`2`，html_export_count=`2`，csv_appendix_count=`2`，excel_compatible_download_count=`2`，pending_reconciliation_count=`12`，confirmed_resolution_count=`0`，formal_report_count=`0`，business_decision_basis_count=`0`，legacy Stage 10 upload artifacts current gate=`false`，GitHub upload status=`not_uploaded_deferred_until_stage1_10_batch`。
- Stage 1-10 batch review 结论: 已本地完成 v0.1.3 Stage 1-10 batch overall review；复核 S01-S10 共 10 个 v0.1.3 stage review manifest，stage_results 全部 `PASS`，open_stage_review_finding_count=`0`，open_batch_finding_count=`0`，fixed_batch_finding_count=`1`，legacy_individual_stage_upload_artifacts_current_gate=`false`，github_upload_ready_next_gate=`true`，github_upload_performed=`false`，github_upload_status=`not_uploaded_ready_for_separate_stage1_10_github_upload_gate`。
- Stage 1-10 GitHub upload gate 结论: 已完成 local validation；已 unshallow/fetch/rebase 到 latest `origin/main`，upload base=`387f2bdd1e4cb06d3fced781417f057f854c2901`，reviewed batch commit=`494a166779fa8fdc1a282d1ebbdca293e3e78886`；upload validator、focused upload unit、focused batch unit、full KMFA tests 326、S01-S10 validators、no-float、no-omission、governance validators、raw/private path scan、strict secret scan、public-safe semantic scan 和 diff check 均 PASS。本 gate 仍保持 `delivery_allowed=false`、`formal_report_allowed=false`、`business_execution_allowed=false`、report grade=`D`、data quality=`Q4`、pending reconciliation=`12`。
- raw boundary: 本轮 GitHub upload gate 未读取、列出、修改、删除、移动、重命名、覆盖或写入 `/Users/linzezhang/Downloads/KMFA_MetaData`；只处理 public-safe governance、validator、test 和 evidence。公开证据不包含 raw 文件名、raw hash、字段/表头明文、sheet 名、ZIP member 名、row values、真实业务值、PDF/Excel 原值、connector secret 或 Redcircle native file；未新增 private diagnostic。
- 未执行: raw value matching、lineage full check、formal report、live connector、Redcircle automatic connector、OpMe deep coupling、business execution。
- 下一步: 若 push 和 post-push parity 完成，则 v0.1.3 Stage 1-10 GitHub upload gate 关闭；后续只能由用户指定下一个单一 phase，不得自动推进 raw value matching、正式报告、lineage full check、live connector 或业务动作。

## 持久本机 raw boundary

- 用户确认 KMFA 后续本机财务原始数据统一放在 `/Users/linzezhang/Downloads/KMFA_MetaData`。
- 该目录属于 raw/private business data；Codex 只能在当前 phase 明确需要时只读读取，不得修改、删除、移动、重命名、覆盖或写入生成文件。
- Codex 生成的私有 inventory、schema/header diagnostic、mapping diagnostic、scratch files 或本地报告只能写入项目受控且 Git 忽略的位置，例如 `KMFA/.codex_private_runtime/`，或另一个明确加入 `.gitignore` 的额外工作目录。
- 2026-07-08 owner 已改变 KMFA 数据治理规则：非 credential 类原始敏感经营文件、银行流水、合同、工资、税务申报、SQLite/数据库导出、明文报告正文等，可在当前线程或签名 upload manifest 明确授权、secret 扫描通过并登记到 `KMFA/metadata/security/owner_authorized_plaintext_upload_manifest.jsonl` 后，以明文提交到 `KMFA/metadata/`；credential/secret 仍永久禁止进入 GitHub。

## 当前状态

- Post-S18 Part 1 Review 已本地通过：新增 `KMFA/tools/check_part1_stages_01_03_review.py`、`KMFA/tests/test_part1_stages_01_03_review.py` 和 `KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/`；当轮全量 KMFA unittest 为 269 tests。
- Post-S18 Part 2 Review 已本地通过：新增 `KMFA/tools/check_part2_stages_04_06_review.py`、`KMFA/tests/test_part2_stages_04_06_review.py` 和 `KMFA/stage_artifacts/PART2_STAGES_04_06_REVIEW/`；全量 KMFA unittest 当前为 270 tests。
- Post-S18 Part 3 Review 已本地通过：新增 `KMFA/tools/check_part3_stages_07_09_review.py`、`KMFA/tests/test_part3_stages_07_09_review.py` 和 `KMFA/stage_artifacts/PART3_STAGES_07_09_REVIEW/`；全量 KMFA unittest 当前为 271 tests。
- Post-S18 Part 4 Review 已本地通过：新增 `KMFA/tools/check_part4_stages_10_12_review.py`、`KMFA/tests/test_part4_stages_10_12_review.py` 和 `KMFA/stage_artifacts/PART4_STAGES_10_12_REVIEW/`；全量 KMFA unittest 当前为 272 tests。
- Post-S18 Part 5 Review 已本地通过：新增 `KMFA/tools/check_part5_stages_13_15_review.py`、`KMFA/tests/test_part5_stages_13_15_review.py` 和 `KMFA/stage_artifacts/PART5_STAGES_13_15_REVIEW/`；全量 KMFA unittest 当前为 273 tests。
- Post-S18 Part 6 Review 已本地通过：新增 `KMFA/tools/check_part6_stages_16_18_review.py`、`KMFA/tests/test_part6_stages_16_18_review.py` 和 `KMFA/stage_artifacts/PART6_STAGES_16_18_REVIEW/`；全量 KMFA unittest 当前为 274 tests。
- Post-S18 Whole Project Final Review 已本地通过且 delivery 仍为 `NO_GO`：新增 `KMFA/tools/check_lineage_completeness.py`、`KMFA/tools/check_whole_project_final_review.py`、`KMFA/tests/test_lineage_completeness.py`、`KMFA/tests/test_whole_project_final_review.py` 和 `KMFA/stage_artifacts/WHOLE_PROJECT_FINAL_REVIEW/`；全量 KMFA unittest 当前为 276 tests。
- KMFA worktree cleanup 已本地完成：新增 `KMFA/tools/check_worktree_cleanup.py` 和 `KMFA/stage_artifacts/WORKTREE_CLEANUP/`；只保留 canonical KMFA sparse worktree；旧 `/Users/linzezhang/Documents/KMFA v0.1` 为空目录骨架，已用 `rmdir` 删除；没有可迁移 KMFA 变更，也没有 raw/private 数据迁入公开仓库。
- Lineage / Report Gate 已本地锁定为 `blocked_no_go_owner_scope_required`：新增 `KMFA/tools/check_lineage_report_gate.py`、`KMFA/tests/test_lineage_report_gate.py`、`KMFA/metadata/quality/lineage_report_release_gate_review.json` 和 `KMFA/stage_artifacts/LINEAGE_REPORT_GATE/`；validator 复算 0 条 actual lineage rows、2 条 D 级 report runtime、12 条 pending reconciliation 和 `delivery_allowed=false`。
- Final GitHub Backup 证据已生成：新增 `KMFA/tools/check_final_no_go_backup_upload.py`、`KMFA/tests/test_final_no_go_backup_upload.py` 和 `KMFA/stage_artifacts/FINAL_GITHUB_BACKUP/`；只允许 `NO_GO governance backup only`，不允许 release、delivery、正式报告或业务执行。
- 已修复复审 findings：`TASKPACK_ZERO_DELTA_FIXTURE_MISSING`、`LINEAGE_COMPLETENESS_VALIDATOR_MISSING`、`CURRENT_GO_NO_GO_STALE_STAGE18_UPLOAD_BLOCKER`。
- `S01-P1` 已在前序工作目录完成，只读计划证据已迁移到 `KMFA/stage_artifacts/S01_P1_read_only_plan/`。
- `S01-P2` 已创建项目根、三中文入口、模型参数文件、Lean v2 与 v1 兼容治理文件、metadata 草案。
- `S01-P3` 已导入完整需求追溯矩阵、新增正式 `KMFA/tools/no_omission_check.py`、建立 18 Stage / 54 Phase / 162 Task 状态登记。
- Stage 1 总复审已通过，复审产物在 `KMFA/stage_artifacts/S01_STAGE_REVIEW/`。
- Stage 1 已上传到 GitHub main: `ff834578e640dc360e764ab18f9da2003c735e3e`。
- `S02-P1` 已建立 metadata 七类目录、标识符协议、公开仓库隐私边界和 `KMFA/tools/metadata_protocol_check.py`。
- `S02-P2` 已建立 raw manifest append-only 规范、派生版本协议、前端 raw 写入边界和 `KMFA/tools/immutability_policy_check.py`。
- `S02-P3` 已建立 Q0-Q5 数据质量等级、A/B/C/D 报告可信等级、发布门禁和 `KMFA/tools/check_report_grade_gate.py`。
- Stage 2 复审已通过，复审产物在 `KMFA/stage_artifacts/S02_STAGE_REVIEW/`。
- Stage 2 已上传 GitHub main: final remote commit `6178b5215f92f12d6facad9a990e8659b3a70ba4`，reviewed content commit `834ff75516405ddbc8289f00ba67579691473709`。
- v1.2 完整任务包已同步到 `KMFA/taskpack/v1_2/`，源 zip SHA256 为 `3bb2ebf16fb4ad8b9d198484e9d80ea2aed3c19c54c483efebe023b772ad0e66`。
- HTML/UIUX/报告验收样板已同步：45 个 HTML，7 个核心验收样板。
- `90_用户原始上传数据` 未进入公开仓库，只保存 SHA256 登记和禁止提交规则。
- Stage 1 v1.2 重放证据在 `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/`。
- `S03-P1` 已完成本地实现与验证：新增 `KMFA/tools/file_import_register.py`、`KMFA/tests/test_file_import_register.py` 和 `KMFA/stage_artifacts/S03_P1_file_import/`。
- S03-P1 只生成文件登记 metadata、hash、size、import_run、source package、私有 storage ref 和 WPS/OLE 提示；未导入真实原始文件，未解析业务字段。
- `S03-P2` 已完成本地实现与验证：新增 `KMFA/tools/source_check_matrix.py`、`KMFA/tests/test_source_check_matrix.py` 和 `KMFA/stage_artifacts/S03_P2_source_check_matrix/`。
- S03-P2 只生成数据源检查矩阵 metadata 和 append-only 状态事件；未提交真实源行，未做源优先级。
- `S03-P3` 已完成本地实现与验证：新增 `KMFA/tools/source_priority.py`、`KMFA/tests/test_source_priority.py` 和 `KMFA/stage_artifacts/S03_P3_source_priority/`。
- S03-P3 只生成源优先级、同源失效重跑事件和跨源差异队列 metadata；未解析真实业务源值，未自动选边，未上传 GitHub。
- Stage 3 复审已通过，发现的源优先级链路对齐问题已修复，并已上传 GitHub main，reviewed content commit `39b0eef52424a12b6c0c8ad368bd878b46300be4`。
- `S04-P1` 已完成本地实现与验证：新增 `KMFA/tools/amount_tools.py`、`KMFA/tools/check_no_float_money.py`、`KMFA/tests/test_amount_tools.py` 和 `KMFA/stage_artifacts/S04_P1_amount_tools/`。
- S04-P1 只提供金额标准化与 no-float 检查；未做字段标准化、zero-delta、A0 基准、事实层、报告或 UI。
- `S04-P2` 已完成本地实现与验证：新增 `KMFA/tools/field_standardization.py`、`KMFA/tests/test_field_standardization.py`、`KMFA/metadata/schema_maps/field_alias_dictionary.csv`、`KMFA/metadata/schema_maps/field_standardization_policy.yaml`、`KMFA/metadata/quality/field_quality_status.jsonl` 和 `KMFA/stage_artifacts/S04_P2_field_standardization/`。
- S04-P2 只提供字段别名、日期、期间、主体、项目、客户/对手方、合同编号标准化和缺字段质量状态；未做 S04-P3 工具测试报告、zero-delta、A0 基准、事实层、报告或 UI。
- `S04-P3` 已完成本地实现与验证：新增 `KMFA/tests/test_basic_tool_boundaries.py`、`KMFA/tools/generate_tool_test_report.py` 和 `KMFA/stage_artifacts/S04_P3_basic_tool_tests/`，并修复中文完整日期转期间边界。
- S04-P3 只提供基础工具合成边界测试和工具函数测试报告；未做 zero-delta、A0 基准、事实层、报告或 UI。
- Stage 4 整体复审已通过：新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/`，复跑 S04-P1/P2/P3 工具测试、治理 validator、no-float 检查和敏感文件扫描。
- Stage 4 复审修复了 `功能清单.md` 中 `FEAT-KMFA-016` 金额工具详情缺口。
- Stage 4 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_upload_manifest.json`。
- `S05-P1` 已完成本地实现与验证：新增 `KMFA/tools/a0_file_register.py`、`KMFA/tools/check_a0_file_registration.py`、`KMFA/tests/test_a0_file_register.py`、`KMFA/metadata/baseline/a0_file_manifest.json`、`KMFA/metadata/baseline/a0_project_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P1_a0_file_registration/`。
- S05-P1 只登记 A0 private source package 的公开安全 source package SHA256、8 个 PDF + 1 个 Excel inventory 记录、legacy 指纹、Q3 机器候选和 Q4 未锁定状态；未抽取字段值、未生成 A0 字段级黄金基准、未做 zero-delta、事实层、报告或 UI。
- S05-P1 执行时未提供可验证私有 A0 source package，所以成员级 `member_sha256` 仍为 `pending_private_zip_unavailable`；S05-P2 后续私有审计发现本机 zip 整包 hash/size 与登记 source package 不匹配，因此不能回填 S05-P1 member SHA256，也没有把 legacy CRC/指纹伪装成 SHA256。
- `S05-P2` 已生成 public-safe 字段合同和候选结构：新增 `KMFA/tools/a0_golden_fixture.py`、`KMFA/tools/check_a0_golden_fixture.py`、`KMFA/tests/test_a0_golden_fixture.py`、`KMFA/metadata/baseline/a0_golden_fixture_manifest.json`、`KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/`。
- S05-P2 当前生成 5 个字段合同和 45 条字段候选：合同额、支出合计、毛利、毛利率、成本分类；每条候选都有 private raw/normalized value ref、source anchor 状态和 Q3/Q4/Q5 门禁。
- 本机提供的 A0 private source package 整包 hash/size 与登记 source package 不匹配；过滤 macOS 隐藏文件后 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配。当前只据此和 Ring4 前序提取包执行 hash-only 部分回填，不把整包标记为 source package 匹配。
- S05-P2 已将 8 个 PDF 候选的 40 条字段记录为 hash/source anchor recorded；1 个 Excel 候选的 5 条字段仍为 `pending_private_source_unavailable`；未提交 raw/normalized 字段值、私有 CSV、zip、PDF 或 Excel。
- S05-P2 已新增 Excel 候选机器复核记录：Excel workbook 更像交叉来源汇总/支持材料，不得机器合成为单一 A0 项目基准，不得生成占位 hash，不得进入 Q4/Q5；证据在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md`。
- S05-P2 已新增 Excel owner 决策包：允许 `provide_private_field_mapping`、`downgrade_to_cross_source_support` 或 `keep_pending` 三类决策；证据在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`。
- S05-P2 已新增 owner 决策包 validator：`KMFA/tools/check_s05_p2_excel_owner_decision.py` 验证决策包、fixture pending 状态、approval/control events 和 Q4/Q5 禁止状态一致。
- S05-P2 已新增 owner 决策 intake contract 和 validator：`KMFA/tools/check_s05_p2_owner_decision_intake.py` 验证 owner/授权决策记录的 public-safe schema、actor role、禁止明文键和 Q4/Q5 边界；active downgrade decision 已通过 intake validator。
- S05-P2 已新增 owner 决策模板和 validator：`KMFA/tools/check_s05_p2_owner_decision_templates.py` 验证三种模板覆盖 allowed decisions，且模板不是 active owner 决策记录。
- S05-P2 已新增 owner decision application preview：`KMFA/tools/preview_s05_p2_owner_decision_application.py` 验证 public-safe 决策如何预览为 private hash backfill、cross-source support downgrade 或继续 pending；active downgrade decision 已输出 ready preview。
- S05-P2 已新增 completion gate validator：`KMFA/tools/check_s05_p2_completion_gate.py` 默认在无 resolving owner/授权决策时返回 `BLOCKED`；使用 active downgrade decision 时返回 `ready`，防止误入 Q4/Q5 但允许本地关闭 S05-P2。
- `S05-P3` 已完成本地实现与验证：新增 `KMFA/tools/a0_authority_baseline_lock.py`、`KMFA/tools/check_a0_authority_baseline_lock.py`、`KMFA/tests/test_s05_p3_authority_baseline_lock.py`、`KMFA/metadata/baseline/a0_authority_baseline_manifest.json`、`KMFA/metadata/baseline/a0_authority_baseline_records.jsonl` 和 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/`。
- S05-P3 已锁定 baseline version `KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK` 和 content hash `sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670`；40 条字段为 `q5_locked_public_safe_hash_baseline`，5 条字段为 `excluded_cross_source_support_only`。
- S05-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV 或字段明文；`formal_report_allowed=false`。
- Stage 5 整体复审已本地通过：新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md`、`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_review_manifest.json`；后续 upload gate 已完成。
- Stage 5 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`；upload base `495bcd977a587b7fd8b1923bfd74f5138f12263e`，reviewed content commit `ca6788949c444188b4b93f7db42c94094d90209f`。
- `S06-P1` 已完成本地实现与验证：新增 `KMFA/tools/zero_delta_validator.py`、`KMFA/tests/test_zero_delta_validator.py` 和 `KMFA/stage_artifacts/S06_P1_zero_delta_validator/`。
- S06-P1 只比较 public-safe 已结构化整数分字段；任意 1 分差异失败并输出包含来源、字段、权威值、系统值和差额的 mismatch report。
- S06-P1 不读取真实 Excel、PDF、zip 或私有 CSV，不写 `KMFA/metadata/quality/zero_delta_results.jsonl` 或 `KMFA/metadata/quality/mismatch_report.csv`，不创建 S06-P2 队列，不做 Stage 6 复审或 GitHub upload。
- `S06-P2` 已完成本地实现与验证：新增 `KMFA/tools/cross_source_difference_queue.py`、`KMFA/tools/check_s06_p2_difference_queue.py`、`KMFA/tests/test_cross_source_difference_queue.py` 和 `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/`。
- S06-P2 只使用 public-safe synthetic PDF/Excel 同项目同字段 1 分差异 fixture；差异进入人工队列，`auto_correction_allowed=false`、`averaging_allowed=false`、`rounding_mask_allowed=false`、`auto_selection_allowed=false`。
- S06-P2 未关闭差异阻断 A 级报告：`report_grade_a_allowed=false`、`maximum_report_grade=B`、`hard_block_reason=unresolved_critical_difference`；不写 metadata/quality 运行时业务差异项，不关闭差异，不做 Stage 6 复审或 GitHub upload。
- `S06-P3` 已完成本地实现与验证：新增 `KMFA/tools/validation_evidence_output.py`、`KMFA/tools/check_s06_p3_validation_evidence.py`、`KMFA/tests/test_validation_evidence_output.py` 和 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/`。
- S06-P3 将 S06-P1/S06-P2 public-safe 结果输出为 `zero_delta_result.json`、sanitized `mismatch_report.csv`、`project_validation_status.jsonl`，并写入 `KMFA/metadata/quality/{zero_delta_results.jsonl,data_quality_results.jsonl,source_difference_queue.jsonl,mismatch_report.csv}`。
- S06-P3 metadata/quality 只保存 hash/ref/status/evidence 和质量门禁状态，不新增字段明文、权威原值、系统原值、PDF 原值或 Excel 原值；不关闭差异，不做 Stage 6 复审或 GitHub upload。
- Stage 6 整体复审已本地通过：新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md`、`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_review_manifest.json`。
- Stage 6 复审复跑 S06-P1/S06-P2/S06-P3 validators、全量 KMFA tests、S05-P3 authority baseline dependency、治理 validator、raw/secret scan、JSON/JSONL parse、parameter CSV shape、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 6 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json`；upload base `fd14057e7427d7f275fdb62a33619936618d0d35`，reviewed content commit `5cd284e500fec5ff215741b0e8ee164912f50268`，reviewed S06-P3 commit `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`。
- `S07-P1` 已完成本地实现与验证：新增 `KMFA/tools/finance_file_adapter.py`、`KMFA/tools/check_s07_p1_finance_file_adapter.py`、`KMFA/tests/test_finance_file_adapter.py`、`KMFA/metadata/imports/finance_support_source_registry.json`、`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/finance_field_candidates.jsonl` 和 `KMFA/stage_artifacts/S07_P1_finance_file_adapter/`。
- S07-P1 覆盖经营分析、日记账、客户账龄、现金、纳税、开票、账户、贷款、研发费用 9 类财务支撑源；生成 45 条 hash-only 字段候选和 9 条只读字段报告。
- S07-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`wps_scope_included=false`、`redcircle_scope_included=false`。
- `S07-P2` 已完成本地实现与验证：新增 `KMFA/tools/wps_file_adapter.py`、`KMFA/tools/check_s07_p2_wps_file_adapter.py`、`KMFA/tests/test_wps_file_adapter.py`、`KMFA/metadata/imports/wps_export_source_registry.json`、`KMFA/metadata/schema_maps/wps_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/wps_field_mappings.jsonl`、`KMFA/metadata/schema_maps/wps_mapping_rule_versions.json`、`KMFA/metadata/schema_maps/wps_file_mapping_policy.yaml` 和 `KMFA/stage_artifacts/S07_P2_wps_file_adapter/`。
- S07-P2 覆盖 WPS 回款、应收账龄、生产项目状态、保证金 4 类导出；生成 20 条 hash-only 字段映射、4 条转换提示、4 条只读字段报告和 1 个映射规则版本。
- S07-P2 不提交 raw business data、WPS 原始文件、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`finance_scope_included=false`、`redcircle_scope_included=false`。
- `S07-P3` 已完成本地实现与验证：新增 `KMFA/tools/redcircle_postponement_policy.py`、`KMFA/tools/check_s07_p3_redcircle_postponement.py`、`KMFA/tests/test_redcircle_postponement_policy.py`、`KMFA/metadata/imports/redcircle_export_source_registry.json`、`KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`、`KMFA/metadata/schema_maps/redcircle_reserved_export_templates.jsonl`、`KMFA/metadata/schema_maps/redcircle_postponement_policy.yaml` 和 `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/`。
- S07-P3 只预留红圈经营、合同、回款、财务 4 类导出模板；D15 文件型 MVP 明确不接自动接口；后续接入必须只读、留 hash、可回滚并需人工授权。
- S07-P3 不提交 raw business data、红圈原始导出文件、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文、接口凭证或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`external_connector_included=false`。
- Stage 7 整体复审已本地通过：新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md`、`KMFA/stage_artifacts/S07_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_review_manifest.json`。
- Stage 7 复审复跑 S07-P1/S07-P2/S07-P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 7 final GitHub upload 已生成证据：新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json`。
- `S08-P1` 已完成本地实现与验证：新增 `KMFA/tools/project_composite_key.py`、`KMFA/tools/check_s08_p1_project_composite_key.py`、`KMFA/tests/test_project_composite_key.py`、`KMFA/metadata/schema_maps/project_composite_key_manifest.json`、`KMFA/metadata/schema_maps/project_identity_profiles.jsonl`、`KMFA/metadata/schema_maps/project_composite_key_matches.jsonl`、`KMFA/metadata/quality/project_identity_review_queue.jsonl` 和 `KMFA/stage_artifacts/S08_P1_project_composite_key/`。
- S08-P1 使用合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个 public-safe 组件和整数 basis points 权重；单字段缺失不全阻断，低于强匹配阈值进入人工复核队列，`auto_merge_allowed=false`。
- S08-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；S08-P2 已由业务实体模型覆盖，但 S08-P1 自身不做 S08-P3、Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。
- `S08-P2` 已完成本地实现与验证：新增 `KMFA/tools/business_entity_model.py`、`KMFA/tools/check_s08_p2_business_entity_model.py`、`KMFA/tests/test_business_entity_model.py`、`KMFA/metadata/schema_maps/business_entity_model_manifest.json`、`KMFA/metadata/schema_maps/business_entity_model_schema.json`、`KMFA/metadata/schema_maps/business_entity_relationships.jsonl`、`KMFA/metadata/schema_maps/business_entity_lifecycle_statuses.jsonl`、`KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md` 和 `KMFA/stage_artifacts/S08_P2_business_entity_model/`。
- S08-P2 定义 customer、contract、project、cost_record、invoice、collection、receivable、tax_evidence 8 类业务实体，建立 14 条实体关系和 32 条生命周期状态；只保存 schema/hash/ref/status/evidence metadata。
- S08-P2 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；不做 S08-P3、Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。
- `S08-P3` 已完成本地实现与验证：新增 `KMFA/tools/entity_matching_quality.py`、`KMFA/tools/check_s08_p3_entity_matching_quality.py`、`KMFA/tests/test_entity_matching_quality.py`、`KMFA/metadata/quality/entity_matching_quality_manifest.json`、`KMFA/metadata/quality/entity_matching_quality_cases.jsonl`、`KMFA/metadata/quality/entity_matching_review_queue.jsonl` 和 `KMFA/stage_artifacts/S08_P3_entity_matching_quality/`。
- S08-P3 覆盖同名项目、多主体、多账户、多期间 4 类 public-safe 质量场景，生成 4 条 quality cases、3 条 manual review queue records 和 1 份 `entity_matching_report`；中高风险候选 `auto_merge_allowed=false`。
- S08-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；不做 Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。
- Stage 8 整体复审已本地通过：新增 `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/stage8_review_report.md`、`KMFA/stage_artifacts/S08_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_review_manifest.json`。
- Stage 8 复审复跑 S08-P1/S08-P2/S08-P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 8 final GitHub upload 为历史 legacy 证据：`KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json` 记录旧基线上传；该证据非当前 v0.1.3 active upload gate，当前 GitHub main 未上传。
- Stage 8 upload 基于最新 `origin/main` commit `ce2881204c49a56da463893db5314ff180c7812d` rebase Stage 8 栈，复跑 validators、治理 validator、raw/secret scan、parse checks、dry-run push、push 和 post-push parity。
- `S10-P1` 已完成本地实现与验证：新增 `KMFA/tools/report_templates.py`、`KMFA/tools/check_s10_p1_report_templates.py`、`KMFA/tests/test_report_templates.py`、`KMFA/metadata/reports/report_template_manifest.json`、`KMFA/metadata/reports/report_templates.jsonl`、`KMFA/metadata/reports/report_template_sections.jsonl` 和 `KMFA/stage_artifacts/S10_P1_report_templates/`。
- S10-P1 覆盖 2 个模板和 11 个章节：项目成本专题报告含经营摘要、项目毛利、成本结构、风险事项；经营总览报告含经营总览、收入、开票、回款、现金、项目、税务。
- S10-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；`formal_report_allowed=false`、`trusted_grade_assignment_allowed=false`、`s10_p2_scope_included=false`、`s10_p3_scope_included=false`、`ui_scope_included=false`。
- `S12-P1` 已完成本地实现与验证：新增 `KMFA/tools/manual_resolution_events.py`、`KMFA/tools/check_s12_p1_manual_resolution_events.py`、`KMFA/tests/test_manual_resolution_events.py`、`KMFA/metadata/approvals/manual_resolution_event_manifest.json`、`KMFA/metadata/approvals/manual_resolution_events.jsonl` 和 `KMFA/stage_artifacts/S12_P1_manual_resolution_events/`。
- S12-P1 只建立 public-safe append-only 人工处理事件，覆盖字段映射、项目匹配、差异处理、备注；每个事件记录处理人、时间、原因、影响范围和版本；approved 事件不可静默改写，只能追加反向事件。
- S12-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；不发布 S12-P2 影响预览，不执行 S12-P3 派生重跑，不做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。
- `S12-P2` 已完成本地实现与验证：新增 `KMFA/tools/manual_impact_preview.py`、`KMFA/tools/check_s12_p2_manual_impact_preview.py`、`KMFA/tests/test_manual_impact_preview.py`、`KMFA/metadata/approvals/manual_impact_preview_manifest.json`、`KMFA/metadata/approvals/manual_impact_previews.jsonl` 和 `KMFA/stage_artifacts/S12_P2_manual_impact_preview/`。
- S12-P2 只建立 public-safe 影响预览，基于 5 条 S12-P1 人工处理事件生成 5 条 impact previews；提交前展示受影响项目、指标、报告；3 条高风险预览需要二次确认，pending 时阻断发布。
- S12-P2 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；不执行 S12-P3 派生重跑，不做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。
- `S12-P3` 已完成本地实现与验证：新增 `KMFA/tools/manual_rerun_mechanism.py`、`KMFA/tools/check_s12_p3_manual_rerun_mechanism.py`、`KMFA/tests/test_manual_rerun_mechanism.py`、`KMFA/metadata/lineage/manual_rerun_manifest.json`、`KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl`、`KMFA/metadata/lineage/manual_rerun_steps.jsonl`、`KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl` 和 `KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/`。
- S12-P3 只对 2 条 preview passed/publish-allowed 事件失效派生缓存并重跑字段映射、事实层、指标和报告引用；3 条高风险 pending preview 不进入重跑。
- S12-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；不生成正式报告，不做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。
- Stage 12 整体复审已完成本地验证：新增 `KMFA/tools/check_s12_stage_review.py`、`KMFA/tests/test_s12_stage_review.py` 和 `KMFA/stage_artifacts/S12_STAGE_REVIEW/`。
- Stage 12 review 复跑 S12-P1/P2/P3 validators、Stage 12 review validator、全量 152 个 KMFA tests、治理 validator、raw/secret scan 和 parse checks；修复 HANDOFF stale next-step finding。
- Stage 12 review 不执行 GitHub upload、S13、lineage full check、正式报告、差异关闭或外部接口。
- Stage 12 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/machine/stage12_upload_manifest.json`，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity。
- `S13-P1` 已完成本地实现与验证：新增 `KMFA/tools/financial_operating_report.py`、`KMFA/tools/check_s13_p1_financial_operating_report.py`、`KMFA/tests/test_financial_operating_report.py`、`KMFA/metadata/reports/financial_operating_report_manifest.json`、`KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl`、`KMFA/metadata/reports/financial_operating_report_drafts.jsonl` 和 `KMFA/stage_artifacts/S13_P1_financial_operating_report/`。
- S13-P1 覆盖经营情况、费用税金资产、现金情况、贷款明细 4 条 public-safe 数据接入 lane，生成经营周报初稿和经营月报初稿；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告和经营决策依据。
- S13-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实账号或 credentials；不执行 S13-P2、S13-P3、Stage 13 review、GitHub upload、lineage full check、正式报告、外部接口、付款、贷款管理或税务申报。
- `S13-P2` 已完成本地实现与验证：新增 `KMFA/tools/collection_receivable_aging.py`、`KMFA/tools/check_s13_p2_collection_receivable_aging.py`、`KMFA/tests/test_collection_receivable_aging.py`、`KMFA/metadata/reports/collection_receivable_aging_manifest.json`、`KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl`、`KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl`、`KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl` 和 `KMFA/stage_artifacts/S13_P2_collection_receivable_aging/`。
- S13-P2 覆盖回款表、应收账龄、客户账龄、日记账、开票计划 5 条 public-safe source lane，识别已开票未回款、完工未结算、结算未开票、超期应收 4 类问题，生成 4 条回款优先级、4 条责任事项和 1 个 HTML evidence；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、催收/付款/法务动作和经营决策依据。
- S13-P2 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实客户/项目明细、真实账号或 credentials；不执行 S13-P3、Stage 13 review、GitHub upload、lineage full check、正式报告、外部接口、开票、付款、银行、税务或法务催收动作。
- `S13-P3` 已完成本地实现与验证：新增 `KMFA/tools/cross_table_review.py`、`KMFA/tools/check_s13_p3_cross_table_review.py`、`KMFA/tests/test_cross_table_review.py`、`KMFA/metadata/reports/cross_table_review_manifest.json`、`KMFA/metadata/reports/cross_table_review_checks.jsonl`、`KMFA/metadata/reports/cross_table_difference_queue.jsonl`、`KMFA/metadata/reports/operating_report_quality_report.json` 和 `KMFA/stage_artifacts/S13_P3_cross_table_review/`。
- S13-P3 覆盖项目、客户、金额、时间 4 个 public-safe 跨表复核维度，将全部不一致放入 4 条人工差异队列事项，并输出 1 份经营报表质量报告和 1 个 HTML evidence；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据和自动差异处理。
- `S14-P1` 已完成本地实现与验证：新增 `KMFA/tools/fund_cash_loan_plan.py`、`KMFA/tools/check_s14_p1_fund_cash_loan_plan.py`、`KMFA/tests/test_fund_cash_loan_plan.py`、`KMFA/metadata/reports/fund_cash_loan_plan_manifest.json`、`KMFA/metadata/reports/fund_cash_loan_source_lanes.jsonl`、`KMFA/metadata/reports/fund_cash_pressure_signals.jsonl`、`KMFA/metadata/reports/loan_due_alerts.jsonl`、`KMFA/metadata/reports/account_balance_summaries.jsonl` 和 `KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/`。
- S14-P1 覆盖账户清单、月度现金、资金计划、贷款明细 4 条 public-safe source lane，输出 4 条现金压力信号、3 条贷款到期提示、3 条账户余额汇总和 1 个 HTML overview；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、付款审批、银行操作、贷款管理、开票和税务动作。
- `S14-P2` 已完成本地实现与验证：新增 `KMFA/tools/invoice_tax_plan.py`、`KMFA/tools/check_s14_p2_invoice_tax_plan.py`、`KMFA/tests/test_invoice_tax_plan.py`、`KMFA/metadata/reports/invoice_tax_plan_manifest.json`、`KMFA/metadata/reports/invoice_tax_source_lanes.jsonl`、`KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl`、`KMFA/metadata/reports/invoice_tax_cash_summaries.jsonl` 和 `KMFA/stage_artifacts/S14_P2_invoice_tax_plan/`。
- S14-P2 覆盖开票计划、纳税明细、开票纳税资金汇总 3 条 public-safe source lane，输出待开票、已开票未回款、税率异常候选 3 类事项、3 条现金汇总和 1 个 HTML overview；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、纳税申报、发票开具、付款审批、银行操作和贷款管理动作。
- `S14-P3` 已完成本地实现与验证：新增 `KMFA/tools/policy_evidence_plan.py`、`KMFA/tools/check_s14_p3_policy_evidence_plan.py`、`KMFA/tests/test_policy_evidence_plan.py`、`KMFA/metadata/reports/policy_evidence_plan_manifest.json`、`KMFA/metadata/reports/policy_evidence_directories.jsonl`、`KMFA/metadata/reports/policy_evidence_gaps.jsonl`、`KMFA/metadata/reports/policy_risk_tips.jsonl` 和 `KMFA/stage_artifacts/S14_P3_policy_evidence_plan/`。
- S14-P3 覆盖科小、高新、专精特新、小巨人、研发费用 5 类 public-safe 政策证据目录，只输出 5 条证据缺口和 5 条风险提示；报告等级显示 D，12 条 pending reconciliation 继续阻断正式政策资格结论、政策申报、补贴申请、正式报告、经营决策依据、纳税申报、发票开具、付款、银行、贷款管理和外部接口动作。
- Stage 14 整体复审已完成本地验证：新增 `KMFA/tools/check_s14_stage_review.py`、`KMFA/tests/test_s14_stage_review.py` 和 `KMFA/stage_artifacts/S14_STAGE_REVIEW/`。
- Stage 14 review 复跑 S14-P1/P2/P3 validators、Stage 14 review validator、全量 191 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 evidence consistency；复审未执行 GitHub upload、S15、lineage full check、正式报告、差异关闭、付款、银行、贷款管理、开票、纳税申报、政策申报、补贴申请或外部接口。
- S13-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实客户/项目明细、真实账号或 credentials；不执行 Stage 13 review、GitHub upload、lineage full check、正式报告、差异关闭、外部接口、开票、付款、银行、税务或法务催收动作。
- Stage 13 整体复审已完成本地验证：新增 `KMFA/tools/check_s13_stage_review.py`、`KMFA/tests/test_s13_stage_review.py` 和 `KMFA/stage_artifacts/S13_STAGE_REVIEW/`。
- Stage 13 review 复跑 S13-P1/P2/P3 validators、Stage 13 review validator、全量 172 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 evidence consistency；复审未执行 GitHub upload、S14、lineage full check、正式报告、差异关闭或外部接口。
- Stage 13 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/machine/stage13_upload_manifest.json`，记录复跑 validators、治理验证、安全扫描、dry-run push、push 和 post-push parity。
- Stage 14 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/machine/stage14_upload_manifest.json`，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity。
- `S15-P1` 已完成本地实现与验证：新增 `KMFA/tools/performance_fact_fields.py`、`KMFA/tools/check_s15_p1_performance_fact_fields.py`、`KMFA/tests/test_performance_fact_fields.py`、`KMFA/metadata/reports/performance_fact_fields_manifest.json`、`KMFA/metadata/reports/performance_fact_field_definitions.jsonl`、`KMFA/metadata/reports/performance_fact_field_bindings.jsonl`、`KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl` 和 `KMFA/stage_artifacts/S15_P1_performance_fact_fields/`。
- S15-P1 只接入开票金额、毛利率、结算速度、回款速度、审计偏差、客情费率 6 个绩效事实字段，绑定项目成本事实、开票纳税、回款应收账龄和跨表复核 evidence；结算速度、回款速度、审计偏差和客情费率缺少完整权威窗口时标记人工复核。
- S15-P1 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、工资、奖金、薪资、合同或税务申报资料；不输出 S15-P2 绩效事实表/复核清单，不做 S15-P3 工资项目边界接口、Stage 15 review 或 GitHub upload。
- `S15-P2` 已完成本地实现与验证：新增 `KMFA/tools/performance_review_list.py`、`KMFA/tools/check_s15_p2_performance_review_list.py`、`KMFA/tests/test_performance_review_list.py`、`KMFA/metadata/reports/performance_review_manifest.json`、`KMFA/metadata/reports/performance_fact_table.jsonl`、`KMFA/metadata/reports/performance_review_items.jsonl` 和 `KMFA/stage_artifacts/S15_P2_performance_review_list/`。
- S15-P2 只输出 4 条 public-safe 绩效事实行和 16 条异常/人工复核事项，覆盖结算速度、回款速度、审计偏差、客情费率；不计算最终工资、不审批奖金、不导出薪资、不生成最终发放建议。
- S15-P2 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、工资、奖金、薪资、合同或税务申报资料；不做 S15-P3 工资项目边界接口、Stage 15 review 或 GitHub upload。
- `S15-P3` 已完成本地实现与验证：新增 `KMFA/tools/performance_salary_boundary.py`、`KMFA/tools/check_s15_p3_salary_boundary.py`、`KMFA/tests/test_performance_salary_boundary.py`、`KMFA/metadata/reports/performance_salary_boundary_manifest.json`、`KMFA/metadata/reports/performance_fact_output_interface_contract.json`、`KMFA/metadata/reports/salary_system_readiness_draft.jsonl` 和 `KMFA/stage_artifacts/S15_P3_salary_boundary/`。
- S15-P3 只预留 1 个 public-safe 绩效事实输出接口契约和 4 条未来工资系统读取草案；最终审批和发放必须人工处理。
- S15-P3 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、工资、奖金、薪资、合同或税务申报资料；不创建 live integration、API endpoint、connector、文件导出、工资计算、奖金审批、薪资导出、最终发放、Stage 15 review 或 GitHub upload。
- Stage 15 整体复审已本地通过：新增 `KMFA/tools/check_s15_stage_review.py`、`KMFA/tests/test_s15_stage_review.py` 和 `KMFA/stage_artifacts/S15_STAGE_REVIEW/`；复跑 S15-P1/P2/P3 validators、全量 207 个 KMFA tests、治理 validator、raw/secret scan 和 parse checks；未执行 GitHub upload、S16、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终发放或外部接口。
- Stage 15 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/machine/stage15_upload_manifest.json`，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity；未执行 S16、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终发放或外部接口。

## 关键决策

- canonical GitHub 目录为 `LinzeColin/CodexProject/KMFA`。
- 本地主仓库 root 为 `/Users/linzezhang/Documents/Codex/CodexProject`；普通开发优先使用项目级长期 worktree，例如 KMFA 使用 `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`。
- 只有并行冲突开发、风险隔离、长期实验或用户明确要求时才创建临时 task worktree；新 worktree 优先 sparse checkout，只展开当前项目和必要根文件。
- 公开仓库不保存原始敏感经营数据，只保存 hash、manifest、状态、证据索引和治理记录。
- 后续所有开发工作以 `KMFA/taskpack/v1_2/` 为任务包基线。
- 涉及 UI、报告、前端或验收的 Stage 必须读取 `KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/`。
- 每次 run work 最多解决一个 Phase；中间 Phase 不上传 GitHub。
- Stage 完成后先整体复审，修复复审问题后再整体上传 GitHub。
- KMFA 后续以 `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa` 作为唯一 canonical 开发入口；除非用户明确要求并行隔离，不再创建新的 `kmfa-s*` 工作树。
- S03-P1 新增的文件登记工具不得保存原始文件 bytes 或明文原始文件名到公开仓库；zip 只能安全解包到私有目录。
- S03-P2 新增的状态事件只能写 metadata，`raw_layer_write_allowed=false`。
- S03-P3 新增的跨源差异队列必须 `auto_selection_allowed=false`，同源不一致只能追加 metadata event。
- S04-P1 金额标准化必须输出整数分；业务金额不得使用 float；空白、横杠、井号、异常文本不得静默转 0。
- S04-P2 字段缺失或异常不得静默跳过；只能进入 metadata 质量状态，且不得写 raw 层或提交真实业务字段值。
- S04-P3 工具测试报告只能使用合成边界值，不得引入真实业务源数据。
- S05-P1 只能登记公开安全 metadata；成员 SHA256 未能从私有 zip 复算时必须显式 pending，不能用 legacy CRC/指纹替代 SHA256。
- S05-P2 公开仓库只能保存字段合同、hash/ref/status 和 private refs；不得保存真实 `raw_value`、`normalized_value`、PDF/Excel/zip、私有 CSV 或业务明文。
- S05-P2 Excel 候选只能通过 owner 或授权私有映射明确角色；机器复核记录不能替代 Q4 人工确认，也不能解除 5 条字段 pending。
- S05-P2 owner decision intake validator 只验证未来决策记录的公开安全边界；它不代表 owner 已作出决策，也不允许进入 Q4/Q5。
- S05-P2 owner decision templates 只帮助生成未来决策记录；模板本身不代表 owner 已决策。
- S05-P2 owner decision application preview 只预演决策的 public-safe 应用路径；active downgrade decision 不代表 Q4/Q5 完成。
- S05-P2 completion gate 的 active downgrade ready 结果只代表 S05-P2 可本地关闭，不代表 Stage 5 完成。
- S05-P3 权威基准锁定只允许 hash/source-anchor 完整且 public-safe 的 40 条 PDF 字段进入 Q5 calculation baseline；Excel candidate 依据 active owner/授权降级决策排除，不得用于正式报告。
- S05-P3 lock、Stage 5 review 和 Stage 5 upload 均已完成；仍不代表 zero-delta、lineage、事实层或报告发布完成。
- S06-P1 zero-delta validator、S06-P2 cross-source difference queue、S06-P3 validation evidence output、Stage 6 review/upload、S07-P1 finance adapter、S07-P2 WPS adapter、S07-P3 redcircle postponement policy、Stage 7 review/upload、S08-P1 project composite key、S08-P2 business entity model、S08-P3 entity matching quality、Stage 8 review/upload、S09-P1 public-safe fact layer、S09-P2 margin/cash margin layer、S09-P3 scope reconciliation、Stage 9 review/upload、S10-P1 report templates、S10-P2 report grade runtime、S10-P3 report export、Stage 10 review/upload、S11-P1 home navigation、S11-P2 source check board、S11-P3 project cost page、Stage 11 review/upload、S12-P1 manual resolution events、S12-P2 impact preview、S12-P3 rerun mechanism、Stage 12 review/upload、S13-P1 financial operating report、S13-P2 collection receivable aging、S13-P3 cross table review、Stage 13 review/upload、S14-P1 fund cash loan plan、S14-P2 invoice tax plan、S14-P3 policy evidence plan、Stage 14 review/upload、S15-P1 performance fact fields、S15-P2 performance review list、S15-P3 salary boundary、Stage 15 review 和 Stage 15 upload 已完成；lineage 和报告发布门禁仍未完成。

## 已改/需看文件

- `KMFA/README.md`
- `KMFA/功能清单.md`
- `KMFA/开发记录.md`
- `KMFA/模型参数文件.md`
- `KMFA/docs/governance/*`
- `KMFA/metadata/*`
- `KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/*`
- `KMFA/stage_artifacts/S01_P1_read_only_plan/*`
- `KMFA/stage_artifacts/S01_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S02_P1_metadata_protocol/*`
- `KMFA/stage_artifacts/S02_P2_immutability_policy/*`
- `KMFA/stage_artifacts/S02_P3_quality_gate/*`
- `KMFA/stage_artifacts/S02_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*`
- `KMFA/stage_artifacts/S03_P1_file_import/*`
- `KMFA/stage_artifacts/S03_P2_source_check_matrix/*`
- `KMFA/stage_artifacts/S03_P3_source_priority/*`
- `KMFA/stage_artifacts/S04_P1_amount_tools/*`
- `KMFA/stage_artifacts/S04_P2_field_standardization/*`
- `KMFA/stage_artifacts/S04_P3_basic_tool_tests/*`
- `KMFA/stage_artifacts/S04_STAGE_REVIEW/*`
- `KMFA/tools/file_import_register.py`
- `KMFA/tools/source_check_matrix.py`
- `KMFA/tools/source_priority.py`
- `KMFA/tools/amount_tools.py`
- `KMFA/tools/check_no_float_money.py`
- `KMFA/tools/field_standardization.py`
- `KMFA/tools/generate_tool_test_report.py`
- `KMFA/tools/a0_file_register.py`
- `KMFA/tools/check_a0_file_registration.py`
- `KMFA/tools/a0_golden_fixture.py`
- `KMFA/tools/check_a0_golden_fixture.py`
- `KMFA/tools/check_s05_p2_excel_owner_decision.py`
- `KMFA/tools/check_s05_p2_owner_decision_intake.py`
- `KMFA/tools/check_s05_p2_owner_decision_templates.py`
- `KMFA/tools/preview_s05_p2_owner_decision_application.py`
- `KMFA/tools/check_s05_p2_completion_gate.py`
- `KMFA/tools/a0_authority_baseline_lock.py`
- `KMFA/tools/check_a0_authority_baseline_lock.py`
- `KMFA/tools/check_part1_stages_01_03_review.py`
- `KMFA/tools/zero_delta_validator.py`
- `KMFA/tests/test_file_import_register.py`
- `KMFA/tests/test_source_check_matrix.py`
- `KMFA/tests/test_source_priority.py`
- `KMFA/tests/test_amount_tools.py`
- `KMFA/tests/test_field_standardization.py`
- `KMFA/tests/test_basic_tool_boundaries.py`
- `KMFA/tests/test_a0_file_register.py`
- `KMFA/tests/test_a0_golden_fixture.py`
- `KMFA/tests/test_s05_p2_excel_owner_decision.py`
- `KMFA/tests/test_s05_p2_owner_decision_intake.py`
- `KMFA/tests/test_s05_p2_owner_decision_templates.py`
- `KMFA/tests/test_s05_p2_owner_decision_application.py`
- `KMFA/tests/test_s05_p2_completion_gate.py`
- `KMFA/tests/test_s05_p3_authority_baseline_lock.py`
- `KMFA/tests/test_part1_stages_01_03_review.py`
- `KMFA/tests/test_zero_delta_validator.py`
- `KMFA/tests/test_cross_source_difference_queue.py`
- `KMFA/tests/test_validation_evidence_output.py`
- `KMFA/tools/cross_source_difference_queue.py`
- `KMFA/tools/check_s06_p2_difference_queue.py`
- `KMFA/tools/validation_evidence_output.py`
- `KMFA/tools/check_s06_p3_validation_evidence.py`
- `KMFA/tools/home_navigation_runtime.py`
- `KMFA/tools/check_s11_p1_home_navigation.py`
- `KMFA/tools/source_check_board_runtime.py`
- `KMFA/tools/check_s11_p2_source_check_board.py`
- `KMFA/tools/project_cost_page_runtime.py`
- `KMFA/tools/check_s11_p3_project_cost_page.py`
- `KMFA/tools/check_s11_stage_review.py`
- `KMFA/tests/test_home_navigation_runtime.py`
- `KMFA/tests/test_source_check_board_runtime.py`
- `KMFA/tests/test_project_cost_page_runtime.py`
- `KMFA/tests/test_s11_stage_review.py`
- `KMFA/metadata/imports/file_import_policy.yaml`
- `KMFA/metadata/sources/source_check_matrix_schema.json`
- `KMFA/metadata/sources/source_check_matrix_policy.yaml`
- `KMFA/metadata/sources/source_check_matrix.jsonl`
- `KMFA/metadata/sources/source_status_events.jsonl`
- `KMFA/metadata/sources/source_priority_policy.yaml`
- `KMFA/metadata/sources/source_priority_events.jsonl`
- `KMFA/metadata/quality/source_difference_queue.jsonl`
- `KMFA/metadata/schema_maps/field_alias_dictionary.csv`
- `KMFA/metadata/schema_maps/field_standardization_policy.yaml`
- `KMFA/metadata/quality/field_quality_status.jsonl`
- `KMFA/metadata/baseline/a0_file_manifest.json`
- `KMFA/metadata/baseline/a0_project_candidates.jsonl`
- `KMFA/metadata/baseline/a0_golden_fixture_manifest.json`
- `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`
- `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`
- `KMFA/metadata/baseline/a0_authority_baseline_records.jsonl`
- `KMFA/metadata/reports/home_navigation_manifest.json`
- `KMFA/metadata/reports/home_navigation_modules.jsonl`
- `KMFA/metadata/reports/source_check_board_manifest.json`
- `KMFA/metadata/reports/source_check_board_rows.jsonl`
- `KMFA/metadata/reports/project_cost_page_manifest.json`
- `KMFA/metadata/reports/project_cost_page_projects.jsonl`
- `KMFA/stage_artifacts/S05_P1_a0_file_registration/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/*`
- `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/*`
- `KMFA/stage_artifacts/S06_P1_zero_delta_validator/*`
- `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/*`
- `KMFA/stage_artifacts/S06_P3_validation_evidence_output/*`
- `KMFA/stage_artifacts/S06_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S11_P1_home_navigation/*`
- `KMFA/stage_artifacts/S11_P2_source_check_board/*`
- `KMFA/stage_artifacts/S11_P3_project_cost_page/*`
- `KMFA/stage_artifacts/S11_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_resolution_manifest.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_packet.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_templates/*`
- `KMFA/metadata/approvals/resolution_events.jsonl`
- `KMFA/metadata/approvals/control_events.jsonl`
- `KMFA/taskpack/v1_2/*`
- `KMFA/metadata/baseline/*`
- `KMFA/metadata/protocol/*`
- `KMFA/metadata/{sources,imports,schema_maps,quality,lineage,reports,approvals}/*`
- `governance/projects.yaml`
- `README.md`

## 验证命令

```bash
python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q
python3 -m unittest KMFA.tests.test_a0_file_register -q
python3 KMFA/tools/check_a0_file_registration.py
python3 -m unittest KMFA.tests.test_a0_golden_fixture -q
python3 KMFA/tools/check_a0_golden_fixture.py
python3 -m unittest KMFA.tests.test_s05_p2_excel_owner_decision -q
python3 KMFA/tools/check_s05_p2_excel_owner_decision.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_intake -q
python3 KMFA/tools/check_s05_p2_owner_decision_intake.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_templates -q
python3 KMFA/tools/check_s05_p2_owner_decision_templates.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_application -q
python3 -m unittest KMFA.tests.test_s05_p2_completion_gate -q
python3 KMFA/tools/check_s05_p2_completion_gate.py --expect-blocked
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py
python3 KMFA/tools/generate_tool_test_report.py --format json
python3 KMFA/tools/generate_tool_test_report.py --format markdown
python3 -m unittest KMFA.tests.test_field_standardization -q
python3 -m unittest KMFA.tests.test_amount_tools -q
python3 KMFA/tools/check_no_float_money.py
python3 -m unittest KMFA.tests.test_source_priority -q
python3 -m unittest KMFA.tests.test_source_check_matrix -q
python3 -m unittest KMFA.tests.test_file_import_register -q
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_cost_page_runtime -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p3_project_cost_page.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
python3 KMFA/tools/check_report_grade_gate.py
git diff --check -- README.md governance/projects.yaml KMFA
```

## 未解决风险

- Stage 5 已完成 S05-P1、S05-P2、S05-P3、整体复审和 GitHub upload；S05-P3 已锁定 40 条 public-safe hash/source-anchor 字段并排除 5 条 Excel 字段；S06-P1、S06-P2、S06-P3、Stage 6 review 和 Stage 6 upload 已完成。
- S05-P1 成员级 SHA256 仍未补算；S05-P2 后续私有审计只确认本机 zip 的 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配，但整包 hash/size 与登记 source package 不匹配。公开仓库不得提交 zip、PDF、Excel 或解包文件。
- S05-P3、Stage 5 review/upload、S06-P1、S06-P2、S06-P3、Stage 6 review/upload、Stage 7 review/upload、Stage 8 review/upload、S09-P1 和 S09-P2 只完成 A0 authority baseline lock、校验/差异/适配/匹配、结构化 fact layer、margin/cash margin 计算合同、整体复审和上传；不能把它扩展解释为差异关闭、lineage 或报告发布。
- S10-P3 public-safe 报告导出、Stage 10 整体复审、final GitHub upload、S11-P1 首页导航、S11-P2 数据源检查板、S11-P3 项目成本页面、Stage 11 review/upload、S12-P1/P2/P3、Stage 12 review/upload、S13-P1 财务经营报表初稿、S13-P2 回款应收账龄草案、S13-P3 跨表复核、Stage 13 review/upload、S14-P1 资金计划现金贷款、S14-P2 开票纳税、S14-P3 政策证据、Stage 14 review/upload、S15-P1 绩效事实字段、S15-P2 绩效复核清单、S15-P3 工资项目边界、Stage 15 review/upload、S16-P1 外协采购归集、S16-P2 项目状态生命周期、S16-P3 客户经营分析、Stage 16 整体复审、Stage 16 upload、S17-P1 权限与安全、S17-P2 通知提醒、S17-P3 运维与 SOP、Stage 17 整体复审、Stage 17 upload、S18-P1 精度与压力测试、S18-P2 全量回归验收、S18-P3 后续接入准备、Stage 18 整体复审和 Stage 18 upload 已完成；lineage 完整检查和运行时正式报告生成尚未实现。
- S02-P3 只实现 report grade gate 协议；正式报告生成和 lineage 完整检查仍属后续 Stage。
- Stage 3 已上传 GitHub main；业务导入解析、A0、zero-delta、lineage 和报告生成仍是后续 Stage。
- v1.2 中私有源数据只能本地使用，不能提交公开 GitHub。

## 下一步

下一步只能另起 run work 执行 `v0.1.3 S10-P3 report export replay` 或用户明确指定的单一 phase；GitHub main upload 必须等 v1.3 Stage 1-10 全部完成、整体复审通过并修复 findings 后一次性执行。本轮 S10-P2 未上传 GitHub；不得把旧 Stage 4/5/6/7/8/9/10 upload gate 作为 active next step，也不得推进 Stage 10 review、raw value matching、lineage full check、正式报告、live connector、Redcircle automatic connector、OpMe 深度耦合或业务执行。

## S19 更新 - 2026-07-07

- 当前目标新增为 `S19｜每日早晚钉钉考勤检查`。
- 自动化名称固定：`每日早晚钉钉考勤检查`。
- 运行时间：每天北京时间 `10:35` 晨报、`20:05` 晚报。
- 私有归档根目录：`/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`，只保留年月一级目录，文件直接落在当月目录下。
- 张霖泽 DingTalk userId：`1iv-1t2oesv2yd`；老板 userId 或小群配置仍需本机私有配置。
- GitHub 仅保存代码、schema、policy、prompt、manifest、validator 和 public-safe evidence；真实员工考勤明文、SQLite、raw API response、报告正文和凭据材料不得提交。
- 缺真实钉钉权限时，`healthcheck.py --config-only` 和 `run_attendance.py` 必须返回 `CONFIG_MISSING`，不得生成样例员工或假打卡。
- S19 考勤异常判定规则：张霖泽、林全意是已知无需考勤人员，仅豁免自身；真实异常不得因豁免名单被隐藏。`recordList=[]`、缺少上下班打卡、summary 当天缺卡/未打卡/旷工/迟到/早退均进入用户可见异常名单；2026-07-07 live 验证应考勤 41 人、当天缺卡异常 2 人。
- 关键文件：`KMFA/tools/dingtalk_attendance/`、`KMFA/metadata/dingtalk_attendance/`、`KMFA/tests/test_dingtalk_attendance.py`、`KMFA/stage_artifacts/S19_DINGTALK_ATTENDANCE/`。
- 下一步：若本轮全部验证、泄密扫描、open PR/open issue、branch/status/worktree 检查通过，才允许一次性 commit 并 push GitHub main；不得留下 PR、issue、branch 或 worktree。

## S21 更新 - 2026-07-08 08:40:56 AEST

- 当前目标新增为 `S21｜fund-weekly-analysis-skill 每日资金与税费 Excel 原生包`。
- 输入源固定为 `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群`；未找到该目录时必须 fail closed 为 `SOURCE_MISSING`，不得读取旧目录、生成样例数据或伪造付款/回款事实。
- 本轮已把用户确认后的 Excel 首页修订版固化为技能模板：Sheet `01` 的 4-7 行卡片为 `可用现金占比`、`银行存款`、`票据/电子汇票`、`期末总资金`，8-11 行卡片为 `保证金可释放`、`外部净流出`、`内部调拨净额`、`资金缺口`；首页保留最近 15 天和最近 30 天两张原生折线图，且 01-06 可见页第 2 行为空。
- 定时语义已按用户最新指令改为本机 Sydney 时间每周一和每周六 `11:00`；北京时间 `09:00` 仅作为当前 UTC+10 偏移下的业务参照，不作为本机调度时区。
- GitHub public-safe 范围仅提交技能代码、模板、规则、测试、prompt、manifest schema 和治理文档；真实 OneDrive 原始文件、运行输出、明细 Excel 包、凭据和私有审计证据必须留在 `KMFA/metadata/fund_weekly_analysis/private_runtime/` 并被 `.gitignore` 排除。
- 关键文件：`KMFA/fund-weekly-analysis-skill/`、`KMFA/tests/test_fund_weekly_analysis_skill.py`、`KMFA/metadata/fund_weekly_analysis/`、`KMFA/功能清单.md`、`KMFA/开发记录.md`、`KMFA/模型参数文件.md`。
- 已验证：`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_fund_weekly_analysis_skill -q`、`python3 KMFA/fund-weekly-analysis-skill/tools/validate_taskpack.py`、`python3 -m py_compile KMFA/fund-weekly-analysis-skill/tools/*.py`、`git diff --cached --check`、staged secret token scan。
- 真实数据 smoke 已执行：`run_fund_weekly_analysis.py --repo-root /Users/linzezhang/CodexProject --run-id validator_smoke_20260708 --timezone Australia/Sydney` 返回 `SOURCE_MISSING`，因为目标 OneDrive 输入目录当前不存在；这是正确阻断状态。
- 后续 runner 增强：目标输入目录缺失时仍返回 `SOURCE_MISSING`，但 ignored private runtime manifest 会列出同 OneDrive 下的 `DWS_Outputs.zip` 和 `DWS_Archive/付款请示群` 候选状态；目标输入目录存在时先输出 `INDEXED_PENDING_EXTRACTION` 无虚构包，包含当前 Excel 母版副本、证据索引、空事实 CSV、异常任务、cross review 和 audit log，但不生成金额、预测或管理结论。
- 后续 materializer 增强：`KMFA/fund-weekly-analysis-skill/tools/materialize_fund_source.py` 可从已验证私有候选源显式复制到目标 `DWS_Outputs/付款请示群`；默认 dry-run，`--apply` 才复制，同 hash 跳过，不同 hash 冲突失败，manifest/CSV 写入 ignored private runtime。
- 当前真实 dry-run 发现 OneDrive 外部阻塞：`DWS_Archive/付款请示群` 共 621 个文件，其中 608 个为 macOS `compressed,dataless` cloud-only 文件；`DWS_Outputs.zip` 也是 `compressed,dataless`。materialize 已正确返回 `SOURCE_UNREADABLE`，因此未执行 apply。
- 后续 runner 增强：即使目标 `DWS_Outputs/付款请示群` 未来存在，只要其中有不可读或 `dataless` 文件，runner 也会返回 `SOURCE_UNREADABLE`，不生成 Excel 包，避免部分数据被误当作完整真实输入。
- 后续 readiness 增强：`KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py` 是 scheduled run 的快速前置门禁；它不 hash/不读取文件内容，只检查目标目录、候选源、zip、dataless/unreadable 状态，输出 `READY`/`SOURCE_MISSING`/`SOURCE_UNREADABLE`。
- 2026-07-08 09:20 AEST 更新：`tools/run_daily_local.sh` 已在 `run_fund_weekly_analysis.py` 前强制调用 `check_source_readiness.py`；非 `READY` 时保持 readiness 原退出码并停止，不生成 Excel 包，也不进入 Codex prompt。
- 2026-07-08 S38 更新：Codex App automation `kmfa` / `KMFA资金周报自动化` 已按用户最新指令改为每周一、周六 11:00 悉尼本地时间；repo mirror、prompt 与 launchd fallback 模板同步更新，真实检查返回 `CODEX_AUTOMATION_READY`。
- 2026-07-08 后续更新：runner 已支持真实结构化 CSV 固定列契约抽取，输出 `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW`，生成 `fund_ledger`、`net_flow_ledger`、`company_bank_matrix` 和 `tax_loan_risk`，但仍保持 `management_conclusion_allowed=false`。
- 2026-07-08 S59 更新：fact promotion authorization/execution gate 阻断计数已精确化；`authorization_required=false` 的 review area 输出 `authorization_not_required_*` / `not_required_*` no-op 状态，只做审计，不计 blocked。真实复跑 `s55_scheduled_entrypoint_real_run_20260708` 后 authorization/execution blocked count 均为 4，execution allowed 仍为 0，`fund_ledger.csv` 与 `funding_forecast.csv` 均为 0 行，`management_conclusion_allowed=false`。
- 2026-07-08 S60 更新：H06 运行时配置规则表已加入原生 Excel 输出，写入 run/source/schedule/no-hallucination/fail-closed/governance 键值行，并由 workbook quality 检查覆盖。
- 2026-07-08 S61 更新：`fact_promotion_execution_dry_run.csv` 已加入 runner、任务包规则和治理台账，用于从执行门禁预览未来受控事实晋升影响；dry-run 只读、no-write，所有正式写账/晋升/管理结论标志仍为 false。
- 2026-07-08 S62 更新：`fact_promotion_execution_plan.csv` 已加入 runner、任务包规则和治理台账，用于把 dry-run 结果转换为 owner-facing 受控执行计划；ready 行只表达未来需要 `controlled_fact_promotion_execution` 授权，仍不执行写账或管理结论。
- 2026-07-08 S63 更新：`fact_promotion_execution_authorization_template.json` / `fact_promotion_execution_authorization_preview.csv` 已加入 runner、任务包规则和治理台账；preview 只验证 private execution authorization manifest 覆盖情况，不执行写账或管理结论。
- 2026-07-08 S64 更新：`fact_promotion_execution_apply_gate.csv` 已加入 runner、任务包规则和治理台账；ready 行只显示未来可 apply 的影响数，仍不执行写账或管理结论。
- 下一步：继续围绕正式 fact promotion writer、正式账本写入实现或 owner review 影响预览推进；当前 source readiness、automation readiness、dry-run、execution plan、execution authorization preview 和 apply gate 已具备，但正式账本、fact promotion 和管理结论仍保持 fail-closed。
