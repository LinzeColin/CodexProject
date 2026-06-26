# Serenity-Alipay Development Bug Regression Log

Timestamp: 20260624 - 14:58 CST / 20260624 - 16:58 AEST

Purpose: record repeated production UX/runtime bugs that must not regress in future agent work. This file is part of the GitHub development record for `LinzeColin/CodexProject/Serenity-Alipay`.

## Non-Negotiable Regression Rules

1. Historical data, snapshots, reports, immutable creation timestamps, first pool entry timestamps, and prior analysis records must not be overwritten, regenerated in place, or silently corrected by UI/runtime fixes.
2. A UI action that writes a manual review decision to SQLite is considered processed immediately for that review todo. Background Serenity refresh status must not decide whether the todo remains open.
3. The macOS `.app` launcher must open exactly one final local homepage tab and then exit. It must not keep an `open-serenity` shell process alive.
4. OpenD/MooMoo lifecycle changes must preserve ownership: user-opened processes are never cleaned up; tool-opened processes are cleaned only after the relevant task completes and only when socket readiness/lifecycle state proves it is safe.
5. Manual Review / data quality degradation / no-new-order informational states must not create noisy production email unless the configured urgent action threshold is met.
6. First pool entry facts must be resolved from historical recommendations before insertion. Later runs must not change a fund's original candidate/holding/observation pool entry time, rank, or run id.

## Repeated Bug 1: Manual Review Saved But Todo Remained

- Symptom: clicking `保存复核` displayed that the decision was written to the database, but the same object still appeared in the manual review list after waiting, closing, reopening, or restarting the app.
- Root cause: the open-todo filter treated `manual_review_decision.refresh_status='running'` as not completed. The UI also waited for background Serenity refresh before removing the card, mixing two different states: database decision completion and report refresh completion.
- Correct behavior: any valid saved `outcome` handles that review todo immediately. Valid outcomes are `observe_pool`, `exclude_current_observation`, and `promote_top5_candidate_pool`.
- Fix record:
  - `app/core/application_portal.py::_decision_is_successful()` now treats a saved valid outcome as successful even when `refresh_status='running'`.
  - The frontend removes the saved card immediately through `removeReviewItem()`.
  - Reopening the review modal applies saved decisions through `applyReviewLog()` and hides already handled items.
- Regression shield:
  - `tests/test_reporting_ui.py::test_manual_review_items_hide_saved_running_decision_immediately`.
  - Browser-level validation used intercepted `/api/manual-review` responses and confirmed the card count changed from 12 to 11 without real database mutation.
- Future agent warning: do not re-couple todo completion to full Serenity refresh completion. Refresh updates homepage/report data; the saved manual decision updates review task state.

## Repeated Bug 2: App Entry Opened Two Tabs Or Failed To Enter

- Symptom: clicking `Serenity 每日分析.app` opened two browser tabs or opened a stale local `downloads-entry.html` bootstrap page that did not reliably reach the service homepage.
- Root cause: the launcher first opened a local file bootstrap page and later opened `http://127.0.0.1:$PORT/`, producing duplicate tabs and relying on fragile `file://` JavaScript redirect behavior.
- Correct behavior: the launcher should wait for the local service health check and open only the final homepage URL once.
- Fix record:
  - `app/core/application_portal.py` no longer emits `BOOTSTRAP` / `downloads-entry.html` behavior for the app launcher.
  - The launcher opens only `http://127.0.0.1:$PORT/`.
  - `app/core/application_server.py` supports a lightweight `python -m app.core.application_server` entry path so the launcher does not import heavy CLI modules during startup.
- Regression shield:
  - `tests/test_reporting_ui.py::test_application_bundle_has_custom_icon` checks launcher content, including absence of stale bootstrap/double-open behavior.
  - `tests/test_application_server.py` covers server startup and API routes.
- Future agent warning: do not restore a separate `file://` entry page unless there is a new tested single-tab contract and a clear user-facing reason.

