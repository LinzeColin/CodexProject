# HANDOFF: Serenity Daily Analysis

Timestamp: 20260614 - 10:42 CST / 20260614 - 12:42 AEST

## 当前目标

Serenity Daily Analysis 已完成 baseline-first 生产时段验证：先由 Serenity 生成基础持仓建议，后续每日更新相对 Serenity baseline 做候选池刷新、策略更新、纪律审计和调仓建议。当前 Alipay 持仓不是 baseline 前置条件，只是可选 personal-position overlay。

## 当前状态

- 重要修正：用户可见“运行时间”只显示最新一次运行时间，不再显示 `验证回填` 或 `生成时间`。controlled backfill 只作为 agent/审计内部责任，不暴露给用户操作界面。
- 最新生产验证 run 仍为 `sda_20260613T094539Z_r7_31fb1cc3`，归属运行时间 `2026-06-15T14:30:00+08:00`，`verification_kind=future_controlled_backfill`，Apple Mail/local notification 均 sent。
- 当前 app/report index 已重新生成：首页、持仓建议、基金库、费用分档、申购/赎回状态、管理费/托管费/销售服务费等信息恢复到最新 pass run；报告索引和首页运行时间仅显示 `YYYYMMDD - HH:MM TimeZone`。
- completion audit：`overall_status=complete`，`completion_percent=98.57%`。
- production preflight：`SERENITY_MAIL_SEND_ENABLED=true` 下 `production_ready=true`，blockers=0，latest shadow run 为 `success/pass`。
- tests：`python -m pytest -q` passed，104 tests collected；push 前置钩子也已跑全量 pytest 通过。
- final package：`outputs/package/serenity_daily_analysis_delivery.zip`，356 members，private evidence excluded。
- 最新 Top5 历史生产验证仍可追溯：`008887`, `011839`, `110026`, `007300`, `013171`。
- 纪律动作历史生产验证：5 个 `Maintain`；该记录在首页继续作为最新建议显示，运行时间按普通运行时间展示。
- 平台交易可用性已改为 advisory-only：`fund_rules.csv`、模板、normalizer、SQLite `fund_rule_snapshot`、pipeline、基金库 UI 都支持 `alipay_trade_status`、`moomoo_trade_status`、`platform_trade_note`；这些字段只做交易路径建议与人工确认提示，不参与 Serenity 候选池排除、不改变 Top5 排序、不因为支付宝或 MooMoo 不支持交易而剔除对象。
- GitHub 备份同步到 `LinzeColin/Serenity-Alipay` 的 `main` 分支；具体 commit 以远端 `main` HEAD 为准。同步源为已验证交付 ZIP 内容，沿用 private evidence 排除规则，本地同步目录为 `/Users/linzezhang/Documents/Codex/2026-06-12/Serenity-Alipay-sync-20260614T020954Z`。
- 历史完整性保护已启用：`python -m app.cli history-integrity --write-baseline --require-pass --json` 已建立 `outputs/audit/history_integrity_baseline.json`，当前基线覆盖 21 张 SQLite 历史表和 142 个历史文件；后续允许新增运行/快照/报告/通知，不允许修改、删除、覆盖或重渲染已进入基线的旧历史行/旧历史文件。
- 历史时间线已启用：`outputs/audit/history_artifact_timeline.csv` / `.md` 记录每个受保护分析报告、通知、MooMoo 快照/原始数据文件的 `file_created_at`、`file_modified_at`、`file_metadata_changed_at`、`size_bytes`、`sha256` 以及可关联的 `run_id`、`run_time_bj`、`run_created_at`；`outputs/audit/history_snapshot_table_timeline.csv` 记录每张受保护 SQLite 快照表的 row count、table hash、首末 run 时间和首末 run 创建时间。
- `completion-audit` 已接入 `history_integrity_append_only`：当前 `completion_percent=98.59%`，70 pass / 1 warn / 0 block；历史完整性 violations=0。
- `asset_master` 已改为 first-seen immutable：后续 Alipay 导入或候选池刷新不会覆盖既有 `asset_code` 的历史身份字段；更新后的名称/分类只能通过新快照或新来源证据表达，不能回写旧身份行。
- Apple Mail + local notification：`sent;local=sent`，收件人 `linzezhang35@gmail.com`。
- Email 模板已升级为 Gmail 可识别的 HTML + 纯文本兜底：实际发送路径 `app/core/pipeline.py`、独立通知路径 `app/core/notification.py::render_notification_for_run` 和 smoke 路径 `app/core/mail_smoke.py` 都会生成 HTML 草稿；Apple Mail 发送优先使用 `html content`，失败后回退纯文本。HTML 邮件含 H1/H2/H3 标题层级、内联样式、加粗/斜体/下划线重点提示、需变化行为高亮、当前持仓建议表格；正文删除 `来源与时间戳`、`sources_json`、source chain、旧英文动作提示和可见 `运行 ID`。最新 dry-run 草稿为 `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.md` 与 `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.html`，标题 `[Serenity自动化][复核] 信号变化，保持当前持仓`。
- 通知 dry-run 副作用已修复：`notify --dry-run` 现在写入独立 `_draft_preview` 记录，不覆盖真实 `sent;local=sent` 记录，也不修改 `run_log.notification_status`；本轮已从交付 ZIP 数据库快照恢复最新生产验证 run 的真实 sent 状态。
- 回归测试 `tests/test_run_visibility.py` 覆盖 future controlled backfill 不过滤最新数据，同时用户可见运行时间保持简单格式，不显示内部验证回填说明。
- 正式报告已全中文化：策略运行报告 Markdown/HTML 由 `app/core/reporting.py::render_markdown_report` 统一输出中文；`data/reports` 中 24 份已有 Markdown/HTML 报告对已按中文模板重渲染；`outputs/preflight/PRODUCTION_READINESS_REPORT.md` 已同步最新 356-member ZIP 摘要；`outputs/preflight/PRODUCTION_READINESS_REPORT.pdf` 为 3 页中文 PDF。
- schedule 已改为北京时间 `08:30-17:30` 每小时一次，共 10 次：`R1=08:30`, `R2=09:30`, `R3=10:30`, `R4=11:30`, `R5=12:30`, `R6=13:30`, `R7=14:30`, `R8=15:30`, `R9=16:30`, `R10=17:30`；当前 Australia/Sydney 显示为 `10:30-19:30 AEST`。
- UI P2 upgrade 已完成：`outputs/application/index.html` 是全中文本地 app 首页，首屏展示当前持仓建议、持仓建议、当前持仓及时间、上轮持仓及时间、目标/基准权重时间、需操作的行为；首页说明性副标题已移除；“时间与口径”不再展示运行 ID；顶部“当前运行”和运行时间线不再把 `R1-N` 作为用户可见时段标题，统一显示最新运行时间 `YYYYMMDD - HH:MM TimeZone`；当前持仓建议卡片显示最新更新时间、策略份额动作和相较对比时间，布局已改为更干净的卡片结构；持仓建议表的基准权重口径可在“初始持仓权重”和“上轮对比权重”之间切换，原“相对上轮”列已改为“相对比例”，按目标权重相对当前选定基准权重计算比例变化；重复的“当前/上轮持仓对比”板块已删除，首页不再重复显示当前/上轮策略份额表；“操作入口”上方新增“运行时间线”板块，默认表格视图，支持点击切换到时间线可视化，买入/增加用红色，卖出/减少用绿色，买卖同时用红绿分段标记；“操作入口”新增“基金库”功能板块，点击后在弹窗中展示所有已入库基金的申购状态、赎回状态、申购/赎回费、管理费、托管费、销售服务费、合计运营费、申购费分档、赎回费分档、来源、上次进入候选池时间、当前进入候选池天数和当前状态，并可从基金库进入单基金详情；“操作入口”新增“使用说明”功能板块，详细说明 Skill 选股逻辑、评分公式、策略等级、权重配置公式、持仓调整逻辑、重平衡触发、人工复核和执行边界，内容只在隐藏弹窗内展示，不污染首页关键区域；“操作入口”新增轻量“人工复核”卡片，完整复核队列只在隐藏弹窗内展示，支持复核动作选择、备注、本地保存、清空和复制复核记录，记录只保存在本机浏览器，不写 SQLite、不自动交易、不提交申购赎回；刷新按钮固定在页面右上角，若通过 `.app` 打开会调用本地 `/api/refresh` 同步最新数据并显示 `目前更新到最新时间 YYYYMMDD - HH:MM TimeZone 保持当前持仓/减仓...` 弹窗；增加/买入红色，减少/卖出绿色，维持浅蓝色；基金名可点击查看当前/上轮 Top5 持仓基金库信息，包括首次进入策略 Top5 时间、上次进入候选池时间、当前进入候选池天数、当前状态、费用/状态快照时间、申购赎回、申购费金额分档、赎回费持有期分档、费率规则时间、管理费、托管费、销售服务费、合计运营费和来源证据。
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
- Codex app cron automations 已同步新 schedule：
  - `serenity-daily-analysis-beijing-hour-slots`：`PAUSED`，保留旧整点组但不唤醒。
  - `serenity-daily-analysis-beijing-half-hour-slots`：`ACTIVE`，当前 Australia/Sydney `10:30-19:30` 半点唤醒，对应北京 `08:30-17:30` 每小时运行。
