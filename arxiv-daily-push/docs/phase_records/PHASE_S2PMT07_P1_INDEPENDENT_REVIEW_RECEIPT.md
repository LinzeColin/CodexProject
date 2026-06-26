# PHASE S2PMT07 P1 INDEPENDENT REVIEW RECEIPT

## Summary

- phase: `S2PM`
- task_id: `S2PMT07`
- acceptance_id: `ACC-S2PMT07-FINAL-REVIEW`
- receipt_id: `ADP-S2PMT07-P1-INDEPENDENT-REVIEW-RECEIPT-20260626`
- status: `review_receipt_ready_no_closure_claim`
- V7.2 contract: `ADP-PRODUCT-CONTRACT-V7.2`
- created_at: `2026-06-26 19:51:01 Australia/Sydney`
- refreshed_at: `2026-06-27 07:15:07 Australia/Sydney`

This receipt organizes the inherited V7.1 P1 evidence set for later independent review. It is not an independent reviewer signoff, does not close any P0/P1 finding, and does not unblock integrated production acceptance.

## Scope

- Record the 37 inherited V7.1 P1 findings that still block production acceptance until S2PMT07 independent review closes them explicitly.
- Bind each P1 finding to the current evidence surface or known evidence gap that should be reviewed.
- Preserve explicit no-production boundaries while S2PMT07 remains blocked.

## Non Scope

No P0/P1 closure, no independent final signoff, no S2PLT04 completion, no final acceptance bundle creation, no real SMTP send, no scheduler installation, no Release upload, no production restore, no public schema change, no DB migration, no production queue mutation, no ranking/source-adapter change, no CURRENT pointer change, no V7.1/V7.2 contract-file edit, no `DAILY_OPERATION`, and no `INTEGRATED_PRODUCTION_ACCEPTED` claim.

## P1 Counts

| Metric | Count |
|---|---:|
| V7.1 total inherited findings | 53 |
| P0 findings retained open | 8 |
| P1 findings retained open | 37 |
| P2 findings retained non-blocking | 8 |

## P1 Distribution

| Group | Count |
|---|---:|
| `S2PAT05` | 4 |
| `S2PHT05` | 1 |
| `S2PIT01` | 1 |
| `S2PIT02` | 1 |
| `S2PIT05` | 1 |
| `S2PMT01` | 3 |
| `S2PMT02` | 3 |
| `S2PMT03` | 8 |
| `S2PMT04` | 5 |
| `S2PMT05` | 6 |
| `S2PMT06` | 4 |

## P1 Review Matrix