## Repeated Bug 3: Dock Icon Kept Jumping / Launcher Stayed Alive

- Symptom: after opening the app, the Dock icon kept bouncing or the launcher stayed active for a long time even when the web service was already running.
- Root cause: the launcher stored `SERVER_PID` and called `wait "$SERVER_PID"`, so macOS treated `/bin/sh .../open-serenity` as the running app process.
- Correct behavior: the launcher starts the Python server in the background if needed, waits only for health readiness, opens the homepage once, and exits.
- Fix record:
  - The launcher uses `nohup python -m app.core.application_server ... &`.
  - The launcher no longer contains `SERVER_PID` or `wait "$SERVER_PID"`.
  - Hot startup leaves no persistent `open-serenity`; cold startup leaves only the Python local service listening on port 8765.
- Regression shield:
  - Launcher text assertions in `tests/test_reporting_ui.py`.
  - Runtime smoke checks confirmed no long-lived `open-serenity` process after app launch.
- Future agent warning: do not make the macOS app shell supervise the server process by waiting on it. If supervision is needed, implement it in the Python service or a dedicated scheduler contract, not in the foreground launcher.

## Related Stability Fix: Save Review Responsiveness

- Symptom: clicking `保存复核` appeared to do nothing or took too long before visual feedback.
- Root cause: full Serenity refresh and short manual-review writes shared blocking paths, and SQLite write contention could surface as `database is locked`.
- Fix record:
  - `app/db.py` enables WAL and busy timeout behavior.
  - `app/core/application_server.py` separates short review write locks from long refresh locks and returns quickly with background refresh status.
  - `app/core/pipeline.py` uses segmented commits during full runs to reduce lock duration.
- Regression shield:
  - `tests/test_application_server.py` and `tests/test_reporting_ui.py` target the API/UI path.
  - `history-integrity --require-pass --json` must stay `status=pass`.

## Related Stability Fix: Immutable First Pool Entry Facts

- Symptom: a later run could write `asset_pool_entry.first_run_id`, `first_rank`, `first_run_time_bj`, and `first_run_created_at` using the current run even when the asset had already appeared in the same pool historically.
- Root cause: `record_asset_pool_entries()` used only the current `run_id/rank/run_time` before inserting with `INSERT OR IGNORE`; if the backfill path had not already populated the row, the later run became the recorded first entry.
- Correct behavior: before inserting, resolve the earliest matching historical recommendation from `recommendation_snapshot + run_log` for the target pool kind:
  - `candidate_pool`: rank 1-10.
  - `holding_pool`: rank 1-5.
  - `observation_pool`: rank 6-10.
- Fix record:
  - `app/db.py::_first_pool_entry_fact()` now selects the earliest historical fact for the asset and pool kind.
  - `record_asset_pool_entries()` inserts that historical fact and still uses `INSERT OR IGNORE`, so existing immutable rows are not rewritten.
- Regression shield:
  - `tests/test_history_integrity.py::test_asset_pool_entry_keeps_first_holding_pool_entry`.
- Future agent warning: never "repair" first-entry timestamps by recalculating them from the latest run. If historical truth changes because older data is newly imported, handle it through an explicit migration/audit contract, not through normal runtime writes.

## Required Verification Before Marking This Cluster Fixed

Run at minimum:

```bash
python -m py_compile app/db.py app/core/application_server.py app/core/application_portal.py app/core/pipeline.py tests/test_application_server.py tests/test_reporting_ui.py
pytest -q tests/test_reporting_ui.py tests/test_application_server.py tests/test_history_integrity.py
```

Only run `python -m app.cli history-integrity --require-pass --json` when explicitly validating the real historical database, and do not commit the generated `outputs/audit/*latest*` files unless that is the intended deliverable.

For real UI acceptance, verify the installed app opens one homepage tab, no long-lived `open-serenity` process remains, and saving a review item removes it from the visible pending list immediately after SQLite success.
