# Serenity-Alipay 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

中文优先，默认全局中文。用户可读优先。本段是 Owner 首屏摘要，用来回答“这是什么、现在到哪、我下一步看哪里、风险是什么”。技术名词、路径、API 名称可以保留英文，但解释必须先给中文结论。

## 一句话结论
Serenity-Alipay 日常数据与报告项目，当前重点是把隐私边界、可运行入口、生成报告和归档风险讲清楚。

这份中文入口不是目录索引，也不是给机器看的字段清单；它先服务 Owner 决策。读者应该先看到当前是否可用、证据是否足够、哪里有风险、下一步该做什么，以及如果判断错误如何回滚。只有在这些中文结论清楚之后，才需要进入下方的详细路径、测试命令和历史记录。

## 摘要
- project_id: `Serenity-Alipay`
- 项目路径：`Serenity-Alipay`
- current_stage: `S4`
- current_phase: `S4PC`
- current_task: `S4PCT02`
- next_gate: `S4-GATE-PASSED`
- evidence_status: `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。

## 当前状态
这个项目已经纳入 Lean v2 治理入口，首屏必须先说明业务含义、当前阶段、可用证据和限制。Owner 不需要先读源码，也不需要先理解 schema，应该能在本页判断是否继续验证、暂停、回滚或进入下一步。

## Owner 操作入口
1. 先读本文件首屏，确认项目目的、当前任务和下一步。
2. 需要看功能范围时读 `功能清单`，只把有证据的能力当作当前事实。
3. 需要看推进历史时读 `开发记录`，按 Stage -> Phase -> Task 和 stop_gate 判断是否能继续。
4. 需要看模型、公式、参数时读 `模型参数文件`，重点看 active 项和未确认项。
5. 需要机器证据时打开 `docs/governance/` 下的 registry、roadmap、events、STATUS 和 OWNER_STATUS。

## 证据与验证
- active_model_count: `5`
- active_formula_count: `12`
- active_parameter_count: `49`
- 总模型数：`5`；总公式数：`12`；总参数数：`49`。
- 当前证据以仓库文件为准；测试命令、CI 结果或 run manifest 缺失时，只能标记为待验证，不能写成已完成。

## 风险与边界
- 不把历史归档、示例、旧报告、生成物或草稿当成当前生产事实。
- 不因为存在文件路径就默认功能已可用；必须有治理证据、测试结果或 Owner 接受记录。
- 不在没有 Owner 明确确认时改变业务含义、模型参数、公式政策、隐私边界或外部自动化行为。

## 下一步
先补齐中文可读入口，再运行 changed-only 治理检查；若检查失败，优先修复证据、状态和中文说明，不用英文索引页绕过验收。普通开发只走 changed-only compact gate，完整治理计算放到计划任务或手动 all scope。

## 回滚
本次中文可读重做只改文档入口、测试和治理验收规则；如需回滚，恢复本文件和对应人类入口文件即可，不需要迁移数据、不需要改业务代码、不需要触发外部服务。

<!-- CODEX_CHINESE_READABILITY_END -->

# Serenity-Alipay 中文 Owner 可读入口

# Serenity-Alipay 中文 Owner 快速入口

- S6PAT02 中文 Owner 快速入口：用户可读优先；中文优先，默认全局中文。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02` 仍在逐项目进行，只补 Owner 路径，不改产品 canonical current_task；S5 结构验收回看任务为 `S5PCT02` / `ACC-S5PCT02`。
- 下一 Gate：`S6PA-GATE` 仍在进行中；S5PC/S5-GATE 的中文验收必须继续以本第一屏和 `docs/Serenity_structure_report.md` 为准。
- 本轮边界：只补 Owner 可读路径，不改运行代码，不改评分/权重/调度/邮件/OpenD/MooMoo/报告算法，不移动文件，不触发 launchd、app 打包或外部账户动作。

| Owner 判断项 | 当前路径 | 状态 |
|---|---|---|
| app | `app/` | 默认应用源码和运行入口，本轮不改 |
| tests | `tests/` | 验证层，本轮不改 |
| data/manual | `data/manual/` | 可审计手工输入，不是自动输出 |
| runtime/output | `data/reports/`、`data/notifications/`、`data/moomoo/`、`data/backups/`、`outputs/` | 运行历史、通知草稿、MooMoo/OpenD 证据、备份和输出包，不作为模型参数事实源 |
| 外部自动化 | OpenD、真实邮件、launchd、app 打包 | 本轮不触发、不安装、不发送、不打包 |
| ops/handoff | `HANDOFF.md`、`BACKUP_SYNC_NOTE.md`、`DEVELOPMENT_BUG_REGRESSION_LOG.md` | 交接和运维说明，不是默认运行入口 |

