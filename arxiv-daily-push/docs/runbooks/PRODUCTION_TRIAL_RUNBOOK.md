# Production Trial Runbook

Project: `arxiv-daily-push`
Notification recipient: `linzezhang35@gmail.com`
Timezone: `Australia/Sydney`

## Purpose

This runbook prepares the real 30-day Phase 11 trial without claiming that the
trial has already passed. The GitHub workflow is manual-only and runs production
preflight first. A scheduled 05:00 production run must not be enabled until the
preflight artifact proves the runner, SMTP, Release target, disk, memory, Git
artifact hygiene, and local cache gates pass.

## GitHub Setup

Required private self-hosted runner:

- Label: `arxiv-daily-push` by default, or the label passed as the workflow
  `runner_label` input.
- Required commands on runner: `python3`, `git`, `node`, `npm`, `gh`, `ffmpeg`,
  `docker`, and `codex`.
- Python HTTPS certificate validation must work for
  `https://export.arxiv.org/api/query`; do not bypass TLS verification.
- Minimum free disk before production work: 80 GiB.
- Minimum memory before production work: 8 GiB.

Required GitHub Actions secrets:

- `ADP_SMTP_HOST`
- `ADP_SMTP_PORT`
- `ADP_SMTP_USERNAME`
- `ADP_SMTP_PASSWORD`

Required GitHub Actions variables:

- `ADP_RELEASE_TARGET`
- `ADP_PRODUCTION_ENABLED`
- `ADP_SCHEDULED_RUN_ENABLED`
- `ADP_DAILY_INPUT_PATH` optional override; leave empty to build from live arXiv
- `ADP_ARXIV_QUERY` optional; default `cat:cs.AI`
- `ADP_ARXIV_MAX_RESULTS` optional; default `10`
- `ADP_RECENT_SOURCE_IDS` optional comma-separated list of recently selected
  `source_id` values
- `ADP_TRIAL_EVIDENCE_INPUT_PATH` optional existing trial evidence JSON path
  available on the runner
- `ADP_TRIAL_ID` optional; default `adp-trial-current`
- `ADP_TRIAL_REF` required before final trial acceptance can pass
- `ADP_TEXT_DEGRADATION_VERIFIED` optional explicit flag for verified text
  degradation path evidence
- `ADP_VIDEO_DEGRADATION_VERIFIED` optional explicit flag for verified video
  degradation path evidence
- `ADP_ALLOW_SMTP_SEND`
- `ADP_ALLOW_RELEASE_UPLOAD`

The workflow maps only secret names into environment variables. It must not echo
secret values, read `~/.codex/auth.json`, upload Releases, or send SMTP mail.

## Preflight Dispatch

Run the workflow:

```text
arXiv Daily Push production trial bootstrap
```

Use these inputs:

- `confirm_production_trial=true`
- `runner_label=arxiv-daily-push` unless the private runner uses another label
- `mode=preflight-only`
- `generated_at=<ISO timestamp>` optional

Expected first artifact:

```text
adp-production-preflight
```

The artifact must contain a JSON report from:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push preflight-production --path . --generated-at <ISO timestamp> --json
```

If preflight exits non-zero, stop. Do not start the 30-day trial.

## Scheduled Production Gate

The scheduled workflow is:

```text
.github/workflows/arxiv-daily-push-scheduled.yml
```

The workflow declares `timezone: "Australia/Sydney"` and these local schedule
slots:

- `04:45` health check;
- `05:00` daily run gate;
- `05:10` watchdog.

Scheduled runs skip by default unless `ADP_PRODUCTION_ENABLED=true` is set in
GitHub Actions variables. Even after that, the scheduled workflow runs
production preflight first and keeps daily side effects blocked unless
`ADP_SCHEDULED_RUN_ENABLED=true` is explicitly configured. The scheduled
workflow uploads two artifacts:

- `adp-scheduled-preflight`;
- `adp-scheduled-source-batch` for daily-run when no override input path is set;
- `adp-scheduled-daily-input` for daily-run when no override input path is set;
- `adp-scheduled-execution`;
- `adp-trial-ledger-update` for daily-run ledger accumulation attempts.
- `adp-trial-evidence-ledger` after a daily ledger append succeeds.

The execution artifact is produced by:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push run-scheduled-production \
  --mode <health-check|daily-run|watchdog> \
  --generated-at <ISO timestamp> \
  --preflight-report <adp-scheduled-preflight.json> \
  --json
```

