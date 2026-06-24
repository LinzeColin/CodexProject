# HANDOFF: Serenity Daily Analysis

Timestamp: 20260623 - 15:29 CST / 20260623 - 17:29 AEST

## 最新交接摘要

- 本轮目标：只修自动调度，验收标准固定为“3分钟内自动 tick 写入数据库 + launchd/替代调度状态明确为成功 + 下一个真实 slot 自动生成 run”。
- 修复路径：未继续依赖不稳定的 legacy `launchd` tick plist；新增 `app/core/application_server.py` 内置 `ApplicationAutoScheduler`，作为明确的替代调度器。只要 `/Applications/Serenity 每日分析.app` 或 Downloads app 拉起本地服务，服务会默认常驻并每 60 秒自动执行一次 `automation_tick`。
- 状态证据：替代调度器写入 `outputs/implementation/AUTOSCHEDULER_STATUS.json`，并通过本地 API `/api/scheduler/status` 暴露 `status/scheduler_kind/thread_alive/last_tick_action/last_run_id/next_real_slot/last_error`。
- 运行边界：非 slot 时间只写 `automation_tick_log` 的 `no_due_slot`，不跑 preflight、不碰 OpenD/MooMoo、不发邮件；due slot 才按原 `automation_tick` 流程做 preflight、run、通知策略和首页刷新。
- 服务生命周期：`application-server` 默认不再 7200 秒自动退出，除非显式传入 `--ttl-seconds` 或环境变量；CLI 新增 `--disable-autoscheduler`、`--autoscheduler-interval-seconds`、`--autoscheduler-initial-delay-seconds`。
- 验收 1 已通过：打开 `/Applications/Serenity 每日分析.app` 后 3 分钟内自动写入 SQLite tick，例：`automation_tick_log.id=3233`，`tick_time_bj=2026-06-23T14:43:31+08:00`，`action=no_due_slot`。
- 验收 2 已通过：`/api/scheduler/status` 返回 `status=success`、`scheduler_kind=application_server_interval`、`thread_alive=true`、`last_exit_code=0`。
- 验收 3 已通过：下一个真实 slot `R8 2026-06-23T15:30:00+08:00` 自动生成 run：`run_id=sda_20260623T072737Z_r8_eb89ce33`，`automation_tick_log.id=3277`，`action=ran`，`dry_run=0`，`created_at=2026-06-23T07:27:37+00:00`。
- 当前状态：本地 app 服务仍在运行，PID `44761`，父进程为 `/Applications/Serenity 每日分析.app/Contents/MacOS/open-serenity`；`launchctl list` 只显示 app 本地服务 label，不再显示 legacy `serenity_launchd_tick`/loop 进程。
- 验证：`/opt/anaconda3/bin/python -m py_compile app/core/application_server.py app/core/automation_tick.py app/cli.py tests/test_application_server.py` 通过；`/opt/anaconda3/bin/python -m pytest -q tests/test_application_server.py tests/test_automation_tick.py` 为 15 passed。
- 注意：本轮未修改选基、权重、基金费率、历史数据保护、邮件策略或 OpenD/MooMoo lifecycle 规则。R8 run 当前 `status=degraded`、`data_quality_status=degraded`，属于策略数据质量状态，不是自动调度失败。

Timestamp: 20260617 - 18:22 CST / 20260617 - 20:22 AEST

## 最新交接摘要

- 本轮目标：紧急修复 OpenD/MooMoo 被 launchd/preflight 反复“自动启动后不到 1 秒关闭”的问题，同时保留“如果是自动化自己启动，任务完成后要关闭；用户已打开的绝不关闭”的生命周期规则。
- 根因确认：`preflight` 的 `moomoo_opend` 和 `benchmark_sources` 检查会 auto-start OpenD，并在短生命周期 smoke/healthcheck 结束后立即 cleanup；launchd 每 180 秒轮询时会重复触发该短检查，导致启动/秒关循环。
- 已先临时停用 `com.serenity.daily-analysis`，完成修复和测试后已恢复加载；恢复后北京时间 `18:22` 不在运行 slot，launchd 只记录 `no_due_slot`，未触发 preflight，也未触发 OpenD lifecycle/cleanup。
- 已改逻辑：`app/core/preflight.py` 的 MooMoo 和 benchmark 检查现在都强制 `auto_start_opend=False`，只检查已存在连接或 fallback，不再在 preflight 阶段启动/关闭 OpenD。
- 已改逻辑：`app/adapters/moomoo_adapter.py` 的 `healthcheck` 不再立即 cleanup；它只返回 `cleanup_required` 和 lifecycle handle。
- 已改逻辑：`app/core/pipeline.py` 在完整 `run_slot` 写完数据库、报告、通知草稿和离线首页后，才调用 `cleanup_started_processes` 关闭本轮自己启动的 OpenD，并写入 `audit_log` 的 `moomoo_opend_cleanup`。
- 已改逻辑：`app/core/pipeline.py` 只在非 dry-run 的真实 `run_slot` 中允许自动启动 OpenD；dry-run 或 preflight 强制降级运行不会启动 OpenD。
- 已改逻辑：`app/core/automation_tick.py` 新增 `data/automation_tick.lock` 非阻塞互斥锁；上一轮 tick 未结束时，下一轮直接返回 `skipped_locked`，不进入 preflight、不进 scheduler、不触碰 OpenD，避免重叠 launchd tick 放大启停问题。
- 安全边界：`app/core/moomoo_lifecycle.py` 清理范围已收紧为本轮新增的 OpenD/MooMoo 相关进程，移除 `CrashReporter` 宽匹配；`started_by_tool=False` 时返回 `not_started_by_tool`，不会触碰用户已打开的 OpenD。
- 邮件策略仍保持上一轮修复：Manual Review / 数据不足 / 暂停新增不发真实邮件；Urgent 风险仍可发。
- 验证：`python -m py_compile app/core/automation_tick.py app/adapters/moomoo_adapter.py app/core/preflight.py app/core/pipeline.py app/core/moomoo_smoke.py app/core/moomoo_lifecycle.py tests/test_automation_tick.py` 通过；目标与入口回归 `tests/test_automation_tick.py tests/test_moomoo_adapter.py tests/test_pipeline_opend_lifecycle.py tests/test_preflight.py tests/test_moomoo_smoke.py tests/test_config.py tests/test_notification.py tests/test_application_server.py tests/test_pipeline_serenity_priority.py tests/test_reporting_ui.py` 45 passed。
- 实测 preflight 证据：`moomoo_opend` 与 `benchmark_sources` 均 `auto_start_skipped_for_preflight=True`，且 `has_lifecycle=False`、`has_cleanup=False`。

Timestamp: 20260615 - 18:38 CST / 20260615 - 20:38 AEST

## 最新交接摘要

- 本轮目标：把 `shadow_ready_gate` 在 `production_ready=true` 时从 warning 改为 pass，消除最后一个非阻断提示。
- 已改逻辑：`app/core/completion_audit.py` 中 `shadow_ready_gate` 现在按 `production_ready=true -> pass/info`；只有 `production_ready=false && shadow_ready=true` 时才作为 shadow-only warning；`shadow_ready=false` 仍 block。
- 已补回归：`tests/test_completion_audit.py::test_completion_audit_shadow_ready_passes_when_production_ready` 固定该口径。
- 当前验证：`python -m py_compile app/core/completion_audit.py` 通过；`pytest -q tests/test_completion_audit.py` 18 passed；`SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json` 为 `overall_status=complete`、`completion_percent=100.00`、71 pass / 0 warn / 0 block；`shadow_ready_gate=pass/info`。
- 用户可见输出：`outputs/completion_audit/completion_audit_latest.md/json` 已由审计命令更新为 100%；`outputs/tests/VALIDATION_SUMMARY.md` 已移除旧 `shadow_ready_gate` warning 文案。

