# Development Status

Updated: 2026-06-14 06:04 AEST

## Objective

Develop a TAB FIFA market research system that can eventually produce daily professional Chinese betting-research reports without automatic betting.

## Delivered

- Local web app entry and Downloads app launcher.
- Professional report generation pipeline.
- Recommendation table with EV, Edge, Kelly, Risk of ruin, market funding proxy, confidence, and action gating.
- Active test and missing report timeline.
- Research-only partial daily report path.
- Raw refresh health and recovery dashboards.
- Live board availability strategy.
- My Bets private read-only bootstrap contract.
- GitHub continuity repository structure.
- GitHub repository initialized at `https://github.com/LinzeColin/FIFA`.
- Local cleanup completed and audited in `ops/local_cleanup_audit_20260613.md`.
- macOS app icon designed and installed. Source and generator live under `tab-research-pipeline/assets/app_icon/`; generated `.iconset` cache is ignored and removed by default.
- Parallel review hardening completed for local app security, raw access policy, private My Bets storage, active-test stability, GitHub-worktree path resolution, and delivery packaging.
- Authorized odds-provider raw framework for The Odds API and OpticOdds: provider staging, TAB bookmaker filtering, coverage manifest, manual TAB final-verification hash gate, and verified publish command.
- Provider Config Doctor: ignored local env diagnosis, key-presence redaction, Unknown Sport guard, legacy sport warning, credit-safe event-probe parameters, UI section, API status, and PDF/JSON/MD artifacts.
- Provider request-level sport guard: legacy The Odds API sport key `soccer_world_cup` is normalized before request construction, so a stale shell env or disabled sports discovery does not directly request an invalid sport.
- Provider raw env fallback: `config/odds_providers.local.env.example` can be read without renaming when `.local.env` is unavailable, while placeholder values are ignored and tracked-secret scanning remains mandatory.
- Provider blocked diagnostics: The Odds API HTTP failures now include redacted request context; `Unknown sport` blocked payloads include discovery and credit-safe next checks.
- Provider transport hardening: The Odds API sports discovery and odds requests now retry with a `certifi` CA bundle when the local Python SSL trust store is missing, without disabling TLS verification.
- Provider historical merge hardening: Team Total event-level probes no longer drop previously preserved Total O/U coverage.
- Provider KPI sync hardening: successful provider refresh now rebuilds `provider_kpi_latest.*` in the same command, preventing raw/coverage refresh ids from drifting away from the KPI shown in the app and GitHub artifacts.
- Provider alternate evidence persistence: `provider_alternate_probe_evidence_latest.json` now preserves event-market evidence across primary-only refreshes, so low-yield Team Total evidence is not erased by a normal `h2h,totals,spreads` refresh.
- Provider operational decision layer: low-yield Team Total event-market samples now route to manual/official-provider priority instead of repeating low-value The Odds API probes.
- Provider alternate value-support queue: non-Team Total event-market samples now drive a credit-safe probe queue for `spreads/alternate_spreads/btts/double_chance/draw_no_bet`, while Team Total remains manual/official-provider fallback.
- Provider event-level selector hardening: refresh now prefers `provider_alternate_plan_latest.json.next_probe_queue` and skips previous `event_odds_event_ids` when no plan queue is available, preventing repeated credit spend on the same partially covered event.
- Provider credit estimate hardening: alternate-plan next-batch cost now includes the required primary odds refresh floor, so batch `1` currently shows `4-7` credits instead of the misleading old `1-4`.
- Provider value-support priority: event-level markets are ordered by coverage scarcity, currently `double_chance,draw_no_bet,btts`.
- Provider command console: homepage now has a user-facing collection cockpit for API batch, Team Total manual path, credit runway, gates, stop conditions, coverage bars, next queue, and copy-command feedback; `/api/status.provider_command_center` exposes the same summary for dynamic UI and handoff checks.
- Provider credit runway guard: command center blocks recommended API batches when the next batch would cross the `200` monthly-credit reserve floor; current state has `remaining=201`, next-batch ceiling `7`, and `can_run_provider_batch=false`.
- Team Total manual verification workflow: candidate queue, CSV template, Over/Under pair templates, import status, import quality matrix, next-batch missing-field/missing-direction diagnostics, error-row audit, operator cockpit, field checklist, workflow steps, action contract, manual intake contract, hash gate, overlay preview, overlay publish preflight, explicit overlay raw publish command, UI section, and API status.
- Public Raw Snapshot import workflow: JSON template, research-only preview raw, stable hash, signature publish preflight, explicit Matches raw publish command, status PDF/JSON/MD, UI section, and API status.

