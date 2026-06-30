# ADP 用户中心

## 2026-06-30 12:37:34 Australia/Sydney - S2PLT04/S2PLT02 最新证据同步

- S2PLT04 completion evidence 现在显示 S2PLT02 授权已通过，但最终报告仍阻断。
- 当前不能把 dry-run 或 disabled scheduler 计入 terminal proof；下一真实缺口仍是第二真实 M1-M4 SMTP 日、8 封真实邮件和真实 scheduler proof。
- 证据：[governance/run_manifests/ADP-S2PMT07-S2PLT04-S2PLT02-LATEST-EVIDENCE-SYNC-20260630.json](../../governance/run_manifests/ADP-S2PMT07-S2PLT04-S2PLT02-LATEST-EVIDENCE-SYNC-20260630.json)。

更新时间：2026-06-30 12:41:12 Australia/Sydney

这里是 ADP 在 GitHub 上的唯一中文用户入口。你不需要打开本机目录、运行文件、深层治理文件或原始 JSON，也能判断今天邮件是否正常、队列里还有什么、学习闭环到了哪一步、哪些结论仍被停止门禁止。

## 总览

| 问题 | 当前结论 | 你该怎么处理 |
|---|---|---|
| 今日已发送 / 总应发送 | 4 / 4 | M1 为历史已发送证据，M2-M4 为 2026-06-28 11:26:41 AEST 补发成功；这不代表 Stage 2 生产验收通过 |
| 邮件发送模板 | [Email V1 学习邮件模板界面预览](./邮件模板预览.md) | 先看用户真实会看到的版式，再看源码和模板规则证据 |
| 截至今日总候选池 | [299 条总候选记录](./截至今日候选池.md)；候选队列前20精选已列分数 | 总候选池来源是 `docs/owner/CONTENT_LEDGER.csv`，前20精选是按公开评分抽取的阅读入口 |
| 各板块数据源 | [5 个板块 / 6 个数据源](./数据源与板块健康.md)；当前生产启用 1 个来源 | 公开每个板块对应来源、启用状态、影子测试/规划状态和证据链接 |
| 复习、行动、收益 | [复习行动与收益](./复习行动与收益.md) 已显示字段、证据链和 2026-06-28 今日快照数字 | 今日数字已由当日运行快照写入；后续每日必须继续由真实运行报告同步 |
| Stage 2 是否正式生产通过 | 没有；最终门仍阻断；S2PLT02 input inventory 已列出 ready/missing inputs，但缺第二真实日、8 封真实邮件、真实 scheduler proof 和 live terminal proof artifact | 不能宣称正式生产通过、每日生产运行已验收或 M1-M4 全量自动发送已通过 |

## 一看三查