- 最小验证路径：进入 `Serenity-Alipay/`，运行 `python -B -m unittest tests.test_s3pct03_lifecycle -q`；本轮结构证据记录为 `Ran 4 tests OK`。
- 外部副作用确认：结构任务不得触发 OpenD、真实邮件、launchd 安装、app 打包或外部账户动作；证据在 `governance/stage_gates/s5pc/serenity_smoke_tests.log`，核心导入记录为 `S5PCT02_SERENITY_CORE_IMPORT_SMOKE_PASS app=app tests=52 outputs=115 data=151 external_side_effects=false`。
- 失败去向：若出现 `No module named pytest`，先按环境 blocker 处理依赖；若 lifecycle 或 core import 断言失败，再查 `Serenity-Alipay/docs/Serenity_structure_report.md` 和 `tests/`。
- 回滚：revert 本次 README/报告/gate 证据提交即可；本轮不改运行代码、不移动文件、不触发外部自动化。

# Serenity Daily Analysis

Local-first, auditable investment research automation for aggressive but controlled off-platform fund candidate screening.

This tool produces research, ranking, discipline labels, and notification drafts. It does not place trades. Future outperformance versus Shanghai Composite or S&P 500 cannot be guaranteed.

## What It Does

- Imports Alipay fund positions from CSV.
- Loads manual candidate universe, fund rules, and price history snapshots.
- Scores fund-first candidates with deterministic rules.
- Enforces hard gates: MDD >= 40.00% and recovery time >= 365 days.
- Enforces candidate NAV history: every fund entering screening or candidate scope must have at least 24 months of NAV history.
- Compares 1m, 3m, 12m, and 10 trading day returns with Shanghai Composite and S&P 500.
- Generates Top5 target weights, current-vs-target deviation, and action labels.
- Persists runs, sources, scores, recommendations, comparisons, review queues, and notifications in SQLite.
- Generates Markdown reports, offline HTML reports, offline report index, and Mail-ready notification drafts.
- Provides `scheduler-tick` for Codex Automation or launchd.

## What It Does Not Do

- It does not automatically buy or sell.
- It does not bypass Alipay, fund company, moomoo, or broker platform controls.
- It does not promise future benchmark outperformance.
- It does not silently treat moomoo/OpenD failure as healthy data.

## Governance

Machine sources of truth live under `docs/governance/`.

中文人类入口：`功能清单`、`开发记录`、`模型参数文件`。这三份文件必须直接保留
owner 可读的功能摘要、Roadmap/任务、模型/参数、证据状态、限制和下一步门禁；
它们不是跳转页，也不是第二套可编辑机器事实源。机器真相仍以
`docs/governance/` 下的 Lean v2 文件为准。

## S5PCT02 结构边界

本节记录 Other8 Wave 2 的结构治理事实，不改变 Review9 Lean v2 产品 Roadmap。

- `app/` 是唯一默认应用源码和运行入口层；本任务不改评分、权重、调度、邮件、OpenD/MooMoo 或报告算法。
- `tests/` 是验证层；`pyproject.toml` 和 `scripts/serenity_launchd_tick.sh` 保留在原位。
- `data/manual/` 是可审计输入数据；`data/reports/`、`data/notifications/`、`data/moomoo/`、`data/backups/`、SQLite 和日志是运行状态、历史事实或恢复证据，不是模型/参数事实源。
- `outputs/` 是生成层，包含 preflight、intake pack、app bundle、package、测试输出和实现参考；S5PCT02 不移动、不归档、不重建历史输出。
- `HANDOFF.md`、`BACKUP_SYNC_NOTE.md`、`DEVELOPMENT_BUG_REGRESSION_LOG.md` 和 `outputs/implementation/` 是 handoff/ops/backup 文档或生成部署参考，不是默认运行入口。
- 结构治理不得触发 OpenD、真实邮件、launchd 安装、app 打包或外部账户动作；机器合同见 `governance/stage_gates/s5pc/serenity_structure_contract.yaml`，Owner 报告见 `docs/Serenity_structure_report.md`。

## Setup

```bash
python -m app.cli doctor
python -m app.cli init-db
pytest -q
```

The MVP uses only Python standard library at runtime. Tests require `pytest`.

## Alipay CSV Format

Template: `app/templates/alipay_positions_template.csv`

```csv
asset_code,asset_name,platform,current_amount,current_weight,cost_basis,unrealized_pnl,as_of,source_note
```

Import:

```bash
python -m app.cli import-alipay --csv data/imports/alipay_positions.csv
```

Additional production intake templates:

```text
app/templates/fund_rules_template.csv
app/templates/candidates_template.csv
app/templates/benchmark_price_history_template.csv
```

Generate a fill-ready production intake pack:

```bash
python -m app.cli production-intake-pack --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli production-unblock-matrix --scan-path ~/Downloads --scan-path ~/Documents --json
python -m app.cli collect-fund-nav-history --apply --require-pass --json
python -m app.cli source-evidence-audit --json
python -m app.cli platform-trade-check --limit 5 --json
```

Outputs are written to:

```text
outputs/preflight/PRODUCTION_DATA_REQUEST.md
outputs/intake_pack/
outputs/preflight/PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md
outputs/preflight/production_unblock_evidence_matrix.csv
outputs/preflight/fund_nav_history_latest.md
outputs/preflight/fund_nav_history_latest.csv
outputs/preflight/source_evidence_audit_latest.md
outputs/preflight/source_evidence_audit_latest.csv
outputs/preflight/platform_trade_check_latest.md
outputs/preflight/platform_trade_check_latest.csv
```

After filling the pack, validate and promote it safely:

```bash
python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --require-pass --json
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
```

`collect-fund-nav-history` fetches candidate fund NAV history, writes a backup before replacing `data/manual/price_history.csv`, and fails closed unless every non-excluded candidate has at least 24 months of NAV history. This is a root rule: any future fund pulled into screening scope or the candidate pool must have 24-month NAV history before it can become Action-Ready. `source-evidence-audit` hashes local evidence files, validates URL shape, and persists rows into SQLite `source_evidence_audit_snapshot`; it also audits candidate NAV history source URLs. `platform-trade-check` fetches Alipay or official fund pages when available, records HTTP status, content hash, evidence snippet, and buy/sell availability into `platform_trade_check_snapshot`; it is advisory-only and must not change candidate inclusion, target weights, or order behavior. For a filled intake pack, local evidence can be placed under `outputs/intake_pack/evidence/` and referenced as `evidence/<file>`; audit it with `source-evidence-audit --pack-dir outputs/intake_pack --json`. `promote-intake-pack --apply` only copies files after placeholder and production validation pass. It creates backups under `data/backups/intake_promotions/` and copies validated pack-local evidence into project-level `evidence/`.

For a single fail-closed production unlock workflow after filling the pack:

```bash
python -m app.cli normalize-fund-rules --csv <current_fund_rules.csv> --as-of YYYY-MM-DD --json
python -m app.cli normalize-candidates --csv <current_candidates.csv> --as-of YYYY-MM-DD --json
python -m app.cli normalize-intake-bundle --fund-rules-csv <current_fund_rules.csv> --candidates-csv <current_candidates.csv> --as-of YYYY-MM-DD --write-pack --json
python -m app.cli production-action-queue --json
python -m app.cli mail-unlock-check --json
python -m app.cli production-unlock-check --json
python -m app.cli production-unlock-check --full-diagnostics --json
python -m app.cli production-unlock-check --apply --require-production --package --json
```

`PRODUCTION_DATA_REQUEST.md` is the shortest user-facing contract for the baseline-first workflow: Serenity baseline candidate source-chain data, fund execution rules, benchmark evidence, and optional Alipay holding overlay. Current Alipay holdings are not required for baseline generation or baseline-relative discipline labels. `normalize-fund-rules` converts current Alipay/fund-company/OCR rule CSVs into canonical intake-pack fund-rule format, including advisory-only Alipay/MooMoo tradability fields; lack of Alipay or MooMoo support must not by itself exclude a Serenity candidate. `normalize-candidates` converts current MooMoo/Alipay/official-source candidate CSVs into canonical intake-pack candidate format and auto-excludes conservative candidates. `normalize-alipay-positions` remains available for a later personal-position overlay. `normalize-intake-bundle` stages the provided inputs into the intake pack, audits pack evidence, and dry-runs promotion. These commands copy local evidence into `outputs/intake_pack/evidence/` by default and do not touch production files unless `--write-pack` is explicit; the bundle command still does not apply production files. `production-action-queue` creates a prioritized No-New-Order evidence queue for remaining blocker or warning-level evidence items. `mail-unlock-check` generates a production-mail launchd template, real-send smoke command, and rollback command without sending mail or modifying launchd. `production-unlock-check` runs pack evidence audit, dry-run promotion, optional apply, preflight, completion audit, and optional ZIP packaging. `--full-diagnostics` continues read-only preflight and completion audit after pack issues while still refusing apply/package side effects. It does not send mail or place trades. `--apply` promotes only after pack evidence and dry-run validation pass.

