# TAB FIFA Research Pipeline

This local pipeline turns read-only TAB odds snapshots and official public-source checks into repeatable research outputs.

It does not log in, click prices, add selections to Bet Slip, or place bets.

Install/check local dependencies:

```bash
python3 -m pip install -r requirements.txt
npm install
```

In this Codex workspace the bundled Node runtime and Playwright cache may already satisfy the Node dependency. The declared `requirements.txt` and `package.json` are the portable contract for future automation hosts. `PyMuPDF` is required for PDF visual smoke QA, which renders sample pages and blocks publication when the formal report is effectively blank.

Run the current daily-report flow manually:

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/work/tab-research-pipeline
python3 run_daily_report.py
```

Stable one-shot runner for future approved automation wiring:

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/work/tab-research-pipeline
scripts/run_tab_fifa_daily_automation.sh
```

Build or refresh the local Downloads app entry:

```bash
python3 scripts/build_downloads_app_entry.py
```

This creates `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app` and the entry page `/Users/linzezhang/Downloads/FIFA Report/TAB FIFA盘口研究系统.html`. The app opens a local-only server at `127.0.0.1:8767` so the homepage buttons can run active checks. The entry links only to public-safe copied artifacts under `Downloads/FIFA Report/app_assets` and the trusted PDF in `Downloads/FIFA Report`.

The homepage is decision-first:

- first screen: `推荐下注板块`, showing time, board, market, selection, odds, stake, action, analysis consistency, market value, EV, editable probability/odds cells, and confidence;
- recommendation execution is fail-closed: if authorized/current raw or the daily publish gate is not ready, buy candidates remain visible as research candidates but action changes to `暂停执行`, executable new exposure becomes AUD 0, and the page asks for an official/authorized feed or user-exported raw snapshot import before any manual betting decision;
- active test button: runs `scripts/active_timeline_check.py --json --write-latest`, checks whether each day has at least 4 effective analyses and 1 report, then starts the safe backfill worker automatically only when public raw is ready;
- active-test results render as a cadence heatmap in both the homepage and `report_intelligence_latest` outputs, showing which 4-5 hour analysis windows are covered, missing, or unknown for each day;
- each active-test run is persisted into the local SQLite database table `active_timeline_audits`, so `report_intelligence_latest` can chart automation availability, cadence completeness, raw readiness, and gap repair trend across runs;
- backfill button: starts `scripts/app_backfill_worker.py` in safe mode only after `raw_refresh_health_latest.json` is ready. If public raw is stale or blocked, the app fails fast and asks for authorized raw or a user-exported snapshot import first.
- public-raw button: checks the raw access policy. TAB rejects AI controlled access, so the app does not start headed fallback, CAPTCHA bypass, fingerprint spoofing, or stealth-browser refresh. Public raw must come from an official/authorized feed or a user-export/import snapshot; until then the system keeps the last trusted report pointer unchanged.
- private-position button: starts `scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --wait-for-login-ms 600000` with headed Chrome and the reusable private profile. If the user finishes TAB authorization in the opened window, the runner imports the private snapshot and reruns the daily report gate.
- daily-rerun button: starts `scripts/run_tab_fifa_daily_automation.sh` with `TAB_FIFA_REFRESH_RAW=reuse_fresh`, then refreshes the Downloads app. If the private snapshot is still missing, it remains fail-closed.

Backfill safety boundary:

- historical backfills set `TAB_FIFA_NO_LATEST_PUBLISH=1` and `TAB_FIFA_BACKFILL_RECONSTRUCTION=1`;
- backfill runs may create run-scoped/backfill artifacts, but they do not publish `latest_commit.json`;
- backfill output is marked as reconstructed from currently available data and must not be treated as an original point-in-time odds snapshot.

Run the active timeline check manually:

```bash
python3 scripts/active_timeline_check.py --json --write-latest
```

Build the report-intelligence bundle manually:

```bash
python3 scripts/build_report_intelligence.py
```

This writes `outputs/report_intelligence_latest.json/.md/.pdf`. The bundle is a business-facing layer over the existing report database: it summarizes the current trusted report, recommended wagering candidates, active timeline gaps, old-vs-new report history, automation gates, and GitHub open-source model alignment. `scripts/build_downloads_app_entry.py` refreshes this bundle automatically before copying public assets into the Downloads app. The daily report pipeline also writes run-scoped `report_intelligence_<run_id>.json/.md/.pdf` artifacts before `latest_commit.json` is published, then copies them to the latest names only after all public-safety gates pass.