| 入口 | 用途 | 适合什么时候看 |
|---|---|---|
| [一看三查](./一看三查.md) | 一屏判断今天是否正常、先查哪里、哪些结论不能说 | 每天第一次打开时 |
| [邮件发送与队列状态](./邮件发送与队列状态.md) | 看今日已发送 / 总应发送、历史发送记录、模板链接和候选池摘要 | 关心邮件发送和队列状态时 |
| [截至今日候选池](./截至今日候选池.md) | 看 299 条总候选记录、候选队列前20精选、库存流转规则、状态、分数和证据链接 | 需要核对完整候选池和精选候选时 |
| [数据源与板块健康](./数据源与板块健康.md) | 看 B1 到 B5 每个板块的数据源、启用状态、影子测试/规划状态和证据链接 | 需要核对来源覆盖和生产边界时 |
| [已生成报告与邮件预览](./已生成报告与邮件预览.md) | 看 30 条已生成报告 / 邮件预览的状态索引 | 需要跳转已生成记录证据时 |
| [邮件模板预览](./邮件模板预览.md) | 看 M1-M4 邮件在用户面前应呈现的界面版本 | 关心邮件长什么样时 |
| [复习行动与收益](./复习行动与收益.md) | 看复习到期、行动窗口、能力资产、收益复盘和真实快照状态 | 关心学习闭环是否落地时 |
| [功能任务测试证据追踪链](./功能任务测试证据追踪链.md) | 看功能/需求、任务、验收、代码、测试和运行证据的 381 条可点击链路 | 需要复审某项功能是否有测试和证据时 |
| [恢复路径安全扫描](./恢复路径安全扫描.md) | 看 P0 A-001 恢复路径穿越、绝对路径、符号链接逃逸和阻断保留探针 | 复审恢复安全阻断项时 |
| [恢复原子替换扫描](./恢复原子替换扫描.md) | 看 P0 A-002 新目标恢复、覆盖保留旧目标备份、无效覆盖保留原目标探针 | 复审恢复原子替换阻断项时 |
| [事务发件箱与消息ID扫描](./事务发件箱与消息ID扫描.md) | 看 P0 A-003 Message-ID、outbox claim、SMTP accepted-before-commit 和 at-least-once/no-exactly-once 探针 | 复审事务发件箱与消息 ID 阻断项时 |
| [前台陈述证据绑定扫描](./前台陈述证据绑定扫描.md) | 看 P0 A-004 fact、inference、hypothesis、action 前台陈述证据绑定和 fail-closed 探针 | 复审前台陈述无证据发布阻断项时 |
| [来源信任边界扫描](./来源信任边界扫描.md) | 看 P0 A-005 外部来源内容、工具、密钥、仓库写入、邮件发送和 URL 渲染边界 | 复审来源内容越权/提示注入阻断项时 |
| [自动唤醒安装生命周期扫描](./自动唤醒安装生命周期扫描.md) | 看 P0 B-001 install/status/trigger/uninstall 证据、外部 isolated proof 和独立复审状态 | 复审自动唤醒安装生命周期阻断项时 |
| [旧邮件标识兼容扫描](./旧邮件标识兼容扫描.md) | 看旧 B1-B5、五邮件和旧英文邮件标识是否仍在活跃运行或用户页面出现 | 复审 C-011 旧邮件标识兼容风险时 |
| [路线图与停止门](./路线图与停止门.md) | 看当前阶段、阻断项、哪些动作被禁止 | 判断能不能继续推进 Stage 2 时 |

## 关键页面

| 页面 | 你能得到什么 |
|---|---|
| [关键结论与用户决策](./关键结论与用户决策.md) | 当前结论、默认建议、需要你确认或拒绝的事项 |
| [功能清单](../功能清单.md) | ADP 已有功能、未完成能力、边界和证据入口 |
| [开发记录](../开发记录.md) | 路线图、任务、验收、历史开发记录和本次用户中心修复记录 |
| [模型参数文件](../模型参数文件.md) | 排序、门禁、复习、行动、收益和邮件模板的参数口径 |

## 证据地图

这些链接用于复审和排错，不要求每天打开。它们吸收了原重复索引页的信息，避免重复入口。

| 你要核实什么 | 证据链接 |
|---|---|
| 当前状态 | [STATUS.md](../docs/governance/STATUS.md) |
| 用户状态 | [OWNER_STATUS.md](../docs/governance/OWNER_STATUS.md) |
| 开发事件 | [DEVELOPMENT_LEDGER.md](../docs/governance/DEVELOPMENT_LEDGER.md) |
| 交付计划 | [DELIVERY_PLAN.md](../docs/governance/DELIVERY_PLAN.md) |
| 阶段记录目录 | [phase_records](../docs/phase_records/) |
| 运行清单目录 | [run_manifests](../../governance/run_manifests/) |
| 复习计划证据 | [S2PJT02 阶段记录](../docs/phase_records/PHASE_S2PJT02_REVIEW_SCHEDULE.md) / [运行清单](../../governance/run_manifests/ADP-S2PJT02-REVIEW-SCHEDULE-20260626.json) |
| 行动、资产、收益证据 | [S2PJT03 阶段记录](../docs/phase_records/PHASE_S2PJT03_ACTION_ASSET_ROI.md) / [运行清单](../../governance/run_manifests/ADP-S2PJT03-ACTION-ASSET-ROI-20260626.json) |
| 周报证据 | [S2PJT04 阶段记录](../docs/phase_records/PHASE_S2PJT04_WEEKLY_REPORT.md) / [运行清单](../../governance/run_manifests/ADP-S2PJT04-WEEKLY-REPORT-20260626.json) |
| 月报证据 | [S2PJT05 阶段记录](../docs/phase_records/PHASE_S2PJT05_MONTHLY_REPORT.md) / [运行清单](../../governance/run_manifests/ADP-S2PJT05-MONTHLY-REPORT-20260626.json) |
| 邮件模板规则 | [Email V1 前台模板规则](../docs/pursuing_goal/v7_2/machine_readable/email_learning_frontstage_overlay_v1.yaml) |
| 邮件模板实现 | [mail_templates.py](../src/arxiv_daily_push/mail_templates.py) |
| 总候选池来源 | [CONTENT_LEDGER.csv](../docs/owner/CONTENT_LEDGER.csv) |
| 板块和数据源配置 | [owner_controls.yaml](../config/owner_controls.yaml) |
| 板块和数据源生成目录 | [SOURCE_CATALOG.md](../docs/owner/SOURCE_CATALOG.md) |
| 功能到证据追踪链 | [功能任务测试证据追踪链](./功能任务测试证据追踪链.md) |
| 恢复路径安全扫描 | [恢复路径安全扫描](./恢复路径安全扫描.md) |
| 恢复原子替换扫描 | [恢复原子替换扫描](./恢复原子替换扫描.md) |
| 事务发件箱与消息ID扫描 | [事务发件箱与消息ID扫描](./事务发件箱与消息ID扫描.md) |
| 前台陈述证据绑定扫描 | [前台陈述证据绑定扫描](./前台陈述证据绑定扫描.md) |
| 来源信任边界扫描 | [来源信任边界扫描](./来源信任边界扫描.md) |
| 自动唤醒安装生命周期扫描 | [自动唤醒安装生命周期扫描](./自动唤醒安装生命周期扫描.md) |
| 旧邮件标识扫描 | [旧邮件标识兼容扫描](./旧邮件标识兼容扫描.md) |