Build the final delivery ZIP with private evidence excluded by default:

```bash
python -m app.cli package-delivery --json
```

The default package excludes `evidence/`, `outputs/intake_pack/evidence/`, and `data/backups/`. Use `--include-private-evidence` only when you intentionally want private evidence inside the ZIP.
The package writer uses a temporary ZIP and atomic replace so overlapping audit commands cannot read a half-written final archive.

## Completion Audit

Run the original delivery requirement audit:

```bash
python -m app.cli completion-audit --json
python -m app.cli completion-audit --require-complete --json
```

`--require-complete` exits non-zero while production blockers remain. Current expected blockers are real Alipay holdings, fund rules, candidate source chain, and real Apple Mail send config.

## Historical Integrity

Historical data is append-only. Past snapshots, reports, notifications, MooMoo raw snapshots, position snapshots, recommendations, scores, fund-rule snapshots, and source logs are facts from their original run time. Later UI, strategy, report, or agent improvements must not rewrite them to match today's view.

Create the baseline only after the current artifacts are verified:

```bash
python -m app.cli history-integrity --write-baseline --require-pass --json
```

For later development and before packaging, verify that historical rows/files were only appended:

```bash
python -m app.cli history-integrity --require-pass --json
python -m app.cli completion-audit --require-complete --json
```

`history-integrity` stores row/file hashes in `outputs/audit/history_integrity_baseline.json` and blocks if any previously observed historical SQLite row or protected historical file is changed, deleted, overwritten, or rerendered. New forward-only records are allowed. Existing `asset_master` entries are first-seen immutable; refreshed names or classifications must be represented by new snapshots/source evidence, not by mutating historical identity rows.

Audit timelines for human review:

```text
outputs/audit/history_artifact_timeline.csv
outputs/audit/history_artifact_timeline.md
outputs/audit/history_snapshot_table_timeline.csv
```

`history_artifact_timeline.csv` records each protected report, notification, and MooMoo snapshot/raw-data file with `file_created_at`, `file_modified_at`, `file_metadata_changed_at`, `size_bytes`, `sha256`, and linked `run_id` / `run_time_bj` / `run_created_at` when available. `history_snapshot_table_timeline.csv` records each protected SQLite snapshot table with row counts, table hash, and first/last run creation times.

## Fund Execution Window Evidence

General Alipay/off-platform fund execution timing evidence is stored at:

```text
outputs/preflight/ALIPAY_FUND_EXECUTION_WINDOW_EVIDENCE.md
outputs/preflight/alipay_fund_execution_window_evidence.json
```

The general rule is 15:00 Beijing-time cutoff, T-day NAV pricing before cutoff, and typical T+1 confirmation for ordinary domestic open-end funds. QDII, global/HK funds, suspended products, conversions, fast redemption, holidays, and fund-specific announcements must be checked separately.

## Holdings Review Matrix

Discovered local QuantLab/Alipay candidate holdings are triaged into:

```text
outputs/preflight/alipay_holdings_review_matrix.csv
outputs/preflight/holdings_discovery_latest.md
```

The current review matrix contains 28 candidate rows, 0 row-level production candidates, 28 stale rows, and 12 rows requiring special fund rule checks. It is a manual-review aid only.
The Markdown view redacts absolute local paths for privacy; the JSON artifact keeps machine-verifiable paths for local checks.

The production intake pack also includes helper files generated from this matrix:

```text
outputs/intake_pack/06_alipay_positions_review_prefill.csv
outputs/intake_pack/07_special_fund_rule_checklist.csv
outputs/intake_pack/08_fund_rules_from_review_checklist.csv
outputs/intake_pack/09_candidate_source_review_prefill.csv
```

These helper files are not promoted automatically. Use them to fill `01/02/03` only after current Alipay page confirmation.

## Run One Slot

```bash
python -m app.cli run --slot R7 --dry-run
```

All slots are Beijing time first:

```bash
python -m app.cli slots
```

## Reports

```bash
python -m app.cli report
```

Offline index:

```text
data/reports/index.html
```

## MooMoo/OpenD Data Collection

Readiness smoke:

```bash
python -m app.cli moomoo-smoke --json
```

Read-only snapshot and historical K-line collection:

```bash
python -m app.cli collect-moomoo --symbol US.SPY --start 2026-06-01 --end 2026-06-12 --require-success --json
```

