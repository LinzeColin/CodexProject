# PHASE S1P5T03-R Real arXiv 30 As-Of Replay

## Scope

- Task: `S1P5T03-R REAL_ARXIV_30_DAY_BACKFILL_AND_LEDGER_RECONCILE`
- Acceptance: `ADP-ACC-S1P5T03-REAL-ARXIV-30-ASOF-REPLAY`
- Model: `MOD-ADP-046` / `adp-stage1-real-arxiv-30-asof-replay-v1`
- Evidence level: `EXTRACTED`
- Current status: `PENDING_CLOUD_CI`

## Result Boundary

This task reopens the strict Stage 1 historical evidence gate. The previous
manual delivery tests prove one-time cloud live fetch/rank/generate/send
behavior, but they do not prove 30 historical as-of-date backfill or durable
selected/queued/email ledger closure.

This phase therefore requires a GitHub Actions/cloud-runner artifact before
strict `ARXIV_PRODUCTION_ACCEPTED` can be restored.

## Local Control Run

Local control run completed with the exact command class that the cloud
workflow will run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_real_replay_live2 PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push real-historical-arxiv-replay --generated-at 2026-06-23T21:45:00+10:00 --start-date 2026-05-24 --end-date 2026-06-22 --count 30 --lookback-days 7 --max-results 10 --artifact-dir /tmp/adp-real-replay-20260623 --write --fetcher curl --polite-delay-seconds 3 --json
```

Observed local result:

- status: `pass`
- success_count: `30`
- required_replay_count: `30`
- unique_as_of_date_count: `30`
- unique_selected_source_count: `30`
- real_arxiv_source_id_count: `30`
- future_leakage_count: `0`
- duplicate_lead_count: `0`
- queue_continuity_break_count: `0`
- unsupported_p0_p1_count: `0`
- daily_input_count/report_count/email_preview_count/queue_ledger_count: `30/30/30/30`
- content_ledger_row_count: `299`
- content_ledger_selected_row_count: `30`
- content_ledger_queued_row_count: `269`
- first selected source: `2026-05-24` / `arxiv:2605.25295` / `math.PR`
- last selected source: `2026-06-22` / `arxiv:2606.22272` / `cs.CL`

## Persisted Ledger

`arxiv-daily-push/docs/owner/CONTENT_LEDGER.csv` is no longer the
`NO_PRODUCTION_CONTENT_ROWS_S1_06` placeholder. It now contains the real replay
ledger rows from the local control run:

- total rows: `299`
- selected lead rows: `30`
- queued candidate rows: `269`
- selected rows include `email_state=preview_generated`
- selected and queued rows include artifact references in `report_path` or
  `reason_detail`

The ledger must be compared against the GitHub Actions artifact ledger before
strict acceptance is restored.

## Cloud Evidence Required

The PR workflow `.github/workflows/arxiv-daily-push-real-backfill.yml` must run
on `ubuntu-latest` and upload artifact
`adp-s1p5t03-real-arxiv-30-day-backfill`.

Required artifact files:

- `adp-real-historical-replay-manifest.json`
- `CONTENT_LEDGER.csv`
- `daily_inputs.jsonl`
- `reports.md`
- `email_previews.txt`
- `queue_ledgers.jsonl`
- `run_records.jsonl`

## Evidence Boundary

- No production email is sent.
- No Gmail SMTP send is attempted.
- No GitHub Release upload is attempted.
- No video artifact is generated.
- No production scheduler is enabled.
- No secret values are read, printed, or persisted.
- Stage 2 does not start.
- Email template quality work is out of scope.

## Next Gate

Open PR, wait for all PR CI to pass, inspect the GitHub Actions artifact, and
only then decide whether strict Stage 1 can return to
`ARXIV_PRODUCTION_ACCEPTED`.