Timestamp: 20260615 - 17:50 CST / 20260615 - 19:50 AEST

## 最新交接摘要

- 本轮目标：保护不可覆盖历史字段（尤其创建时间、首次进入持仓池时间）并修通 OpenD 自动唤醒/登录后 socket 健康检查，使 MooMoo live gate 通过。
- 历史不可变字段修复：新增 SQLite 表 `asset_pool_entry`，记录 `candidate_pool`、`holding_pool`、`observation_pool` 的首次入池事实；字段包括 `first_run_id`、`first_rank`、`first_run_time_bj`、`first_run_created_at`、`created_at`。该表由历史 `recommendation_snapshot + run_log` 衍生回填，后续每次新 run 只 `INSERT OR IGNORE`，不会覆盖首次进入持仓池时间。
- UI 取数修复：基金库详情里的“首次进入策略 Top5”优先读取不可变 `asset_pool_entry(pool_kind='holding_pool')`；“上次进入候选池时间/当前进入候选池天数”继续按当前连续候选池状态计算。
- 历史完整性接入：`asset_pool_entry` 已加入 `history_integrity.PROTECTED_TABLES` 和 completion audit 必备 schema，后续基线会保护该表旧行不被修改/删除。
- OpenD 自动唤醒修复：`run_moomoo_smoke` 支持 `auto_start_opend`、`keep_auto_started_opend`、`opend_wait_seconds`，并把 `opend_lifecycle`/`cleanup` 写入 preflight 证据；`preflight` 默认会先尝试唤醒 OpenD 再做 socket+SDK 判断。
- 日常运行修复：`moomoo_adapter.healthcheck` 和 `pipeline.run_slot` 已接入同一套 OpenD lifecycle，automation-tick 运行时会先尝试唤醒再判断是否降级，并把 lifecycle 写入 `audit_log.context_json`。
- 当前真实验证：`python -m app.cli moomoo-smoke --auto-start-opend --keep-auto-started-opend --require-ready --json` 通过，socket `127.0.0.1:11111` 可达，SDK `10.6.6608` 可用；lifecycle 显示 `socket_was_reachable=true`、`started_by_tool=false`，因此未关闭用户已有 OpenD 进程。
- 当前生产验证：`SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json` 为 `production_ready=true`、`blockers=[]`，`moomoo_opend=pass`；`SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json` 为 `overall_status=complete`、`completion_percent=98.59`、70 pass / 1 warn / 0 block，`moomoo_opend_gate=pass`、`history_integrity_append_only=pass`。
- 当前历史保护验证：`python -m app.cli history-integrity --require-pass --json` 通过，`violation_count=0`；`asset_pool_entry` 当前 28 行，其中 `candidate_pool=13`、`holding_pool=12`、`observation_pool=3`。
- 当前交付物：`python -m app.cli application-portal --json` 通过并重建 Downloads/Applications 入口；`python -m app.cli package-delivery --json` 通过，ZIP 为 `outputs/package/serenity_daily_analysis_delivery.zip`，565 members，private evidence excluded；`unzip -tq` 通过。
- 测试结果：`python -m py_compile app/db.py app/core/pipeline.py app/core/application_portal.py app/core/moomoo_smoke.py app/core/preflight.py app/adapters/moomoo_adapter.py app/cli.py app/config.py app/core/completion_audit.py app/core/history_integrity.py` 通过；目标测试 `tests/test_history_integrity.py tests/test_moomoo_smoke.py tests/test_preflight.py tests/test_reporting_ui.py` 18 passed；全量 `pytest -q` 通过。

Timestamp: 20260615 - 13:38 CST / 20260615 - 15:38 AEST

## 最新交接摘要

- 本轮目标：修复数据质量仍显示 `manual_review`、Codex Automation 自动运行后出现在 sidebar chat、Apple Mail `AppleEvent timed out (-1712)`。
- 数据质量修复：`app/core/pipeline.py` 现在只用 Top5/action pool 判断全局 `data_quality_status`；观察池 #6/#7 的 `manual_review_required` 仍保留为待补证据，但不再把整轮策略 run 降级为 `manual_review`。最新可见生产 run `sda_20260615T051256Z_r5_89f194f3` 为 `success/pass`，Top5 manual review 数为 0，观察池 manual review 数为 2。
- 通知严重级别修复：`app/core/notification.py` 只用 Top5 判断 Urgent/Alert/Manual Review 全局严重级别，观察池待复核不会触发执行锁或高优先级邮件。
- sidebar chat 修复：Codex App cron automation 已暂停，`serenity-daily-analysis-beijing-hour-slots=PAUSED`、`serenity-daily-analysis-beijing-half-hour-slots=PAUSED`；本地生产轮询由 launchd `com.serenity.daily-analysis` 承担，避免 recurring tick 创建 Codex sidebar chat。
- Apple Mail 修复：`app/adapters/mail_notifier.py` 增加 AppleScript `with timeout`、`activate`、`ignoring application responses` 和 subprocess timeout 兜底；真实 mail smoke 已发送成功，后续 `automation-tick --send-mail --local` 也成功写入 sent/local sent。
- 最新 run 可见性修复：`app/core/run_visibility.py` 的 future controlled backfill 过滤已接入 preflight、application portal、application server、pipeline offline index、completion audit，避免 6月15日未来验证回填覆盖 6月14日/当前真实可见记录。
- 正式报告审计修复：completion audit 不再要求盘中动态 benchmark 收益数值逐分钟回写正式报告；报告必须包含基准代码、行数、日期和收益窗口证据，盘中收益数值漂移作为 timestamped snapshot 差异容忍，避免为了通过审计而反复改写快照。
- 用户入口状态：`python -m app.cli application-portal --json` 通过，`current_run_id=sda_20260615T051256Z_r5_89f194f3`，`manual_review_rows=0`，Downloads 和 `/Applications` app 入口均已重建。
- 最终验证：目标回归测试 37 passed；`SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json` 为 `status=pass`、`production_ready=true`、blockers=[]；`python -m app.cli completion-audit --json` 为 `overall_status=complete`、`completion_percent=98.59`、70 pass / 1 warn / 0 block；`python -m app.cli package-delivery --json` 通过，ZIP 536 members，private evidence excluded，`unzip -tq` 通过；history integrity 最终 `status=pass`、`violation_count=0`。
- 注意：目录不是 git 仓库，无法用 `git status`/`git diff` 汇总。历史策略报告和 SQLite 历史事实未被改写；本轮只追加新 run/审计输出并更新当前交付物。

Timestamp: 20260615 - 16:21 CST / 20260615 - 18:21 AEST

## Sidebar 修复追加

- 用户反馈 launchd 自动运行仍出现在 sidebar。实际根因不是 launchd，而是 `serenity-daily-analysis-beijing-half-hour-slots` Codex App cron 仍为 `ACTIVE`。
- 已通过 `codex_app.automation_update` 将两个 Serenity Codex cron 都更新为 `PAUSED`：
  - `serenity-daily-analysis-beijing-hour-slots=PAUSED`
  - `serenity-daily-analysis-beijing-half-hour-slots=PAUSED`
