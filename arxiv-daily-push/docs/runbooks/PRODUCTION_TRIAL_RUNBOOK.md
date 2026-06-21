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
`ADP_SCHEDULED_RUN_ENABLED=true` is explicitly configured. This scheduler gate
does not send SMTP mail or upload Releases; those remain separately gated by
the SMTP and Release delivery commands.

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