## 阅读规则

| 规则 | 原因 |
|---|---|
| 本页是唯一用户中心索引 | 不再维护重复索引页，避免信息漂移 |
| GitHub 用户中心是主阅读面 | 用户不应该去本机目录找答案 |
| 本机运行文件只做证据 | 本机 JSON、SMTP 报告和候选队列不是日常阅读入口 |
| 先给结论，再给证据 | 避免把用户页面写成工程日志 |
| 全局中文优先 | 只有产品名、任务编号、文件名、代码标识和必要协议名保留原文 |
| 不用用户中心当生产开关 | 发信、改队列、改计划任务、改公共结构都必须另走任务和验收 |
| 具体更新时间必须由脚本写入 | 避免人工手写未来时间或静态时间漂移 |

计划来源：Email V1 每日 3+1（M1, M2, M3, M4），总应发送 4 封；这不是 Stage 2 生产验收通过声明。

## 2026-06-30 07:41:53 Australia/Sydney - S2PLT02 live 授权状态

- 已写入并校验 `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`；`live_authorization_artifact_status=pass`。
- 当前下一任务是 `S2PLT02_TERMINAL_DELIVERY_PROOF`：仍需第二个真实 M1-M4 SMTP 日、8 封真实邮件总量、真实 launchd scheduler proof 和 terminal delivery proof artifact。
- SMTP、scheduler、Release、restore、DAILY_OPERATION 和 integrated production acceptance 均未启用。

## 2026-06-30 09:19:10 Australia/Sydney - S2PLT02 terminal proof 候选生成器

- 新增 `build-s2plt02-terminal-delivery-proof-artifact-draft`，用于未来从两个真实 M1-M4 SMTP delivery manifest 和真实 scheduler proof manifest 生成 stdout-only 候选 artifact。
- 当前 `artifact_written=false`、`artifact_validation_errors=[]`、sample state hash `beb8f19417b694428749bef5eb01de375ce2321f209c9086dfe4862bf48c2a8b`；这不是 `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` live proof。
- 当前 dry-run/scheduler-disabled 捕获窗口仍 blocked；不启用 SMTP、scheduler、Release、restore、DAILY_OPERATION，也不声明 S2PLT02/S2PMT07 或 integrated production acceptance。

## 2026-06-30 09:48:07 Australia/Sydney - S2PLT02 scheduler proof 输入验证器

- 新增 `validate-s2plt02-real-scheduler-proof`，用于未来先校验真实 launchd scheduler proof manifest，再交给 terminal proof 候选生成器。
- 当前 `scheduler_proof_ready=true` 只来自 fixture；`artifact_written=false`、`scheduler_install_enabled=false`、sample state hash `5e1157dc9c710501cb2bf2e5dcdd3cc09afb40ee68164ff32d844e993843fb80`。
- 这不是当前 runtime scheduler proof；不启用 SMTP、scheduler、Release、restore、DAILY_OPERATION，也不声明 S2PLT02/S2PMT07 或 integrated production acceptance。