- 已把两个 Codex cron prompt 标注为 DISABLED / must remain paused，后续不应再被误认为 sidebar-free 运行入口。
- 已归档 3 个已出现的 Serenity half-hour automation sidebar 线程：
  - `019ec91d-99a7-78c1-ab8d-28d5716132d4`
  - `019ec98c-802e-79c0-9cd0-fd3ecb995be5`
  - `019ec954-a2fb-7871-9b30-4fd1a3fe907a`
- 复查 `codex_app.list_threads(query="Serenity Daily Analysis")` 返回空列表；`~/.codex/automations` 中只有这两个 Serenity automation 指向本 workspace，且都为 `PAUSED`。
- launchd 仍保留：`com.serenity.daily-analysis` 运行本地 Python `app.cli automation-tick`，不会创建 Codex sidebar thread。当前 launchd plist 的工作目录路径中包含 `Documents/Codex/...`，这不是 Codex App cron。
- `tests/test_completion_audit.py` 17 passed；`codex_app_automation_active` 审计项已 pass。当前 completion audit 仍有一个 OpenD socket 不可达 blocker，和 sidebar 修复无关，本轮未自动启动/关闭用户的 MooMoo/OpenD。

Timestamp: 20260614 - 19:41 CST / 20260614 - 21:41 AEST

## 当前目标

Serenity Daily Analysis 已完成 baseline-first 生产时段验证：先由 Serenity 生成基础持仓建议，后续每日更新相对 Serenity baseline 做候选池刷新、策略更新、纪律审计和调仓建议。当前 Alipay 持仓不是 baseline 前置条件，只是可选 personal-position overlay。

## 当前状态