## Current Runtime State

- App URL: `http://127.0.0.1:8767/`
- Current local server: launched by user LaunchAgent `com.linzezhang.tab-fifa-research`, serving `http://127.0.0.1:8767/` from `github_sync/FIFA/tab-research-pipeline`; local plist `/Users/linzezhang/Library/LaunchAgents/com.linzezhang.tab-fifa-research.plist` now has `KeepAlive=true`.
- Latest GitHub main SHA: run `git rev-parse HEAD` in the repository root.
- App icon source: `tab-research-pipeline/assets/app_icon/TABFIFAResearch.icns`
- App icon cache policy: keep PNG/ICNS/generator/design notes only; do not keep `*.iconset/` or `__pycache__/`.
- Public raw status: blocked.
- Public raw access policy blocker: `ai_controlled_access_rejected`
- Provider raw status: The Odds API Matches live refresh succeeded; provider analysis is ready for Result/Handicap/Total O/U research, but formal publish remains blocked.
- Provider config doctor: `provider_config_doctor_latest.json/md/pdf`, status `ready`; local env exists; The Odds API key present but redacted; OpticOdds key currently not present; sports discovery enabled; current requested sports `soccer_fifa_world_cup`; no legacy sport remains; event probe limit `0`; stake `AUD 0`.
- Latest provider refresh: `20260613T194716Z-provider-2fec0bef`.
- Latest provider coverage: `soccer_fifa_world_cup`, Matches `64`, Result `64/64`, Handicap `46/64`, Total O/U `51/64`, BTTS `14/64`, Double Chance `11/64`, Draw No Bet `12/64`, Team Total O/U `0/64`, latest request cost `7`, used `299`, remaining `201`.
- Latest event-market evidence: 14 TAB event-market samples show non-Team Total availability for `spreads`、`totals`、`btts`、`double_chance`、`draw_no_bet`、`h2h`; Team Total available sample remains `0`; persisted in `provider_alternate_probe_evidence_latest.json`.
- Provider KPI: `provider_kpi_latest.json/md/pdf`, score `61.50%`, primary gap `Team Total Score O/U 覆盖: 0/64`. Coverage improved, but the credit reserve remains below 50%, so the KPI risk component keeps the recommended batch size at `1`.
- Provider alternate markets plan: `provider_alternate_plan_latest.json/md/pdf`, status `in_progress`, operational decision `alternate_probe_plus_team_total_manual`, non-Team Total probe queue `50`, Team Total fallback queue `64`, recommended next batch `1`, estimated total credit `4-7`.
- Provider command center: `/api/status.provider_command_center` returns refresh `20260613T194716Z-provider-2fec0bef`, batch `1`, queue `50`, credit `4-7`, remaining `201`, credit runway `next_batch_would_cross_reserve`, `can_run_provider_batch=false`, TT batch `TT-001`, stake `AUD 0`, formal/full automation `false`.
- Provider fallback verification queue: `provider_fallback_verification_latest.json/md/pdf`, status `provider_blocked_manual_verification_required`, queue `64`, high priority `51`, blocker `opticodds_access_denied_1010`.
- Provider manual verification import: `provider_manual_verification_template_latest.csv`, `provider_manual_pair_template_latest.csv`, `provider_manual_next_batch_pair_template_latest.csv`, and `provider_manual_verification_status_latest.json/md/pdf`, status `import_missing`, complete `0/64`, high priority complete `0/51`, invalid rows `0`, pair rows `128/16`.
- Provider manual workbench operator cockpit: current batch `TT-001`, next batch `8` events, required pair rows `16`, remaining events `64`, remaining high priority `51`, field checklist `11`, workflow steps `5`, publish status `blocked_until_manual_import_and_signature`, current executable new stake `AUD 0`.
- Provider manual intake contract: current batch `TT-001`, template `provider_manual_next_batch_pair_template_latest.csv`, import target `outputs/manual_verification/provider_team_total_manual_verification.csv`, rebuild command `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`, missing `64`, partial `0`, invalid `0`, complete `0`, next-batch pair rows `16`, exposed through `/api/status.provider_manual_workbench` and `/api/status.provider_command_center`.
- Provider manual import quality: status `waiting_for_manual_rows`, missing events `64`, next batch quality `missing_rows=8`, missing directions `over=8/under=8`, current executable new stake `AUD 0`.
- Provider manual hash gate: `provider_manual_hash_gate_latest.json/md/pdf`, status `waiting_for_import`, ready_for_manual_signature `false`, approved_by_user `false`, publish_compatible_with_provider_raw `false`.
- Provider manual Team Total overlay preview: `provider_manual_overlay_preview_latest.json/md/pdf` and `provider_manual_team_total_overlay_raw_latest.json`, status `waiting_for_import`, overlay `0/64`, formal_publish_allowed `false`.
- Provider manual Team Total overlay publish preflight: `provider_manual_overlay_approval_template_latest.json` and `provider_manual_overlay_publish_preflight_latest.json/md/pdf`, status `waiting_for_import`, overlay_publish_preflight_passed `false`, formal_publish_allowed `false`.
- Provider manual Team Total overlay publish: `provider_manual_overlay_publish_latest.json/md/pdf`, status `blocked_overlay_publish_preflight`, ok `false`, overlay `0/64`, formal_raw_publish_performed `false`, raw_batch_manifest_written `false`, current executable new stake `AUD 0`.
- Public snapshot import: `public_snapshot_import_manifest_template_latest.json`, `public_snapshot_import_status_latest.json/md/pdf`, and `public_snapshot_import_preview_raw_latest.json`, status `waiting_for_snapshot_import`, preview_ready `false`, formal_publish_allowed `false`.
- Public snapshot publish preflight: `public_snapshot_import_approval_template_latest.json` and `public_snapshot_import_publish_preflight_latest.json/md/pdf`, status `waiting_for_snapshot_import`, snapshot_publish_preflight_passed `false`, formal_publish_allowed `false`.
- Public snapshot raw publish: `public_snapshot_raw_publish_latest.json/md/pdf`, status `blocked_publish_preflight`, ok `false`, formal_raw_publish_performed `false`, raw_batch_manifest_written `false`, current executable new stake `AUD 0`.
- Recommended next provider action: pause The Odds API batch execution because the next batch would cross the `200` credit reserve floor; keep Team Total on OpticOdds official access/whitelist or TAB manual final verification from the `TT-001` pair template.
- Duplicate-probe prevention: fixed. The next event-level probe prefers the alternate plan queue, excludes historical covered event IDs, skips previous `event_odds_event_ids` when falling back, and new staging raw merges historical target markets with `provider_historical_merge` warning while keeping formal publish blocked.
- OpticOdds status: earlier live probe was blocked by Cloudflare `1010 Access denied`; blocked attempts are stored in `odds_provider_blocked_latest.json`. The current KPI marks old blocked attempts as `stale_history_only=true` when they do not match the active refresh.
- Research-only scope: `4/5` boards from historical fresh partial raw evidence; current formal publish remains blocked.
- Australia Markets: unavailable / route mismatch.
- My Bets private position: profile login required.
- Current executable new stake: `AUD 0`.
- Latest external review ZIP naming pattern: `/Users/linzezhang/Downloads/FIFA Report/FIFA_agent_review_package_14062026_<git-short-sha>.zip`.