`collect-moomoo` may auto-start OpenD from the discovered workbench when the socket is closed. If the socket was already reachable before the command, it treats OpenD as user-managed and leaves it running. If the command had to start OpenD itself, it cleans up the started process after the run unless `--keep-auto-started-opend` is provided.

Outputs are written to:

```text
data/moomoo/<run_id>/
```

Historical K-line rows are also persisted into SQLite `market_kline_snapshot` with a `source_log` entry using source priority `1` for moomoo.

## Benchmark Smoke

Production benchmark sources must support exact Shanghai Composite and S&P 500 comparisons across 1m, 3m, 12m, and recent 10 trading days.

```bash
python -m app.cli benchmark-smoke --require-production --json
```

Current implementation can generate exact benchmark fallback history into `data/manual/benchmark_price_history.csv` using Yahoo Finance chart data. This unlocks benchmark calculation but remains source priority 5 public aggregation; MooMoo, official exchange/index provider, Alipay, or fund-company official evidence remains preferred.

MooMoo exact-index probes must cover the full 1m/3m/12m/recent-10-trading-day window before they can unlock production benchmark proof. ETF proxies such as SPY/VOO can support warning-level review but cannot unlock exact benchmark proof by themselves.

## Notifications

Dry-run notification:

```bash
python -m app.cli notify --dry-run
```

Controlled Apple Mail smoke, defaulting to draft-only:

```bash
python -m app.cli mail-smoke --json
python -m app.cli mail-unlock-check --json
```

Real Apple Mail send is blocked by default. After production data gates pass, test a real send with explicit environment and confirmation:

```bash
SERENITY_MAIL_SEND_ENABLED=true python -m app.cli mail-smoke --send --confirm-real-send SEND --require-send-ready --json
```

Local macOS notification dry-run writes an AppleScript file. Non-dry-run local notification requires:

```bash
python -m app.cli notify --no-dry-run --local
```

## Scheduler

Manual dispatcher:

```bash
python -m app.cli scheduler-tick --dry-run
```

Production-safe automation dispatcher:

```bash
python -m app.cli automation-tick --no-dry-run --send-mail --local --json
```

`automation-tick` runs preflight first. If production is not ready, it forces dry-run and writes only shadow/manual-review reports and notification drafts.

Test a specific time:

```bash
python -m app.cli scheduler-tick --now 2026-06-12T14:00:00+08:00 --dry-run --allow-duplicate
python -m app.cli automation-tick --now 2026-06-12T15:30:00+08:00 --allow-duplicate --no-dry-run --json
```

launchd template:

```text
outputs/implementation/com.serenity.daily-analysis.plist
```

The launchd template polls every 180 seconds and lets `automation-tick` decide whether a Beijing slot is due. Completion audit checks the template uses the preflight-gated command, current workspace, `SERENITY_DRY_RUN=true`, and `SERENITY_MAIL_SEND_ENABLED=false`.

Install guide:

```text
outputs/implementation/LAUNCHD_INSTALL_GUIDE.md
```

## Production Preflight

Before treating any output as production-ready, run:

```bash
python -m app.cli preflight --require-production --json
```

This gate checks:

- moomoo/OpenD socket and SDK availability.
- moomoo read-only collection evidence when available.
- exact benchmark source readiness for Shanghai Composite and S&P 500.
- whether optional Alipay holding overlay data is real or sample data.
- whether fund rules contain execution-critical fee/status fields.
- whether scheduler artifacts exist.
- whether Apple Mail is script-addressable.
- latest shadow run status.

Current baseline production preflight passes when runtime mail sending is explicitly enabled. Remaining open items are warning-level evidence upgrades, mainly exact benchmark source priority; optional Alipay holding data is ignored by baseline production gates unless you intentionally enable the personal-position overlay path.

If the command exits non-zero, keep the system in shadow mode:

```bash
python -m app.cli scheduler-tick --dry-run
```

## Scoring

The score uses:

- data completeness
- timeliness
- source credibility
- benchmark-relative return
- risk
- execution feasibility

Grades:

- `Action-Ready`: score >= 85 and no hard cap
- `Watch`: 70-84
- `Manual Review`: 55-69 or review-triggered downgrade
- `Block`: <55 or hard-risk/conservative exclusion

Aggregated fallback cannot make a candidate Action-Ready by itself.

## Troubleshooting

- `moomoo_status=unavailable`: OpenD is not reachable at `127.0.0.1:11111`; run remains degraded/research-only.
- Missing fee/redemption status: output is No-New-Order or Manual Review.
- Official source count < 2: cannot be Action-Ready.
- Malformed Alipay CSV: importer reports missing required columns.
- Apple Mail not configured: notification remains draft or records send failure.