- 重要修正：用户可见“运行时间”只显示最新一次运行时间，不再显示 `验证回填` 或 `生成时间`。controlled backfill 只作为 agent/审计内部责任，不暴露给用户操作界面。
- 当前最新策略 run 为 `sda_20260614T102245Z_r10_a5e55fa7`，运行时间 `20260614 - 18:22 CST` / `20260614 - 20:22 AEST`，`status=degraded`，`data_quality_status=manual_review`。这是页面“保存复核”触发的真实当前时间手动 run，不是 dry-run；执行锁仍强制 No-New-Order。
- 最新 Top5 持仓池：`008887`, `011839`, `110026`, `007300`, `013171`；观察池：`270042` 排名 #6、`018043` 排名 #7。当前非排除候选只有 7 只，因此不会虚构 #8-#10。因最新 run 为 Manual Review，执行锁强制 No-New-Order；页面和通知只输出纪律建议，不表示已发送本轮真实邮件或可直接下单。
- 持有期口径已改为 `1个月-1年`；收益窗口为 `1个月 / 3个月 / 1年 / 最近10交易日`，对照沪指和标普500。
- 当前 app/report index 已重新生成：首页、持仓建议、持仓池/观察池排序、基金库、费用分档、申购/赎回状态、管理费/托管费/销售服务费等信息基于最新 run 展示；报告索引和首页运行时间仅显示 `YYYYMMDD - HH:MM TimeZone`。
- 本轮入口性能修复：`.app` 启动慢的根因是 launcher 先等待 `/api/health` 后才打开页面，且旧 health curl 没有短超时，导致 Dock 图标长时间跳动。现在 `/Applications/Serenity 每日分析.app` 和 `~/Downloads/Serenity 每日分析.app` 会先立即打开轻量 `outputs/application/downloads-entry.html` 启动页，后台再启动/复用本地服务；启动页并行探测 `127.0.0.1:8765-8795` 的 `/api/health`，找到后自动跳转到服务首页。launcher health check 已加 `--connect-timeout 0.2 --max-time 0.5`，不再等待服务启动完成才打开浏览器。
- 本轮入口验证：`python -m app.cli application-portal --json` 已重建 Downloads 与 Applications app 入口；生成后检查确认两个 launcher 均包含 `open "$BOOTSTRAP"`、短超时 health check，且不再使用 `open "$URL"` 作为首屏入口；内置浏览器验证 `http://127.0.0.1:8769/` 首页可加载、控制台 0 error；因浏览器安全策略不能打开 `file://`，改用临时本地 HTTP 暴露 `outputs/application/downloads-entry.html` 验证启动页逻辑，入口页约 2.3 秒跳转到 `http://127.0.0.1:8769/`，控制台 0 error；临时静态服务已关闭。
- 本轮 UI 修正：`使用说明` 弹窗已改为左侧目录 + 右侧分区说明，默认展示“先看结论，再追溯原因”；目录支持阅读顺序、Skill 选股逻辑、证据置信度、权重配置、调仓纪律、复核与边界切换；文案明确 Serenity 判断优先，Score 只做置信度/数据说服力，不再残留 `1-3个月` 或 `跑赢次数/6`。
- 本轮 UI 修正：`操作入口` 已提前到首页关键状态下方，卡片顺序固定为 `基金库`、`使用说明`、`人工复核`、`报告`、`当前快照`；旧底部重复操作入口已移除。
- 本轮 UI/逻辑修正：`需操作的行为` 改为完全基于持仓建议表的“相对比例”动作，不再混用数据库 `action_label`。`_relative_ratio` 现在按 `|ratio| <= 1.00%` 判定为 `维持`，超过 1.00% 才显示 `增加/买入` 或 `减少/卖出`；切换“初始持仓权重/上轮对比权重”时，顶部关键状态和“需操作的行为”决策条会同步更新。
- 本轮人工复核修正：复核结果收束为 `放入观察池继续观察`、`剔除这一轮观察池`、`进入 Top 5 候选操作池` 三类；每个复核对象展示“为什么需要人工复核”和基金分析排序；保存复核必须实时写入 SQLite，不再提供浏览器端保存；任一复核结果保存后都会立即触发一次 Serenity 全流程真实刷新并同步首页/报告/数据库；首页“刷新”按钮也改为手动主动运行一次 Serenity 全流程，按当前真实时间追加 run。
- 本轮人工复核待办语义修正：人工复核现在按 todo list 处理。保存成功后，同一基金 + 同一复核原因会从当前待处理列表移除，不再因为下一次真实 run 重新生成相同 open queue 而反复显示；`放入观察池继续观察` 和 `进入 Top 5 候选操作池` 会持续抑制同原因待办，`剔除这一轮观察池` 只抑制 14 天，原因变化则重新进入待办。首页“持仓池 / 观察池排序”的动作列也同步显示 `已复核/观察中`，不再与弹窗待办状态冲突。
- 本轮观察池修正：pipeline 持久化 Serenity 排名 Top10，Top1-5 作为持仓池，Top6-10 作为观察池；首页新增“持仓池 / 观察池排序”板块，人工复核基金显示分析排序、等级和证据置信度。当前最新 run 有 7 条 recommendation_snapshot，其中 #6/#7 为观察池。
- 本轮页面真实验证：已修复“刷新/保存复核依旧报错”。根因是 `/api/refresh` 会在业务刷新时重建 `.app` 图标/安装包，`ThreadingHTTPServer` 下连续点击会并发删除/读取 `SerenityIcon.iconset`，触发 `image file is truncated` 或 `No such file or directory`。修复后业务刷新调用 `build_application_portal(..., install_apps=False)`，状态变更接口加写锁；`.app` 已重建并重启本地服务到 `http://127.0.0.1:8769/`。浏览器点击“刷新”追加真实 run `sda_20260614T102050Z_r10_2aa74f67`，toast `目前更新到最新时间 20260614 - 20:20 AEST 保持当前持仓`；点击“保存复核”写入 SQLite `manual_review_decision.review_id=115`，`refresh_status=pass`，追加真实 run `sda_20260614T102245Z_r10_a5e55fa7`，浏览器控制台 0 error。
- 本轮验证：`python -m py_compile app/core/application_portal.py app/core/application_server.py app/core/pipeline.py` 通过；`pytest -q tests/test_application_server.py tests/test_reporting_ui.py tests/test_integration.py tests/test_pipeline_serenity_priority.py` 通过 16 项；`pytest -q` 全量通过；`python -m app.cli completion-audit --json` 为 95.77%，68 pass / 1 warn / 2 block。
- 本轮基金库修复：基金库默认视图改为 `表格`，`卡片/表格` 切换已修复；表格列和数据列重新对齐，避免申购费/赎回费错位；基金库摘要和表格只保留基金本身费用、申赎、候选池状态等关键信息，不再显示支付宝/MooMoo advisory 和来源优先级等干扰字段；申购费/赎回费分档按 `；` 拆成多行显示；表格横向滚动时冻结 `代码` 和 `基金名称` 两列。验证：`python -m py_compile app/core/application_portal.py`、`pytest -q tests/test_reporting_ui.py`、`pytest -q` 全量通过；浏览器验证默认表格、切换回表格、6 行基金数据、费率分档换行、冻结列 sticky、控制台无 error。
- completion audit：`overall_status=blocked`，`completion_percent=95.77%`，68 pass / 1 warn / 2 block；当前剩余 blocker 为 `apple_mail_smoke_artifact` 和 `production_slot_backfill_verified`。这两个 blocker 属于生产时段/邮件验证口径，不影响本轮页面“刷新/保存复核”真实 run 验收。
- production preflight：当前 `production_ready=true`，`blockers=[]`；生产邮件真实发送仍需在触发调仓/风险提醒时显式启用 `SERENITY_MAIL_SEND_ENABLED=true` 或安装经确认的 production-mail 调度。
- 本轮生产质量升级：新增 `platform-trade-check` 平台交易可用性真实校验器，优先抓取支付宝或官方基金页，记录 HTTP 状态、内容哈希、证据片段、申购/赎回建议、置信度和 `advisory_only=1`；结果只进入 `outputs/preflight/platform_trade_check_latest.*` 和 SQLite `platform_trade_check_snapshot`，不改候选池、不改权重、不自动交易、不污染首页。
- 本轮真实 smoke：`python -m app.cli platform-trade-check --limit 2 --timeout-seconds 6 --json` 通过并追加 2 行 SQLite 证据；`status=watch`，因为 `007300` 官方 PDF 当前环境缺少 `pypdf` 只能抓取未解析，`008887` 官方 HTML 识别为申购 `open` 但赎回 `unknown`。这是预期降级，执行前仍需支付宝或官方交易确认页人工确认。
- 本轮根本规则升级：候选/筛选范围内的非排除基金必须具备 24 个月净值历史；配置为 `min_candidate_nav_history_months=24`、`min_candidate_nav_history_span_days=730`。`scoring` 会把不足 24 个月的候选标为 `nav_history_24m` 并 `Block`，`validate-intake` 和 `preflight` 会在生产前阻断。
- 本轮净值历史补齐：`python -m app.cli collect-fund-nav-history --apply --require-pass --workers 8 --timeout-seconds 12 --json` 成功，`data/manual/price_history.csv` 已从 1120 行补齐到 3596 行，覆盖 7 只非排除候选基金；每只 513-514 行，最早 `2024-04-30`，最新 `2026-06-11/2026-06-12`，跨度 772-773 天。旧文件备份在 `data/backups/nav_history/price_history_20260614T120927_0800.csv`。来源为 `Eastmoney/Tiantian Fund historical NAV API`，`source_type=public_aggregation`，`source_priority=5`，因此作为真实可核验补齐数据通过 24 个月硬规则，但仍保留“未来优先升级到 MooMoo/Alipay/官方源”的 warning。
- 本轮一次性非 dry-run 邮件验证：`SERENITY_MAIL_SEND_ENABLED=true python -m app.cli mail-smoke --send --confirm-real-send SEND --require-send-ready ... --json` 通过，`send_status=sent`，收件人 `linzezhang35@gmail.com`，主题 `[Serenity自动化][验证] 24个月净值历史规则已启用`。这只是邮件链路验证，没有安装 recurring production-mail launchd，没有自动交易。
- tests：`python -m py_compile app/core/platform_trade_checker.py app/core/history_integrity.py app/db.py app/cli.py` 通过；`pytest tests/test_platform_trade_checker.py tests/test_source_evidence_audit.py` 通过，6 passed；`python -m app.cli application-portal --json` 通过并重建 Downloads/Applications app 入口。
- 本轮测试更新：`pytest` 全量通过，116 passed；`python -m app.cli source-evidence-audit --json` 通过，24 valid references，其中 `candidate_nav_history=7`；`SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json` 通过，`production_ready=true`，`candidate_nav_history=pass`，`rows=3596`。
- browser verification：通过本机 `127.0.0.1` 临时静态服务验证操作入口顺序为 `基金库 -> 使用说明 -> 人工复核 -> 报告 -> 当前快照`；持仓建议表当前为 4 个 `维持` + 1 个 `新增/买入`，`需操作的行为` 同步为增加/买入 1 项；切换上轮基准后仍一致；临时服务已关闭。
- history integrity：`python -m app.cli history-integrity --require-pass --json` 通过，violations=0，baseline 未覆盖；新 `platform_trade_check_snapshot` 已加入后续历史完整性保护清单。
- final package：`outputs/package/serenity_daily_analysis_delivery.zip`，最新打包目标为 475 members，private evidence excluded，`unzip -tq` 通过。
- 平台交易可用性已改为 advisory-only：`fund_rules.csv`、模板、normalizer、SQLite `fund_rule_snapshot`、pipeline、基金库 UI 都支持 `alipay_trade_status`、`moomoo_trade_status`、`platform_trade_note`；这些字段只做交易路径建议与人工确认提示，不参与 Serenity 候选池排除、不改变 Top5 排序、不因为支付宝或 MooMoo 不支持交易而剔除对象。
- GitHub 备份同步到 `LinzeColin/Serenity-Alipay` 的 `main` 分支；具体 commit 以远端 `main` HEAD 为准。同步源为已验证交付 ZIP 内容，沿用 private evidence 排除规则，本地同步目录为 `/Users/linzezhang/Documents/Codex/2026-06-12/Serenity-Alipay-sync-20260614T020954Z`。
- 历史完整性保护已启用：`python -m app.cli history-integrity --write-baseline --require-pass --json` 已建立 `outputs/audit/history_integrity_baseline.json`，当前基线覆盖 21 张 SQLite 历史表和 142 个历史文件；后续允许新增运行/快照/报告/通知，不允许修改、删除、覆盖或重渲染已进入基线的旧历史行/旧历史文件。
- 历史时间线已启用：`outputs/audit/history_artifact_timeline.csv` / `.md` 记录每个受保护分析报告、通知、MooMoo 快照/原始数据文件的 `file_created_at`、`file_modified_at`、`file_metadata_changed_at`、`size_bytes`、`sha256` 以及可关联的 `run_id`、`run_time_bj`、`run_created_at`；`outputs/audit/history_snapshot_table_timeline.csv` 记录每张受保护 SQLite 快照表的 row count、table hash、首末 run 时间和首末 run 创建时间。
- `completion-audit` 已接入 `history_integrity_append_only`；当前百分比和 blocker 以本文件顶部“当前状态”中的最新审计结果为准，历史完整性 violations=0。
- `asset_master` 已改为 first-seen immutable：后续 Alipay 导入或候选池刷新不会覆盖既有 `asset_code` 的历史身份字段；更新后的名称/分类只能通过新快照或新来源证据表达，不能回写旧身份行。
- Apple Mail + local notification：`sent;local=sent`，收件人 `linzezhang35@gmail.com`。
- Email 模板已升级为 Gmail 可识别的 HTML + 纯文本兜底：实际发送路径 `app/core/pipeline.py`、独立通知路径 `app/core/notification.py::render_notification_for_run` 和 smoke 路径 `app/core/mail_smoke.py` 都会生成 HTML 草稿；Apple Mail 发送优先使用 `html content`，失败后回退纯文本。HTML 邮件含 H1/H2/H3 标题层级、内联样式、加粗/斜体/下划线重点提示、需变化行为高亮、当前持仓建议表格；正文删除 `来源与时间戳`、`sources_json`、source chain、旧英文动作提示和可见 `运行 ID`。最新 dry-run 草稿为 `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.md` 与 `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.html`，标题 `[Serenity自动化][复核] 信号变化，保持当前持仓`。
- 通知 dry-run 副作用已修复：`notify --dry-run` 现在写入独立 `_draft_preview` 记录，不覆盖真实 `sent;local=sent` 记录，也不修改 `run_log.notification_status`；本轮已从交付 ZIP 数据库快照恢复最新生产验证 run 的真实 sent 状态。
- 回归测试 `tests/test_run_visibility.py` 覆盖 future controlled backfill 不过滤最新数据，同时用户可见运行时间保持简单格式，不显示内部验证回填说明。
- 正式报告已全中文化：策略运行报告 Markdown/HTML 由 `app/core/reporting.py::render_markdown_report` 统一输出中文；`outputs/preflight/PRODUCTION_READINESS_REPORT.md` 已同步当前 production-ready、24个月净值规则、Top5/观察池和最新 475-member ZIP 摘要；`outputs/preflight/PRODUCTION_READINESS_REPORT.pdf` 为 2 页中文 PDF。
- schedule 已改为北京时间 `08:30-17:30` 每小时一次，共 10 次：`R1=08:30`, `R2=09:30`, `R3=10:30`, `R4=11:30`, `R5=12:30`, `R6=13:30`, `R7=14:30`, `R8=15:30`, `R9=16:30`, `R10=17:30`；当前 Australia/Sydney 显示为 `10:30-19:30 AEST`。
- UI P2 upgrade 已完成：`outputs/application/index.html` 是全中文本地 app 首页，首屏展示当前持仓建议、持仓建议、当前持仓及时间、上轮持仓及时间、目标/基准权重时间、需操作的行为；首页说明性副标题已移除；“时间与口径”不再展示运行 ID；顶部“当前运行”和运行时间线不再把 `R1-N` 作为用户可见时段标题，统一显示最新运行时间 `YYYYMMDD - HH:MM TimeZone`；当前持仓建议卡片显示最新更新时间、策略份额动作和相较对比时间，布局已改为更干净的卡片结构；持仓建议表的基准权重口径可在“初始持仓权重”和“上轮对比权重”之间切换，原“相对上轮”列已改为“相对比例”，按目标权重相对当前选定基准权重计算比例变化；重复的“当前/上轮持仓对比”板块已删除，首页不再重复显示当前/上轮策略份额表；“操作入口”上方新增“运行时间线”板块，默认表格视图，支持点击切换到时间线可视化，买入/增加用红色，卖出/减少用绿色，买卖同时用红绿分段标记；“操作入口”新增“基金库”功能板块，点击后在弹窗中展示所有已入库基金的申购状态、赎回状态、申购/赎回费、管理费、托管费、销售服务费、合计运营费、申购费分档、赎回费分档、来源、上次进入候选池时间、当前进入候选池天数和当前状态，并可从基金库进入单基金详情；“操作入口”新增“使用说明”功能板块，详细说明 Serenity 选股判断、证据置信度、权重配置公式、持仓调整逻辑、重平衡触发、人工复核和执行边界，内容只在隐藏弹窗内展示，不污染首页关键区域；“操作入口”新增轻量“人工复核”卡片，完整复核队列只在隐藏弹窗内展示，支持复核动作选择、备注、保存到数据库、清空和复制复核记录，不自动交易、不提交申购赎回；刷新按钮固定在页面右上角，若通过 `.app` 打开会调用本地 `/api/refresh` 同步最新数据并显示 `目前更新到最新时间 YYYYMMDD - HH:MM TimeZone 保持当前持仓/减仓...` 弹窗；增加/买入红色，减少/卖出绿色，维持浅蓝色；基金名可点击查看当前/上轮 Top5 持仓基金库信息，包括首次进入策略 Top5 时间、上次进入候选池时间、当前进入候选池天数、当前状态、费用/状态快照时间、申购赎回、申购费金额分档、赎回费持有期分档、费率规则时间、管理费、托管费、销售服务费、合计运营费和来源证据。
- 费率分档 P2 修正已完成：`fund_rules.csv`、SQLite `fund_rule_snapshot`、normalizer、preflight/intake、scoring、application portal 均支持 `subscription_fee_schedule`、`redemption_fee_schedule`、`fee_schedule_as_of`、`fee_schedule_note`；缺失申购/赎回分档会作为 execution-critical gap，不能再用单一 headline fee 硬下结论。
- 时间格式统一已完成：用户可见的 app 首页、刷新 toast、后续 Markdown 报告和通知正文统一使用 `YYYYMMDD - HH:MM TimeZone`；SQLite 内部 ISO 时间、文件名时间戳、`YYYY-MM-DD` 导入模板保持不变，以免破坏查询和数据校验。
- App 入口已设置：`~/Downloads/Serenity 每日分析.app` 与 `/Applications/Serenity 每日分析.app` 是干净 shell `.app` bundle，打开本地首页；旧 `~/Downloads/application` 下属于本项目的 Serenity 入口已清理，不再作为主入口。
- App 图标已设置并重新安装：`outputs/application/serenity-app-icon.png` 是 1024px 预览图；`outputs/application/SerenityIcon.iconset/` 生成多尺寸 macOS iconset；`outputs/application/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns`、`~/Downloads/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns` 和 `/Applications/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns` 均已存在，最新 `.icns` 大小 604959 bytes，SHA256 一致；`Info.plist` 已设置 `CFBundleIconFile=SerenityIcon` 和 workspace-scoped bundle id；`Contents/PkgInfo=APPL????`；LaunchServices 已重新注册两个入口，Finder/Dock 已刷新。completion audit 的 Downloads 与 Applications app entry 检查现在把 `icon=True`、`icon_size`、`bundle_id_scoped=True`、`pkginfo=True` 和 `icon_plist=True` 纳入通过条件。
- 首页“打开快照”入口已修复并完成验证：SQLite 中的绝对 `offline_html_path` 现在会按 `outputs/application` 生成相对链接，当前生成 href 为 `../../data/reports/sda_20260613T053528Z_r8_2579b9f4_report.html`，目标文件存在；报告页标题已改为 `Serenity 每日分析正式报告 sda_20260613T053528Z_r8_2579b9f4`，正文标题为 `Serenity 每日分析正式报告`。
- P2 risk-gate quality upgrade 已完成：`outputs/tests/risk_gate_regression_latest.json` 证明 `max_drawdown_block` 与 `recovery_time_block` 两个 hard gate 都会 fail-closed。
- P2 benchmark queue 已改成按 benchmark 拆分：当前 action queue 为 4 个 P2 source-quality rows，`benchmark_source_priority=2`，`benchmark_history=2`。