## 2026-06-13 Parallel Review Fixes

- Security: local POST APIs now require a per-process action token plus local Host/Origin/Referer checks. Browser verified the token is injected into the page.
- Security: private My Bets snapshots are rejected if they target public `outputs/private/**`; public safety scans now detect nested private position leaks instead of skipping `private` paths.
- Safety: public raw refresh and live discovery remain access-policy blocked for `ai_controlled_access_rejected`; no headed fallback, CAPTCHA bypass, fingerprint spoofing, or stealth browser path is allowed.
- Correctness: GitHub worktree and original local workspace now resolve workspace/output/private directories through `tab_research.paths` instead of brittle fixed parent-depth paths.
- Stability: active-test now returns cached preview first, then fresh result; if research-only daily report is not ready it says `未达到 ready` instead of falsely saying `已补写`.
- Concurrency: local background runner start paths now use a process lock and write PID files from the parent process.
- Runtime: Downloads HTML and macOS app were rebuilt from the GitHub worktree; `http://127.0.0.1:8767/` is running from `github_sync/FIFA/tab-research-pipeline`.

## Latest Verified Behavior

`/api/public-raw-refresh` returns:

- `started=false`
- `blocked=true`
- `mode=public_raw_access_policy_blocked`

`/api/live-board-discovery` returns:

- `started=false`
- `blocked=true`
- `mode=live_board_discovery_access_policy_blocked`

`/api/status.raw_refresh` includes:

- `access_policy.status=blocked_by_access_policy`
- `blocker_code=ai_controlled_access_rejected`
- `automated_public_raw_refresh_allowed=false`

## Verification Results

Latest full local test:

```text
python3 -m unittest tab-research-pipeline.tests.test_pipeline
Ran 205 tests in 13.329s
OK
```

Additional checks passed:

- Target regression tests for Team Total manual intake contract generation and API exposure.
- Target regression tests for provider credit runway reserve blocking and command-center API exposure.
- Target regression tests for credit-safe non-Team Total alternate/value-support queue, provider market canonicalization, sample availability counts, and status API exposure.
- Target regression tests for provider event-level selector preference for the alternate plan queue and fallback skipping of previous `event_odds_event_ids`.
- Target regression tests for primary-refresh-inclusive provider credit estimates and fallback skipping of previous event-market probes.
- Target regression tests for The Odds API certifi TLS fallback and historical merge key preservation.
- Target regression tests for The Odds API legacy sport mapping before request construction.
- Target regression tests for Team Total operator cockpit, field checklist, workflow steps, action contract, import quality matrix, next-batch quality diagnostics, and API status exposure.
- Target regression tests for fixed example env fallback, config doctor fallback warning, and Unknown Sport blocked diagnostics.
- Target regression tests for low-yield Team Total fallback, persistent event-probe evidence across primary refresh, provider KPI same-refresh rebuild, stale blocked-attempt labeling, and provider alternate-plan status API.
- Provider config doctor regression tests for key redaction, legacy sport warning, missing env/key blocking, and API status route.
- Target regression tests for historical covered event exclusion, historical event odds merge, requested-market merge filter, blocked provider preservation, and Provider KPI.
- Provider fallback verification queue regression test.
- Provider manual verification template/import regression tests.
- Provider manual verification workbench regression tests; CSV template now covers all 68 candidates without truncation.
- Provider manual hash gate regression coverage.
- Public snapshot import, publish preflight, and explicit raw publish regression tests.
- Provider manual overlay import, publish preflight, and explicit raw publish regression tests.
- Local app status section route regression test for `/api/status.provider_manual_overlay_publish`.
- Python compile checks for changed modules.
- Shell syntax checks for runner scripts.
- Node syntax checks for public raw, live discovery, and My Bets capture scripts.
- Browser smoke: desktop `1280px` and mobile `390px` both show Provider KPI, alternate/value-support plan, history-only blocked label, evidence link, stake `AUD 0`, no console errors, and no horizontal overflow.
- Browser smoke: desktop `1280px` and mobile `390px` both show `Team Total 人工校验队列`, queue `64`, high priority `51`, no-bet/no-click boundary text, and no horizontal overflow.
- Browser smoke: desktop `1280px` and mobile `390px` both show `人工校验导入状态`, CSV template link, `0/64`, `0/51`, stake `AUD 0`, and no horizontal overflow.
- Browser smoke: desktop `1280px` and mobile `390px` both show manual workbench, batch count `9`, next batch `TT-001`, remaining `68`, high priority remaining `55`, pair-template buttons, `16/136`, quality gate `waiting_for_manual_rows`, `missing_rows`, stake `AUD 0`, no console errors, and no horizontal overflow.
- Browser smoke: desktop `1280px` and mobile `390px` both show Hash Gate `waiting_for_import`, Hash Gate PDF link, `approved_by_user false`, stake `AUD 0`, and no horizontal overflow.
- Browser smoke: desktop `1280px` and mobile `390px` both show Overlay 发布 link, `blocked_overlay_publish_preflight`, stake `AUD 0`, safety copy, no console errors, and no horizontal overflow.
- Browser smoke: desktop `1280px` and mobile `390px` both show Public Snapshot Raw发布 link/status, stake `AUD 0`, and no horizontal overflow.
- API smoke: `/api/status.provider_manual_overlay_publish` returns `blocked_overlay_publish_preflight`, `ok=false`, `formal_raw_publish_performed=false`, `raw_batch_manifest_written=false`, and stake `AUD 0`.
- API smoke: `/api/status.provider_manual_workbench` returns `waiting_for_first_batch`, batch count `8`, next batch `TT-001`, remaining `64`, high priority remaining `51`, pair rows `128/16`, and stake `AUD 0`.
- API smoke: `/api/status.provider_config_doctor` returns `ready`, `local_env_exists=true`, keys present redacted, `sports_discovery_enabled=true`, no legacy sport, recommended sport `soccer_fifa_world_cup`, event probe limit `0`, and stake `AUD 0`.
- Node security tests: `refresh_tab_readonly_security.test.mjs`, `capture_tab_my_bets_readonly_security.test.mjs`.
- Local API smoke: missing action token returns `403 invalid_action_token`; valid local token returns raw policy blocked response without starting raw refresh.
- In-app browser smoke: homepage loads at `http://127.0.0.1:8767/`; Provider 采集控制台 is visible with latest refresh `20260613T193148Z-provider-0bf93159`, credit range `4-7`, remaining credits `222`, command order `double_chance,draw_no_bet,btts`, queue `53`, Team Total `0/64`, batch `1`, KPI `61.50%`, and stake `AUD 0`; desktop `1280px` and mobile `390px` have page overflow `0`, console error `0`, and no key-style leak in the DOM.
- API smoke: `/api/status.provider_command_center` returns provider alternate `in_progress`, decision `alternate_probe_plus_team_total_manual`, refresh `20260613T193148Z-provider-0bf93159`, probe queue `53`, batch `1`, estimated credit `4-7`, remaining credits `222`, TT batch `TT-001`, stake `AUD 0`, formal publish `false`, and full automation `false`.
- `git diff --check` OK; tracked secret scan for the known The Odds API key and key-like env assignments has no hits.
- In-app browser smoke: provider config doctor is visible on desktop `1280px` and mobile `390px`; it shows `ready`, Unknown Sport guard enabled, recommended `soccer_fifa_world_cup`, Event Probe `0`, stake `AUD 0`, no horizontal overflow, no console errors, and no key-style leak in the DOM.
- Downloads HTML/assets scanned for old raw-refresh wording.
- App icon verification: `CFBundleIconFile=TABFIFAResearch`; app bundle contains `Contents/Resources/TABFIFAResearch.icns`.
- App icon asset hygiene verified: no `*.iconset/` or `__pycache__/` remains under `tab-research-pipeline/assets/app_icon/`.