- MooMoo/OpenD benchmark exact probe 不能伪装成成功：`SH.000001` 因 CN MarketIndixes quote permission 被拒，MooMoo exact SPX symbol 不支持/unknown，`US.SPY` proxy 可取但不能提升为 exact index proof。

## 已改/需看文件

- Core:
  - `app/adapters/manual_sources.py`
  - `app/db.py`
  - `app/core/pipeline.py`
  - `app/core/scoring.py`
  - `app/core/preflight.py`
  - `app/core/intake_validator.py`
  - `app/core/fund_rule_normalizer.py`
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
  - `app/core/completion_audit.py`
  - `data/manual/fund_rules.csv`
  - `app/templates/fund_rules_template.csv`
  - `app/templates/mail_info.md`
  - `app/templates/mail_urgent.md`
  - `app/templates/mail_warn.md`
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
# overall_status=complete, completion_percent=98.57, pass/warn/block=69/1/0; schedule_exact pass; codex_app_automation_active pass with hour PAUSED + half-hour ACTIVE

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

下一步不是继续修 blocker，而是观察下一个真实北京工作日自动化是否按 Codex app cron 唤醒。若要启用 launchd 真实邮件常驻，需要用户明确确认安装 `outputs/implementation/com.serenity.daily-analysis.production-mail.plist`。