## 关键决策

- 不自动下单，不提交基金申购/赎回。
- `baseline_snapshot` 是后续纪律审计 reference；不再以用户当前 Alipay 仓位做 baseline。
- Alipay holdings CSV 若是 sample-like，只 warning 并忽略，不阻断 production baseline。
- 支付宝/MooMoo 交易可用性只作为交易路径建议与人工确认提示；不能因为不支持支付宝或 MooMoo 交易就把 Serenity 候选对象排除。
- `automation-tick --now <future workday>` 的日期传递已修复；scheduler 现在把目标 workday date 传入 `run_slot`。
- comparison 现在跳过非北京工作日或非 `success/pass` 的历史 R-slot，避免周末/测试 run 污染 previous-day 对比。
- 用户已明确 OpenD 是自己打开的；不要关闭 user-owned OpenD/MooMoo。
- recurring production-mail launchd 未自动安装；launchd 仍 shadow-safe。
- Codex app cron automations 已禁用，避免自动运行创建 sidebar chat：
  - `serenity-daily-analysis-beijing-hour-slots`：`PAUSED`，保留旧整点组但不唤醒。
  - `serenity-daily-analysis-beijing-half-hour-slots`：`PAUSED`，保留旧半点组但不唤醒；北京 `08:30-17:30` 每小时运行由本地 launchd 负责。
