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