| finding_id | fix task | title | current evidence surface | receipt state | independent reviewer decision still required |
|---|---|---|---|---|---|
| `A-006` | `S2PMT03-RUNTIME-LOCK-A006` | tick 写入异常时 runtime.lock 永久残留 | `PHASE_S2PMT03_RUNTIME_LOCK_A006.md`, `ADP-S2PMT03-RUNTIME-LOCK-A006-20260626.json`, `test_stage1_runtime.py` | refreshed current evidence located; independent review required; closure not claimed | 模拟死进程后仅新 fencing token 可接管 |
| `A-007` | `S2PMT03-STATE-HISTORY-A007` | 状态历史不验证声明的 from_state | `PHASE_S2PMT03_STATE_HISTORY_A007.md`, `ADP-S2PMT03-STATE-HISTORY-A007-20260626.json`, `test_state_machine.py` | refreshed current evidence located; independent review required; closure not claimed | 缺 reason/at 或时间倒序必须失败 |
| `A-008` | `S2PMT03-STATE-CONSISTENCY-A008` | current_state 与 state_history 末态可不一致 | `PHASE_S2PMT03_STATE_CONSISTENCY_A008.md`, `ADP-S2PMT03-STATE-CONSISTENCY-A008-20260626.json`, `test_state_machine.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 末态不一致和 status 不一致均失败 |
| `A-009` | `S2PMT03-OPTIMISTIC-FENCING-A009` | 状态转换缺少乐观并发控制与 fencing token | `PHASE_S2PMT03_OPTIMISTIC_FENCING_A009.md`, `ADP-S2PMT03-OPTIMISTIC-FENCING-A009-20260626.json`, `test_stage2_lease_fencing.py` | refreshed current evidence located; independent review required; closure not claimed | 过期 worker 的写入被 fencing token 拒绝 |
| `A-010` | `S2PMT02-ARTIFACT-ATOMIC-PUBLISH` | 报告文件在质量验证前写入正式目录 | `PHASE_S2PMT02_ARTIFACT_ATOMIC_PUBLISH.md`, `ADP-S2PMT02-ARTIFACT-ATOMIC-PUBLISH-20260626.json`, `test_stage1_b1_report.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 强制验证失败时正式目录 0 新文件 \| 中途异常后无半发布 package |
| `A-011` | `S2PMT02-ARTIFACT-SHA256` | artifact_files.sha256 字段不是文件字节 SHA-256 | `PHASE_S2PMT02_ARTIFACT_SHA256.md`, `ADP-S2PMT02-ARTIFACT-SHA256-20260626.json`, `test_stage1_b1_report.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 每个 artifact manifest SHA 与 sha256sum 完全相同 |
| `A-012` | `S2PMT01` | 邮件原文链接未限制 URL scheme | `PHASE_S2PMT01_INPUT_URL_SAFETY_A012.md`, `ADP-S2PMT01-INPUT-URL-SAFETY-A012-20260626.json`, `test_security_boundary.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: javascript/data/file/带凭据 URL 均拒绝或降级为无链接文本 |
| `A-013` | `S2PMT04-SCHEDULER-TEMPLATE-A013` | 调度模板路径未结构化转义，macOS plist 甚至不可解析 | `PHASE_S2PMT04_SCHEDULER_TEMPLATE_A013.md`, `ADP-S2PMT04-SCHEDULER-TEMPLATE-A013-20260626.json`, `test_stage1_runtime.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 空格、中文、分号、& 路径均安全；plistlib/systemd-analyze/PowerShell parser 通过 |
| `A-014` | `S2PMT02-SUPPORTING-FILE-COLLISION` | 备份辅助文件同名时静默覆盖 | `PHASE_S2PMT02_SUPPORTING_FILE_COLLISION.md`, `ADP-S2PMT02-SUPPORTING-FILE-COLLISION-20260626.json`, `test_stage1_runtime.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 不同目录同名文件均可完整恢复，manifest path 无重复 |
| `A-015` | `S2PMT05-FUTURE-HEARTBEAT-A015` | 未来时间戳被钳制为 age=0，时钟漂移可长期伪装新鲜 | `PHASE_S2PMT05_FUTURE_HEARTBEAT_A015.md`, `ADP-S2PMT05-FUTURE-HEARTBEAT-A015-20260627.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 未来 5 分钟以上 heartbeat 阻塞；DST 不影响 lease 计算 |
| `A-016` | `S2PMT03-LESSON-REVISION-A016` | lesson_id 只依赖 claim_id，不依赖内容/证据/模型版本 | `PHASE_S2PMT03_LESSON_REVISION_A016.md`, `ADP-S2PMT03-LESSON-REVISION-A016-20260626.json`, `test_lesson.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 任一证据或内容变更导致 revision 变化，stable key 不变 |
| `A-017` | `S2PMT03` | SMTP delivery_id 不含正文/内容版本，且缺标准 Message-ID | `PHASE_S2PMT03_SMTP_IDENTITY_A017.md`, `ADP-S2PMT03-SMTP-IDENTITY-A017-20260626.json`, `test_smtp_delivery.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 同 revision 重试 Message-ID 不变；内容修订 revision 变化且需显式 supersede/resend |
| `A-018` | `S2PAT05` | V7 要求展示 ROI，但旧邮件验证明确禁止 ROI | `PHASE_S2PAT05_ROI_DISCLOSURE_A018.md`, `ADP-S2PAT05-ROI-DISCLOSURE-A018-20260626.json`, `TRACEABILITY_MATRIX.csv` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: V7.1 合法 ROI 可发布；无成本/概率/证据的收益声明被拒绝 |
| `A-019` | `S2PMT01-ZERO-CRITICAL-CLAIM-A019` | 零关键 Claim 时覆盖率被计算为 100% | `PHASE_S2PMT01_ZERO_CRITICAL_CLAIM_A019.md`, `ADP-S2PMT01-ZERO-CRITICAL-CLAIM-A019-20260627.json`, `test_stage1_b1_report.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 0 critical claim 不能通过关键证据门 |
| `A-020` | `S2PMT01` | 依赖、CI Action、SBOM 与权限最小化未形成供应链基线 | `PHASE_S2PMT01_SUPPLY_CHAIN_A020.md`, `ADP-S2PMT01-SUPPLY-CHAIN-A020-20260626.json`, `test_security_boundary.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: CI 自动审计依赖和 Action 引用；高危漏洞按例外审批流程阻断 |
| `A-021` | `S2PAT05` | Roadmap 依赖为空、Stop Code 混用自由文本，机器门不可可靠执行 | `PHASE_S2PAT05_ROADMAP_STOP_CODE_A021.md`, `ADP-S2PAT05-ROADMAP-STOP-CODE-A021-20260626.json`, `test_v7_2_roadmap_machine_gate.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 任务图无缺失引用/环；所有 stop condition 均在 registry |
| `B-002` | `S2PMT04-PROCESS-LIFECYCLE-B002` | 缺少统一进程生命周期：STARTING/RUNNING/DRAINING/CHECKPOINTING/STOPPED | `PHASE_S2PMT04_PROCESS_LIFECYCLE_B002.md`, `ADP-S2PMT04-PROCESS-LIFECYCLE-B002-20260627.json`, `test_stage2_lifecycle_cache.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 每个阶段注入 SIGTERM/SIGINT，重启后无丢失/重复不可控副作用 |
| `B-003` | `S2PMT03` | watchdog 只报告 stale lock，不执行可证明安全的恢复 | `PHASE_S2PMT03_WATCHDOG_RECOVERY_B003.md`, `ADP-S2PMT03-WATCHDOG-RECOVERY-B003-20260626.json`, `test_stage2_lease_fencing.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 活进程慢任务不被误杀；死进程锁自动安全接管 |
| `B-004` | `S2PMT04` | 启动时没有在途任务、outbox、临时文件和残锁 reconciliation | `PHASE_S2PMT04_STARTUP_CONVERGENCE_B004.md`, `ADP-S2PMT04-STARTUP-CONVERGENCE-B004-20260626.json`, `test_stage2_lifecycle_cache.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 在每个持久状态断电后重启，状态最终收敛且计数守恒 |
| `B-005` | `S2PMT04` | 无安全缓存分类、TTL、容量上限、清理与保留证据 | `PHASE_S2PMT04_CACHE_LOW_DISK_B005.md`, `ADP-S2PMT04-CACHE-LOW-DISK-B005-20260626.json`, `test_stage2_lifecycle_cache.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 路径穿越/符号链接不删；低磁盘自动降载；durable 目录永不清理 |
| `B-006` | `S2PMT05` | 缺少正式负载、压力、峰值、浸泡和容量基线 | `PHASE_S2PMT05_CAPACITY_BASELINE_B006.md`, `ADP-S2PMT05-CAPACITY-BASELINE-B006-20260627.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 至少 24h soak；2x 峰值；队列有界且可恢复 |
| `B-009` | `S2PMT05` | 缺少磁盘满、只读目录、数据库锁死、损坏缓存/备份等故障注入 | `PHASE_S2PMT05_FAULT_INJECTION_B009.md`, `ADP-S2PMT05-FAULT-INJECTION-B009-20260627.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: ENOSPC/EACCES/SQLITE_BUSY/corrupt JSON/PDF/backup 均有明确状态和恢复路径 |
| `B-010` | `S2PMT05` | 缺少 Australia/Sydney DST、时钟跳变、漏跑和补跑政策测试 | `PHASE_S2PMT05_TIME_POLICY_B010.md`, `ADP-S2PMT05-TIME-POLICY-B010-20260627.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: DST forward/backward、NTP 前后跳、休眠 8h 后补跑均确定性 |
| `B-011` | `S2PMT03` | M4 水位线缺少 cycle_id、超时、迟到数据和降级策略 | `PHASE_S2PMT03_M4_WATERMARK_B011.md`, `ADP-S2PMT03-M4-WATERMARK-B011-20260626.json`, `test_stage2_lease_fencing.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: M2 失败/M3 超时/迟到/重跑/跨日均生成正确 M4 状态 |
| `B-012` | `S2PMT05` | 没有覆盖 3+1 日报、周报、月报、复习、行动、ROI 的完整流程测试 | `PHASE_S2PMT05_E2E_B012.md`, `ADP-S2PMT05-E2E-B012-20260627.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 一条命令生成可审计 run bundle，分项总数守恒、链接可达 |
| `B-013` | `S2PMT05-RESULT-VALIDITY-B013` | 结果有效性测试偏结构存在性，缺语义、证据和非模板化验收 | `PHASE_S2PMT05_RESULT_VALIDITY_B013.md`, `ADP-S2PMT05-RESULT-VALIDITY-B013-20260626.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 金标五维≥4/5；关键事实人工抽检；模板重复率上限 |
| `B-014` | `S2PMT05` | 无背压、熔断、降级和负载丢弃优先级 | `PHASE_S2PMT05_BACKPRESSURE_B014.md`, `ADP-S2PMT05-BACKPRESSURE-B014-20260627.json`, `test_stage2_stress_e2e.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 2x/5x 峰值下高优先项 SLO，低优先项明确延后/丢弃原因 |
| `B-015` | `S2PMT04` | 后台清理与数据保存没有事务边界和可观察完成信号 | `PHASE_S2PMT04_TRANSACTION_COMPLETION_B015.md`, `ADP-S2PMT04-TRANSACTION-COMPLETION-B015-20260626.json`, `test_stage2_lifecycle_cache.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 关闭中每一步 kill，重启可从 receipt 精确恢复 |
| `C-001` | `S2PIT01-SHALLOW-USER-CENTER-C001` | 当前仓库未落地唯一中文 00_用户中心首屏 | `PHASE_S2PIT01_SHALLOW_USER_CENTER_C001.md`, `ADP-S2PIT01-SHALLOW-USER-CENTER-C001-20260627.json`, `test_stage2_sources.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 从项目根两次点击内完成所有常用操作 |
| `C-002` | `S2PIT02-OWNER-STATUS-C002` | 总控台偏配置容量，缺真实排队/讲解/发送/复习/行动数量 | `PHASE_S2PIT02_OWNER_STATUS_C002.md`, `ADP-S2PIT02-OWNER-STATUS-C002-20260627.json`, `test_stage2_sources.py` | refreshed current evidence located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 各分项与总数守恒；空/延迟/失败状态正确显示 |
| `C-003` | `S2PIT05-FOUR-CHECK-FRESHNESS-C003` | 四查视图缺统一 freshness、事实源与漂移状态 | `PHASE_S2PIT05_FOUR_CHECK_FRESHNESS_C003.md`, `ADP-S2PIT05-FOUR-CHECK-FRESHNESS-C003-20260627.json`, `test_stage2_sources.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 故意制造漂移/过期时 CI 和页面同时报警 |
| `C-005` | `S2PMT06-RECOVERABLE-ERROR-C005` | 错误和阻塞信息缺少恢复动作、负责人和安全重试入口 | `PHASE_S2PMT06_RECOVERABLE_ERROR_C005.md`, `ADP-S2PMT06-RECOVERABLE-ERROR-C005-20260627.json`, `test_stage2_owner_ux.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 每个 P0/P1 错误至少一个可执行恢复动作或明确人工门 |
| `C-006` | `S2PMT06-SAFE-CONFIG-C006` | 修改配置缺少预览、diff、校验、影响分析和一键回滚 | `PHASE_S2PMT06_SAFE_CONFIG_C006.md`, `ADP-S2PMT06-SAFE-CONFIG-C006-20260627.json`, `test_stage2_owner_ux.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 非法配置无法应用；应用后可回滚到上个 revision |
| `C-007` | `S2PMT06-APPEND-ONLY-AUDIT-C007` | 用户控制修改缺少 append-only 审计历史 | `PHASE_S2PMT06_APPEND_ONLY_AUDIT_C007.md`, `ADP-S2PMT06-APPEND-ONLY-AUDIT-C007-20260627.json`, `test_stage2_owner_ux.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 每次有效修改都有 revision；结果产物记录使用的 revision |
| `C-010` | `S2PAT05-TRACEABILITY-CHAIN-C010` | 功能→Task→测试→运行证据在 UI 中没有可点击追踪链 | `PHASE_S2PAT05_TRACEABILITY_CHAIN_C010.md`, `ADP-S2PAT05-TRACEABILITY-CHAIN-C010-20260627.json`, `用户中心/功能任务测试证据追踪链.md`, `test_stage2_sources.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 每个 required feature 追踪覆盖 100%，无孤儿 Task/测试/证据 |
| `C-011` | `S2PAT05` | 旧 B1–B5/五邮件/英文名称与新 3+1 合同并存 | `PHASE_S2PHT01V1_1_T01_EMAIL_PATH_AUDIT.md`, `PHASE_S2PHT01V1_1_T02_T04_EMAIL_V1_RENDERER.md`, `PHASE_S2PMT06_OWNER_UX.md`, `并行审查汇总与合并结论.md` | evidence surface located; sufficiency/gap review required; closure not claimed | Verify V7.1 fix/test requirement: 全仓扫描旧标识仅允许在 archive/compat 列表出现 |
| `C-012` | `S2PMT06-SAFE-MANUAL-ACTION-C012` | 缺少手动重试、取消、重新排队、跳过和重新生成的安全交互 | `PHASE_S2PMT06_SAFE_MANUAL_ACTION_C012.md`, `ADP-S2PMT06-SAFE-MANUAL-ACTION-C012-20260627.json`, `test_stage2_owner_ux.py` | refreshed current evidence located; independent review required; closure not claimed | Verify V7.1 fix/test requirement: 重复点击不重复发送；非法状态动作被禁用并解释原因 |