- MooMoo/OpenD benchmark exact probe 不能伪装成成功：`SH.000001` 因 CN MarketIndixes quote permission 被拒，MooMoo exact SPX symbol 不支持/unknown，`US.SPY` proxy 可取但不能提升为 exact index proof。

## 已改/需看文件

- Core:
  - `app/adapters/manual_sources.py`
  - `app/db.py`
  - `app/core/pipeline.py`
  - `app/core/scoring.py`
  - `app/core/preflight.py`
  - `app/core/intake_validator.py`
  - `app/core/intake_promoter.py`
  - `app/core/fund_rule_normalizer.py`
  - `app/core/fund_nav_history_collector.py`
  - `app/core/platform_trade_checker.py`
  - `app/core/production_intake_pack.py`
  - `app/core/risk_gate_regression.py`
  - `app/core/application_portal.py`
  - `app/core/application_server.py`
  - `app/core/reporting.py`
  - `app/core/notification.py`
  - `app/core/mail_smoke.py`
  - `app/adapters/mail_notifier.py`
  - `app/core/time_display.py`
  - `app/core/run_visibility.py`
  - `app/core/history_integrity.py`
  - `app/core/completion_audit.py`
  - `data/manual/fund_rules.csv`
  - `data/manual/price_history.csv`
  - `app/templates/fund_rules_template.csv`
  - `app/templates/mail_info.md`
  - `app/templates/mail_urgent.md`
  - `app/templates/mail_warn.md`
  - `pyproject.toml`
- Tests:
  - `tests/test_scoring.py`
  - `tests/test_risk_gate_regression.py`
  - `tests/test_fund_rule_normalizer.py`
  - `tests/test_intake_bundle_normalizer.py`
  - `tests/test_intake_promoter.py`
  - `tests/test_production_unlock.py`
  - `tests/test_reporting_ui.py`
  - `tests/test_notification.py`
  - `tests/test_mail_smoke.py`
  - `tests/test_mail_notifier.py`
  - `tests/test_run_visibility.py`
  - `tests/test_platform_trade_checker.py`
  - `tests/test_fund_nav_history_collector.py`
  - `tests/__init__.py`
- User-facing:
  - `outputs/application/index.html`
  - `outputs/application/downloads-entry.html`
  - `outputs/application/Serenity 每日分析.app`
  - `outputs/application/serenity-app-icon.png`
  - `outputs/application/SerenityIcon.iconset/`
  - `outputs/tests/VALIDATION_SUMMARY.md`
  - `outputs/implementation/CODEX_AUTOMATION_READY.md`
  - `outputs/implementation/CODEX_AUTOMATION_PROPOSALS.md`
  - `outputs/implementation/LAUNCHD_INSTALL_GUIDE.md`
  - `outputs/implementation/automation_manifest.json`
  - `outputs/preflight/PRODUCTION_READINESS_REPORT.md`
  - `outputs/preflight/PRODUCTION_READINESS_REPORT.pdf`
  - `outputs/preflight/platform_trade_check_latest.md`
  - `outputs/preflight/platform_trade_check_latest.csv`
  - `outputs/preflight/platform_trade_check_latest.json`
  - `outputs/preflight/fund_nav_history_latest.md`
  - `outputs/preflight/fund_nav_history_latest.csv`
  - `outputs/preflight/fund_nav_history_latest.json`
  - `outputs/preflight/price_history_candidate.csv`
  - `outputs/completion_audit/completion_audit_latest.md`
  - `outputs/tests/risk_gate_regression_latest.json`
  - `outputs/tests/risk_gate_regression_latest.md`
  - `outputs/package/serenity_daily_analysis_delivery.zip`

## 验证命令与结果