Daily runs also require `ADP_DAILY_INPUT_PATH` to point to a small daily input
package, or the workflow builds a daily input report from live arXiv source
ingest using:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push fetch-arxiv-latest --query "${ADP_ARXIV_QUERY:-cat:cs.AI}" --max-results "${ADP_ARXIV_MAX_RESULTS:-10}" --generated-at <ISO timestamp> --json
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-daily-input --source-batch <source-batch.json> --date <YYYY-MM-DD> --generated-at <ISO timestamp> --json
```

The daily input builder uses only arXiv Atom `<summary>` and metadata claims. It
does not download PDFs, perform bulk harvest, or claim peer review from arXiv.
The selected daily input report is used as the initial Release evidence asset.
Dry-run SMTP or dry-run Release results are recorded as `degraded` with
`exit_code=2`; they cannot be counted toward Phase 11 production acceptance.
Production-ready daily evidence requires both real SMTP delivery and real
private Release creation to return evidence refs.

After a daily-run execution artifact exists, the scheduled workflow attempts to
append it to the trial evidence ledger with:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push update-trial-ledger \
  --scheduled-execution <adp-scheduled-execution.json> \
  --generated-at <ISO timestamp> \
  --trial-id "${ADP_TRIAL_ID:-adp-trial-current}" \
  --trial-ref "${ADP_TRIAL_REF:-}" \
  --json
```

When `ADP_TRIAL_EVIDENCE_INPUT_PATH` is set, the command also reads the existing
trial evidence JSON and appends one new daily entry. The ledger updater refuses
dry-run or degraded non-production evidence, duplicate daily dates, duplicate
source IDs, duplicate publication IDs, missing P0 traceability, unsupported
claim publication, misleading failure output, and missing daily Release/SMTP/
resource refs. It can record daily Release/SMTP/resource evidence from
production-ready scheduled execution, but it does not mark weekly/monthly replay
or recovery drill evidence complete unless those later evidence refs are
explicitly supplied.

If `ADP_TRIAL_EVIDENCE_INPUT_PATH` is not set, the workflow tries to restore the
previous successful run's `adp-trial-evidence-ledger` artifact using `gh run
download` with the workflow `GITHUB_TOKEN`. After a successful append, it exports
the updated `trial_evidence` object with:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push export-trial-ledger-state \
  --ledger-update <adp-trial-ledger-update.json> \
  --json
```

The exported state is uploaded as `adp-trial-evidence-ledger` and is the default
carry-forward input for later scheduled daily runs. If the ledger update blocks,
the state export also blocks and no replacement state artifact is uploaded.

After weekly replay, monthly replay, or recovery drill evidence exists, do not
hand-edit the trial evidence JSON. For weekly/monthly replay, first build a
replay evidence report from the accumulated trial ledger and archive that report
as a durable artifact or Release ref:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-trial-replay-evidence \
  --path <trial-evidence.json> \
  --generated-at <ISO timestamp> \
  --weekly-replay \
  --monthly-replay \
  --replay-ref <weekly-monthly-evidence-ref> \
  --json
```

The replay command validates production-ready daily refs, duplicate-free
coverage, at least 7 consecutive days for weekly replay, at least 30 consecutive
days for monthly replay, and a non-empty durable ref. It does not create Release
assets, send email, generate media, or mutate the trial ledger.

For recovery drill evidence, first archive both the failed/degraded scheduled
daily-run report and the recovered production-ready rerun report. Then build the
recovery evidence report:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-trial-recovery-evidence \
  --failure-execution <failed-or-degraded-scheduled-execution.json> \
  --recovery-execution <recovered-scheduled-execution.json> \
  --generated-at <ISO timestamp> \
  --failure-ref <failure-evidence-ref> \
  --recovery-ref <recovery-evidence-ref> \
  --json
```

The recovery command requires a real sent failure notification, a recovered
`production_evidence_ready=true` daily-run report with daily run, Release, SMTP,
and resource refs, and durable failure/recovery refs. It does not rerun the
scheduler, send mail, upload Releases, mutate the trial ledger, or claim
production acceptance.

Then merge the explicit evidence refs with:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push annotate-trial-ops-evidence \
  --path <trial-evidence.json> \
  --generated-at <ISO timestamp> \
  --weekly-replay-verified \
  --monthly-replay-verified \
  --weekly-monthly-ref <weekly-monthly-evidence-ref> \
  --recovery-drill-verified \
  --recovery-ref <recovery-drill-evidence-ref> \
  --json