Build the automation doctor bundle manually:

```bash
python3 scripts/build_automation_doctor.py
```

This writes `outputs/automation_doctor_latest.json/.md/.pdf`. The bundle is the business-facing repair plan for entering daily report automation: it summarizes required gates, primary blockers, active timeline gaps, and the ordered command/action queue. It does not create recurring automation and does not place bets.

Build the goal-traceability bundle manually:

```bash
python3 - <<'PY'
from pathlib import Path
from tab_research.goal_traceability import write_goal_traceability_bundle
out = Path("/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/outputs")
write_goal_traceability_bundle(out, out / "tab_fifa_reports.sqlite3")
PY
```

This writes `outputs/goal_traceability_latest.json/.md/.pdf` and stores a snapshot in the SQLite table `goal_traceability_snapshots`. The report maps the user objective to current evidence: requirement/source files, GitHub open-source models, visual dashboards, PDF/database storage, old-vs-new report comparison, the recommendation-first homepage, active-test backfill, raw-data gates, private position monitoring, and automation readiness. `scripts/build_downloads_app_entry.py` refreshes this bundle before `report_visual_inventory_latest.*`, so the visual inventory includes the traceability report.

The stable one-shot runner `scripts/run_tab_fifa_daily_automation.sh` remains the recommended command for a future scheduler after explicit user approval. It runs the local report pipeline once, writes a machine-readable summary, and exits non-zero when the pipeline fails closed. It does not create cron, launchd, or Codex recurring automation by itself.

Automation authorization is explicit and default-off:

```text
config/automation.toml
RUNBOOK.md
```

`config/automation.toml` must remain disabled until the user explicitly authorizes recurring report generation. `allow_auto_betting` must remain `false`; this system is report generation only.

Runner outputs:

- `outputs/automation_run_latest.json`
- `work/private/tab_fifa/automation_run_logs/tab_fifa_daily_<UTC>-<pid>.summary.json`
- `work/private/tab_fifa/automation_run_logs/tab_fifa_daily_<UTC>-<pid>.stdout.log`
- `work/private/tab_fifa/automation_run_logs/tab_fifa_daily_<UTC>-<pid>.stderr.log`

Only the latest machine-readable summary is public-output safe. Raw runner logs stay under the private tree with owner-only permissions.

Each runner execution is also persisted into the public-safe SQLite table `automation_runs` and surfaced in `outputs/tab_fifa_dashboard_latest.html` under `自动化运行历史`, plus `outputs/report_index_latest.json/.md/.pdf` as report-index history. This history records only sanitized fields such as mode, verification mode, status, exit code, raw-refresh readiness, publish readiness, and private-position capture/import exit codes. It is an audit trail, not a latest-success pointer; consumers must still use `outputs/latest_commit.json` for the last formally publishable report.

Run only the offline verification layer through the same wrapper:

```bash
scripts/run_tab_fifa_daily_automation.sh --verify-only
```

`--verify-only` defaults to `TAB_FIFA_VERIFY_MODE=hermetic`, so it checks code, fixtures, read-only browser contracts, and dry-runs without requiring the current live private-position snapshot to be publishable. Use `TAB_FIFA_VERIFY_MODE=artifact-chain-only`, `live-artifacts`, or `full` explicitly when you want those stricter gates.

Run the offline automation-readiness verifier:

```bash
scripts/verify_fifa_automation_readiness.sh
```

This verifier does not open TAB live pages. It checks Python compile, unit/integration fixtures, PDF fixture rendering plus visual smoke QA, JavaScript syntax, read-only refresh dry-run, smoke dry-run, and output safety scanning.

The canonical output directory is the workspace-root `outputs` folder:

```text
/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/outputs
```

Run a minimal live TAB smoke check:

```bash
scripts/tab_real_refresh_smoke.sh --live
```

The live smoke opens Chrome in read-only mode, captures only one `2026 World Cup Matches` fixture into a temporary staging directory, writes `outputs/tab_real_refresh_smoke_latest.json`, and does not promote raw data into the main `outputs` snapshots.