```bash
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json
# production_ready=true, blockers=[]

SERENITY_MAIL_SEND_ENABLED=true python -m app.cli automation-tick --now 2026-06-15T14:30:00+08:00 --allow-duplicate --no-dry-run --send-mail --local --json
# action=ran, due_slot=R8, data_quality_status=pass, send_status=sent, local_status=sent

pytest -q
# passed

python -m app.cli benchmark-smoke --json
# production_ready=true; MooMoo exact index unavailable for SH.000001/SPX, exact fallback windows still computable

python -m py_compile app/core/application_portal.py
# passed

pytest -q tests/test_reporting_ui.py tests/test_application_server.py
# 5 passed

python -m py_compile app/core/application_portal.py app/core/completion_audit.py
# passed

python -m py_compile app/core/notification.py app/core/reporting.py
# passed

python -m py_compile app/core/reporting.py app/core/pipeline.py app/core/completion_audit.py
# passed

pytest -q tests/test_reporting_ui.py tests/test_application_server.py tests/test_completion_audit.py
# 21 passed

pytest -q tests/test_notification.py tests/test_automation_tick.py tests/test_integration.py
# 5 passed

python -m pytest -q tests/test_reporting_ui.py tests/test_integration.py tests/test_notification.py
# 6 passed

python -m pytest -q tests/test_completion_audit.py tests/test_reporting_ui.py tests/test_integration.py tests/test_notification.py
# 21 passed

python -m pytest -q
# 93 tests passed; 1 third-party moomoo DeprecationWarning

python -m pytest --collect-only
# 93 tests collected

python -m app.cli notify --run-id sda_20260613T053528Z_r8_2579b9f4 --dry-run --json
# send_status=drafted; title=[Serenity自动化][复核] 信号变化，保持当前持仓; run_log.notification_status remains sent; sent notification row remains sent;local=sent

python -m app.cli application-portal --json
# status=pass; Downloads and /Applications app entries rebuilt with SerenityIcon.icns

python - <<'PY'
from pathlib import Path
paths = [
    Path('outputs/application/serenity-app-icon.png'),
    Path('outputs/application/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns'),
    Path.home() / 'Downloads/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns',
    Path('/Applications/Serenity 每日分析.app/Contents/Resources/SerenityIcon.icns'),
]
for path in paths:
    print(path, path.exists(), path.stat().st_size if path.exists() else 0)
info = Path('/Applications/Serenity 每日分析.app/Contents/Info.plist').read_text(encoding='utf-8')
print('CFBundleIconFile' in info, 'SerenityIcon' in info)
PY
# preview png exists; all three app SerenityIcon.icns files exist; /Applications Info.plist icon key/name true

python -m app.cli application-portal --json
# status=pass; Downloads and /Applications app entries rebuilt

python -m app.cli slots --json
# R1-R10 = 08:30,09:30,10:30,11:30,12:30,13:30,14:30,15:30,16:30,17:30 Beijing time

pytest -q tests/test_timezones.py tests/test_scheduler.py tests/test_automation_tick.py tests/test_completion_audit.py
# 25 passed

# Browser verification via local preview at http://127.0.0.1:8877/outputs/application/index.html
# 点击基金库后 5 张基金卡片显示当前状态和入池天数；点击查看详情后显示上次进入候选池时间、当前进入候选池天数和当前状态
# 维持浅蓝色样式 computed background: rgb(232, 244, 255)

python - <<'PY'
from pathlib import Path
import re
html=Path('outputs/application/index.html').read_text()
m=re.search(r'<a class="action" href="([^"]+)">打开快照</a>', html)
print({'href': m.group(1) if m else None})
if m:
    p=(Path('outputs/application') / m.group(1)).resolve()
    print({'resolved': str(p), 'exists': p.exists()})
PY
# href=../../data/reports/sda_20260613T053528Z_r8_2579b9f4_report.html; exists=True

# Browser verification via local preview at http://127.0.0.1:8877/outputs/application/index.html
# Clicking 打开快照 navigated to /data/reports/sda_20260613T053528Z_r8_2579b9f4_report.html
# Report heading detected: Serenity 每日分析正式报告

python -m app.cli risk-gate-regression --require-pass --json
# status=pass; cases=max_drawdown_block,recovery_time_block

file outputs/preflight/PRODUCTION_READINESS_REPORT.pdf
# PDF document, version 1.4, 3 pages

mdls -name kMDItemNumberOfPages -name kMDItemContentType -name kMDItemFSSize outputs/preflight/PRODUCTION_READINESS_REPORT.pdf
# content type=com.adobe.pdf; pages=3; size=716375

sips -s format png outputs/preflight/PRODUCTION_READINESS_REPORT.pdf --out /tmp/serenity_readiness_report_page1.png
# first-page PNG rendered successfully

SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json
# overall_status=complete, completion_percent=98.59, pass/warn/block=70/1/0; schedule_exact pass; codex_app_automation_active pass with both Serenity Codex cron automations PAUSED

python -m app.cli package-delivery --json
# status=pass, member_count=342, included_private_like_members=[]

unzip -tq outputs/package/serenity_daily_analysis_delivery.zip
# no compressed data errors
```

## 未解决风险

- `shadow_ready_gate` warning 是保守语义：production preflight 已 pass，但 shadow-safe launchd 仍存在且默认不发真实邮件。
- benchmark exact source 仍有 public aggregation fallback；MooMoo/官方 exact index source 是剩余 P2 quality upgrade。
- MooMoo A-share ETF/CN index quote permission 有限制；US/HK proxy K-line 已采集并入库。

## 下一步

下一步不是继续修 blocker，而是观察下一个真实北京工作日自动化是否由本地 launchd 静默运行且不再创建 Codex sidebar chat。若要启用 launchd 真实邮件常驻，需要用户明确确认安装 `outputs/implementation/com.serenity.daily-analysis.production-mail.plist`。

## 2026-06-13 人工复核持久化更新

当前目标：人工复核记录必须能保存进数据库，不能只存在浏览器本地缓存。

已改：
- `app/db.py` 新增并扩展 `manual_review_decision` 表，用于保存 `review_id/run_id/decision/outcome/outcome_label/system_disposition/refresh_fields/note/saved_at`。
- `app/core/application_server.py` 新增 `/api/manual-review` GET/POST/DELETE，POST upsert 到 SQLite；复核结果只允许三类处置，选择 `promote_top5_candidate_pool` 时触发 `refresh_application()`。
- `app/core/application_portal.py` 人工复核弹窗改为数据库强制保存，不再降级到浏览器端保存；弹窗内展示三类复核结果含义和每个对象“为什么需要人工复核”；文案改为“复核结果/保存复核/清空复核记录/保存到数据库”。
- `app/core/completion_audit.py` 将 `manual_review_decision` 纳入必备 SQLite schema。
- `tests/test_application_server.py` 覆盖保存、更新、清空复核记录；`tests/test_reporting_ui.py` 覆盖前端 API 路径和数据库保存文案。

验证结果：
- `python -m py_compile app/db.py app/core/application_server.py app/core/application_portal.py app/core/completion_audit.py` 通过。
- `python -m pytest -q tests/test_application_server.py tests/test_reporting_ui.py tests/test_completion_audit.py` 通过，22 项全绿。
- `python -m pytest -q` 通过，只有 moomoo 依赖 deprecation warning。
- `python -m app.cli application-portal --json` 通过，并同步 `/Users/linzezhang/Downloads/Serenity 每日分析.app` 与 `/Applications/Serenity 每日分析.app`。
- 浏览器验证 `http://127.0.0.1:8876/`：首页关键区域、刷新按钮、人工复核入口存在；人工复核弹窗可打开，7 项复核项带原因说明，三类复核结果可选，页面无浏览器端缓存实现和旧缓存提示文案；使用说明包含三类复核结果、数据库保存和触发 Serenity 全流程说明；控制台无 error。
- 临时 server POST 写入 `manual_review_decision` 返回 `source=sqlite`，SQLite 直接查询可读回；测试记录 `review_id=999999` 已删除，剩余 0。
- `python -m app.cli package-delivery --json` 通过，ZIP 342 members。
- `python -m app.cli completion-audit --json`：overall_status=complete，completion_percent=98.57，pass/warn/block=69/1/0。

剩余风险：
- 直接打开静态 HTML 时无法写 SQLite，会明确提示必须通过 `.app` 本地服务入口写入数据库；不再浏览器端缓存复核记录。
- 当前 DELETE API 是清空全部复核记录；UI 目前只提供“清空复核记录”，未来若真实复核记录增多，建议补单条删除/归档动作。

## 2026-06-13 基金库详情层级交互修复

当前目标：基金库内点击“查看详情”后，关闭基金详情时必须回到基金库，不能直接退回首页。

