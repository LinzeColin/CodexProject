# Serenity Daily Analysis

Local-first, auditable investment research automation for aggressive but controlled off-platform fund candidate screening.

This tool produces research, ranking, discipline labels, and notification drafts. It does not place trades. Future outperformance versus Shanghai Composite or S&P 500 cannot be guaranteed.

## What It Does

- Imports Alipay fund positions from CSV.
- Loads manual candidate universe, fund rules, and price history snapshots.
- Scores fund-first candidates with deterministic rules.
- Enforces hard gates: MDD >= 40.00% and recovery time >= 365 days.
- Compares 1m, 3m, and 10 trading day returns with Shanghai Composite and S&P 500.
- Generates Top5 target weights, current-vs-target deviation, and action labels.
- Persists runs, sources, scores, recommendations, comparisons, review queues, and notifications in SQLite.
- Generates Markdown reports, offline HTML reports, offline report index, and Mail-ready notification drafts.
- Provides `scheduler-tick` for Codex Automation or launchd.

## What It Does Not Do

- It does not automatically buy or sell.
- It does not bypass Alipay, fund company, moomoo, or broker platform controls.
- It does not promise future benchmark outperformance.
- It does not silently treat moomoo/OpenD failure as healthy data.

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
python -m app.cli source-evidence-audit --json
```

Outputs are written to:

```text
outputs/preflight/PRODUCTION_DATA_REQUEST.md
outputs/intake_pack/
outputs/preflight/PRODUCTION_UNBLOCK_EVIDENCE_MATRIX.md
outputs/preflight/production_unblock_evidence_matrix.csv
outputs/preflight/source_evidence_audit_latest.md
outputs/preflight/source_evidence_audit_latest.csv
```

After filling the pack, validate and promote it safely:

```bash
python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --require-pass --json
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
```

`source-evidence-audit` hashes local evidence files, validates URL shape, and persists rows into SQLite `source_evidence_audit_snapshot`. For a filled intake pack, local evidence can be placed under `outputs/intake_pack/evidence/` and referenced as `evidence/<file>`; audit it with `source-evidence-audit --pack-dir outputs/intake_pack --json`. `promote-intake-pack --apply` only copies files after placeholder and production validation pass. It creates backups under `data/backups/intake_promotions/` and copies validated pack-local evidence into project-level `evidence/`.

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

Production benchmark sources must support exact Shanghai Composite and S&P 500 comparisons across 1m, 3m, and recent 10 trading days.

```bash
python -m app.cli benchmark-smoke --require-production --json
```

Current implementation can generate exact benchmark fallback history into `data/manual/benchmark_price_history.csv` using Yahoo Finance chart data. This unlocks benchmark calculation but remains source priority 5 public aggregation; MooMoo, official exchange/index provider, Alipay, or fund-company official evidence remains preferred.

MooMoo exact-index probes must cover the full 1m/3m/recent-10-trading-day window before they can unlock production benchmark proof. ETF proxies such as SPY/VOO can support warning-level review but cannot unlock exact benchmark proof by themselves.

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