If TAB returns `Access Denied`, treat it as `ai_controlled_access_rejected` for public raw. Do not switch to headed fallback, CAPTCHA bypass, fingerprint spoofing, or stealth browser. Keep the raw gate fail-closed and use one of the allowed recovery paths:

- official/authorized odds feed;
- authorized third-party TAB-labeled odds API, staged first and formally published only after TAB manual final verification;
- user-exported public raw snapshot imported into the pipeline as a fallback, not as the primary daily path;
- existing fresh partial raw only for `research-only` diagnostics, never for executable betting reports.

Authorized third-party odds-provider path:

```bash
# The Odds API: AU region, TAB bookmaker, decimal odds.
# Put real keys only in config/odds_providers.local.env or the shell environment.
cp config/odds_providers.local.env.example config/odds_providers.local.env
# edit config/odds_providers.local.env locally; do not commit it

export TAB_FIFA_THE_ODDS_API_SPORTS="soccer_fifa_world_cup"
export TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY="1"
export TAB_FIFA_PROVIDER_SCOPE="matches"
export TAB_FIFA_THE_ODDS_API_MATCH_MARKETS="h2h,totals,spreads"

# Optional only after provider support is verified for the sport/bookmaker:
# export TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS="team_totals,alternate_team_totals"

# OpticOdds: set the exact endpoint/query from your OpticOdds account/docs.
export TAB_FIFA_OPTICODDS_ENDPOINT="/fixtures/odds"
export TAB_FIFA_OPTICODDS_QUERY="sport=soccer&sportsbook=TAB"

python3 scripts/build_provider_config_doctor.py
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches

# Credit-aware event-level probe for Total/Team Total coverage.
# Keep the probe limit small; do not scan all 68 matches by default.
python3 refresh_odds_provider_raw.py \
  --provider the_odds_api \
  --scope matches \
  --event-market-probe-limit 3 \
  --event-odds-limit 3 \
  --event-odds-markets totals,alternate_totals,team_totals,alternate_team_totals
```

Default provider refresh is Matches-first and ignores region-specific boards such as `2026 World Cup Australia Markets`. The primary market focus is `Result`, `Total Goals Over/Under`, and provider-supplied `Team Total Goals Over/Under`; `spreads` is retained as handicap context. `outrights` are fetched only with `--scope futures` or `--scope all`.

If Python's local SSL trust store is missing, provider requests retry with the bundled `certifi` CA path while keeping TLS verification enabled. Do not disable certificate verification to fix provider access.

`provider_kpi_latest.json/md/pdf` summarizes live coverage, credit usage, market gaps, and next actions. The latest public-safe KPI copy is committed under `artifacts/latest/provider_kpi_latest.*`.

`refresh_odds_provider_raw.py` now rebuilds `provider_kpi_latest.*` after every successful provider refresh, so the KPI refresh id should match the raw/coverage refresh id.

`provider_alternate_plan_latest.json/md/pdf` converts the coverage gap into a credit-aware next-probe queue. It excludes matches already covered by event-level odds, recommends a small batch size, and records stop conditions so the 500-credit monthly budget is not spent scanning all 68 matches by default. Event-level evidence is persisted in `provider_alternate_probe_evidence_latest.json`; a primary-only refresh must not erase low-yield Team Total evidence.

When Team Total event-market probes return no TAB Team Total market keys in the small sample, the plan switches to `fallback_required` and `manual_or_official_provider_priority`. In that state, do not keep spending The Odds API credits on default Team Total probing; use OpticOdds official access/whitelist or the manual TT batch template instead.

Provider Team Total fallback is handled by an explicit manual overlay path, not by scraping TAB or assuming provider coverage:

```bash
# Rebuild the Team Total manual CSV template/status/hash gate/overlay preview/preflight.
python3 provider_manual_verification.py

# Review the generated manual workbench before filling the CSV.
# It batches all 68 candidates, highlights the next batch, and keeps stake at AUD 0.
open "../../outputs/provider_manual_workbench_latest.pdf"

# After manually filling manual_verification/provider_team_total_manual_verification.csv
# and saving a matching manual_verification/provider_team_total_overlay_approval.json,
# explicitly publish the verified overlay into the Matches raw slot.
python3 publish_provider_manual_overlay.py
```