## 2026-06-30 10:12:54 Australia/Sydney - S2PLT02 terminal proof 输入清单

- 新增 `audit-s2plt02-terminal-delivery-inputs`，用于在写任何 live terminal proof 前列出当前输入清单。
- 已就绪：S2PLT01 terminal acceptance、第一真实发送日、无重复邮件、M4 水印 proof、真实 SMTP proof、P0/P1 zero-proof。
- 仍缺失：第二真实发送日、8 封真实邮件、真实 launchd scheduler proof、`FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json`；当前 `artifact_written=false`、`real_smtp_send_enabled=false`、`scheduler_install_enabled=false`、state hash `5976272c0102361222027116f94f5a73cc53e87fa18d1b0e9a5d82208e7c4444`。
- 这不是 S2PLT02 accepted；不启用 SMTP、scheduler、Release、restore、DAILY_OPERATION，也不声明 S2PLT02/S2PMT07 或 integrated production acceptance。

## 2026-06-29 18:04:46 Australia/Sydney - S2PLT02 历史授权门状态

- 当时下一步为 `S2PLT02-REAL-PROOF-CAPTURE-AUTHORIZATION`，且 `authorization_artifact_present=false`。
- 当前状态以上方 2026-06-30 live 授权记录为准；历史 owner packet 不等于 terminal proof。

## 2026-06-29 22:44:04 Australia/Sydney - S2PLT02 runtime readiness 状态

- readiness 现在显示 daily/health/watchdog LaunchAgents 已加载且有 calendar trigger，但仍 disabled 且 not running。
- 当前 `scheduler_runtime_evidence_status=launchagents_loaded_but_disabled_not_terminal_scheduler_proof`；这不是 scheduler proof，不允许推进 S2PLT02 terminal delivery proof。
- 不启用 SMTP、scheduler、Release、restore、DAILY_OPERATION，也不声明 S2PLT02/S2PMT07 或 integrated production acceptance。

## 2026-06-29 20:57:12 Australia/Sydney - S2PLT02 授权草稿 CLI 状态

- 新增 `build-s2plt02-real-proof-capture-authorization-artifact-draft`，只把未来授权 artifact 草稿打印到 stdout，帮助后续明确授权时减少 schema/hash 错误。
- 当前 `authorization_artifact_written=false`、`authorization_artifact_present_in_repo=false`、`authorization_gate_satisfied_by_this_command=false`；正式授权文件仍缺失。
- 不启用 SMTP、scheduler、Release、restore、DAILY_OPERATION，也不声明 S2PLT02/S2PMT07 或 integrated production acceptance。

- 2026-06-29 23:05:25 Australia/Sydney：已补齐 S2PLT02 授权模板 `FINAL_ACCEPTANCE_BUNDLE/templates/s2plt02_real_proof_capture_authorization.template.json`；该模板当时不等于 live 授权，当前 live 授权以上方 2026-06-30 记录为准。
- 2026-06-30 07:41:53 Australia/Sydney：已写入并校验 S2PLT02 live authorization artifact；下一步为 `S2PLT02_TERMINAL_DELIVERY_PROOF`，但 S2PLT02/S2PMT07/production acceptance 仍未通过。



## 2026-06-30 12:09:41 Australia/Sydney - S2PLT02 terminal capture window audit CLI

- 新增 `audit-s2plt02-terminal-capture-window` 可复现当前授权后捕获窗口状态：blocked / exit 2，`state_hash=6ad683a0590f9d43c808cf7812edc7c7f93feabec52d365ddb2a8abbbf42b4bf`。
- 结论：2026-06-29 与 2026-06-30 M1-M4 均为 dry-run，`real_sent_candidate_email_count=0`、`observed_terminal_email_count_credit=4/8`、LaunchAgents disabled；不能计入第二真实日、8 封真实邮件或 scheduler proof。
- 证据：[阶段记录](../docs/phase_records/PHASE_S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT_CLI.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-CLI-20260630.json)。

## S2PLT02 terminal capture window audit