## 2026-06-13 人工复核持久化更新

当前目标：人工复核记录必须能保存进数据库，不能只存在浏览器本地缓存。

已改：
- `app/db.py` 新增 `manual_review_decision` 表，用于保存 `review_id/run_id/decision/note/saved_at`。
- `app/core/application_server.py` 新增 `/api/manual-review` GET/POST/DELETE，POST upsert 到 SQLite。
- `app/core/application_portal.py` 人工复核弹窗改为数据库优先保存，静态入口离线时才降级到 `localStorage` 临时缓存；文案改为“保存复核/清空复核记录/保存到数据库”。
- `app/core/completion_audit.py` 将 `manual_review_decision` 纳入必备 SQLite schema。
- `tests/test_application_server.py` 覆盖保存、更新、清空复核记录；`tests/test_reporting_ui.py` 覆盖前端 API 路径和数据库保存文案。

验证结果：
- `python -m py_compile app/db.py app/core/application_server.py app/core/application_portal.py app/core/completion_audit.py` 通过。
- `python -m pytest -q tests/test_application_server.py tests/test_reporting_ui.py tests/test_completion_audit.py` 通过，22 项全绿。
- `python -m pytest -q` 通过，只有 moomoo 依赖 deprecation warning。
- `python -m app.cli application-portal --json` 通过，并同步 `/Users/linzezhang/Downloads/Serenity 每日分析.app` 与 `/Applications/Serenity 每日分析.app`。
- 浏览器验证 `http://127.0.0.1:8896/`：人工复核弹窗可打开，2 项复核项带 `run_id`，旧“保存本地复核”不存在，数据库保存说明和按钮可见。
- 临时 server POST 写入 `manual_review_decision` 返回 `source=sqlite`，SQLite 直接查询可读回；测试记录 `review_id=999999` 已删除，剩余 0。
- `python -m app.cli package-delivery --json` 通过，ZIP 342 members。
- `python -m app.cli completion-audit --json`：overall_status=complete，completion_percent=98.57，pass/warn/block=69/1/0。

剩余风险：
- 直接打开静态 HTML 时无法写 SQLite，会明确降级为浏览器临时缓存；正常 `.app` 入口会启动本地 server，因此可以持久化。
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