```

The command can also merge explicit scheduler, manual rerun, Release, SMTP, and
resource refs when those are produced outside the daily ledger update. It blocks
verified flags without refs and does not generate weekly/monthly reports,
recovery drills, SMTP sends, Releases, or production acceptance claims.

To carry the annotated state forward without local persistence, export the state
only from a passing annotation report:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push export-trial-ops-state \
  --ops-update <trial-ops-update.json> \
  --json
```

Validate the scheduled workflow contract locally or on the runner:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-scheduler --path . --generated-at <ISO timestamp> --json
```

Before enabling scheduled source collection, verify live arXiv source ingest:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push fetch-arxiv-latest --query 'cat:cs.AI' --max-results 1 --generated-at <ISO timestamp> --json
```

If this blocks on Python SSL certificate validation, update the runner CA trust
store or Python certificate bundle. Do not switch to insecure TLS behavior.

After source ingest succeeds, verify daily input construction with the emitted
source batch:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-daily-input --source-batch <source-batch.json> --date <YYYY-MM-DD> --generated-at <ISO timestamp> --json
```

If this blocks on missing Atom summary, duplicate recent source ID, metadata
conflict, or missing P0 evidence, stop the daily run and inspect the uploaded
`adp-scheduled-source-batch` and `adp-scheduled-daily-input` artifacts.

Before enabling real notification sending, verify the SMTP delivery boundary in
dry-run mode:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push send-notification \
  --run-id adp-notification-probe \
  --summary "SMTP delivery boundary probe" \
  --date <YYYY-MM-DD> \
  --generated-at <ISO timestamp> \
  --json
```

Real SMTP sending is allowed only after production preflight passes and the SMTP
secrets are configured. Use the explicit flag so accidental dispatches fail
closed by default:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push send-notification \
  --run-id adp-notification-probe \
  --summary "SMTP delivery boundary probe" \
  --date <YYYY-MM-DD> \
  --generated-at <ISO timestamp> \
  --allow-send \
  --json
```

The delivery report must be archived as evidence. It records the recipient,
subject, body SHA256, delivery status, and configured key names only; it must not
log SMTP secret values or the email body.

Before enabling private Release creation, verify the Release delivery boundary
in dry-run mode with a small metadata/report asset:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push publish-release \
  --tag adp-release-probe-<YYYYMMDD> \
  --title "arXiv Daily Push release probe" \
  --notes "Release delivery boundary probe" \
  --asset <trial-evidence-or-run-record.json> \
  --generated-at <ISO timestamp> \
  --json
```

Real GitHub Release creation is allowed only after production preflight passes,
`ADP_RELEASE_TARGET` is configured, and the asset list has passed the local
secret/model suffix and size gates. Use an explicit flag; published Releases
also require `--publish` because draft is the default:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push publish-release \
  --tag adp-release-probe-<YYYYMMDD> \
  --title "arXiv Daily Push release probe" \
  --notes-file <release-notes.md> \
  --asset <trial-evidence-or-run-record.json> \
  --generated-at <ISO timestamp> \
  --allow-upload \
  --json
```

The Release delivery report must be archived as evidence. It records asset
names, sizes, SHA256 values, tag, target, and a redacted command preview only.
It must not log Release notes text, secret values, `gh` stdout, or `gh` stderr.

## Trial Evidence

After production side effects are explicitly enabled in a later controlled step,
collect one evidence entry for each daily run. The final evidence package must
cover at least 30 unique daily dates and then pass:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push evaluate-trial --path <trial-evidence.json> --generated-at <ISO timestamp> --json
```

The package must prove:

- no duplicate daily publication;
- key P0 claims are traceable;
- failures do not generate misleading content;
- 05:00 scheduler evidence and manual rerun evidence exist;
- private Release or equivalent publishing evidence exists;
- real SMTP evidence to `linzezhang35@gmail.com` exists;
- weekly and monthly replay evidence exists;
- recovery drill evidence exists;
- disk, memory, cache, Git artifact, and secret hygiene evidence exists.

Only a passing `adp-trial-evidence-v1` report can be used by `build-acceptance`
to mark production acceptance as complete.

## Current Boundary

The bootstrap workflow does not schedule production, upload a Release, send
SMTP mail, render media, download models, or claim 30-day acceptance. It is a
pre-production gate for starting the real trial safely.