## Evidence Refresh 2026-06-27

This refresh updates the P1 receipt to point completed P1 remediation rows at their dedicated phase records and manifests instead of older aggregate evidence surfaces. It does not close any P1 finding and does not provide independent review signoff.

- refreshed_findings: `A-006`, `A-007`, `A-008`, `A-009`, `A-010`, `A-011`, `A-012`, `A-013`, `A-014`, `A-015`, `A-016`, `A-017`, `A-018`, `A-019`, `A-020`, `A-021`, `B-002`, `B-003`, `B-004`, `B-005`, `B-006`, `B-009`, `B-010`, `B-011`, `B-012`, `B-013`, `B-014`, `B-015`, `C-001`, `C-002`, `C-003`, `C-005`, `C-006`, `C-007`, `C-010`, `C-012`
- refresh_manifest: `governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C010-20260627.json`
- previous_refresh_manifest: `governance/run_manifests/ADP-S2PMT07-P1-REVIEW-RECEIPT-REFRESH-C003-20260627.json`
- closure_claimed: `false`
- independent_review_signoff_present: `false`

## Preserved Blockers

- `reviewer_independence_not_proven`
- `p0_closure_not_claimed`
- `p1_closure_not_claimed`
- `s2plt04_not_completed`
- `final_acceptance_bundle_missing`
- `independent_final_signoff_missing`
- `independent_final_command_execution_missing`

## No Production Side Effects

- `real_smtp_sent`: `false`
- `scheduler_install_enabled`: `false`
- `release_packaging_enabled`: `false`
- `production_restore_enabled`: `false`
- `daily_operation_enabled`: `false`
- `integrated_production_accepted`: `false`
- `current_pointer_changed`: `false`
- `v7_1_baseline_changed`: `false`
- `v7_2_contract_files_changed`: `false`

## Next

An independent reviewer must re-run or inspect the referenced evidence, decide each P1 closure explicitly, and produce a separate signoff before inherited P1 counters can change. Until then, S2PMT07 remains blocked and Stage 2 integrated production acceptance remains false.