## Not Done

- Full formal automation is not ready.
- Official/authorized raw data feed is connected for staged The Odds API Matches research, but not formally publish-ready.
- OpticOdds is not live-configured; full 5/5 provider coverage is not proven.
- User-exported raw snapshot import workflow remains a fallback, not the primary practical path.
- Australia Markets route mismatch remains unresolved.
- My Bets private position import still requires local user authorization.
- The system still uses some planned probability-engineering labels that must not be overstated as completed full xG/MCMC/Monte Carlo production modeling.

## Local Cleanup Summary

- Deleted paths: 397.
- Deleted files: 2952.
- Freed space: 159.72 MiB.
- Root after cleanup: about 70M.
- Local retained core: `work/tab-research-pipeline/`, `outputs/*_latest.*`, `outputs/research_only_raw/`, private My Bets profile non-cache files, and `github_sync/FIFA`.
- GitHub backup archives: `artifacts/backups/tab_fifa_reports_20260613.sqlite3.gz`, `artifacts/backups/public_outputs_without_sqlite_20260613.tar.gz`, `artifacts/backups/legacy_fifa_analysis_db_20260613.sqlite3.gz`.

## Recommended Next Task

Run the next credit-safe provider step:

1. Configure `THE_ODDS_API_KEY` and/or `OPTICODDS_API_KEY` locally through `config/odds_providers.local.env`; never commit real keys.
2. First run `python3 scripts/build_provider_config_doctor.py`; current ignored local env already uses `TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup` and `TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1`.
3. For The Odds API daily primary path, use `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 0`.
4. For the next credit-conservation alternate/value-support batch, use `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 1 --event-odds-limit 1 --event-odds-markets btts,double_chance,draw_no_bet`.
5. Inspect `outputs/odds_provider_coverage_latest.json` for `provider_analysis_ready`, `formal_publish_allowed`, `full_automation_allowed`, and quota usage.
6. Move Team Total to OpticOdds live configuration or TAB manual final-verification workflow. Current fastest manual path is `provider_manual_next_batch_pair_template_latest.csv` for `TT-001`, then save completed rows to `manual_verification/provider_team_total_manual_verification.csv`.
7. Keep region-specific boards ignored unless the user explicitly asks to restore them.
8. Keep executable stake at `AUD 0` unless provider/raw/private/preflight all pass.