If the manual CSV or approval signature is missing or mismatched, the publish command writes `provider_manual_overlay_publish_latest.json/md/pdf` with `status=blocked_overlay_publish_preflight`, does not write the formal raw slot, does not write the 5-board batch manifest, and keeps the current executable new stake at AUD 0.

This writes provider evidence to:

- `outputs/provider_raw/<refresh_id>/`
- `outputs/odds_provider_raw_latest.json`
- `outputs/odds_provider_coverage_latest.json`

Provider raw is not formal TAB raw by default. To publish verified Matches raw, create a manual TAB final-verification file whose `refresh_id`, `board_id`, and `sha256` match the staged artifact, then run:

```bash
python3 refresh_odds_provider_raw.py \
  --input-json /path/to/provider_payload.json \
  --refresh-id <refresh_id> \
  --verification-file outputs/provider_tab_final_verification_latest.json \
  --publish-verified
```

The verification file format is documented in `config/odds_providers.example.json`. Until provider coverage and manual verification both pass, the current executable new stake remains AUD 0.

Scope publish and full automation are separate. A verified Matches raw can be published for match-board research, but `full_automation_allowed` stays `false` until the required non-region boards, private My Bets snapshot, and preflight gates are also ready.

Private My Bets position snapshots are imported through a private-only chain:

```bash
# Optional live read-only capture into work/private/tab_fifa.
# By default this uses work/private/tab_fifa/tab_chrome_profile as a reusable dedicated profile.
TAB_FIFA_HEADLESS=0 \
node scripts/capture_tab_my_bets_readonly.mjs --report-date DDMMYYYY --wait-for-login-ms 600000

# Convert private raw text into the preflight snapshot consumed by the report pipeline.
python3 import_my_bets_snapshot.py \
  --source ../../work/private/tab_fifa/tab_my_bets_raw_DDMMYYYY.txt \
  --report-date DDMMYYYY
```

`capture_tab_my_bets_readonly.mjs` blocks mutating requests, Bet Slip/place-bet URLs, account profile/payment URLs, and non-My-Bets account pages while allowing read-only My Bets/bets/history data needed to render positions. It reuses a private dedicated Chrome profile at `work/private/tab_fifa/tab_chrome_profile` unless overridden by `TAB_FIFA_CHROME_USER_DATA_DIR` or `--chrome-user-data-dir`; it does not store TAB credentials. The `--wait-for-login-ms` option is for a one-time headed login/bootstrap window; after that, later report runs can reuse the same private profile. On both success and fail-closed login/session failures it writes a private diagnostic file named `tab_my_bets_capture_diagnostics_DDMMYYYY.json`, containing only sanitized status fields such as `auth_status`, `auth_mode`, text length, and a query-stripped URL. `import_my_bets_snapshot.py` writes only to `work/private/tab_fifa/tab_my_bets_positions_DDMMYYYY.json` with owner-only permissions. Public outputs never include raw My Bets text or private stake detail.

The daily runner can optionally execute this private read-only chain before report generation:

```bash
scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY
TAB_FIFA_HEADLESS=0 scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY --wait-for-login-ms 600000
```

This option is explicit and off by default. It does not log in on the user's behalf, click prices, add Bet Slip selections, or place bets. When enabled, it attempts the private capture, imports `tab_my_bets_raw_DDMMYYYY.txt` if present, then continues to the normal fail-closed report gate. The public `automation_run_latest.json` records only sanitized capture/import status and private log basenames.

`automation_readiness_latest.json/.md/.pdf` also includes a public-safe `private_position_bootstrap` section. It reports whether the private profile exists, whether raw My Bets text or the private position snapshot exists, the sanitized capture status, and the next action (`capture` vs `import`) without exposing raw bet content, account identifiers, or local private paths.