- 最新审计：[PHASE_S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT.md](../docs/phase_records/PHASE_S2PLT02_TERMINAL_CAPTURE_WINDOW_AUDIT.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-TERMINAL-CAPTURE-WINDOW-AUDIT-20260630.json)
- 结论：live authorization 已通过，但 2026-06-29/2026-06-30 仍为 dry-run，`ADP_ALLOW_SMTP_SEND=false`，ADP launchd labels disabled；不能计入 S2PLT02 terminal proof。

## S2PLT02 terminal delivery proof artifact draft builder

- 最新记录：[PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT_BUILDER.md](../docs/phase_records/PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_ARTIFACT_DRAFT_BUILDER.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-ARTIFACT-DRAFT-BUILDER-20260630.json)
- 结论：builder 只能从未来真实 evidence manifests 输出候选 `FINAL_ACCEPTANCE_BUNDLE/s2plt02_terminal_delivery_proof.json` 内容到 stdout；本轮 `artifact_written=false`，不能代替真实 terminal proof 或 production acceptance。

## S2PLT02 scheduler proof 输入验证器

- 最新记录：[PHASE_S2PLT02_REAL_SCHEDULER_PROOF_INPUT_VALIDATOR.md](../docs/phase_records/PHASE_S2PLT02_REAL_SCHEDULER_PROOF_INPUT_VALIDATOR.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-REAL-SCHEDULER-PROOF-INPUT-VALIDATOR-20260630.json)
- 结论：validator 只能校验未来真实 launchd scheduler proof manifest；当前 `artifact_written=false`、`scheduler_install_enabled=false`，不能代替真实 scheduler proof、terminal proof 或 production acceptance。

## S2PLT02 terminal delivery 输入清单

- 最新记录：[PHASE_S2PLT02_TERMINAL_DELIVERY_INPUT_INVENTORY.md](../docs/phase_records/PHASE_S2PLT02_TERMINAL_DELIVERY_INPUT_INVENTORY.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-INPUT-INVENTORY-20260630.json)
- 结论：ready inputs 已公开，missing inputs 仍阻断 terminal proof；该清单只读且 `artifact_written=false`，不能代替真实 terminal proof 或 production acceptance。

## S2PLT02 terminal proof 捕获计划

- 最新记录：[PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN.md](../docs/phase_records/PHASE_S2PLT02_TERMINAL_DELIVERY_PROOF_CAPTURE_PLAN.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-TERMINAL-DELIVERY-PROOF-CAPTURE-PLAN-20260630.json)
- 结论：capture plan 只规定后续真实捕获和复审顺序：第二真实 M1-M4 SMTP 日、真实 scheduler proof、stdout-only draft、独立复审、写入 reviewed artifact、运行 validator。当前 `next_executable_step=CAPTURE_SECOND_REAL_M1_M4_SMTP_DAY`、`artifact_written=false`，仍不能代替真实 terminal proof 或 production acceptance。

## S2PLT02 real delivery manifest 输入验证器

- 最新记录：[PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_INPUT_VALIDATOR.md](../docs/phase_records/PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_INPUT_VALIDATOR.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-REAL-DELIVERY-MANIFEST-INPUT-VALIDATOR-20260630.json)
- 结论：validator 只校验未来完整单日 M1-M4 real delivery manifest；规范化第一天 evidence 可通过，但历史 2026-06-28 manifest 直接 strict CLI 会 blocked，因为缺少显式 no-production 字段。它不采集第二真实日、不发送 SMTP、不启用 scheduler，也不能代替 S2PLT02 terminal proof 或 production acceptance。

## 2026-06-30 11:45:16 Australia/Sydney - S2PLT02 real delivery manifest 规范化输入

- 最新记录：[PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION.md](../docs/phase_records/PHASE_S2PLT02_REAL_DELIVERY_MANIFEST_NORMALIZATION.md) / [运行清单](../../governance/run_manifests/ADP-S2PLT02-REAL-DELIVERY-MANIFEST-NORMALIZATION-20260630.json)
- 结论：历史 2026-06-28 第一真实 M1-M4 manifest 已规范化为 strict S2PLT02 输入；raw hash `a795bd90778b5a0bbbd217d286f696936954af47a1a547ed689f907b677d9fa2`，normalized manifest validation state hash `91bf1a4477c621a75fceed90efecdb620341cfc97d5a751c127cc5ffbd6a0d99`。
- 边界：这不采集第二真实日、不发 SMTP、不启用 scheduler、不写 terminal proof，不代表 S2PLT02 或 production accepted。