已改：
- `app/core/application_portal.py` 中基金库详情按钮不再隐藏基金库；基金详情层以更高 z-index 覆盖在基金库上。
- 从基金库进入基金详情时，详情关闭按钮显示“返回基金库”；从首页基金名进入时仍显示“关闭”。
- `Escape` 键改成逐层退出：先关闭基金详情，再关闭基金库，不会一次退出两层。
- 基金库详情按钮新增 `data-open-fund-detail`，方便稳定测试和后续自动化验证。
- `tests/test_reporting_ui.py` 增加层级、按钮文案和旧错误路径的反向断言。

验证结果：
- `python -m py_compile app/core/application_portal.py` 通过。
- `python -m pytest -q tests/test_reporting_ui.py` 通过，4 项全绿。
- `python -m pytest -q tests/test_application_server.py tests/test_reporting_ui.py tests/test_completion_audit.py` 通过，22 项全绿。
- `python -m pytest -q` 通过，仅 moomoo 依赖 deprecation warning。
- 浏览器验证 `http://127.0.0.1:8897/`：打开基金库后点击 `007300` 详情，基金库和详情同时保持打开；详情关闭按钮显示“返回基金库”；点击后只关闭详情，基金库仍显示；再关闭基金库才回首页。

## 2026-06-13 Serenity 优先级与证据置信度修正

当前目标：Score 不应压过 Serenity 选股逻辑；Top5 和目标权重必须先服从 Serenity 判断，Score 只作为证据置信度、数据说服力和小幅权重修正。

已改：
- `app/core/pipeline.py` 新增 Serenity priority 排序与 confidence multiplier；Top5 先按可执行性/人工复核降级、Serenity 候选顺序、再按证据置信度 tie-break 排序。
- `app/core/scoring.py` 将触发原因从 score 主导改为 `serenity judgment supported by evidence confidence` / `evidence confidence watch band`。
- `app/core/reporting.py` 与 `app/core/application_portal.py` 用户可见标签从“得分/Score”改为“证据置信度/ConfidenceScore”，并说明 ConfidenceScore 不是选股主排序。
- `outputs/preflight/PRODUCTION_READINESS_REPORT.md` 与 PDF 同步最新 Top5 排序、证据置信度表头、352-member ZIP 摘要。
- 新增 `tests/test_pipeline_serenity_priority.py` 覆盖 Serenity 优先于更高 Score、Manual Review 降级、Score 只做 bounded modifier、同优先级再按置信度 tie-break。

验证结果：
- `python -m py_compile app/core/pipeline.py app/core/scoring.py app/core/reporting.py app/core/application_portal.py tests/test_pipeline_serenity_priority.py` 通过。
- `python -m pytest -q` 通过，仅 moomoo 依赖 deprecation warning。
- `SERENITY_MAIL_SEND_ENABLED=true python -m app.cli preflight --json`：production_ready=true，blockers=[]，Alipay sample-like 为可选 warning。
- `SERENITY_MAIL_SEND_ENABLED=true python -m app.cli automation-tick --now 2026-06-15T14:30:00+08:00 --force-slot R7 --allow-duplicate --no-dry-run --send-mail --local --json`：run_id=`sda_20260613T094539Z_r7_31fb1cc3`，data_quality_status=pass，Apple Mail/local notification 均 sent。
- 最新 Top5：`008887` 28.70%、`011839` 23.40%、`110026` 19.28%、`007300` 15.83%、`013171` 12.78%。其中 `007300` 证据置信度 91.20 高于前三部分标的但排名第 4，证明 Score 不再机械主导排序。
- Browser 验证 `http://127.0.0.1:8898/`：首页显示“证据置信度”，旧公式 `RawWeight_i = Score_i / sum(Top5 Score)` 不存在，说明页展示 `RawWeight_i = SerenityBase_i x ConfidenceModifier_i`。
- `python -m app.cli application-portal --json` 通过，并同步 `~/Downloads/Serenity 每日分析.app` 与 `/Applications/Serenity 每日分析.app`。
- `python -m app.cli package-delivery --json` 通过，ZIP 352 members，未包含 private-like members。
- `unzip -tq outputs/package/serenity_daily_analysis_delivery.zip` 通过。
- `SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json`：overall_status=complete，completion_percent=98.57，pass/warn/block=69/1/0。

剩余风险：
- `shadow_ready_gate` 仍为 warning，是保守语义：生产预检已 pass，但 shadow-safe launchd 模板默认仍关闭真实邮件。
- SQLite 内部字段仍叫 `total_score/score_snapshot` 以保持 schema 兼容；用户界面和报告语义已改为“证据置信度”。
- 当前正式 PDF 使用本地 reportlab 重新渲染，内容与 Markdown 同步且可用 `sips` 渲染，但视觉样式比旧版更轻量。

## 2026-06-13 调仓逻辑说明与 1% 偏离阈值更新

当前目标：将维持阈值改为 `|Deviation| <= 1.00%`，并把“持仓调整逻辑”从术语解释升级为可理解的决策链：凭什么、为什么、怎么做、做多少、为什么做这么多。

已改：
- `app/config.py` 默认 `deviation_threshold` 从 `0.05` 改为 `0.01`，实际调仓纪律和说明口径一致。
- `app/core/application_portal.py` 使用说明中“持仓调整逻辑”新增完整决策链：
  - 凭什么：数据质量、申赎/费率、非 Block、Serenity baseline 对比。
  - 为什么：偏离代表 Serenity 新判断相对旧 baseline 的变化，不是账户盈亏。
  - 怎么做：`|Deviation| <= 1.00%` 维持，正偏离增配，负偏离减少，非 Action-Ready 暂停新增或复核。
  - 做多少：策略调整份额等于 `TargetWeight - BaselineWeight`，金额需人工按计划投入资金换算。
  - 为什么这么多：目标权重已由 Serenity 优先级、证据置信度、30% cap 和归一化计算完成。
- `tests/test_discipline.py` 增加 1% 边界保持维持、1.1% 触发事件。
- `tests/test_reporting_ui.py` 覆盖新说明文案，并反向断言旧 5% 文案不存在。
- 同步更新 `outputs/preflight/PRODUCTION_READINESS_REPORT.md`、Task Pack 和 PRD 中的目标权重偏离阈值。

验证结果：
- `python -m py_compile app/config.py app/core/application_portal.py tests/test_reporting_ui.py tests/test_discipline.py` 通过。
- `python -m pytest -q tests/test_discipline.py tests/test_reporting_ui.py` 通过，6 项全绿。
- `python -m pytest -q` 通过，仅 moomoo 依赖 deprecation warning。
- `python -m app.cli application-portal --json` 通过，并同步 `~/Downloads/Serenity 每日分析.app` 与 `/Applications/Serenity 每日分析.app`。
- Browser 验证 `http://127.0.0.1:8899/`：使用说明 DOM 中存在 1% 维持带、凭什么/为什么/怎么做/做多少/为什么做这么多，旧 5% 文案不存在。
- `python -m app.cli package-delivery --json` 通过，ZIP 352 members，未包含 private-like members。
- `unzip -tq outputs/package/serenity_daily_analysis_delivery.zip` 通过。
- `SERENITY_MAIL_SEND_ENABLED=true python -m app.cli completion-audit --json`：overall_status=complete，completion_percent=98.57，pass/warn/block=69/1/0。

剩余风险：
- 最新数据库中的历史运行仍是按当时阈值生成的历史证据；未来新运行会按 1% 阈值执行。
- 1% 阈值会更敏感，可能增加邮件/复核频率；如果噪声过高，下一步应增加“连续两轮确认”或“费用后净收益覆盖”二级门槛。