Run a strict one-match refresh diagnostic when debugging match-detail expansion:

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node scripts/refresh_tab_readonly.mjs --board matches --output-dir /private/tmp/tab-fifa-strict-smoke --limit 1 --refresh-id strict-smoke --timeout-ms 30000
```

Inputs:

- `outputs/tab_fifa_matches_main_markets_raw_v0_9.json`
- `outputs/previous_report_baseline_v0_9.json`
- FIFA official schedule / qualified teams / men's ranking pages

Outputs:

- `outputs/public_source_audit_v0_11.json`
- `outputs/event_monitor_v0_11.json`
- `outputs/tab_fifa_world_cup_matches_recommendations_v0_11.json`
- `outputs/automation_gate_v0_11.json`
- `outputs/tab_fifa_world_cup_matches_v0_11_pipeline_report.md`
- `outputs/tab_fifa_world_cup_futures_raw_v0_13.json`
- `outputs/tab_fifa_world_cup_futures_recommendations_v0_13.json`
- `outputs/automation_gate_futures_v0_13.json`
- `outputs/tab_fifa_world_cup_futures_v0_13_report.md`
- `outputs/tab_fifa_world_cup_group_betting_raw_v0_14.json`
- `outputs/tab_fifa_world_cup_group_betting_recommendations_v0_14.json`
- `outputs/automation_gate_group_betting_v0_14.json`
- `outputs/tab_fifa_world_cup_group_betting_v0_14_report.md`
- `outputs/tab_fifa_world_cup_australia_markets_expanded_raw_v0_17.json`
- `outputs/tab_fifa_world_cup_australia_markets_recommendations_v0_17.json`
- `outputs/automation_gate_australia_markets_v0_17.json`
- `outputs/tab_fifa_world_cup_australia_markets_v0_17_report.md`
- `outputs/tab_fifa_world_cup_team_futures_multi_raw_v0_16.json`
- `outputs/tab_fifa_world_cup_team_futures_multi_recommendations_v0_16.json`
- `outputs/automation_gate_team_futures_multi_v0_16.json`
- `outputs/tab_fifa_world_cup_team_futures_multi_v0_16_report.md`
- `outputs/portfolio_automation_gate_v0_12.json`
- `outputs/tab_fifa_portfolio_readiness_v0_12.md`
- `outputs/raw_refresh_health_latest.json`
- `outputs/raw_refresh_diagnostics_latest.json`
- `outputs/automation_run_latest.json`
- `outputs/latest_commit.json`

Read `outputs/latest_commit.json` as the single latest-success pointer. It is written last, atomically, after the latest dashboard, latest manifest, latest baseline, latest portfolio compare, PDF copy, bankroll plan, and SQLite database are updated. Consumers should use this file rather than independently combining multiple `*_latest` files.

Automation gate currently requires:

- 95%+ match detail coverage
- 90%+ full core Main Markets coverage
- zero TAB market expansion errors
- TAB raw snapshots captured within 4 hours
- official public-source audit passing
- event/news monitor feed audit passing

The script is intended to become schedulable after user approval. It intentionally does not create any recurring automation by itself. Before scheduling, run the offline verifier, a live smoke check, and a full live daily report successfully.

Current scope distinction:

- `2026 World Cup Matches` is available for research-only diagnostics when its latest partial raw is fresh.
- `2026 World Cup Futures` is available for research-only diagnostics when its latest partial raw is fresh.
- `2026 World Cup Group Betting` is available for research-only diagnostics when its latest partial raw is fresh.
- `2026 World Cup Team Futures Multi` is available for research-only diagnostics when its latest partial raw is fresh.
- `2026 World Cup Australia Markets` is currently unavailable / route mismatch and must not be counted as ready.
- Full TAB FIFA portfolio automation gate must pass at `5/5` on fresh authorized raw snapshots plus private-position preflight before daily automation is enabled.

TAB snapshot refresh note:

- TAB pages are read-only scraped from Chrome; price buttons are not clicked.
- TAB rejects AI controlled access for public raw; the current app blocks automatic public raw refresh instead of attempting headed fallback.
- Live refresh writes to staging first; staged raw is safety-scanned before any promotion into canonical `outputs`.
- Staged raw also must pass freshness, one-batch `refresh_id`, and board parser validation before promotion.
- Current public artifacts are safety-scanned before `latest_commit.json` is published; private fields and local absolute paths are blockers.
- Required raw snapshots must share one `refresh_id`; mixed or legacy no-refresh-id batches are blocked.
- Australia Markets uses header-only expansion (`#market_id .template-header`) to expose lazy-loaded prices.
- Recurring scheduling should only be created after user approval.
